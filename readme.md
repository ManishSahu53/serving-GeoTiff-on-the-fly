# Cloud Optimized Geotiff API

## APIs available
* /bounds
    * **options**
        * url
* /metadata
    * **options**
        * url
* /tiles
    * **tile_z**
        * Integer
    * **tile_y**
        * Integer
    * **tile_x**
        * Integer
    * **format**
        * png or jpg

* /value
    * **options**
        * url
        * x = longitude
        * y = latitude
       
 * /profile
    * **options**
        * url
        * x = array of longitude
        * y = array of latitude
 * /volume
    * **options**
        * url
        * x = array of longitude
        * y = array of latitude
 

## How to run 
```
docker build -t cog_api2 .
docker run -d -p 8000 2359d646ac11(Image name)
docker ps (To display container id)
docker logs container_id
```
