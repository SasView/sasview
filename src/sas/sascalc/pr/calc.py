"""
Converted invertor.c's methods.
Implements low level inversion functionality, with conditional Numba njit compilation.
"""
from __future__ import division


import numpy as np
from numpy import pi


try:
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
    return (2.0 * r) * np.sin((pi*n/d_max)*r)

#TODO: unused?
@njit('f8[:](f8, u8, f8[:])')
def ortho_derived(d_max, n, r):
    """
    First derivative in of the orthogonal function dB(r)/dr.

    :param d_max: d_max.
    :param n: n.

    :return: First derivative in dB(r)/dr.
    """
    pinr = (pi * n / d_max) * r
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
    for i, pars_i in enumerate(pars):
        total += pars_i * ortho(d_max, i+1, r)
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

    for i, pars_i in enumerate(pars):
        func_values = ortho(d_max, i+1, r)
        total += pars_i * func_values
        total_err += err[i, i] * (func_values ** 2)

    pr_value = total

    pr_value_err = np.zeros(len(total_err))
    index_greater = total_err > 0
    index_less = total_err <= 0
    pr_value_err[index_greater] = np.sqrt(total_err[index_greater])
    pr_value_err[index_less] = total[index_less]
    #pr_value_err = np.sqrt(total_err) if (total_err > 0) else total

    ret = np.zeros((2, len(r)), dtype=np.float64)
    ret[0, :] = pr_value
    ret[1, :] = pr_value_err
    return ret

@njit('f8[:](f8, f8, f8[:])')
def dprdr_calc(i, d_max, r):
    return 2.0*(np.sin(pi*(i+1)*r/d_max) + pi*(i+1)*r/d_max * np.cos(pi*(i+1)*r/d_max))

@njit('f8[:](f8[:], f8, f8[:])')
def dprdr(pars, d_max, r):
    """
    dP(r)/dr calculated from the expansion.

    :param pars: c-parameters.
    :param d_max: d_max.
    :param r: r-value.

    :return: dP(r)/dr.
    """
    total = np.zeros(len(r))
    for i, pars_i in enumerate(pars):
        total += pars_i * dprdr_calc(i, d_max, r)
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
    qd = q * (d_max/pi)
    return ( 8.0 * d_max**2 * n * (-1.0)**(n+1) ) * np.sinc(qd) / (n**2 - qd**2)

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
    total = np.zeros(size_q, dtype=np.float64)

    for i, p_i in enumerate(p):
        total += p_i * ortho_transformed_smeared(q, d_max, i+1, height, width, npts)

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
    total = np.zeros(len(q), dtype=np.float64)

    for i, pars_i in enumerate(pars):
        total += pars_i * ortho_transformed(q, d_max, i+1)

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
    dx = d_max/nslice
    r = np.linspace(0., d_max - dx, nslice)
    deriv = dprdr(pars, d_max, r)
    total = np.sum(deriv ** 2)

    return total*dx

@njit('f8(f8[:], f8, u8)')
def int_pr_square(pars, d_max, nslice):
    """
    Regularization term calculated from the expansion.

    :param pars: c-parameters.
    :param d_max: d_max.
    :param nslice: nslice.

    :return:  Regularization term calculated from the expansion.
    """
    dx = d_max/nslice
    r = np.linspace(0., d_max - dx, nslice)
    values = pr(pars, d_max, r)
    total = np.sum(values ** 2)
    
    return total * dx

@njit('f8(f8[:], f8, u8)')
def int_pr(pars, d_max, nslice):
    """
    Integral of P(r).

    :param pars: c-parameters.
    :param d_max: d_max.
    :param nslice: nslice.

    :return: Integral of P(r).
    """
    dx = d_max/nslice
    r = np.linspace(0., d_max - dx, nslice)
    values = pr(pars, d_max, r)

    total = np.sum(values)

    return total * dx

@njit('u8(f8[:], f8, u8)')
def npeaks(pars, d_max, nslice):
    """
    Get the number of P(r) peaks.

    :param pars: c-parameters.
    :param d_max: d_max.
    :param nslice: nslice.

    :return: Number of P(r) peaks.
    """
    dx = d_max/nslice
    r = np.linspace(0., d_max - dx, nslice)
    values = pr(pars, d_max, r)

    # Build an index vector with True for ascending and false for flat or descending
    pos = values[:-1] < values[1:]
    # Count the number of slope changes
    count = np.sum((pos[:-1] != pos[1:]) & pos[:-1])
    # Check if starting descending or ending ascending
    count += 1 - pos[0] + pos[-1]

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
    dx = d_max/nslice
    r = np.linspace(0., d_max - dx, nslice)
    values = pr(pars, d_max, r)

    total = np.sum(np.fabs(values))
    total_pos = np.sum(values[values > 0.0])
    return 0 if total == 0 else total_pos / total

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
    dx = d_max/nslice
    r = np.linspace(0., d_max - dx, nslice)
    pr_vals = pr_err(pars, err, d_max, r)

    pr_val = pr_vals[0, :]
    pr_val_err = pr_vals[1, :]

    total = np.sum(np.fabs(pr_val))

    index = pr_val > pr_val_err
    total_pos = np.sum(pr_val[index])
    return 0 if total == 0 else total_pos / total

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
    dx = d_max/nslice
    r = np.linspace(0., d_max - dx, nslice)
    values = pr(pars, d_max, r)

    total = np.sum(values)
    total_r2 = np.sum((r ** 2) * values)
    return 0 if total == 0 else np.sqrt(total_r2 / (2.0*total))  # dx cancels
