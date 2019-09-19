import rasterio
import pyproj
import numpy as np
import os
from rio_tiler.errors import InvalidFormat


# Extracting values from the rasters
def get_value(address, coord_x, coord_y):
    """
    Address  = /vsicurl/https:xxx.tif
    coord_x  = array of longitude 
    coord_y  = array of latitude
    """

    with rasterio.open(address) as src:
        # Use pyproj to convert point coordinates
        utm = pyproj.Proj('%s' % (src.crs))  # Pass CRS of image from rasterio
        lonlat = pyproj.Proj(init='epsg:4326')

        # If different length of arrays
        # Try to do this if array, else if single float data then except Typeerror
        try:
            if len(coord_x) != len(coord_y):
                print('Length of lat and long array provided is not equal')
                raise InvalidFormat
            else:
                len_data = len(coord_x)
                num_bands = src.count
                value = np.zeros((len_data, num_bands), dtype=float)
                value_json = {}
        except TypeError:
            len_data = 1
            num_bands = src.count
            value = np.zeros((len_data, num_bands), dtype=float)
            value_json = {}

        # Setting loop for array of dataset
        for i in range(len_data):

            # Initializing bands json
            band_json = {}
            try:
                lon, lat = (coord_x[i], coord_y[i])
            except:
                lon, lat = (coord_x, coord_y)
            east, north = pyproj.transform(lonlat, utm, float(lon), float(lat))

            # What is the corresponding row and column in our image?
            # spatial --> image coordinates
            row, col = src.index(east, north)
            for j in range(num_bands):
                value[i, j] = src.read(
                    j+1, window=rasterio.windows.Window(col, row, 1, 1))
                band_json['b%s' % (j)] = round(float(value[i, j]), 3)
            value_json['%s' % (i)] = band_json

    return value_json


def get_value_index(url, coord_x, coord_y, satellite, index='ndvi'):

    if index == 'ndvi':
        red = get_value(os.path.join(url, 'B04.tif'), coord_x, coord_y)
        nir = get_value(os.path.join(url, 'B08.tif'), coord_x, coord_y)

        arr = {'index': index}
        for i in range(len(coord_x)):
            _red = float(red[str(i)]['b0'])
            _nir = float(nir[str(i)]['b0'])
            arr[str(i)] = (_nir - _red)/(_nir + _red)

    elif index == 'ndwi':
        swir = get_value(os.path.join(url, 'B11.tif'), coord_x, coord_y)
        nir = get_value(os.path.join(url, 'B08.tif'), coord_x, coord_y)

        arr = {'index': index}
        for i in range(len(coord_x)):
            _swir = float(swir[str(i)]['b0'])
            _nir = float(nir[str(i)]['b0'])
            arr[str(i)] = (_nir - _swir)/(_nir + _swir)

    elif index == 'nddi':
        red = get_value(os.path.join(url, 'B04.tif'), coord_x, coord_y)
        swir = get_value(os.path.join(url, 'B11.tif'), coord_x, coord_y)
        nir = get_value(os.path.join(url, 'B08.tif'), coord_x, coord_y)

        arr = {'index': index}
        for i in range(len(coord_x)):
            _red = float(red[str(i)]['b0'])
            _nir = float(nir[str(i)]['b0'])
            _swir = float(swir[str(i)]['b0'])
            _ndvi = (_nir - _red)/(_nir + _red)
            _ndwi = (_nir - _swir)/(_nir + _swir)

            arr[str(i)] = (_ndvi - _ndwi)/(_ndvi + _ndwi)
    
    elif index[0] == 'b':
        # For B01.tif
        if len(index[1:]) == 1:
            path = os.path.join(url, 'B0' + index[1] + '.tif')
        
        # For B11.tif
        else:
            path = os.path.join(url, 'B' + index[1:] + '.tif')

        band = get_value(path, coord_x, coord_y)

        arr = {'index': index}
        for i in range(len(coord_x)):
            _band = float(band[str(i)]['b0'])
            arr[str(i)] = _band
    else:
        arr = {
            'status': '404',
            'body': 'Index requested not available'
        }
    return arr
