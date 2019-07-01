
import numpy as np
import sys
import math
import time
import copy
import os
import re
import logging
import timeit
import time
from numba import njit

"""
Starting to convert invertor.c, eventually the Cinvertor class to python

At the moment experimenting with different methods of implementing individual
functions.
"""

"""
Slightly faster with njit(), njit() not working with smeared functions
with external function calls
"""
@njit()
def ortho_transformed_py(d_max, n, q):
    #qd = q * (d_max / math.pi)
    #return 8.0 *d_max**2/math.pi * n * (-1.0)**(n + 1) * np.sinc(qd) / (n**2 - qd**2) 
    """C = 8.0*pi**2*d_max**2 * n * (-1.0)**(n+1)
    pi_n_sq = (pi*n)**2
    result = np.zeros_like(q)
    for j, qj in enumerate(q):
        qd = qj * d_max
        result[j] = C * sin(qd) / qd / (pi_n_sq - qd*qd) if qd != 0. else C / pi_n_sq
    return result"""
    return 8.0 * math.pow(math.pi, 2.0)/q * d_max * n * math.pow(-1.0, n + 1) * math.sin(q*d_max) / ( math.pow(math.pi*n, 2.0)
    - math.pow(q * d_max, 2.0) ) 


"""
Implementation using map, filter, lambda
"""

def ortho_transformed_smeared_py(d_max, n, height, width, q, npts):
    y = 0
    z = 0
    sum = 0

    i = 0
    j = 0
    n_height = 0
    n_width = 0
    count_w = 0
    fnpts = 0
    sum = 0.0
    fnpts = float(npts-1.0)
    
    n_height = (1, npts)[height>0]
    n_width = (1, npts)[width>0]
    

    count_w = 0.0

    z_func = lambda j,height=height,fnpts=fnpts : (0.0, height/fnpts*float(j))[height>0]
    
    j_iter = np.arange(n_height)
    i_iter = np.arange(n_width)

    z_result = map(z_func, j_iter)
    
    z_values = np.fromiter((z_result), dtype = np.float)

    y_func = lambda i, width=width, fnpts=fnpts : (0.0, -width/2.0+width/fnpts*float(i))[width>0]
    
    y_result = map(y_func, i_iter)
    y_values = np.fromiter((y_result), dtype = np.float)


    calc_func = lambda y,z,q=q : (((q - y) * (q - y) + z * z))
    calc_values = np.zeros([n_width * n_height])
    for i in range(0, n_height):
        for j in range(0, n_width): 
            calc_values[i + (j * n_width)]= calc_func(y_values[i], z_values[j])

    result_to_transform = filter(lambda x : x > 0, calc_values)

    vals_to_transform = np.fromiter((result_to_transform), dtype = np.float)

    
    transformed_values = map(lambda x : ortho_transformed_py(d_max, n, math.sqrt(x)), vals_to_transform)
    count_w = calc_values.shape[0]
    final_vals = np.fromiter(transformed_values, dtype = np.float)
    sum = np.sum(final_vals)
    
    return sum/count_w

"""
Basic implementation in Python for reference
"""
def ortho_transformed_smeared(d_max, n, height, width, q, npts):
    y = 0
    z = 0
    sum = 0

    i = 0
    j = 0
    n_height = 0
    n_width = 0
    count_w = 0
    fnpts = 0
    sum = 0.0
    fnpts = float(npts-1.0)

    n_height = (1, npts)[height>0]
    n_width = (1, npts)[width>0]

    count_w = 0.0

    for j in range(0,n_height):
        if(height>0):
            z = height/fnpts* float(j)
        else:
            z = 0.0
        for i in range(0, n_width):
            if(width>0):
                y = -width/2.0+width/fnpts* float(i)
            else:
                y = 0.0
            if (((q - y) * (q - y) + z * z) > 0.0):
                count_w += 1.0
                sum += ortho_transformed_py(d_max, n, math.sqrt((q - y)*(q - y) + z * z))
    return sum / count_w

start = time.clock()
x = ortho_transformed_smeared_py(1, 1, 1000, 1000, 1, 5)
end = time.clock()
print(x)
print("Time elapsed py : %s" % (end - start))

start = time.clock()
y = ortho_transformed_smeared(1, 1, 1000, 1000, 1, 5)
end = time.clock()
print(y)
print("Time elapsed normal : %s" % (end - start))



start = time.clock()
z = ortho_transformed_smeared(1, 1, 1000, 1000, 1, 5)
end = time.clock()
print(z)
print("Time elapsed normal : %s" % (end - start))

start = time.clock()
l = ortho_transformed_smeared_py(1, 1, 1000, 1000, 1, 5)
end = time.clock()
print(l)
print("Time elapsed py : %s" % (end - start))
