import numpy as np
from src import cmap


def jet_colormap(arr, arr_min=None, arr_max=None, mask=None, colormap='majama', nodata=None):
    """
    Applying jet color map to array
    """

    if arr_min is None:
        # If nodata is present then remove nodata and then calculate minimum value
        if nodata is not None:
            ma = np.ma.masked_equal(arr, nodata, copy=False)
            arr_min = np.min(ma)
        # Else compute minimum value
        else:
            arr_min = max(np.min(arr), 0)

    if arr_max is None:
        arr_max = np.max(arr)

    # Scaling data from minimum to maximum
    m = 255.0/(arr_max - arr_min)
    c = -m*arr_min
    norm_arr = np.uint8((arr*m + c))

    if colormap == 'jet':
        colors = np.uint8(cmap.jet(norm_arr))

    elif colormap == 'majama':
        colors = np.uint8(cmap.majama(norm_arr))

    elif colormap == 'magma':
        colors = np.uint8(cmap.magma(norm_arr))
    else:
        # Default
        colors = np.uint8(cmap.magma(norm_arr))

    if mask is not None:
        colors = np.dstack((colors, mask))

    return colors


def remap_array(arr):
    """
    Remapping [256,256,4] to [4,256,256]
    """
    return np.moveaxis(arr, 2, 0)
