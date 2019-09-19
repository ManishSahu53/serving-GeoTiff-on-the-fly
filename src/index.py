import numpy as np
from rio_tiler.errors import InvalidFormat
from rio_tiler import main
import os

# Defining indexes


def get_ndvi(nir, red):
    nir = nir.astype(np.float)
    red = red.astype(np.float)
    return (nir-red)/(nir+red)


def get_ndwi(nir, swir):
    nir = nir.astype(np.float)
    swir = swir.astype(np.float)
    return (nir-swir)/(nir+swir)


def get_nddi(ndvi, ndwi):
    ndvi = ndvi.astype(np.float)
    ndwi = ndwi.astype(np.float)
    return (ndvi-ndwi)/(ndvi+ndwi)

# Extracting tile information


def get_tile(url, tile_x, tile_y, tile_z,
             indexes, tilesize=256, scale=2,
             nodata=0, resampling_method='nearest'):

    arr, mask = main.tile(url,
                          tile_x,
                          tile_y,
                          tile_z,
                          indexes=indexes,
                          tilesize=tilesize*scale,
                          nodata=nodata,
                          resampling_method="nearest")
    return arr, mask

# Calculating indexes


# def get_index(index, url, tile_x, tile_y, tile_z,
#               indexes, tilesize=256, scale=2,
#               nodata=0, resampling_method='nearest'):

#     if index == 'ndvi':
#         red, mask = get_tile(os.path.join(url, 'B04.tif'), tile_x, tile_y, tile_z,
#                              indexes, tilesize, scale, nodata, resampling_method)

#         nir, mask = get_tile(os.path.join(url, 'B08.tif'), tile_x, tile_y, tile_z,
#                              indexes, tilesize, scale, nodata, resampling_method)

#         tile = get_ndvi(nir=nir, red=red)

#     elif index == 'ndwi':
#         swir, mask = get_tile(os.path.join(url, 'B11.tif'), tile_x, tile_y, tile_z,
#                               indexes, tilesize, scale, nodata, resampling_method)

#         nir, mask = get_tile(os.path.join(url, 'B08.tif'), tile_x, tile_y, tile_z,
#                              indexes, tilesize, scale, nodata, resampling_method)

#         tile = get_ndwi(nir=nir, swir=swir)

#     elif index == 'nddi':
#         ndvi, mask = get_index(index='ndvi', url=url, tile_x=tile_x, tile_y=tile_y, tile_z=tile_z,
#                                indexes=indexes, tilesize=tilesize, scale=scale, nodata=nodata,
#                                resampling_method=resampling_method)

#         ndwi, mask = get_index(index='ndwi', url=url, tile_x=tile_x, tile_y=tile_y, tile_z=tile_z,
#                                indexes=indexes, tilesize=tilesize, scale=scale, nodata=nodata,
#                                resampling_method=resampling_method)

#         tile = get_nddi(ndvi=ndvi, ndwi=ndwi)
#     else:
#         tile = None
#         mask = None

#     return tile, mask
