from rasterstats import zonal_stats
from shapely.geometry import Polygon
import numpy as np

def get_stats_rasterstats(address, coord_x, coord_y):
    """
        address: url of TIF file
        coord_x: list of longitude coordinates
        coord_y: list of latitude coordinates
    """
    poly = Polygon([[coord_x[i], coord_y[i]] for i in range(len(coord_x))])
    stats = zonal_stats(poly, address)
    return stats[0]


def mode(ndarray, axis=0):
    # Check inputs
    ndarray = np.asarray(ndarray)
    ndim = ndarray.ndim
    
    if ndarray.size == 1:
        return ndarray[0]
    elif ndarray.size == 0:
        raise Exception('Cannot compute mode on empty array')
    
    # If array is 1-D and np version is > 1.9 np.unique will suffice

    modals, counts = np.unique(ndarray, return_counts=True)
    index = np.argmax(counts)
    return modals[index]

def get_stats_shp(address, path_shp):
    """
        address: url of TIF file
        path_shp: url of SHP file
    """
    
    stats = zonal_stats(path_shp, address)
    print('%d shapes found' % (len(stats)))

    return stats