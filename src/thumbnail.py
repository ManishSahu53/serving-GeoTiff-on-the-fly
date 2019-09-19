from flask import jsonify

import rasterio
import numpy as np
import os

import boto3
import time

from src import satellite as satelliteobj
from src import exception as excep
from src import extract
import gconfig

def get_thumbnail(data, date, stac_url, satellite, coord_x, coord_y, farmid, index='visual'):
    
        # print(threading.currentThread().getName(), 'Starting')
        # Checking satellite requested
        if satellite.lower() == 's2':
            satellite_data = satelliteobj.sentinel2(base_json=stac_url)

        elif satellite.lower() == 'l8':
            satellite_data = satelliteobj.landsat8(base_json=stac_url)
        else:
            satellite_data = {
                'status': '404',
                'body': 'Satellite %s is not available' % (satellite)
            }
            return jsonify(satellite_data)

        # Reading satellite dataset
        # In value api where pyproj transform is used, x and y are reversed
        st_time = time.time()
        try:
            # print(threading.currentThread().getName(), 'Reading data')
            arr, msg = satellite_data.get_thumbnail_index(
                        coord_x=coord_x, coord_y=coord_y, index=index)
            # print(threading.currentThread().getName(), 'Finished Reading data')
            print('array shape:', arr.shape)
            if arr is None:
                return excep.general(msg)

            # Defining upload paramter
            print('Uploading %s ...' %(date))
            bucket = gconfig.BUCKET

            key = 'testing/%s/%s' %(farmid, date.replace('-','')) + '.jpg'

            try:
                img_obj = extract.array2img(arr)
                extract.upload2S3(img_obj=img_obj, bucket=bucket, key=key)
    
            except Exception as e:
                msg = 'Error: Upload failed. %s' %(e)
                print(msg)
                return excep.general(msg)
                
            print('Uploading %s completed, Bucket=%s, Key=%s'  %(date, bucket, key))
            
        except Exception as e:
            msg = 'Cound not process index: %s, from url: %s. %s' % (
                index, stac_url, e)
            return excep.general(msg)

        end_time = time.time()

        print('Thunbnail Time Taken: %s secs' % (end_time-st_time))
        # print(threading.currentThread().getName(), 'Finished')
        cdn = gconfig.CDNURL

        data[date] = os.path.join(cdn, key)
        return data
