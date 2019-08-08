"""
Converted invertor.c's methods.
Implements low level inversion functionality, at the moment Numba is conditional, has about
a 2x slowdown without Numba.
"""
import sys
import math
import time
import copy
import os
import re
import logging
import time

import numpy as np
#from numpy import pi
from functools import reduce

pi = np.float64(3.1416) #Temporary, to pass tests.

try:
    from numba import njit
except ImportError:
    # identity decorator for njit which ignores type signature.
    njit = lambda *args, **kw: (lambda x: x)

@njit('f8(f8, f8)')
def pr_sphere(R, r):
    """
    P(r) of a sphere, for test purposes

    :param R: radius of the sphere
    :param r: distance, in same units as the radius
    :return: P(r)
    """
    if(r <= 2.0*R):
        return 12.0* (0.5*r/R)**2 * (1.0-0.5*r/R)**2 * (2.0+0.5*r/R)
    else:
        return 0

@njit('f8(f8, u8, f8)')
def ortho(d_max, n, r):
    """
    Orthogonal Functions:
    B(r) = 2r sin(pi*nr/d)
    """
    return (2.0 * r) * np.sin(pi*(n*r)/d_max)

@njit('f8(f8, u8, f8)')
def ortho_derived(d_max, n, r):
    """
    First derivative in of the orthogonal function dB(r)/dr
    """
    pinr = pi * n * r/d_max
    return 2.0 * np.sin(pinr) + 2.0 * r * np.cos(pinr)

@njit('f8(f8[:], f8, f8)')
def pr(pars, d_max, r):
    """
    P(r) calculated from the expansion
    """
    sum = 0.0
    for i in range(pars.shape[0]):
        sum += pars[i] * ortho(d_max, i+1, r)
    return sum

@njit('f8[:](f8[:], f8[:,:], f8, f8)')
def pr_err(pars, err, d_max, r):
    """
    P(r) calculated from the expansion,
    with errors
    changed to instead of return value by reference, returns
    np array of [pr_value, pr_value_err]
    """
    sum = 0.0
    sum_err = 0.0
    func_value = 0.0
    n_c = pars.shape[0]

    for i in range(n_c):
        func_value = ortho(d_max, i+1, r)
        sum += pars[i] * func_value
        sum_err += err[i, i] * func_value * func_value

    pr_value = np.float64(sum)
    if(sum_err > 0):
        pr_value_err = np.sqrt(sum_err)
    else:
        pr_value_err = sum

    ret = np.zeros(2, dtype = np.float64)
    ret[0] = pr_value
    ret[1] = pr_value_err
    return ret

@njit('f8(f8[:], f8, f8)')
def dprdr(pars, d_max, r):
    sum = 0.0
    for i in range(0, pars.shape[0]):
        sum += pars[i] * 2.0*(np.sin(pi*(i+1)*r/d_max) + pi*(i+1)*r/d_max * np.cos(pi*(i+1)*r/d_max))
    return sum

@njit('f8[:](f8[:], f8, i8)')
def ortho_transformed(q, d_max, n):
    return 8.0*(pi)**2/q * d_max * n * (-1.0)**(n+1) * np.sin(q*d_max) / ( (pi*n)**2 - (q*d_max)**2 )

@njit('f8[:](f8[:], f8, i8, f8, f8, u8)')
def ortho_transformed_smeared(q, d_max, n, height, width, npts):
    n_width = npts if width > 0 else 1
    n_height = npts if height > 0 else 1
    dz = height/(npts-1)
    y0, dy = -0.5*width, width/(npts-1)
    total = np.zeros(len(q), dtype=np.float64)

    for j in range(n_height):
        zsq = (j * dz)**2
        for i in range(n_width):
            y = y0 + i*dy
            qsq = (q - y)**2 + zsq
            total += ortho_transformed(np.sqrt(qsq), d_max, n)

    return total / (n_width*n_height)

@njit('f8[:](f8[:], f8[:], f8, f8, f8, u8)')
def iq_smeared(p, q, d_max, height, width, npts):
    size_q = len(q)
    size_p = len(p)
    total = np.zeros(size_q, dtype=np.float64)

    for i in range(size_p):
        total += p[i] * ortho_transformed_smeared(q, d_max, i+1, height, width, npts)

    return total

@njit('f8[:](f8[:], f8, f8[:])')
def iq(pars, d_max, q):
    """
    Scattering intensity calculated from the expansion
    :param: pars
    :param: d_max
    :param: q, scalar or vector.
    :return: vector of results, len 1 if q was scalar
    """
    sum = np.zeros(len(q), dtype = np.float64)

    for i in range(len(pars)):
        sum += pars[i] * ortho_transformed(q, d_max, i+1)

    return sum

@njit('f8(f8[:], f8, u8)')
def reg_term(pars, d_max, nslice):
    """
    Regularization term calculated from the expansion.
    """
    sum = 0.0
    r = 0.0
    deriv = 0.0
    nslice_d = np.float64(nslice)

    for i in range(nslice):
        r = d_max/nslice_d * i
        deriv = dprdr(pars, d_max, r)
        sum += deriv * deriv

    return sum/nslice_d * d_max

@njit('f8(f8[:], f8, u8)')
def int_p2(pars, d_max, nslice):
    """
    Regularization term calculated from the expansion.
    """
    sum = 0.0
    r = 0.0
    value = 0.0
    nslice_d = np.float64(nslice)

    for i in range(nslice):
        r = d_max/nslice_d * i
        value = pr(pars, d_max, r)
        sum += value * value

    return sum/nslice_d * d_max

@njit('f8(f8[:], f8, u8)')
def int_pr(pars, d_max, nslice):
    """
    Integral of P(r)
    """
    sum = 0.0
    r = 0.0
    value = 0.0
    nslice_d = np.float64(nslice)

    for i in range(nslice):
        r = d_max/nslice_d * i
        value = pr(pars, d_max, r)
        sum += value

    return sum/nslice_d * d_max

@njit('u8(f8[:], f8, u8)')
def npeaks(pars, d_max, nslice):
    """
    Get the number of P(r) peaks
    """
    r = 0.0
    value = 0.0
    previous = 0.0
    slope = 0.0
    count = 0

    for i in range(nslice):
        r = d_max/np.float64(nslice) * i
        value = pr(pars, d_max, r)
        if(previous <= value):
            slope = 1
        else:
            if(slope > 0):
                count += 1
            slope = -1
        previous = value

    return count

@njit('f8(f8[:], f8, u8)')
def positive_integral(pars, d_max, nslice):
    """
    Get the fraction of the integral of P(r) over the whole
    range of r that is above 0.
    A valid P(r) is defined as being positive for all r.
    """
    r = 0.0
    value = 0.0
    sum_pos = 0.0
    sum = 0.0
    nslice_d = np.float64(nslice)

    for i in range(nslice):
        r = d_max/nslice_d * i
        value = pr(pars, d_max, r)
        if(value > 0.0):
           sum_pos += value
        sum += math.fabs(value)
    return sum_pos / sum

@njit('f8(f8[:], f8[:,:], f8, u8)')
def positive_errors(pars, err, d_max, nslice):
    """
    Get the fraction of the integral of P(r) over the whole range
    of r that is at least one sigma above 0.
    """
    r = 0.0
    sum_pos = 0.0
    sum = 0.0
    nslice_d = np.float64(nslice)

    for i in range(nslice):
        r = d_max/nslice_d * i
        (pr_val, pr_val_err) = pr_err(pars, err, d_max, r)
        if(pr_val > pr_val_err):
            sum_pos += pr_val
        sum += np.fabs(pr_val)

    return sum_pos / sum

@njit('f8(f8[:], f8, u8)')
def rg(pars, d_max, nslice):
    """
    R_g radius of gyration calculation

    R_g**2 = integral[r**2 * p(r) dr] / (2.0 * integral[p(r) dr])
    """
    sum_r2 = 0.0
    sum = 0.0
    r = 0.0
    value = 0.0

    for i in range(nslice):
        r = (d_max/nslice) * i
        value = pr(pars, d_max, r)
        sum += value
        sum_r2 += r * r * value

    return np.sqrt(sum_r2 / (2.0*sum))