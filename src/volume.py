import numpy as np
import utm
import math
from src.profile import longlat2utm, xy2longlat
from src.value import get_value
from shapely.geometry import Polygon
from shapely.geometry import Point
import time


class TilerError(Exception):
    """Base exception class."""


def floatrange(start, stop, step):
    while start < stop:
        yield start
        start += step


# Calculates bounds from list of coordinates
def cal_bounds(coord_x, coord_y):
    """
    ul - upper left (min easting, max northing)
    lr - lower right (max easting, min northing)
    """
    ul = [min(coord_x), max(coord_y)]
    lr = [max(coord_x), min(coord_y)]
    return ul, lr


# Calculate distance between plane and point of interest
def DistPoint2Plane(para, grid):
    """
    points will be nx3 dimension
    plane_parameters will be 3x1 dimension wiht a,b,c parameters
    Distance = AX0 + BY0 + CZ0 + D /(sqrt(A^2 + B^2 + C^2)) so adding D term
    """
    three = para[0:3]
    d = para[3]
    Dist = np.dot(grid, three.T) + d
    deno = math.sqrt(np.sum(three*three))
    Dist = Dist/deno
    return Dist


# Calculates volume
def volume(Dist, pixelWidth, pixelHeight):
    """
    Volume in Cubic Metres
    Cut Volume is when Distance between plane and point is negative
    Absolute term as it gives negative value
    """
    cutvolume = Dist[Dist < 0]
    cutvolume = abs(np.sum(cutvolume * pixelWidth * pixelHeight))

    # Fill Volume is when Distance between plane and point is positive
    fillvolume = Dist[Dist > 0]
    fillvolume = np.sum(fillvolume * pixelWidth * pixelHeight)

    return cutvolume, fillvolume


def optimum_parameter(XYZ):
    # extract data
    xs = XYZ[:, 0]
    ys = XYZ[:, 1]
    zs = XYZ[:, 2]

    # do fit
    tmp_A = []
    tmp_b = []
    for i in range(len(xs)):
        tmp_A.append([xs[i], ys[i], 1])
        tmp_b.append(zs[i])

    b = np.matrix(tmp_b).T
    A = np.matrix(tmp_A)
    fit = (A.T * A).I * A.T * b
    fit = np.asarray(fit)
    errors = b - A * fit
    residual = np.linalg.norm(errors)
    para = np.asarray([fit[0][0], fit[1][0], -1, fit[2][0]])
    return para, residual


def get_volume(address, coord_x, coord_y, step):

    # Checking if in geographic coordinates system then
    # convert it into projected coordinate system

    # Extracting all the values from raster
    vertex = []
    if coord_x[0] > 180 or coord_y[0] > 180:
        raise TilerError(
            'volume.py: coordinates should be in geographic coordinate system')

    start_time = time.time()

    for i in range(len(coord_x)):
        east, north, zone, hemi = longlat2utm(coord_x[i], coord_y[i])

        value_dict = get_value(
            address=address, coord_x=coord_x[i], coord_y=coord_y[i])

        """
            We are taking first point with first band value. For example:
            value_dict = {
                '0':{
                    'b0':{
                        292.22
                    }
                }
            }
        """

        value = float(list(value_dict['0'].values())[0])
        if value is None or value < 0:
            raise TilerError('Polygon drawing is outside the layer boundary')

        # Appending new elevation values
        vertex.append((east, north, value))

    end_time = time.time()
    print('Vertex calculation:%d' % (end_time-start_time))

    start_time = time.time()
    # Estimating equation of plane
    param, residual = optimum_parameter(np.asarray(vertex))
    end_time = time.time()
    print('Best fit plane: %d' % (end_time - start_time))
    # Calculating bounds
    # ul, lr = cal_bounds(coord_x, coord_y)
    start_time = time.time()
    polygon = Polygon((vertex))
    bounds = polygon.bounds
    ur = bounds[2:]
    ll = bounds[:2]
    end_time = time.time()
    print('Calculating bounds:%d' % (end_time-start_time))
    # contains easting northing and elevation list
    data = []

    print('Total data:', ((ll[0] - ur[0])/step)*((ll[1] - ur[1])/step))
    # iterating all over raster grids
    start_time = time.time()
    for x in floatrange(ll[0], ur[0], step):
        for y in floatrange(ll[1], ur[1], step):
            point = Point(x, y)

            # Converting back to geographic coordinate system
            long, lat = xy2longlat(x, y, zone, hemi)
            if point.within(polygon):
                grid_value_dict = get_value(
                    address=address, coord_x=long, coord_y=lat)

                grid_value = float(list(grid_value_dict['0'].values())[0])
                data.append([point.x, point.y, grid_value])

    end_time = time.time()
    print('Calculating grids:%d' % (end_time-start_time))
    data = np.asarray(data)

    # XYZ = np.asarray(vertex)
    #     coordinates (XYZ) of P1,P2,P3,P4,P5 etc .....
    #         Inital guess of the plane is random initialization...
    #         ...inside optimum_parameter function
    #         Equation of plane is aX + bY + cZ + d = 0 in this form.

    #    sol = leastsq(residuals, p0, args=(None, XYZ))[0];
    #    optimum_error =  (f_min(XYZ, sol)**2).sum();
    #    sol = np.asarray(sol);

    # Distance between plane and point

    Height = DistPoint2Plane(param, data)
    cutvolume, fillvolume = volume(Height, step, step)  # in metres

    data = [{"CutVolume": str(cutvolume), "FillVolume": str(
        fillvolume), "error": str(residual)}]
    return data
