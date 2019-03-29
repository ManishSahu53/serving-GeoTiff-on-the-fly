# Converting line to points according to step size
import math
import utm


class TilerError(Exception):
    """Base exception class."""


# For converting geographic to projected coordinate system
def longlat2utm(long, lat):
    coord = utm.from_latlon(lat, long)
    easting = coord[0]
    northing = coord[1]
    zone = coord[2]
    hemi = coord[3]
    return easting, northing, zone, hemi


# For converting projected to geographic coordinate system
def xy2longlat(easting, northing, zone, hemi):
    lat, long = utm.to_latlon(easting, northing, zone, hemi)
    return long, lat


# 2 UTM points to line
def get_point2line(easting1, northing1, easting2, northing2, step=0.5):
    """
    Converts 2 UTM points to Line coordinates
    """

    if easting1 < 180 or northing1 < 180:
        easting1, northing1, zone, hemi = longlat2utm(easting1, northing1)

    if easting2 < 180 or northing2 < 180:
        easting2, northing2, _, _ = longlat2utm(easting2, northing2)

    easting3 = []
    northing3 = []
    easting3.append(easting1)
    northing3.append(northing1)
    distance = math.sqrt(math.pow(easting2-easting1, 2) +
                         math.pow(northing2-northing1, 2))

    if distance > 10000:
        raise TilerError('Length should be less than 10KMs')

    for i in range(int(distance/step)):
        easting3.append(easting1 + step * (i+1) * (easting2-easting1)/distance)
        northing3.append(northing1 + step * (i+1) *
                         (northing2-northing1)/distance)

    easting3.append(easting2)
    northing3.append(northing2)

    if len(easting3) != len(northing3):
        raise TilerError('Length of x and y coordinates should be equal')

    long = []
    lat = []

    for i in range(len(easting3)):
        temp_long, temp_lat = xy2longlat(easting3[i], northing3[i], zone, hemi)
        long.append(temp_long)
        lat.append(temp_lat)

    return long, lat
