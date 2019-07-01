
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
from numba import njit, vectorize, float64

tests = 5

"""
Starting to convert invertor.c, eventually the Cinvertor class to python

At the moment experimenting with different methods of implementing individual
functions.
"""

"""
ortho transformed implemented in Python


With vectorize time was 
@vectorize() ~= 1.4e-05
@njit() ~= 3e-06
@njit(parallel=True) - Compiler returns no transformation for parallel execution possible
and time was the same as @njit()
"""
@njit()
def ortho_transformed(d_max, n, q):
    return 8.0*(np.pi)**2/q * d_max * n * (-1.0)**(n+1) * np.sin(q*d_max) / ( (np.pi*n)**2 - (q*d_max)**2 )

#For loop implementation using njit
#@njit() - 5 - time roughly 4.5e-05
#@njit() - npts 1000 - 0.031
#@njit(parallel = True) - no transformation possible same time.
#@vectorize([float64(float64, float64, float64, float64, float64, float64)])  npts = 5 ~= 1.6e-05
#npts = 1000 ~= 0.02
@njit()
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
    if(height > 0):
        n_height = npts
    else:
        n_height = 1
    if(width > 0):
        n_width = npts
    else:
        n_width = 1

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
                sum += ortho_transformed(d_max, n, math.sqrt((q - y)*(q - y) + z * z))
    return sum / count_w

for i in range(0, tests):
    start = time.clock()
    x = ortho_transformed_smeared_old(1, 1, 1, 1, 1, 1000)
    end = time.clock()
    print(x)
    print("Time elapsed py : %s" % (end - start))
