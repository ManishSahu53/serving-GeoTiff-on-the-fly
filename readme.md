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

* /elevation
    * **tile_z**
        * Integer
    * **tile_y**
        * Integer
    * **tile_x**
        * Integer
    * **format**
        * png or jpg
    * **params**
        * Only one color scheme is available **Mapzen**

* /value
    * **options**
        * url
        * x = longitude
        * y = latitude
 

## How to run 
```
docker build -t cog_api2 .
docker run -d -p 8000 2359d646ac11(Image name)
docker ps (To display container id)
docker logs container_id
```