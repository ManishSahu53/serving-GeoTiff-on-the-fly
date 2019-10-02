from flask import Flask, request, jsonify, Response, send_file
import base64
from requests.utils import requote_uri
import requests

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
from src import stats as get_stats
from src import index as get_index
from src import satellite as satelliteobj
from src import exception as excep
from src import extract
from src import thumbnail as get_thumbnail
from src import timeline as get_timeline

import support
import time
import gzip
import datetime
import gconfig


import threading
import multiprocessing as mp
from multiprocessing import Process, Manager

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
    return "Welcome to, COG API!"


# Generates bounds of Raster data
@app.route('/api/v1/bounds', methods=['GET'])
def bounds():
    """Handle bounds requests."""
    url = request.args.get('url', default='', type=str)
    url = requote_uri(url)
    satellite = request.args.get('satellite', default='l8', type=str)

    # address = query_args['url']
    # Checking satellite requested
    if satellite.lower() == 's2':
        satellite_data = satelliteobj.sentinel2(base_json=url)

    elif satellite.lower() == 'l8':
        satellite_data = satelliteobj.landsat8(base_json=url)

    else:
        satellite_data = {
            'status': '404',
            'body': 'Satellite %s is not available' % (satellite)
        }
        return jsonify(satellite_data)

    url = satellite_data.path_band['b1']
    print(url)

    try:
        info = main.bounds(url)
    except Exception as e:
        return jsonify(excep.general(e))

    return (jsonify(info))


# Generates metadata of raster
@app.route('/api/v1/metadata', methods=['GET'])
def metadata():
    """Handle metadata requests."""
    url = request.args.get('url', default='', type=str)
    url = requote_uri(url)

    # address = query_args['url']
    try:
        info = main.metadata(url)
    except Exception as e:
        return excep.general(e)

    return (jsonify(info))


# Generate PNG/JPEG tiles of the given tile from raster
@app.route('/api/v1/index/<int:tile_z>/<int:tile_x>/<int:tile_y>', methods=['GET'])
@app.route('/api/v1/index/<int:tile_z>/<int:tile_x>/<int:tile_y>.<tileformat>', methods=['GET'])
def index(tile_z, tile_x, tile_y, tileformat='png'):
    if int(tile_z) < 5:
        data = {
            'status': '404',
            'body': 'Zoom level should be greater than 5'
        }
        return jsonify(data)

    url = request.args.get('url', default='', type=str)
    url = requote_uri(url)

    colormap = request.args.get('cmap', default='blue', type=str)
    min_value = request.args.get('min', default=0, type=float)
    max_value = request.args.get('max', default=1, type=float)
    nodata = request.args.get('nodata', default=0, type=float)
    tilesize = request.args.get('tile', 256)
    indexes = request.args.get('indexes')
    scale = request.args.get('scale', default=1, type=int)
    index = request.args.get('index', default='ndvi', type=str)
    satellite = request.args.get('satellite', default='l8', type=str)

    # Converting to standard formats
    index = index.lower()
    scale = int(scale)
    tilesize = int(tilesize) if isinstance(tilesize, str) else tilesize

    # If critical inputs are not defined then throw out error
    if not url:
        data = {
            'status': '404',
            'body': "Missing 'url' parameter"
        }
        return jsonify(data)

    if url[-4:].lower() != 'json':
        msg = 'url object must be STAC JSON object'
        return excep.general(msg)

    if indexes:
        indexes = tuple(int(s) for s in re.findall(r'\d+', indexes))

    if tileformat == 'jpg':
        tileformat = 'jpeg'

    if not satellite.lower() in support.SATELLITE_SUPPORTED:
        data = {
            'status': '404',
            'body': 'Satellite %s is not available' % (satellite)
        }
        return jsonify(data)

    # If defined the making sure it is in suitable data type
    if nodata is not None:
        nodata = int(nodata)

    # Starting reading timer
    st_time = time.time()

    # Checking satellite requested
    if satellite.lower() == 's2':
        satellite_data = satelliteobj.sentinel2(base_json=url)

    elif satellite.lower() == 'l8':
        satellite_data = satelliteobj.landsat8(base_json=url)
        tilesize = 512
    else:
        satellite_data = {
            'status': '404',
            'body': 'Satellite %s is not available' % (satellite)
        }
        return jsonify(satellite_data)

    # Getting particular index tile

    try:
        tile, mask = satellite_data.get_tile_index(index=index, tile_x=tile_x, tile_y=tile_y, tile_z=tile_z,
                                                   indexes=indexes, tilesize=tilesize, scale=scale, nodata=nodata,
                                                   resampling_method='nearest')
    # Handling exceptions
    except Exception as e:
        return excep.general(e)

    if tile is None:
        data = {
            'status': '404',
            'body': 'This %s is not compatible. Only NDVI, NDWI, NDDI is compatile' % (index)
        }
        return jsonify(data)

    # Endind timer here
    end_time = time.time()
    print('Reading time: ', end_time-st_time)

    # Getting number of bands
    numband = tile.shape[0]

    # Coloring 1 dimension array to 3 dimension color array
    if numband == 1:
        try:
            color_arr = ele_func.jet_colormap(
                tile[0, :, :], arr_min=min_value, arr_max=max_value, colormap=colormap, mask=mask, nodata=nodata)

            # Remapping [row, col, dim] to [dim, row, col] format
            tile = ele_func.remap_array(arr=color_arr)

        except Exception as e:
            print(e)
            return excep.general(e)

    elif numband == 3 or numband == 4:
        tile = np.uint8(tile)

    else:
        data = {
            'status': '404',
            'body': 'Number of bands allowed are 0, 3, 4. Given %d bands' % (numband)
        }
        return jsonify(data)

    # Converting 3 band array to image format in base64 encoding
    img = response.array_to_img(
        arr=tile, tilesize=tilesize, scale=scale, tileformat=tileformat, mask=mask)

    return Response(img, mimetype='image/%s' % (tileformat))


# Generate PNG/JPEG tiles of the given tile from raster
@app.route('/api/v1/tiles/<int:tile_z>/<int:tile_x>/<int:tile_y>', methods=['GET'])
@app.route('/api/v1/tiles/<int:tile_z>/<int:tile_x>/<int:tile_y>.<tileformat>', methods=['GET'])
def tiles(tile_z, tile_x, tile_y, tileformat='png'):

    url = request.args.get('url', default='', type=str)
    url = requote_uri(url)

    nodata = request.args.get('nodata', default=-9999, type=float)
    tilesize = request.args.get('tile', 256)
    indexes = request.args.get('indexes')
    scale = request.args.get('scale', default=1, type=int)
    numband = request.args.get('numband', default=3, type=int)

    min_value = request.args.get('min', default=0, type=int)
    max_value = request.args.get('max', default=1, type=int)
    colormap = request.args.get('cmap', default='green', type=str)
    satellite = request.args.get('satellite', default='l8', type=str)

    # Converting to standard formats
    scale = int(scale)
    tilesize = int(tilesize) if isinstance(tilesize, str) else tilesize
    if nodata is not None:
        nodata = int(nodata)
    if numband is not None:
        numband = int(numband)

    # If critical inputs are not defined then throw out error
    if not url:
        return excep.general('URL parameter Missing')
    if indexes:
        indexes = tuple(int(s) for s in re.findall(r'\d+', indexes))
    if tileformat == 'jpg':
        tileformat = 'jpeg'

    if numband == 3 or numband == 4:
        # Defining formula for true color
        true_color = url + 'TCI.tif'

        # Starting timers
        st_time = time.time()

        # Reading data from url
        tile, mask = main.tile(true_color,
                               tile_x,
                               tile_y,
                               tile_z,
                               indexes=indexes,
                               tilesize=tilesize*scale,
                               nodata=nodata,
                               resampling_method="nearest")

        # Endind timer
        end_time = time.time()
        print('Reading time: ', end_time-st_time)

        # Converting to uint8 array type
        tile = np.uint8(tile)

        # Converting array to image type in base64 encoding
        img = response.array_to_img(
            arr=tile, tilesize=tilesize, scale=scale, tileformat=tileformat)

    # Converting one band dataset to colorband
    elif numband == 1:
        tile, mask = main.tile(url,
                               tile_x,
                               tile_y,
                               tile_z,
                               indexes=indexes,
                               tilesize=tilesize*scale,
                               nodata=nodata,
                               resampling_method="cubic_spline")

        # Coloring 1 dimension array to 3 dimension color array
        color_arr = ele_func.jet_colormap(
            tile[0, :, :], arr_min=min_value, arr_max=max_value, colormap=colormap, mask=mask, nodata=nodata)

        # Remapping [row, col, dim] to [dim, row, col] format
        color_arr = ele_func.remap_array(arr=color_arr)
        img = response.array_to_img(
            arr=color_arr, tilesize=tilesize, scale=scale, tileformat=tileformat, mask=mask)

    return Response(img, mimetype='image/%s' % (tileformat))


# Gives data stats from raster
@app.route('/api/v1/stats', methods=['GET'])
def stats():
    """Handle Value requests."""
    url = request.args.get('url', default='', type=str)
    url = requote_uri(url)

    # If critical inputs are not defined then throw out error
    if not url:
        raise TilerError("Missing 'url' parameter")

    # If shapefile is not given then compute using coordinates
    print('Calculating statistics using Coordinates')
    # Gives an list of string
    x = request.args.get('x')
    y = request.args.get('y')

    x = np.array(x.split(','), dtype=float)
    y = np.array(y.split(','), dtype=float)

    # Name of Satellite
    satellite = request.args.get('satellite', default='l8', type=str)
    satellite = satellite.lower()

    index = request.args.get('index', default='ndvi', type=str)


    # If critical inputs are not defined then throw out error
    if len(x) != len(y):
        raise TilerError(
            'Number of Latitudes and Longitudes given are not same')

    if not url:
        data = {
            'status': '404',
            'body': "Missing 'url' parameter"
        }
        return jsonify(data)

    if url[-4:].lower() != 'json':
        msg = 'url object must be STAC JSON object'
        return excep.general(msg)

    if not satellite in support.SATELLITE_SUPPORTED:
        data = {
            'status': '404',
            'body': 'Satellite %s is not available' % (satellite)
        }
        return jsonify(data)

     # Checking satellite requested
    if satellite.lower() == 's2':
        satellite_data = satelliteobj.sentinel2(base_json=url)

    elif satellite.lower() == 'l8':
        satellite_data = satelliteobj.landsat8(base_json=url)
    else:
        satellite_data = {
            'status': '404',
            'body': 'Satellite %s is not available' % (satellite)
        }
        return jsonify(satellite_data)

    st_time = time.time()

    try:
        stats, msg = satellite_data.get_stats_index(coord_x=x, coord_y=y, index=index)
    except Exception as e:
        msg = 'Cound not get statistcs: %s, from url: %s. %s' % (index, url, e)
        return excep.general(msg)

    end_time = time.time()
    print('Total Time taken to get statistics : %s secs '%(end_time-st_time))

    if stats is None:
        return excep.general(msg)

    return jsonify(stats)


# Gives index data value from raster
@app.route('/api/v1/value', methods=['GET'])
def value():
    """Handle Value requests."""
    # Base URL of the dataset
    url = request.args.get('url', default='', type=str)
    url = requote_uri(url)

    index = request.args.get('index', default='ndvi', type=str)
    index = index.lower()

    # Number of coordinates
    x = request.args.get('x')
    y = request.args.get('y')

    x = np.array(x.split(','), dtype=float)
    y = np.array(y.split(','), dtype=float)

    # Name of Satellite
    satellite = request.args.get('satellite', default='l8', type=str)
    satellite = satellite.lower()

    # If critical inputs are not defined then throw out error
    if not url:
        data = {
            'status': '404',
            'body': "Missing 'url' parameter"
        }
        return jsonify(data)

    if url[-4:].lower() != 'json':
        msg = 'url object must be STAC JSON object'
        return excep.general(msg)

    if not satellite in support.SATELLITE_SUPPORTED:
        data = {
            'status': '404',
            'body': 'Satellite %s is not available' % (satellite)
        }
        return jsonify(data)

    # Checking satellite requested
    if satellite.lower() == 's2':
        satellite_data = satelliteobj.sentinel2(base_json=url)

    elif satellite.lower() == 'l8':
        satellite_data = satelliteobj.landsat8(base_json=url)
    else:
        satellite_data = {
            'status': '404',
            'body': 'Satellite %s is not available' % (satellite)
        }
        return jsonify(satellite_data)

    st_time = time.time()

    # Reading satellite dataset
    try:
        info = satellite_data.get_value_index(
            coord_x=x, coord_y=y, index=index)

    except Exception as e:
        msg = 'Cound not process index: %s, from url: %s. %s' % (index, url, e)
        return excep.general(msg)

    # If info data is None
    if info is None:
        msg = 'Cound not process index: %s, from url: %s. Make sure the index exist' % (
            index, url)
        return excep.general(msg)

    end_time = time.time()
    print('Total Time taken : %s secs' % (end_time - st_time))

    return (jsonify(info))


@app.route('/api/v1/timeline', methods=['GET'])
def timeline():
    """Handle Value requests."""
    # Base URL of the dataset
    table_name = request.args.get(
        'table_name', default='satellite_dataset', type=str)
    table_name = table_name.lower()

    index = request.args.get('index', default='ndvi', type=str)
    index = index.lower()

    # Number of coordinates
    x = request.args.get('x')  # Logitude
    y = request.args.get('y')  # Latitude

    x = np.array(x.split(','), dtype=float)
    y = np.array(y.split(','), dtype=float)

    # Name of Satellite
    satellite = request.args.get('satellite', default='l8', type=str)
    satellite = satellite.lower()

    # Default dates should be one week from today's date
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=7)

    start_date = request.args.get(
        'start_date', default=str(week_ago), type=str)
    end_date = request.args.get('end_date', default=str(today), type=str)

    # If critical inputs are not defined then throw out error
    if not satellite in support.SATELLITE_SUPPORTED:
        data = {
            'status': '404',
            'body': 'Satellite %s is not available' % (satellite)
        }
        return jsonify(data)

    # x is longitude in searchapi and y is latitude
    payload = (('start_date', start_date), ('end_date', end_date),
               ('satellite', satellite), ('table_name', table_name),
               ('x', x), ('y', y))

    r = requests.get(gconfig.SEARCH_API, params=payload)
    response = r.json()
    dates = list(response.keys())

    manager = Manager()
    temp = manager.dict()

    data = {
        'index': index
    }
    data['data'] = {}

    processes = list()
    for i in range(len(dates)):
        url = response[dates[i]]
        process = Process(target=get_timeline.get_lambda, args=(dates[i], url, satellite, index, x, y, temp, ))
        process.start()
        processes.append(process)
    
    for process in processes:
        process.join()
    
    # threads = []
    # for i in range(len(dates)):
    #     url = response[dates[i]]
    #     t = threading.Thread(target=get_timeline.get_lambda, args=(dates[i], url, satellite, index, x, y, temp))
    #     threads.append(t)
    #     t.start()

    # for tt in threads:
    #     tt.join()

    data['data'] = dict(temp)
    return jsonify(data)


@app.route('/api/v1/thumbnail', methods=['GET'])
def thumbnail():
    """Handle Value requests."""
    # Base URL of the dataset
    table_name = request.args.get(
        'table_name', default='satellite_dataset', type=str)
    table_name = table_name.lower()

    index = request.args.get('index', default='ndvi', type=str)
    index = index.lower()

    farmid = request.args.get('farmid', default='', type=str)

    # Number of coordinates
    x = request.args.get('x')  # Logitude
    y = request.args.get('y')  # Latitude

    x = np.array(x.split(','), dtype=float)
    y = np.array(y.split(','), dtype=float)

    # Name of Satellite
    # satellite = request.args.get('satellite', default='s2', type=str)
    # satellite = satellite.lower()
    satellite = 'l8' # Currently fixed

    start_date = request.args.get(
        'start_date', default='2019-01-01', type=str)
    
    end_date = request.args.get('end_date', default='2019-07-01', type=str)

    # If critical inputs are not defined then throw out error
    if not satellite in support.SATELLITE_SUPPORTED:
        data = {
            'status': '500',
            'body': 'Satellite %s is not available' % (satellite)
        }
        return jsonify(data)

    if not farmid:
        data = {
            'status': '500',
            'body': 'farmid not given'
        }
        return jsonify(data)
    
    if len(x) != len(y):
        data = {
            'status': '500',
            'body': 'Length of X and Y is not same. Check Inputs' % (satellite)
        }
        return jsonify(data)

    # x is longitude in searchapi and y is latitude
    payload = (('start_date', start_date), ('end_date', end_date),
               ('satellite', satellite), ('table_name', table_name),
               ('x', x), ('y', y))

    r = requests.get(gconfig.SEARCH_API, params=payload)
    response = r.json()
    dates = list(response.keys())

    manager = Manager()
    data = manager.dict()

    # multiprocessing POST
    processes = list()
    for i in range(len(dates)):
        date = dates[i]
        stac_url = response[date]
        process = Process(target=get_thumbnail.get_thumbnail, args=(data, date, stac_url, satellite, x, y, farmid, index, ))
        process.start()
        processes.append(process)
    
    for process in processes:
        process.join()

    data = dict(data)
    return jsonify(data)


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


@app.route('/api/v1/favicon.ico', methods=['GET'])
def favicon():
    """Favicon."""
    output = {}
    output['status'] = '205'  # Not OK
    output['type'] = 'text/plain'
    output['data'] = ''
    return (json.dumps(output))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)


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
