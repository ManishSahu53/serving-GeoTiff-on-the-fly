from rio_tiler.errors import InvalidFormat
from rio_tiler import main

import requests, json
from multiprocessing import Process, Manager

from src import response as get_response
import gconfig

import boto3
import botocore
import io
import numpy as np

import rasterio
import pyproj
from rasterio import mask
from PIL import Image


def get_json(url):
    content = requests.get(url)
    data = json.loads(content.content)
    return data

def get_value(url, coord_x, coord_y):
    """
    url  = /vsicurl/https:xxx.tif
    coord_x  = array of longitude 
    coord_y  = array of latitude
    """

    with rasterio.open(url) as src:
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

        except TypeError:
            len_data = 1
            coord_x = [coord_x]
            coord_y = [coord_y]

        num_bands = src.count

        # Defining multiprocessing function
        def compute(value_json, x, y):
            # Initializing bands json
            band_json = {}
            
            if utm == lonlat:
                east, north = x, y
            else:
                east, north = pyproj.transform(lonlat, utm, float(x), float(y))


            # What is the corresponding row and column in our image?
            # spatial --> image coordinates
            row, col = src.index(east, north)

            for j in range(num_bands):
                value = src.read(j+1, window=rasterio.windows.Window(col, row, 1, 1))[0][0]

                band_json['b%s' % (j)] = round(float(value), 3)
        
            value_json['%s' % (i)] = band_json

            return value_json

        # Creating common dataset for multiple processing
        manager = Manager()
        value_json = manager.dict()

        # Setting loop for array of dataset
        processes = list()
        for i in range(len_data):
            process = Process(target=compute, args=(value_json, coord_x[i], coord_y[i], ))
            process.start()
            processes.append(process)
        
        for process in processes:
            process.join()


    value_json = dict(value_json)
    return value_json

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


def get_thumbnail(url, coord_x, coord_y):
    coord = [[[coord_x[i], coord_y[i]] for i in range(len(coord_x))]]

    # Creating specific geometry
    poly = {}
    poly['coordinates'] = coord
    poly['type'] = 'Polygon'

    with rasterio.open(url) as src:
        arr, _ = mask.mask(dataset=src, shapes=[poly], crop=True)

    return arr

def get_stats(url, coord_x, coord_y):
    coord = [[[coord_x[i], coord_y[i]] for i in range(len(coord_x))]]

    # Adding first coordinate at last    
    coord[0].append([coord_x[0], coord_y[0]])

    # Creating specific geometry
    poly = {}
    poly['coordinates'] = coord
    poly['type'] = 'Polygon'

    with rasterio.open(url) as src:
        arr, _ = mask.mask(dataset=src, shapes=[poly], crop=True)
    return arr

def upload2S3(img_obj, key, bucket='satellte-dataset'):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=gconfig.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=gconfig.AWS_SECRET_ACCESS_KEY,
    )
    s3_client.put_object(Body=img_obj, Bucket=bucket, Key=key, ContentType='image/jpeg')


def array2img(arr, tileformat='jpeg'):
    arr = get_response.reshape_as_image(arr)
    
    img = Image.fromarray(arr, mode='RGB')
 
    sio = io.BytesIO()
    img.save(sio, tileformat)
    sio.seek(0)
    return sio