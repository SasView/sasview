"""
Compute scattering from a set of points.

For 1-D scattering use *Iq(q, x, y, z, sld, vol, is_avg)*
"""
import os

import numpy as np

try:
    if os.environ.get('SAS_NUMBA', '1').lower() in ('1', 'yes', 'true', 't'):
        from numba import njit
    else:
        raise ImportError("fail")
except ImportError:
    # if no numba then njit does nothing
    def njit(*args, **kw):
        # Check for bare @njit, in which case we just return the function.
        if len(args) == 1 and callable(args[0]) and not kw:
            return args[0]
        # Otherwise we have @njit(...), so return the identity decorator.
        return lambda fn: fn

# TODO: probably twice as fast to use f4 everywhere, but need to check accuracy
def Iq(q, x, y, z, sld, vol, is_avg=False):
    """
    Computes 1D isotropic.

    Isotropic: Assumes all slds are real (no magnetic)

    Also assumes there is no polarization: No dependency on spin.

    All values must be numpy vectors of the correct size.

    Returns *I(q)*
    """
    coords = np.vstack((x, y, z))
    index = (sld != 0.)
    if not index.all():
        coords, sld, vol = (v[index] for v in (sld, coords, vol))
    I_out = np.empty_like(q, dtype='d')
    if is_avg:
        r = np.linalg.norm(coords, axis=0)
        #print('avg', I_out.shape, q.shape, r.shape, sld.shape, vol.shape)
        _calc_Iq_avg(I_out, q, r, sld, vol)
    else:
        #print('not avg', I_out.shape, q.shape, coords.shape, sld.shape, vol.shape)
        _calc_Iq(I_out, q, coords, sld, vol)
    return I_out * (1.0E+8/np.sum(vol))

def Iqxy(qx, qy, x, y, z, sld, vol, mx, my, mz, in_spin, out_spin, s_theta):
    """
    Computes 2D anisotropic.

    *in_spin* and *out_spin* indicate portion of polarizer and analyzer
    transmission that are spin up.  *s_theta* is the polarization direction.

    All other values must be numpy vectors of the correct size.

    Returns *I(qx, qy)*
    """
    qx, qy = np.broadcast_arrays(qx, qy)
    is_magnetic = (mx != 0.) | (my != 0.) | (mz != 0.)
    if is_magnetic.any():
        index = (sld != 0.) | is_magnetic
        if not index.all():
            x, y, mx, my, mz, sld, vol \
                = (v[index] for v in (x, y, mx, my, mz, sld, vol))
        I_out = _calc_Iqxy_magnetic(
            qx, qy, x, y, sld, vol, (mx, my, mz),
            in_spin, out_spin, s_theta)
    else:
        index = (sld != 0.)
        if not index.all():
            x, y, sld, vol = (v[index] for v in (x, y, sld, vol))
        I_out = _calc_Iqxy(qx, qy, x, y, sld, vol)
    return I_out * (1.0E+8/np.sum(vol))

@njit('(f8[:], f8[:], f8[:], f8[:], f8[:])')
def _calc_Iq_avg(Iq, q, r, sld, vol):
    weight = sld * vol
    for i, qi in enumerate(q):
        # use q/pi since np.sinc = sin(pi x)/(pi x)
        bes = np.sinc((qi/np.pi)*r)
        Fq = np.sum(weight * bes)
        Iq[i] = Fq**2

@njit('(f8[:], f8[:], f8[:, :], f8[:], f8[:])')
def _calc_Iq(Iq, q, coords, sld, vol):
    weight = sld * vol
    npoints = len(weight)
    for i, qi in enumerate(q):
        qi = qi/np.pi  # precompute q/pi since np.sinc = sin(pi x)/(pi x)
        total = 0.0
        for j in range(npoints):
            # Compute dx for one row of the upper triangle matrix
            dx = coords[:, j:] - coords[:, j:j+1]
            # Find the length of each dx vector
            r = np.sqrt(np.sum(dx**2, axis=0))
            # Compute I_jk = rho_j rho_k j0(q ||x_j - x_k||)
            bes = np.sinc(qi*r)
            I_jk = weight[j:] * weight[j] * bes
            # Accumulate terms I(j,j), I(j, k+1..n) and by symmetry I(k+1..n, j)
            total += 2*np.sum(I_jk) - I_jk[0] # don't double-count the diagonal
        Iq[i] = total

@njit('f8[:](f8[:], f8[:], f8[:], f8[:], f8[:], f8[:])')
def _calc_Iqxy(qx, qy, x, y, sld, vol):
    """
    Compute I(q) for a set of points (x, y).

    Uses::

        I(q) = |sum V(r) rho(r) e^(1j q.r)|^2 / sum V(r)

    Since qz is zero for SAS, only need 2D vectors q = (qx, qy) and r = (x, y).
    """
    scale = sld*vol
    Iq = [abs(np.sum(scale*np.exp(1j*(qx_k*x + qy_k*y))))**2
          for qx_k, qy_k in zip(qx.flat, qy.flat)]
    return np.asarray(Iq).reshape(qx.shape)

def _calc_Iqxy_magnetic(
        qx, qy, x, y, vol, rho, rho_m,
        up_frac_i=0, up_frac_f=0, up_angle=0.):
    """
    Compute I(q) for a set of points (x, y), with magnetism on each point.

    Uses::

        I(q) = sum_xs w_xs |sum V(r) rho(q, r, xs) e^(1j q.r)|^2 / sum V(r)

    where rho is adjusted for the particular q and polarization cross section.
    The cross section weights depends on the polarizer and analyzer
    efficiency of the measurement.  For example, with polarization up at 100%
    efficiency and no analyzer, (up_frac_i=1, up_frac_f=0.5), then uu and ud
    will both be 0.5.

    Since qz is zero for SAS, only need 2D vectors q = (qx, qy) and r = (x, y).
    """
    # Determine contribution from each cross section
    dd, du, ud, uu = _spin_weights(up_frac_i, up_frac_f)

    # Precompute helper values
    up_angle = np.radians(up_angle)
    cos_spin, sin_spin = np.cos(-up_angle), np.sin(-up_angle)
    mx, my, mz = rho_m

    # Flatten arrays so everything is 1D
    shape = qx.shape
    qx, qy = (np.asarray(v, 'd').flatten() for v in (qx, qy))
    Iq = np.empty(shape=qx.shape, dtype='d')
    print("mag", [v.shape for v in (x, y, rho, vol, mx, my, mz)])
    _calc_Iqxy_magnetic_helper(
        Iq, qx, qy, x, y, vol, rho, mx, my, mz,
        cos_spin, sin_spin, dd, du, ud, uu)
    return Iq.reshape(shape)

@njit("(" + "f8[:], "*10 + "f8, "*6 + ")")
def _calc_Iqxy_magnetic_helper(
        Iq, qx, qy, x, y, vol, rho, mx, my, mz, cos_spin, sin_spin,
        dd, du, ud, uu):
    # Process each qx, qy
    # Note: enumerating a pair is slower than direct indexing in numba
    for k in range(len(qx)):
        qxk, qyk = qx[k], qy[k]
        # If q is 0 then px and py are also zero.
        one_over_qsq = 1./(qxk**2 + qyk**2) if qxk != 0. and qyk != 0. else 0.
        perp = one_over_qsq*(qyk*mx - qxk*my)
        px = perp*(qyk*cos_spin + qxk*sin_spin)
        py = perp*(qyk*sin_spin - qxk*cos_spin)
        ephase = vol*np.exp(1j*(qxk*x + qyk*y))
        if dd > 1e-10:
            Iq[k] += dd * abs(np.sum((rho-px)*ephase))**2
        if uu > 1e-10:
            Iq[k] += uu * abs(np.sum((rho+px)*ephase))**2
        if du > 1e-10:
            Iq[k] += du * abs(np.sum((py-1j*mz)*ephase))**2
        if ud > 1e-10:
            Iq[k] += ud * abs(np.sum((py+1j*mz)*ephase))**2

def _spin_weights(in_spin, out_spin):
    """
    Compute spin cross weights given in_spin and out_spin

    Returns weights (dd, du, ud, uu)
    """
    in_spin = np.clip(in_spin, 0.0, 1.0)
    out_spin = np.clip(out_spin, 0.0, 1.0)
    # Previous version of this function took the square root of the weights,
    # under the assumption that
    #
    #     w*I(q, rho1, rho2, ...) = I(q, sqrt(w)*rho1, sqrt(w)*rho2, ...)
    #
    # However, since the weights are applied to the final intensity and
    # are not interned inside the I(q) function, we want the full
    # weight and not the square root.  Anyway no function will ever use
    # set_spin_weights as part of calculating an amplitude, as the weights are
    # related to polarisation efficiency of the instrument. The weights serve to
    # construct various magnet scattering cross sections, which are linear combinations
    # of the spin-resolved cross sections. The polarisation efficiency e_in and e_out
    # are parameters ranging from 0.5 (unpolarised) beam to 1 (perfect optics).
    # For in_spin or out_spin <0.5 one assumes a CS, where the spin is reversed/flipped
    # with respect to the initial supermirror polariser. The actual polarisation efficiency
    # in this case is however e_in/out = 1-in/out_spin.

    norm = 1 - out_spin if out_spin < 0.5 else out_spin

    # The norm is needed to make sure that the scattering cross sections are
    # correctly weighted, such that the sum of spin-resolved measurements adds up to
    # the unpolarised or half-polarised scattering cross section. No intensity weighting
    # needed on the incoming polariser side (assuming that a user), has normalised
    # to the incoming flux with polariser in for SANSPOl and unpolarised beam, respectively.

    weight = (
        (1.0-in_spin) * (1.0-out_spin) / norm, # dd
        (1.0-in_spin) * out_spin / norm,       # du
        in_spin * (1.0-out_spin) / norm,       # ud
        in_spin * out_spin / norm,             # uu
    )
    return weight
