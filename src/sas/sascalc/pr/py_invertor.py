"""
Starting to convert invertor.c, eventually the Cinvertor class to python

At the moment experimenting with different methods of implementing individual
functions.
"""
import numpy as np
from numpy import pi
import sys
import math
import time
import copy
import os
import re
import logging
import time
from numba import jit, njit, vectorize, float64, guvectorize, prange

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


@njit()
def pr_sphere(R, r):
    """
    P(r) of a sphere, for test purposes

    @param R: radius of the sphere
    @param r: distance, in same units as the radius
    @return: P(r)
    """
    if(r <= 2.0*R):
        return 12.0* (0.5*r/R)**2 * (1.0-0.5*r/R)**2 * (2.0+0.5*r/R)
    else:
        return 0

@njit()
def ortho(d_max, n, r):
    """
    Orthogonal Functions:
    B(r) = 2r sin(pi*nr/d)
    """
    return 2.0 * r * np.sin(pi * n * r/d_max)

@njit()
def ortho_transformed(d_max, n, q):
    """
    Fourier transform of the nth orthagonal function
    
    With vectorize time was 
    \@vectorize() ~= 1.4e-05
    \@njit() ~= 3e-06
    \@njit(parallel=True) - Compiler returns no transformation for parallel execution possible
    and time was the same as @njit()
    """
    #return 8.0*(np.pi)**2/q * d_max * n * (-1.0)**(n+1) * math.sin(q*d_max) / ( (math.pi*n)**2 - (q*d_max)**2 )
    qd = q * (d_max/pi)
    return ( 8.0 * d_max**2/pi * n * (-1.0)**(n+1) ) * np.sinc(qd) / (n**2 - qd**2)



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
    dz = height/(npts-1)
    y0 = -0.5*width
    dy = width/(npts-1)

    for j in range(0, n_height):
        zsq = (j * dz)**2

        for i in range(0, n_width):
            y = y0 + i*dy
            qsq = (q - y)**2 + zsq
            count_w += qsq > 0
            sum += ortho_transformed(d_max, n, np.sqrt(qsq))
    return sum / count_w

@njit()
def ortho_derived(d_max, n, r):
    """
    First derivative in of the orthogonal function dB(r)/dr
    """
    pinr = pi * n * r/d_max
    return 2.0 * np.sin(pinr) + 2.0 * r * np.cos(pinr)

@njit(parallel = True)
def iq(pars, d_max, q):
    """
    Scattering intensity calculated from the expansion

    Dataset of 10,000 pars 302 q
    using njit, parallel ~= 0.04
    using njit default ~= 0.11
    using vectorize ~= 7
    using default python ~= 18
    """
    #q = np.asanyarray(q)
    sum = 0.0
    for i in prange(pars.shape[0]):
        for j in prange(q.shape[0]):
            sum += pars[i] * ortho_transformed(d_max, i + 1, q[j])
    return sum

def iq_vectorize(pars, d_max, q):
    """
    Scattering intensity calculated from the expansion

    basic python ~=0.00014 with array of size 20
    vectorised operations ~= 0.0002
    using njit, no parallel possible ~= 1.3e-05

    Array size 300 
    3386 result
    """
    q = np.asanyarray(q)
    def result(x, y):
        def apply_q(q):
            return x * ortho_transformed(d_max, y + 1, q)
        g = np.vectorize(apply_q)
        return np.sum(g(q[0]))

    f = np.vectorize(result)
    result = f(pars, np.arange(pars.shape[0]))

    final_result = np.sum(result)

    return final_result

@njit()
def parallel_test(n):
    shp = (13, 17)
    result1 = 2 * np.ones(shp, np.int_)
    tmp = 2 * np.ones_like(result1)

    for i in prange(n):
        result1 *= tmp

    return result1


@njit(parallel = True)
def iq_smeared(pars, d_max, height, width, q, npts):
    """
    Scattering intensity calculated from expansion,
    slit smeared.

    for test data of size 20 ~= 0.0005 basic
    ~= 0.0003 njit
    ~= 0.12 using numba vectorize()
    Couldn't use njit and vectorize in same method, looked on
    github seems to be issue for a long time with numba.
    Maybe faster if work together ?
    njit() compilation only slightly faster. Maybe with working
    njit() and vector operations be faster.
    
    iq_smeared(np.arange(10000), 3, 100, 100, 30, 400) - no parallel - 75
    - parallel - 23.13, over 3x speedup. 
    
    """
    sum = 0.0

    for i in prange(pars.shape[0]):
        sum += pars[i] * ortho_transformed_smeared(d_max, i + 1, height, width, q, npts)
    return sum

@njit()
def pr(pars, d_max, r):
    """
    P(r) calculated from the expansion
    """
    sum = 0.0
    for i in range(0, pars.shape[0]):
        sum += pars[i] * ortho(d_max, i+1, r)
    return sum

@njit()
def pr_err(pars, err, d_max, r, pr_value, pr_value_err):
    """
    P(r) calculated from the expansion,
    with errors
    """
    sum = 0.0
    sum_err = 0.0
    func_value = 0
    n_c = pars.shape[0]
    
    for i in range(0, n_c):
        func_value = ortho(d_max, i+1, r)
        sum += pars[i] * func_value
        sum_err += err[i * n_c + i] * func_value * func_value
    
    pr_value = sum
    if(sum_err > 0):
        pr_value_err = np.sqrt(sum_err)
    else:
        pr_value_err = sum

@njit()
def dprdr(pars, d_max, r):
    #test sample 10,000 - 0.00039/38
        #adv - 0.00048
        
    sum = 0.0
    #300, 2.5e-05
    for i in range(0, pars.shape[0]):
        sum += pars[i] * 2.0*(np.sin(pi*i+1)*r/d_max) + pi*(i+1)*r/d_max * np.cos(pi*(i+1)*r/d_max)
    return sum

@njit()
def dprdr_adv(pars, d_max, r):
    sum = 0.0
    var = pi * r/d_max
    def func(x, y):
        temp = (x + 1) * var
        return y * 2.0 * (np.sin(temp) + temp * np.cos(temp))

    for i in range(0, pars.shape[0]):
        sum += func(i, pars[i])
    return sum





#testing

def demo_ot():
    print(pr(np.arange(100), 20, 100))


def demo():
    tests = 6
    minq = 0
    maxq = 30000
    q = np.arange(minq, maxq, maxq/301)
    #iq(np.arange(10000), 3, q)
    print(q)
    for i in range(0, tests): 
        start = time.clock() 
        x = iq_smeared(np.arange(10000), 3, 100, 100, 30, 400)
        end = time.clock()
        print("Time elapsed py : %s" % (end - start))
        
if(__name__ == "__main__"):
    demo_ot()