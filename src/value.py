import rasterio
import pyproj
import numpy as np
from rio_tiler.errors import InvalidFormat

# Extracting values from the rasters
def get_value(address, coord_x, coord_y):
    """
    Address will be /vsicurl/https:xxx.tif
    coord_x will be array of longitude 
    coord_y will be array of latitude
    """
    
    with rasterio.open(address) as src:
        # Use pyproj to convert point coordinates
        utm = pyproj.Proj(src.crs) # Pass CRS of image from rasterio
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
                lon,lat = (coord_x[i], coord_y[i])
            except:
                lon,lat = (coord_x, coord_y)
            
            east,north = pyproj.transform(lonlat, utm, lon, lat)

            # What is the corresponding row and column in our image?
            # spatial --> image coordinates
            row, col = src.index(east, north) 
            for j in range(num_bands):
                value[i,j] = src.read(j+1, window=rasterio.windows.Window(col,row, 1, 1))
                band_json['b%s'%(j)] = round(float(value[i,j]),3)
            value_json['%s'%(i)] = band_json
    
    return value_json