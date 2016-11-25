import sys
import numpy


def build_matrix(data, qx_data, qy_data):
    """
    Build a matrix for 2d plot from a vector
    Returns a matrix (image) with ~ square binning
    Requirement: need 1d array formats of
    data, qx_data, and qy_data
    where each one corresponds to z, x, or y axis values

    """
    # No qx or qy given in a vector format
    if qx_data == None or qy_data == None \
            or qx_data.ndim != 1 or qy_data.ndim != 1:
        return data

    # maximum # of loops to fillup_pixels
    # otherwise, loop could never stop depending on data
    max_loop = 1
    # get the x and y_bin arrays.
    x_bins, y_bins = get_bins(qx_data, qy_data)
    # set zero to None

    #Note: Can not use scipy.interpolate.Rbf:
    # 'cause too many data points (>10000)<=JHC.
    # 1d array to use for weighting the data point averaging
    #when they fall into a same bin.
    weights_data = numpy.ones([data.size])
    # get histogram of ones w/len(data); this will provide
    #the weights of data on each bins
    weights, xedges, yedges = numpy.histogram2d(x=qy_data,
                                                y=qx_data,
                                                bins=[y_bins, x_bins],
                                                weights=weights_data)
    # get histogram of data, all points into a bin in a way of summing
    image, xedges, yedges = numpy.histogram2d(x=qy_data,
                                                y=qx_data,
                                                bins=[y_bins, x_bins],
                                                weights=data)
    # Now, normalize the image by weights only for weights>1:
    # If weight == 1, there is only one data point in the bin so
    # that no normalization is required.
    image[weights > 1] = image[weights > 1] / weights[weights > 1]
    # Set image bins w/o a data point (weight==0) as None (was set to zero
    # by histogram2d.)
    image[weights == 0] = None

    # Fill empty bins with 8 nearest neighbors only when at least
    #one None point exists
    loop = 0

    # do while loop until all vacant bins are filled up up
    #to loop = max_loop
    while not(numpy.isfinite(image[weights == 0])).all():
        if loop >= max_loop:  # this protects never-ending loop
            break
        image = fillup_pixels(image=image, weights=weights)
        loop += 1

    return image

def get_bins(qx_data, qy_data):
    """
    get bins
    return x_bins and y_bins: 1d arrays of the index with
    ~ square binning
    Requirement: need 1d array formats of
    qx_data, and qy_data
    where each one corresponds to  x, or y axis values
    """
    # No qx or qy given in a vector format
    if qx_data == None or qy_data == None \
            or qx_data.ndim != 1 or qy_data.ndim != 1:
        return data

    # find max and min values of qx and qy
    xmax = qx_data.max()
    xmin = qx_data.min()
    ymax = qy_data.max()
    ymin = qy_data.min()

    # calculate the range of qx and qy: this way, it is a little
    # more independent
    x_size = xmax - xmin
    y_size = ymax - ymin

    # estimate the # of pixels on each axes
    npix_y = int(numpy.floor(numpy.sqrt(len(qy_data))))
    npix_x = int(numpy.floor(len(qy_data) / npix_y))

    # bin size: x- & y-directions
    xstep = x_size / (npix_x - 1)
    ystep = y_size / (npix_y - 1)

    # max and min taking account of the bin sizes
    xmax = xmax + xstep / 2.0
    xmin = xmin - xstep / 2.0
    ymax = ymax + ystep / 2.0
    ymin = ymin - ystep / 2.0

    # store x and y bin centers in q space
    x_bins = numpy.linspace(xmin, xmax, npix_x)
    y_bins = numpy.linspace(ymin, ymax, npix_y)

    #set x_bins and y_bins
    return x_bins, y_bins

def fillup_pixels(image=None, weights=None):
    """
    Fill z values of the empty cells of 2d image matrix
    with the average over up-to next nearest neighbor points

    :param image: (2d matrix with some zi = None)

    :return: image (2d array )

    :TODO: Find better way to do for-loop below

    """
    # No image matrix given
    if image == None or numpy.ndim(image) != 2 \
            or numpy.isfinite(image).all() \
            or weights == None:
        return image
    # Get bin size in y and x directions
    len_y = len(image)
    len_x = len(image[1])
    temp_image = numpy.zeros([len_y, len_x])
    weit = numpy.zeros([len_y, len_x])
    # do for-loop for all pixels
    for n_y in range(len(image)):
        for n_x in range(len(image[1])):
            # find only null pixels
            if weights[n_y][n_x] > 0 or numpy.isfinite(image[n_y][n_x]):
                continue
            else:
                # find 4 nearest neighbors
                # check where or not it is at the corner
                if n_y != 0 and numpy.isfinite(image[n_y - 1][n_x]):
                    temp_image[n_y][n_x] += image[n_y - 1][n_x]
                    weit[n_y][n_x] += 1
                if n_x != 0 and numpy.isfinite(image[n_y][n_x - 1]):
                    temp_image[n_y][n_x] += image[n_y][n_x - 1]
                    weit[n_y][n_x] += 1
                if n_y != len_y - 1 and numpy.isfinite(image[n_y + 1][n_x]):
                    temp_image[n_y][n_x] += image[n_y + 1][n_x]
                    weit[n_y][n_x] += 1
                if n_x != len_x - 1 and numpy.isfinite(image[n_y][n_x + 1]):
                    temp_image[n_y][n_x] += image[n_y][n_x + 1]
                    weit[n_y][n_x] += 1
                # go 4 next nearest neighbors when no non-zero
                # neighbor exists
                if n_y != 0 and n_x != 0 and\
                        numpy.isfinite(image[n_y - 1][n_x - 1]):
                    temp_image[n_y][n_x] += image[n_y - 1][n_x - 1]
                    weit[n_y][n_x] += 1
                if n_y != len_y - 1 and n_x != 0 and \
                    numpy.isfinite(image[n_y + 1][n_x - 1]):
                    temp_image[n_y][n_x] += image[n_y + 1][n_x - 1]
                    weit[n_y][n_x] += 1
                if n_y != len_y and n_x != len_x - 1 and \
                    numpy.isfinite(image[n_y - 1][n_x + 1]):
                    temp_image[n_y][n_x] += image[n_y - 1][n_x + 1]
                    weit[n_y][n_x] += 1
                if n_y != len_y - 1 and n_x != len_x - 1 and \
                    numpy.isfinite(image[n_y + 1][n_x + 1]):
                    temp_image[n_y][n_x] += image[n_y + 1][n_x + 1]
                    weit[n_y][n_x] += 1

    # get it normalized
    ind = (weit > 0)
    image[ind] = temp_image[ind] / weit[ind]

    return image
