"""
Module contains functions frequently used in this package
"""
import numpy


def get_weight(data, is2d, flag=None):
    """
    Received flag and compute error on data.
    :param flag: flag to transform error of data.
    :param is2d: flag to distinguish 1D to 2D Data
    """
    weight = None
    if is2d:
        dy_data = data.err_data
        data = data.data
    else:
        dy_data = data.dy
        data = data.y
    if flag == 0:
        weight = numpy.ones_like(data)
    elif flag == 1:
        weight = dy_data
    elif flag == 2:
        weight = numpy.sqrt(numpy.abs(data))
    elif flag == 3:
        weight = numpy.abs(data)
    return weight
