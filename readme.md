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

 * api/v1/stats
    * **options**
        * url = url of TIF file
        * x = array of longitude
        * y = array of latitude

        or 

        * shp = url of shapefile
        
**Example**: https://localhost:4000/api/v1/stats?url=https://dwa0i5u31qk1r.cloudfront.net/sentinel2/43/R/EL/2019/5/13/0/B08.tif&shp=https://manishtestingbucket.s3.ap-south-1.amazonaws.com/stats/stats.shp

or 

https://localhost:4000/api/v1/stats?url=https://dwa0i5u31qk1r.cloudfront.net/sentinel2/43/R/EL/2019/5/13/0/B08.tif&x=75.22036840794368,75.22387712165525,75.23013698589065,75.23027653700419,75.2240964162622375.22409641626223,75.22036840794368&y=27.43031716654922,27.43442395646162,27.43187216467139,27.42541294170238,27.42613063314338,27.42613063314338,27.43031716654922


 
## AWS Lambda
This API is hosted on AWS Lambda at url - https://px7dducuh9.execute-api.us-east-1.amazonaws.com/dev/

## How to run 
```
docker build -t cog_api2 .
docker run -d -p 8000 2359d646ac11(Image name)
docker ps (To display container id)
docker logs container_id
```
