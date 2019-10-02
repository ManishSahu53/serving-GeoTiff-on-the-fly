import gconfig
import requests

def get_lambda(date, url, satellite, index, x, y, temp):
    # x is longitude in searchapi and y is latitude
    payload = (('url', url), ('satellite', satellite),
               ('index', index),
               ('x', x), ('y', y))
    print('Hitting')
    r = requests.get(gconfig.LAMBDA_VALUE_API, params=payload)
    response = r.json()
    print('Response got: %s' %(date))
    if response:
        temp[date] = response['0']
    else:
        temp[date] = -9999
      
    return temp
