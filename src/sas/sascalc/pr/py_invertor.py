"""
Starting to convert invertor.c, eventually the Cinvertor class to python

At the moment experimenting with different methods of implementing individual
functions.
"""
import numpy as np
import sys
import math
import time
import copy
import os
import re
import logging
import time
from numba import njit, vectorize, float64

#class stub for final Pinvertor class
#taking signatures from Cinvertor.c and docstrings
class Pinvertor:
    def __init__(self):
        pass
    def residuals(self, args):
        """
        Function to call to evaluate the residuals\n
	    for P(r) inversion\n
	    @param args: input parameters\n
	    @return: list of residuals
        """
        pass

#Private Methods
@njit
def pr_sphere(R, r):
    if(r <= 2.0*R):
        return 12.0* (0.5*r/R)**2 * (1.0-0.5*r/R)**2 * (2.0+0.5*r/R)
    else:
        return 0

#@njit()
def ortho_transformed(d_max, n, q):
    """
    Fourier transform of the nth orthagonal function
    
    With vectorize time was 
    \@vectorize() ~= 1.4e-05
    \@njit() ~= 3e-06
    \@njit(parallel=True) - Compiler returns no transformation for parallel execution possible
    and time was the same as @njit()
    """
    return 8.0*(np.pi)**2/q * d_max * n * (-1.0)**(n+1) * np.sin(q*d_max) / ( (np.pi*n)**2 - (q*d_max)**2 )
    #pi = math.pi
    #qd = q * (d_max/math.pi)
    #return ( 8.0 * d_max**2/pi * n * (-1.0)**(n+1) ) * np.sinc(qd) / (n**2 - qd**2)

def quick_demo():
    print(ortho_transformed(1,1,1))

@njit()
def ortho_transformed_smeared(d_max, n, height, width, q, npts):
    """
    Slit-smeared Fourier transform of the nth orthagonal function.
    Smearing follows Lake, Acta Cryst. (1967) 23, 191.

    \@njit() - 5 - time roughly 4.5e-05
    \@njit() - npts 1000 - 0.031
    \@njit(parallel = True) - no transformation possible same time.
    \@vectorize([float64(float64, float64, float64, float64, float64, float64)])  npts = 5 ~= 1.6e-05
    npts = 1000 ~= 0.02
    """
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

    #Pre compute dz, y0 and dy
    dz = height/fnpts
    y0, dy = -0.5*width, width/fnpts

    for j in range(0, n_height):
        zsq = (j * dz)**2

        for i in range(0, n_width):
            y = y0 + i*dy
            qsq = (q - y)**2 + zsq
            count_w += qsq > 0
            sum += ortho_transformed(d_max, n, math.sqrt(qsq))
    return sum / count_w

def demo():
    tests = 5
    for i in range(0, tests):
        start = time.clock()
        x = ortho_transformed_smeared(1, 1, 1, 1, 1, 5)
        end = time.clock()
        print(x)
        print("Time elapsed py : %s" % (end - start))

if(__name__ == "__main__"):
    quick_demo()
