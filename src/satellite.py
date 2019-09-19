import os
import numpy as np
from rio_tiler.errors import InvalidFormat

from src import index as get_index
from src import extract
from src import exception as excep
from src import elevation as ele_func
from src import stats as get_stats

import support
import time
from PIL import Image

class sentinel2():
    # Initializing variables

    def __init__(self, base_json):
        self.resolution = 10
        self.base_json = base_json
        self.ext = '.TIF'
        self.epsg = '4326'
        st_time = time.time()
        self.data = extract.get_json(base_json)
        end_time = time.time()
        print('JSON Time Taken : ', end_time - st_time)

        self.base_path = os.path.basename(self.base_json)

        # Initializing index dataset
        self.path_red = self.data['bands']['B04']['href'][:-5] + self.ext
        self.path_nir = self.data['bands']['B08']['href'][:-5] + self.ext
        self.path_swir = self.data['bands']['B11']['href'][:-5] + self.ext
        self.path_visual = self.data['assets']['tci']['href'][:-5] + self.ext

        # Initializing band dataset
        self.path_band = {
            'b1': self.data['bands']['B01']['href'][:-5] + self.ext,
            'b2': self.data['bands']['B02']['href'][:-5] + self.ext,
            'b3': self.data['bands']['B03']['href'][:-5] + self.ext,
            'b4': self.data['bands']['B04']['href'][:-5] + self.ext,
            'b5': self.data['bands']['B05']['href'][:-5] + self.ext,
            'b6': self.data['bands']['B06']['href'][:-5] + self.ext,
            'b7': self.data['bands']['B07']['href'][:-5] + self.ext,
            'b8': self.data['bands']['B08']['href'][:-5] + self.ext,
            'b9': self.data['bands']['B09']['href'][:-5] + self.ext,
            'b10': self.data['bands']['B10']['href'][:-5] + self.ext,
            'b11': self.data['bands']['B11']['href'][:-5] + self.ext,
            'b12': self.data['bands']['B12']['href'][:-5] + self.ext,
            'b8a': self.data['bands']['B8A']['href'][:-5] + self.ext
        }
    
    # Getting Tile Index PNG
    def get_tile_index(self, index, tile_x, tile_y, tile_z,
                       indexes, tilesize=256, scale=2,
                       nodata=0, resampling_method='nearest'):

        # For NDVI index PNG
        print('Reading tile...')
        try:
            if index.lower() == 'ndvi':            
                red, mask = extract.get_tile(url=self.path_red, tile_x=tile_x, tile_y=tile_y,
                                            tile_z=tile_z, indexes=indexes, tilesize=tilesize, scale=scale,
                                            nodata=nodata, resampling_method=resampling_method)

                nir, mask = extract.get_tile(url=self.path_nir, tile_x=tile_x, tile_y=tile_y,
                                            tile_z=tile_z, indexes=indexes, tilesize=tilesize, scale=scale,
                                            nodata=nodata, resampling_method=resampling_method)

                tile = get_index.get_ndvi(nir=nir, red=red)

            # For NDWI index PNG
            elif index.lower() == 'ndwi':
                swir, mask = extract.get_tile(url=self.path_swir, tile_x=tile_x, tile_y=tile_y,
                                            tile_z=tile_z, indexes=indexes, tilesize=tilesize, scale=scale,
                                            nodata=nodata, resampling_method=resampling_method)

                nir, mask = extract.get_tile(url=self.path_nir, tile_x=tile_x, tile_y=tile_y,
                                            tile_z=tile_z, indexes=indexes, tilesize=tilesize, scale=scale,
                                            nodata=nodata, resampling_method=resampling_method)

                tile = get_index.get_ndwi(nir=nir, swir=swir)

            # For NDDI index PNG
            elif index.lower() == 'nddi':
                ndvi, mask = self.get_tile_index(index='ndvi', tile_x=tile_x, tile_y=tile_y, tile_z=tile_z,
                                                indexes=indexes, tilesize=tilesize, scale=scale, nodata=nodata,
                                                resampling_method=resampling_method)

                ndwi, mask = self.get_tile_index(index='ndwi', tile_x=tile_x, tile_y=tile_y, tile_z=tile_z,
                                                indexes=indexes, tilesize=tilesize, scale=scale, nodata=nodata,
                                                resampling_method=resampling_method)

                tile = get_index.get_nddi(ndvi=ndvi, ndwi=ndwi)

            # For visual (RGB) index PNG
            elif index.lower() == 'visual':
                tile, mask = extract.get_tile(url=self.path_visual, tile_x=tile_x, tile_y=tile_y,
                                            tile_z=tile_z, indexes=indexes, tilesize=tilesize, scale=scale,
                                            nodata=nodata, resampling_method=resampling_method)

            # For particular band PNG
            elif 'band' in index.lower():
                band_num = int(index.lower().replace('band', ''))
                path_file = self.path_band['b'+str(band_num)]
                tile, mask = extract.get_tile(url=path_file, tile_x=tile_x, tile_y=tile_y,
                                            tile_z=tile_z, indexes=indexes, tilesize=tilesize, scale=scale,
                                            nodata=nodata, resampling_method=resampling_method)
            else:
                tile = None
                mask = None
        except Exception as e:
            msg = 'Unable to get tile from cloud. Check data if exist. Error : %s' %(e)
            print(msg)
            return None, None
    
        return tile, mask

    # Getting value at particular coordinates
    def get_value(self, url, coord_x, coord_y):
        return extract.get_value(url=url, coord_x=coord_x, coord_y=coord_y)

    # Getting value at particular coordinate for particular index
    def get_value_index(self, coord_x, coord_y, index='ndvi'):
        
        try:
            # For NDVI index value
            if index.lower() == 'ndvi':
                red = self.get_value(url=self.path_red, coord_x=coord_x, coord_y=coord_y)
                nir = self.get_value(url=self.path_nir, coord_x=coord_x, coord_y=coord_y)

                arr = {'index': index}
                for i in range(len(coord_x)):
                    _red = float(red[str(i)]['b0'])
                    _nir = float(nir[str(i)]['b0'])

                    if _nir + _red != 0:
                        arr[str(i)] = (_nir - _red)/(_nir + _red)
                    else:
                        arr[str(i)] = 0

            # For NDWI index value
            elif index.lower() == 'ndwi':
                swir = self.get_value(self.path_swir, coord_x, coord_y)
                nir = self.get_value(self.path_nir, coord_x, coord_y)

                arr = {'index': index}
                for i in range(len(coord_x)):
                    _swir = float(swir[str(i)]['b0'])
                    _nir = float(nir[str(i)]['b0'])

                    if _nir + _swir !=0:
                        arr[str(i)] = (_nir - _swir)/(_nir + _swir)
                    else:
                        arr[str(i)] = 0

            # For NDDI index value
            elif index.lower() == 'nddi':
                red = self.get_value(self.path_red, coord_x, coord_y)
                swir = self.get_value(self.path_swir, coord_x, coord_y)
                nir = self.get_value(self.path_nir, coord_x, coord_y)

                arr = {'index': index}
                for i in range(len(coord_x)):
                    _red = float(red[str(i)]['b0'])
                    _nir = float(nir[str(i)]['b0'])
                    _swir = float(swir[str(i)]['b0'])
                    _ndvi = (_nir - _red)/(_nir + _red)
                    _ndwi = (_nir - _swir)/(_nir + _swir)
                    
                    if _ndvi + _ndwi != 0:
                        arr[str(i)] = (_ndvi - _ndwi)/(_ndvi + _ndwi)
                    else:
                        arr[str(i)] = 0

            # For particular band value
            elif 'band' in index.lower():
                band_num = int(index.lower().replace('band', ''))
                path = self.path_band['b'+str(band_num)]
                band = self.get_value(path, coord_x, coord_y)

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

        except Exception as e:
            msg = 'Unable to get tile from cloud. Check data if exist. Error : %s' %(e)
            print(msg)
            return None

    def get_thumbnail(self, url, coord_x, coord_y):
        return extract.get_thumbnail(url, coord_x, coord_y)

    def get_thumbnail_index(self, coord_x, coord_y, index='ndvi', min_value=0, max_value=1, colormap='green'):

        try:
            msg  = 'Done'
            # For NDVI index value
            if index.lower() == 'ndvi':
                red= self.get_thumbnail(self.path_red, coord_x, coord_y)
                nir = self.get_thumbnail(self.path_nir, coord_x, coord_y)

                arr = (red - nir)/(red + nir)

                # Coloring 1 dimension array to 3 dimension color array
                color_arr = ele_func.jet_colormap(
                    arr[0, :, :], arr_min=np.nanmin(arr), arr_max=np.nanmax(arr), colormap=colormap, nodata=0)

                # Remapping [row, col, dim] to [dim, row, col] format
                arr = ele_func.remap_array(arr=color_arr)

            # For NDWI index value
            elif index.lower() == 'ndwi':
                swir= self.get_thumbnail(self.path_swir, coord_x, coord_y)
                nir = self.get_thumbnail(self.path_nir, coord_x, coord_y)

                arr = (swir - nir)/(swir + nir)
                
                # Coloring 1 dimension array to 3 dimension color array
                color_arr = ele_func.jet_colormap(
                    arr[0, :, :], arr_min=np.nanmin(arr), arr_max=np.nanmax(arr), colormap='blue', nodata=0)

                # Remapping [row, col, dim] to [dim, row, col] format
                arr = ele_func.remap_array(arr=color_arr)

            # For NDDI index value
            elif index.lower() == 'nddi':
                red = self.get_thumbnail(self.path_red, coord_x, coord_y)
                swir = self.get_thumbnail(self.path_swir, coord_x, coord_y)
                nir = self.get_thumbnail(self.path_nir, coord_x, coord_y)


                ndvi = (nir - red)/(nir + red)
                ndwi = (nir - swir)/(nir + swir)

                arr = (ndvi - ndwi)/(ndvi + ndwi)
                
                # Coloring 1 dimension array to 3 dimension color array
                color_arr = ele_func.jet_colormap(
                    arr[0, :, :], arr_min=np.nanmin(arr), arr_max=np.nanmax(arr), colormap=colormap, nodata=0)

                # Remapping [row, col, dim] to [dim, row, col] format
                arr = ele_func.remap_array(arr=color_arr)

            # For particular band value
            elif 'band' in index.lower():
                band_num = int(index.lower().replace('band', ''))
                path = self.path_band['b'+str(band_num)]
                arr = self.get_thumbnail(path, coord_x, coord_y)

                # Coloring 1 dimension array to 3 dimension color array
                color_arr = ele_func.jet_colormap(
                    arr[0, :, :], arr_min=np.nanmin(arr), arr_max=np.nanmax(arr), colormap='green', nodata=0)

                # Remapping [row, col, dim] to [dim, row, col] format
                arr = ele_func.remap_array(arr=color_arr)

            elif index.lower() == 'visual':
                arr = self.get_thumbnail(self.path_visual, coord_x, coord_y)

            return arr, msg

        except Exception as e:
            msg = 'Unable to get tile from cloud. Check data if exist. Error : %s' %(e)
            print(msg)
            return None, msg

    def get_stats(self, url, coord_x, coord_y):
        return extract.get_stats(url, coord_x, coord_y)

    def get_stats_index(self, coord_x, coord_y, index='ndvi'):
        stats = {'index': index}
        try:
            msg  = 'Done'
            # For NDVI index value
            if index.lower() == 'ndvi':
                red = self.get_stats(self.path_red, coord_x, coord_y)
                nir = self.get_stats(self.path_nir, coord_x, coord_y)
                arr = (nir - red)/(nir + red)
                arr = arr[0, :, :]


    # TO DO....
    # Data has different resolutions
            # # For NDWI index value
            # elif index.lower() == 'ndwi':
            #     swir= self.get_stats(self.path_swir, coord_x, coord_y)
            #     nir = self.get_stats(self.path_nir, coord_x, coord_y)

            #     arr = (swir - nir)/(swir + nir)
            #     arr = arr[0, :, :]
                

            # # For NDDI index value
            # elif index.lower() == 'nddi':
            #     red = self.get_stats(self.path_red, coord_x, coord_y)
            #     swir = self.get_stats(self.path_swir, coord_x, coord_y)
            #     nir = self.get_stats(self.path_nir, coord_x, coord_y)


            #     ndvi = (nir - red)/(nir + red)
            #     ndwi = (nir - swir)/(nir + swir)

            #     arr = (ndvi - ndwi)/(ndvi + ndwi)
            #     arr = arr[0, :, :]

            # For particular band value
            elif 'band' in index.lower():
                band_num = int(index.lower().replace('band', ''))
                path = self.path_band['b'+str(band_num)]
                arr = self.get_stats(path, coord_x, coord_y)
                arr = arr[0, :, :]
            else:
                msg = 'Index requested not available. Available indexes are: ndvi, ndwi, nddi, bandx'
                return None, msg

            arr = np.round(arr, 2)
            stats['min'] = float(np.nanmin(arr))
            stats['max'] = float(np.nanmax(arr))
            stats['median'] = float(np.nanmedian(arr))
            value = float(get_stats.mode(arr))
            stats['mode'] = value
            return stats, msg

        except Exception as e:
            msg = 'Unable to get tile from cloud. Check data if exist. Error : %s' %(e)
            return None, msg


# Landsat8 class
class landsat8():

    # Initializing variables

    def __init__(self, base_json):
        self.resolution = 30
        self.ext = '.TIF'
        self.base_json = base_json
        self.epsg = '4326'
        self.base_path = os.path.basename(base_json)

        st_time = time.time()
        self.data = extract.get_json(base_json)
        end_time = time.time()
        print('JSON Reading time : %s' %(end_time - st_time))

        self.path_red = self.cdn_s3(self.data['bands']['B4']['href'][:-5] + self.ext)
        self.path_nir = self.cdn_s3(self.data['bands']['B5']['href'][:-5] + self.ext)
        self.path_swir = self.cdn_s3(self.data['bands']['B7']['href'][:-5] + self.ext)
        # Initializing band dataset

        self.path_band = {
            'b1': self.cdn_s3(self.data['bands']['B1']['href'][:-5] + self.ext),
            'b2': self.cdn_s3(self.data['bands']['B2']['href'][:-5] + self.ext),
            'b3': self.cdn_s3(self.data['bands']['B3']['href'][:-5] + self.ext),
            'b4': self.cdn_s3(self.data['bands']['B4']['href'][:-5] + self.ext),
            'b5': self.cdn_s3(self.data['bands']['B5']['href'][:-5] + self.ext),
            'b6': self.cdn_s3(self.data['bands']['B6']['href'][:-5] + self.ext),
            'b7': self.cdn_s3(self.data['bands']['B7']['href'][:-5] + self.ext),
            'b8': self.cdn_s3(self.data['bands']['B8']['href'][:-5] + self.ext),
            'b9': self.cdn_s3(self.data['bands']['B9']['href'][:-5] + self.ext),
            'b10': self.cdn_s3(self.data['bands']['B10']['href'][:-5] + self.ext),
            'b11': self.cdn_s3(self.data['bands']['B11']['href'][:-5] + self.ext)
            }

    # Converting CDN link to Landsat Public S3 Paths
    @staticmethod
    def cdn_s3(url):
        parts = url.split('landsat8')
        return support.PATH_L8_S3 + parts[1]

    # Getting Tile Index PNG
    def get_tile_index(self, index, tile_x, tile_y, tile_z,
                       indexes, tilesize=256, scale=2,
                       nodata=0, resampling_method='nearest'):

        # Getting Paticular index NDVI PNG
        try:
            if index == 'ndvi':
                red, mask = extract.get_tile(url=self.path_red, tile_x=tile_x, tile_y=tile_y,
                                            tile_z=tile_z, indexes=indexes, tilesize=tilesize, scale=scale,
                                            nodata=nodata, resampling_method=resampling_method)

                nir, mask = extract.get_tile(url=self.path_nir, tile_x=tile_x, tile_y=tile_y,
                                            tile_z=tile_z, indexes=indexes, tilesize=tilesize, scale=scale,
                                            nodata=nodata, resampling_method=resampling_method)

                tile = get_index.get_ndvi(nir=nir, red=red)

            # Getting Paticular index NDWI PNG
            elif index == 'ndwi':
                swir, mask = extract.get_tile(url=self.path_swir, tile_x=tile_x, tile_y=tile_y,
                                            tile_z=tile_z, indexes=indexes, tilesize=tilesize, scale=scale,
                                            nodata=nodata, resampling_method=resampling_method)

                nir, mask = extract.get_tile(url=self.path_nir, tile_x=tile_x, tile_y=tile_y,
                                            tile_z=tile_z, indexes=indexes, tilesize=tilesize, scale=scale,
                                            nodata=nodata, resampling_method=resampling_method)

                tile = get_index.get_ndwi(nir=nir, swir=swir)

            # Getting Paticular index NDDI PNG
            elif index == 'nddi':
                ndvi, mask = self.get_tile_index(index='ndvi', tile_x=tile_x, tile_y=tile_y, tile_z=tile_z,
                                                indexes=indexes, tilesize=tilesize, scale=scale, nodata=nodata,
                                                resampling_method=resampling_method)

                ndwi, mask = self.get_tile_index(index='ndwi', tile_x=tile_x, tile_y=tile_y, tile_z=tile_z,
                                                indexes=indexes, tilesize=tilesize, scale=scale, nodata=nodata,
                                                resampling_method=resampling_method)

                tile = get_index.get_nddi(ndvi=ndvi, ndwi=ndwi)

            # Getting Paticular index Visual PNG
            elif index == 'visual':
                # tile, mask = extract.get_tile(url=self.path_visual, tile_x=tile_x, tile_y=tile_y,
                #                               tile_z=tile_z, indexes=indexes, tilesize=tilesize, scale=scale,
                #                               nodata=nodata, resampling_method=resampling_method)
                tile, mask = None, None

            # Getting Paticular band PNG
            elif 'band' in index.lower():
                band_num = int(index.lower().replace('band', ''))
                path_file = self.path_band['b'+str(band_num)]

                tile, mask = extract.get_tile(url=path_file, tile_x=tile_x, tile_y=tile_y,
                                            tile_z=tile_z, indexes=indexes, tilesize=tilesize, scale=scale,
                                            nodata=nodata, resampling_method=resampling_method)
            else:
                tile = None
                mask = None
        except Exception as e:
            msg = 'Unable to get tile from cloud. Check data if exist. Error : %s' %(e)
            print(msg)
            return None, None

        return tile, mask

    # Getting particular value
    def get_value(self, url, coord_x, coord_y):
        return extract.get_value(url=url, coord_x=coord_x, coord_y=coord_y)

    # Getting particular index value
    def get_value_index(self, coord_x, coord_y, index='ndvi'):

        # Getting NDVI index value
        try:
            if index == 'ndvi':
                red = self.get_value(self.path_red, coord_x, coord_y)
                nir = self.get_value(self.path_nir, coord_x, coord_y)

                arr = {'index': index}
                for i in range(len(coord_x)):
                    _red = float(red[str(i)]['b0'])
                    _nir = float(nir[str(i)]['b0'])

                    if _nir + _red !=0:
                        arr[str(i)] = (_nir - _red)/(_nir + _red)
                    else:
                        arr[str(i)] = 0

            # Getting NDWI index value
            elif index == 'ndwi':
                swir = self.get_value(self.path_swir, coord_x, coord_y)
                nir = self.get_value(self.path_nir, coord_x, coord_y)

                arr = {'index': index}
                for i in range(len(coord_x)):
                    _swir = float(swir[str(i)]['b0'])
                    _nir = float(nir[str(i)]['b0'])

                    if _nir + _swir !=0:
                        arr[str(i)] = (_nir - _swir)/(_nir + _swir)
                    else:
                        arr[str(i)] = 0

            # Getting NDDI index value
            elif index == 'nddi':
                red = self.get_value(self.path_red, coord_x, coord_y)
                swir = self.get_value(self.path_swir, coord_x, coord_y)
                nir = self.get_value(self.path_nir, coord_x, coord_y)

                arr = {'index': index}
                for i in range(len(coord_x)):
                    _red = float(red[str(i)]['b0'])
                    _nir = float(nir[str(i)]['b0'])
                    _swir = float(swir[str(i)]['b0'])
                    _ndvi = (_nir - _red)/(_nir + _red)
                    _ndwi = (_nir - _swir)/(_nir + _swir)

                    if _ndvi + _ndwi !=0:
                        arr[str(i)] = (_ndvi - _ndwi)/(_ndvi + _ndwi)
                    else:
                        arr[str(i)] = 0
                        
            # Getting particular band value
            elif 'band' in index.lower():
                band_num = int(index.lower().replace('band', ''))
                path = self.path_band['b'+str(band_num)]

                band = self.get_value(path, coord_x, coord_y)
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

        except Exception as e:
            msg = 'Unable to get tile from cloud. Check data if exist. Error : %s' %(e)
            print(msg)
            return None

    def get_stats(self, url, coord_x, coord_y, index='ndvi'):
        return extract.get_stats(url, coord_x, coord_y)

    def get_stats_index(self, coord_x, coord_y, index='ndvi'):
        stats = {}
        try:
            msg  = 'Done'
            # For NDVI index value
            if index.lower() == 'ndvi':
                red= self.get_stats(self.path_red, coord_x, coord_y)
                nir = self.get_stats(self.path_nir, coord_x, coord_y)

                arr = (red - nir)/(red + nir)
                arr = arr[0, :, :]

            # Cannot do NDWI and NDDI because of different resolution of datasets
    # TO DO....

            # # For NDWI index value
            # elif index.lower() == 'ndwi':
            #     swir= self.get_stats(self.path_swir, coord_x, coord_y)
            #     nir = self.get_stats(self.path_nir, coord_x, coord_y)

            #     arr = (swir - nir)/(swir + nir)
            #     arr = arr[0, :, :]
                

            # # For NDDI index value
            # elif index.lower() == 'nddi':
            #     red = self.get_stats(self.path_red, coord_x, coord_y)
            #     swir = self.get_stats(self.path_swir, coord_x, coord_y)
            #     nir = self.get_stats(self.path_nir, coord_x, coord_y)


            #     ndvi = (nir - red)/(nir + red)
            #     ndwi = (nir - swir)/(nir + swir)

            #     arr = (ndvi - ndwi)/(ndvi + ndwi)
            #     arr = arr[0, :, :]

            # For particular band value
             # For particular band value
            elif 'band' in index.lower():
                band_num = int(index.lower().replace('band', ''))
                path = self.path_band['b'+str(band_num)]
                arr = self.get_stats(path, coord_x, coord_y)
                arr = arr[0, :, :]

            else:
                msg = 'Index requested not available. Available indexes are: ndvi, ndwi, nddi, bandx'
                return None, msg

            arr = np.round(arr, 2)
            stats['min'] = float(np.nanmin(arr))
            stats['max'] = float(np.nanmax(arr))
            stats['median'] = float(np.nanmedian(arr))
            value = float(get_stats.mode(arr))
            stats['mode'] = float(value)
            return stats, msg

        except Exception as e:
            msg = 'Unable to get tile from cloud. Check data if exist. Error : %s' %(e)
            print(msg)
            return {}, msg
