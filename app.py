from flask import Flask, request, jsonify, Response, send_file
import base64
from requests.utils import requote_uri
"""app.main: handle request for lambda-tiler"""

import re
import json

import numpy as np
from flask_compress import Compress
from flask_cors import CORS

from rio_tiler import main
from rio_tiler.utils import (array_to_image,
                             linear_rescale,
                             get_colormap,
                             expression,
                             mapzen_elevation_rgb)

from src import cmap
from src import elevation as ele_func
from src import value as get_value
from src import response
from src import profile as get_profile

import time
import gzip
# from lambda_proxy.proxy import API


class TilerError(Exception):
    """Base exception class."""


app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app)

app.config['COMPRESS_MIMETYPES'] = ['text/html', 'text/css', 'text/xml',
                                    'application/json',
                                    'application/javascript',
                                    'image/png',
                                    'image/PNG',
                                    'image/jpg',
                                    'imgae/jpeg',
                                    'image/JPG',
                                    'image/JPEG']
app.config['COMPRESS_LEVEL'] = 9
app.config['COMPRESS_MIN_SIZE'] = 0
Compress(app)


# Welcome page
@app.route('/')
def hello():
    return "Welcome to, Indshine COG API!"


# Generates bounds of Raster data
@app.route('/api/v1/bounds', methods=['GET'])
def bounds():
    """Handle bounds requests."""
    url = request.args.get('url', default='', type=str)
    url = requote_uri(url)

    # address = query_args['url']
    info = main.bounds(url)
    return (jsonify(info))


# Generates metadata of raster
@app.route('/api/v1/metadata', methods=['GET'])
def metadata():
    """Handle metadata requests."""
    url = request.args.get('url', default='', type=str)
    url = requote_uri(url)

    # address = query_args['url']
    info = main.metadata(url)
    return (jsonify(info))


# Generate PNG/JPEG tiles of the given tile from raster
@app.route('/api/v1/tiles/<int:tile_z>/<int:tile_x>/<int:tile_y>', methods=['GET'])
@app.route('/api/v1/tiles/<int:tile_z>/<int:tile_x>/<int:tile_y>.<tileformat>', methods=['GET'])
def tile(tile_z, tile_x, tile_y, tileformat='png'):

    # Rendering only if zoom level is greater than 9
    if int(tile_z) < 9:
        return Response(None)

    """Handle Tile requests."""
    if tileformat == 'jpg':
        tileformat = 'jpeg'

    # query_args = APP.current_request.query_params
    # query_args = query_args if isinstance(query_args, dict) else {}

    url = request.args.get('url', default='', type=str)
    url = requote_uri(url)

    colormap = request.args.get('cmap', default='majama', type=str)
    min_value = request.args.get('min', type=float)
    max_value = request.args.get('max', type=float)
    nodata = request.args.get('nodata', default=-9999, type=float)
    tilesize = request.args.get('tile', 256)
    indexes = request.args.get('indexes')
    numband = request.args.get('numband', type=int)
    scale = request.args.get('scale', default=1, type=int)
    scale = int(scale)

    if not url:
        raise TilerError("Missing 'url' parameter")
    if indexes:
        indexes = tuple(int(s) for s in re.findall(r'\d+', indexes))

    tilesize = int(tilesize) if isinstance(tilesize, str) else tilesize

    if nodata is not None:
        nodata = int(nodata)

    if numband is not None:
        numband = int(numband)

    if numband == 3 or numband == 4:
        st_time = time.time()
        tile, mask = main.tile(url,
                               tile_x,
                               tile_y,
                               tile_z,
                               indexes=indexes,
                               tilesize=tilesize*scale,
                               nodata=None,
                               resampling_method="cubic_spline")

        end_time = time.time()
        print('Reading time: ', end_time-st_time)

        # Converting it to Unsigned integer 8 bit if not.
        tile = np.uint8(tile)

        # Convering from array to image bytes type
        # img = array_to_image(tile)
        img = response.array_to_img(
            arr=tile, tilesize=tilesize, scale=scale, tileformat=tileformat)

    elif numband == 1:
        st_time = time.time()
        tile, mask = main.tile(url,
                               tile_x,
                               tile_y,
                               tile_z,
                               indexes=indexes,
                               tilesize=tilesize*scale,
                               nodata=nodata,
                               resampling_method="cubic_spline")

        end_time = time.time()
        print('Reading time: ', end_time-st_time)

        # Coloring 1 dimension array to 3 dimension color array
        color_arr = ele_func.jet_colormap(
            tile[0, :, :], arr_min=min_value, arr_max=max_value, colormap=colormap, mask=mask, nodata=nodata)

        # Remapping [row, col, dim] to [dim, row, col] format
        color_arr = ele_func.remap_array(arr=color_arr)
        # img = array_to_image(arr=color_arr)
        img = response.array_to_img(
            arr=color_arr, tilesize=tilesize, scale=scale, tileformat=tileformat)

    return Response(img, mimetype='image/%s' % (tileformat))


# Gives data value from raster
@app.route('/api/v1/value', methods=['GET'])
def value():
    """Handle Value requests."""
    url = request.args.get('url', default='', type=str)
    url = requote_uri(url)

    x = request.args.get('x', type=float)
    y = request.args.get('y', type=float)
    # address = query_args['url']
    info = get_value.get_value(address=url, coord_x=x, coord_y=y)
    return (jsonify(info))


# Generates elevation/data profile from raster
@app.route('/api/v1/profile', methods=['GET'])
def profile():
    """Handle Elevation profile requests."""
    url = request.args.get('url', default='', type=str)
    step = request.args.get('step', default=0.30, type=float)

    url = requote_uri(url)

    # Gives an list of string
    x = request.args.get('x')
    y = request.args.get('y')

    x = np.array(x.split(','), dtype=float)
    y = np.array(y.split(','), dtype=float)

    print('data:', x)
    print('length:', len(x))

    coord_x = []
    coord_y = []

    # Checking length of x and y
    if len(x) != len(y):
        return Response('Error: Length of X and Y parameters are not equal')

    elif len(x) < 2:
        return Response('Error: Length of parameters should be greater than 1')

    for i in range(len(x)-1):
        print('Generating line from points')
        temp_x, temp_y = get_profile.get_point2line(
            x[i], y[i], x[i+1], y[i+1], step=step)

        if temp_x is None or temp_y is None:
            return ('Error: Distance between points should be less than 10KM')

        for j in range(len(temp_x)):
            coord_x.append(temp_x[j])
            coord_y.append(temp_y[j])

    print('Generated %d number of points' % (len(coord_x)))
    # Initializing dataset
    data = []
    info = get_value.get_value(
        address=url, coord_x=coord_x, coord_y=coord_y)
    return (jsonify(info))


@app.route('/api/v1/favicon.ico', methods=['GET'])
def favicon():
    """Favicon."""
    output = {}
    output['status'] = '205'  # Not OK
    output['type'] = 'text/plain'
    output['data'] = ''
    return (json.dumps(output))


if __name__ == '__main__':
    app.run(debug=True, threaded=True)


"""
Status Codes :

200 OK
    Standard response for successful HTTP requests. The actual response will depend on the request method used. In a GET request, the response will contain an entity corresponding to the requested resource. In a POST request, the response will contain an entity describing or containing the result of the action.[9]
201 Created
    The request has been fulfilled, resulting in the creation of a new resource.[10]
202 Accepted
    The request has been accepted for processing, but the processing has not been completed. The request might or might not be eventually acted upon, and may be disallowed when processing occurs.[11]
203 Non-Authoritative Information (since HTTP/1.1)
    The server is a transforming proxy (e.g. a Web accelerator) that received a 200 OK from its origin, but is returning a modified version of the origin's response.[12][13]
204 No Content
    The server successfully processed the request and is not returning any content.[14]
205 Reset Content
    The server successfully processed the request, but is not returning any content. Unlike a 204 response, this response requires that the requester reset the document view.[15]
206 Partial Content (RFC 7233)
    The server is delivering only part of the resource (byte serving) due to a range header sent by the client. The range header is used by HTTP clients to enable resuming of interrupted downloads, or split a download into multiple simultaneous streams.[16]
207 Multi-Status (WebDAV; RFC 4918)
    The message body that follows is by default an XML message and can contain a number of separate response codes, depending on how many sub-requests were made.[17]
208 Already Reported (WebDAV; RFC 5842)
    The members of a DAV binding have already been enumerated in a preceding part of the (multistatus) response, and are not being included again.
226 IM Used (RFC 3229)
    The server has fulfilled a request for the resource, and the response is a representation of the result of one or more instance-manipulations applied to the current instance.
    """
