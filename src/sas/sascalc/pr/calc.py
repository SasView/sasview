"""
Converted invertor.c's methods.
Implements low level inversion functionality, with conditional Numba njit compilation.
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
from numpy import pi
from functools import reduce

try:
    raise ImportError
    from numba import njit
except ImportError:
    #Identity decorator for njit which ignores type signature.
    njit = lambda *args, **kw: (lambda x: x)

@njit('f8[:](f8, u8, f8[:])')
def ortho(d_max, n, r):
    """
    Orthogonal Functions:
    B(r) = 2r sin(pi*nr/d)

    :param d_max: d_max.
    :param n: n.

    :return: B(r).
    """
    return (2.0 * r) * np.sin(pi*(n*r)/d_max)

@njit('f8(f8, u8, f8)')
def ortho_derived(d_max, n, r):
    """
    First derivative in of the orthogonal function dB(r)/dr.

    :param d_max: d_max.
    :param n: n.

    :return: First derivative in dB(r)/dr.
    """
    pinr = pi * n * r/d_max
    return 2.0 * np.sin(pinr) + 2.0 * r * np.cos(pinr)

@njit('f8[:](f8[:], f8, f8[:])')
def pr(pars, d_max, r):
    """
    P(r) calculated from the expansion

    :param pars: c-parameters.
    :param d_max: d_max.
    :param r: r-value to evaluate P(r).

    :return: P(r).
    """
    total = np.zeros(len(r))
    for i in range(len(pars)):
        total += pars[i] * ortho(d_max, i+1, r)
    return total

@njit('f8[:, :](f8[:], f8[:,:], f8, f8[:])')
def pr_err(pars, err, d_max, r):
    """
    P(r) calculated from the expansion,
    with errors.

    :param pars: c-parameters.
    :param err: err.
    :param r: r-value.

    :return: [P(r), dP(r)].
    """
    total = np.zeros(len(r))
    total_err = np.zeros(len(r))
    n_c = len(pars)
    for i in range(n_c):
        func_values = ortho(d_max, i+1, r)
        total += pars[i] * func_values
        total_err += err[i, i] * (func_values ** 2)

    pr_value = total

    pr_value_err = np.zeros(len(total_err))
    index_greater = total_err > 0
    index_less = total_err <= 0
    pr_value_err[index_greater] = np.sqrt(total_err[index_greater])
    pr_value_err[index_less] = total[index_less]
    #pr_value_err = np.sqrt(total_err) if (total_err > 0) else total

    ret = np.zeros((2, len(r)), dtype = np.float64)
    ret[0, :] = pr_value
    ret[1, :] = pr_value_err
    return ret

@njit('f8[:](f8[:], f8, f8)')
def f(i, d_max, r):
    return 2.0*(np.sin(pi*(i+1)*r/d_max) + pi*(i+1)*r/d_max * np.cos(pi*(i+1)*r/d_max))

@njit('f8(f8[:], f8, f8)')
def dprdr(pars, d_max, r):
    """
    dP(r)/dr calculated from the expansion.

    :param pars: c-parameters.
    :param d_max: d_max.
    :param r: r-value.

    :return: dP(r)/dr.
    """
    total = 0.0

    total = np.dot(np.ascontiguousarray(pars), np.ascontiguousarray(f(np.arange(1.0, pars.shape[0] + 1), d_max, r)))
    return total


@njit('f8[:](f8[:], f8, i8)')
def ortho_transformed(q, d_max, n):
    """
    Fourier transform of the nth orthogonal function.

    :param q: q (vector).
    :param d_max: d_max.
    :param n: n.

    :return: Fourier transform of nth orthogonal function across all q.
    """
    return 8.0*(pi)**2/q * d_max * n * (-1.0)**(n+1) * np.sin(q*d_max) / ( (pi*n)**2 - (q*d_max)**2 )

@njit('f8[:](f8[:], f8, i8, f8, f8, u8)')
def ortho_transformed_smeared(q, d_max, n, height, width, npts):
    """
    Slit-smeared Fourier transform of the nth orthogonal function.
    Smearing follows Lake, Acta Cryst. (1967) 23, 191.

    :param q: q (vector).
    :param d_max: d_max.
    :param n: n.
    :param height: slit_height.
    :param width: slit_width.
    :param npts: npts.

    :return: Slit-smeared Fourier transform of nth orthogonal function across all q.
    """
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
    """
    Scattering intensity calculated from the expansion, slit-smeared.

    :param p: c-parameters.
    :param q: q (vector).
    :param height: slit_height.
    :param width: slit_width.
    :param npts: npts.

    :return: Scattering intensity from the expansion slit-smeared across all q.
    """
    size_q = len(q)
    size_p = len(p)
    total = np.zeros(size_q, dtype=np.float64)

    for i in range(size_p):
        total += p[i] * ortho_transformed_smeared(q, d_max, i+1, height, width, npts)

    return total

@njit('f8[:](f8[:], f8, f8[:])')
def iq(pars, d_max, q):
    """
    Scattering intensity calculated from the expansion.

    :param pars: c-parameters.
    :param d_max: d_max.
    :param q: q (vector).

    :return: Scattering intensity from the expansion across all q.
    """
    total = np.zeros(len(q), dtype = np.float64)

    for i in range(len(pars)):
        total += pars[i] * ortho_transformed(q, d_max, i+1)

    return total

@njit('f8(f8[:], f8, u8)')
def reg_term(pars, d_max, nslice):
    """
    Regularization term calculated from the expansion.

    :param pars: c-parameters.
    :param d_max: d_max.
    :param nslice: nslice.

    :return: Regularization term calculated from the expansion.
    """
    total = 0.0
    r = 0.0
    deriv = 0.0
    nslice_d = np.float64(nslice)

    for i in range(nslice):
        r = d_max/nslice_d * i
        deriv = dprdr(pars, d_max, r)
        total += deriv * deriv

    return total/nslice_d * d_max

@njit('f8(f8[:], f8, u8)')
def int_p2(pars, d_max, nslice):
    """
    Regularization term calculated from the expansion.

    :param pars: c-parameters.
    :param d_max: d_max.
    :param nslice: nslice.

    :return:  Regularization term calculated from the expansion.
    """
    total = 0.0
    r = 0.0
    value = 0.0
    nslice_d = np.float64(nslice)
    i_r = np.arange(nslice)
    r = d_max/nslice_d * i_r
    values = pr(pars, d_max, r)
    total = np.sum(values ** 2)
    #for i in range(nslice):
    #    r = d_max/nslice_d * i
    #    value = pr(pars, d_max, r)
    #    total += value * value

    return total/nslice_d * d_max

@njit('f8(f8[:], f8, u8)')
def int_pr(pars, d_max, nslice):
    """
    Integral of P(r).

    :param pars: c-parameters.
    :param d_max: d_max.
    :param nslice: nslice.

    :return: Integral of P(r).
    """
    total = 0.0
    r = 0.0
    value = 0.0
    nslice_d = np.float64(nslice)

    i_r = np.arange(nslice)
    r = d_max/nslice_d * i_r
    values = pr(pars, d_max, r)

    total = np.sum(values)
    #for i in range(nslice):
    #    r = d_max/nslice_d * i
    #    value = pr(pars, d_max, r)
    #    total += value

    return total/nslice_d * d_max

@njit('u8(f8[:], f8, u8)')
def npeaks(pars, d_max, nslice):
    """
    Get the number of P(r) peaks.

    :param pars: c-parameters.
    :param d_max: d_max.
    :param nslice: nslice.

    :return: Number of P(r) peaks.
    """
    r = 0.0
    value = 0.0
    previous = 0.0
    slope = 0.0
    count = 0
    i_r = np.arange(nslice)
    r = d_max/np.float64(nslice) * i_r
    values = pr(pars, d_max, r)

    for i in range(nslice):
        value = values[i]
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

    :param pars: c-parameters.
    :param d_max: d_max.
    :param nslice: nslice.

    :return: The fraction of the integral of P(r) over the whole
    range of r that is above 0.
    """
    r = 0.0
    value = 0.0
    total_pos = 0.0
    total = 0.0
    nslice_d = np.float64(nslice)
    i_r = np.arange(nslice)
    r = d_max/nslice_d * i_r
    values = pr(pars, d_max, r)

    for i in range(nslice):
        value = values[i]
        if(value > 0.0):
           total_pos += value
        total += math.fabs(value)
    return total_pos / total

@njit('f8(f8[:], f8[:,:], f8, u8)')
def positive_errors(pars, err, d_max, nslice):
    """
    Get the fraction of the integral of P(r) over the whole range
    of r that is at least one sigma above 0.

    :param pars: c-parameters.
    :param err: error terms.
    :param d_max: d_max.
    :param nslice: nslice.

    :return: The fraction of the integral of P(r) over the whole range
    of r that is at least one sigma above 0.
    """
    r = 0.0
    total_pos = 0.0
    total = 0.0
    nslice_d = np.float64(nslice)
    i_r = np.arange(nslice)
    r = d_max/nslice_d * i_r
    full = pr_err(pars, err, d_max, r)

    for i in range(nslice):
        pr_val, pr_val_err = full[0, i], full[1, i]
        if(pr_val > pr_val_err):
            total_pos += pr_val
        total += np.fabs(pr_val)

    return total_pos / total

@njit('f8(f8[:], f8, u8)')
def rg(pars, d_max, nslice):
    """
    R_g radius of gyration calculation

    R_g**2 = integral[r**2 * p(r) dr] / (2.0 * integral[p(r) dr])

    :param pars: c-parameters.
    :param d_max: d_max.
    :param nslice: nslice.

    :return: R_g radius of gyration.
    """
    total_r2 = 0.0
    total = 0.0
    r = 0.0
    value = 0.0
    i_r = np.arange(nslice)
    r = (d_max / nslice) * i_r
    values = pr(pars, d_max, r)

    for i in range(nslice):
        value = values[i]
        total += value
        total_r2 += (r[i]**2)  * value

    return np.sqrt(total_r2 / (2.0*total))

