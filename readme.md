# Cloud Optimized Geotiff API

## APIs available
* api/v1/bounds
    * **options**
        * url
        
**Example**: https://px7dducuh9.execute-api.us-east-1.amazonaws.com/dev/api/v1/bounds?url=https://s3.amazonaws.com/indshine-felix/10561/10562/DSM.tif

* api/v1/metadata
    * **options**
        * url
        
**Example**: https://px7dducuh9.execute-api.us-east-1.amazonaws.com/dev/api/v1/metadata?url=https://s3.amazonaws.com/indshine-felix/10561/10562/DSM.tif

* api/v1/tiles
    * **tile_z**
        * Integer
    * **tile_y**
        * Integer
    * **tile_x**
        * Integer
    * **format**
        * png or jpg
        
**Example**: https://px7dducuh9.execute-api.us-east-1.amazonaws.com/dev/api/v1/tiles/18/186114/115406.png?url=https://s3.amazonaws.com/indshine-felix/10561/10562/DSM.tif&numband=1

* api/v1/value
    * **options**
        * url
        * x = longitude
        * y = latitude
        
**Example**: https://px7dducuh9.execute-api.us-east-1.amazonaws.com/dev/api/v1/value?url=https://s3.amazonaws.com/indshine-felix/10561/10562/DSM.tif&x=75.58277256&y=21.02150925

 * api/v1/profile
    * **options**
        * url
        * x = array of longitude
        * y = array of latitude
        
**Example**: https://px7dducuh9.execute-api.us-east-1.amazonaws.com/dev/api/v1/value?url=https://s3.amazonaws.com/indshine-felix/10561/10562/DSM.tif&x=75.580711,75.580701,75.580788,75.580711&y=21.018307,21.018545,21.018521,21.018307

 * api/v1/volume
    * **options**
        * url
        * x = array of longitude
        * y = array of latitude
 
**Example**: https://px7dducuh9.execute-api.us-east-1.amazonaws.com/dev/api/v1/value?url=https://s3.amazonaws.com/indshine-felix/10561/10562/DSM.tif&x=75.580711,75.580701,75.580788,75.580711&y=21.018307,21.018545,21.018521,21.018307
 
## AWS Lambda
This API is hosted on AWS Lambda at url - https://px7dducuh9.execute-api.us-east-1.amazonaws.com/dev/

## How to run 
```
docker build -t cog_api2 .
docker run -d -p 8000 2359d646ac11(Image name)
docker ps (To display container id)
docker logs container_id
```
