from sanic import Sanic
from sanic import response as Response
from requests.utils import requote_uri
from rio_tiler import main
from asgiref.sync import sync_to_async
import re
import numpy as np

from rio_tiler import main
from rio_tiler.utils import array_to_image

from src import cmap
from src import elevation as ele_func
from src import value as get_value
from src import response

import time

app = Sanic()


def get_query(request, param, default, datatype):
    try:
        data = request.args[param][0]
    except:
        data = default

    if data is None:
        return data
    else:
        return datatype(data)


@app.route("/")
async def hello(request):
    # request.args is a dict where each value is an array.
    return Response.text("Welcome to Indshine COG API")


@app.route("/bounds")
async def bounds(request):
    url = get_query(request, param='url',
                    default='www.indshine.com', datatype=str)
    print('hit bounds')
    url = requote_uri(url)
    info = await sync_to_async(main.bounds)(url)
    print('completed bounds')
    return Response.json(info)


@app.route("/metadata")
async def metadata(request):
    url = get_query(request, param='url',
                    default='www.indshine.com', datatype=str)
    print('hit metadata')
    url = requote_uri(url)
    info = await sync_to_async(main.metadata)(url)
    print('completed metadata')
    return Response.json(info)


@app.route('/tiles/<tile_z:int>/<tile_x:int>/<tile_y:int>', methods=['GET'])
@app.route('/tiles/<tile_z:int>/<tile_x:int>/<tile_y:int>.<tileformat>', methods=['GET'])
async def tile(request, tile_z, tile_x, tile_y, tileformat='png'):
    print('hit tiles')
    # Rendering only if zoom level is greater than 9
    if int(tile_z) < 9:
        return Response(None)

    """Handle tile requests."""
    if tileformat == 'jpg':
        tileformat = 'jpeg'

    # query_args = APP.current_request.query_params
    # query_args = query_args if isinstance(query_args, dict) else {}

    url = get_query(request, param='url',
                    default='www.indshine.com', datatype=str)
    url = requote_uri(url)

    colormap = get_query(request, param='cmap', default='majama', datatype=str)
    min_value = get_query(request, param='min', default=None, datatype=float)
    max_value = get_query(request, param='max', default=None, datatype=float)
    nodata = get_query(request, param='nodata', default=-9999, datatype=float)
    tilesize = get_query(request, param='tile', default=256, datatype=int)
    indexes = get_query(request, param='indexes', default='None', datatype=str)
    numband = get_query(request, param='numband', default=3, datatype=int)
    scale = get_query(request, param='scale', default=2, datatype=int)

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
        tile, mask = await sync_to_async(main.tile)(url,
                                                    tile_x,
                                                    tile_y,
                                                    tile_z,
                                                    tilesize=tilesize*scale,
                                                    nodata=None,
                                                    resampling_method="cubic_spline")

        end_time = time.time()
        print('Reading time: ', end_time-st_time)

        # Converting it to Unsigned integer 8 bit if not.
        tile = np.uint8(tile)

        # Convering from array to image bytes type
        # img = array_to_image(tile)

        img = await sync_to_async(response.array_to_img)(
            arr=tile, tilesize=tilesize, scale=scale, tileformat=tileformat)

    elif numband == 1:
        st_time = time.time()
        tile, mask = await sync_to_async(main.tile)(url,
                                                    tile_x,
                                                    tile_y,
                                                    tile_z,
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
        img = await sync_to_async(response.array_to_img)(
            arr=color_arr, tilesize=tilesize, scale=scale, tileformat=tileformat)

    return Response.raw(img, content_type='image/%s' % (tileformat))


@app.route('/value', methods=['GET'])
async def value(request):
    """Handle bounds requests."""
    url = get_query(request, param='url',
                    default='www.indshine.com', datatype=str)
    print('hit value')
    url = requote_uri(url)

    x = get_query(request, param='x',
                  default=75.58277256, datatype=float)

    y = get_query(request, param='y',
                  default=21.02150925, datatype=float)

    # address = query_args['url']
    info = await sync_to_async(get_value.get_value)(address=url, coord_x=x, coord_y=y)
    return Response.json(info)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
