from PIL import Image
from io import BytesIO, StringIO
import base64
import numpy as np
from rio_tiler.errors import (RioTilerError,
                              InvalidFormat,
                              InvalidLandsatSceneId,
                              InvalidSentinelSceneId,
                              InvalidCBERSSceneId)

                              
def reshape_as_image(arr):
    """Returns the source array reshaped into the order
    expected by image processing and visualization software
    (matplotlib, scikit-image, etc)
    by swapping the axes order from (bands, rows, columns)
    to (rows, columns, bands)

    Parameters
    ----------
    arr : array-like of shape (bands, rows, columns)
        image to reshape
    """
    # swap the axes order from (bands, rows, columns) to (rows, columns, bands)
    im = np.ma.transpose(arr, [1, 2, 0])
    return im


def array_to_img(arr, mask=None, color_map=None, tileformat='png', tilesize=256, scale=1):
    """Convert an array to an base64 encoded img

    Attributes
    ----------
    arr : numpy ndarray
        Image array to encode.
    Mask: numpy ndarray
        Mask
    color_map: numpy array
        ColorMap array (see: utils.get_colormap)

    Returns
    -------
    img : object
        Pillow image
    """
    quality = 90
    compress_level = 9
    arr = reshape_as_image(arr)

    if arr.shape[2] == 4:
        alpha = arr[:,:,3]

        if int(np.min(alpha)) == 255:
            img = Image.fromarray(arr[:,:,:3], mode='RGB')
            params = {'quality': quality,
                      'optimize': True,
                      'compress_level':compress_level}
            
            # Resize back to default tilesize
            img = img.resize((tilesize,tilesize), Image.ANTIALIAS)

            sio = BytesIO()
            img.save(sio, 'JPEG', **params)
            sio.seek(0)

        else:
            img = Image.fromarray(arr, mode='RGBA')
            params = {'compress_level': 9}
            # Resize back to default tilesize
            img = img.resize((tilesize,tilesize), Image.ANTIALIAS)

            sio = BytesIO()
            img.save(sio, tileformat.upper(), **params)
            sio.seek(0)

    else:
        img = Image.fromarray(arr[:,:,:3], mode='RGB')
        params = {'quality': quality,
                  'optimize': True,
                  'compress_level':compress_level}

        # Resize back to default tilesize
        img = img.resize((tilesize,tilesize), Image.ANTIALIAS)

        sio = BytesIO()
        img.save(sio, 'JPEG', **params)
        sio.seek(0)

    return sio.getvalue()


def b64_encode_img(img, tileformat):
    """Convert a Pillow image to an base64 encoded string
    Attributes
    ----------
    img : object
        Pillow image
    tileformat : str
        Image format to return (Accepted: "jpg" or "png")

    Returns
    -------
    out : str
        base64 encoded image.
    """
    params = {'compress_level': 9}

    if tileformat == 'jpeg':
        img = img.convert('RGB')

    sio = BytesIO()
    img.save(sio, tileformat.upper(), **params)
    sio.seek(0)
    return base64.b64encode(sio.getvalue()).decode()