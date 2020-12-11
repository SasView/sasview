"""
Compute scattering from a set of points.
For 1-D scattering use *Iq(q, x, y, z, sld, vol, is_avg)*
"""
import os

import numpy as np

try:
    if os.environ.get('SAS_NUMBA', '1').lower() in ('1', 'yes', 'true', 't'):
        from numba import njit, prange
        USE_NUMBA = True
    else:
        raise ImportError("fail")
except ImportError:
    USE_NUMBA = False
    # if no numba then njit does nothing
    def njit(*args, **kw):
        # Check for bare @njit, in which case we just return the function.
        if len(args) == 1 and callable(args[0]) and not kw:
            return args[0]
        # Otherwise we have @njit(...), so return the identity decorator.
        return lambda fn: fn

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
    q, coords, sld, vol = [np.asarray(v, dtype='d') for v in (q, coords, sld, vol)]
    I_out = np.empty_like(q)
    if is_avg:
        r = np.linalg.norm(coords, axis=0)
        #print('avg', I_out.shape, q.shape, r.shape, sld.shape, vol.shape)
        _calc_Iq_avg(I_out, q, r, sld, vol)
    else:
        #print('not avg', I_out.shape, q.shape, coords.shape, sld.shape, vol.shape)
        _calc_Iq(I_out, q, coords, sld, vol)
    return I_out * (1.0E+8/np.sum(vol))

def Iqxy(qx, qy, x, y, z, sld, vol, mx, my, mz, in_spin, out_spin, s_theta, s_phi):
    """
    Computes 2D anisotropic.
    *in_spin* and *out_spin* indicate portion of polarizer and analyzer
    transmission that are spin up.  *s_theta* and *s_phi* are the polarization direction angles.
    All other values must be numpy vectors of the correct size.
    Returns *I(qx, qy)*
    """
    qx, qy = np.broadcast_arrays(qx, qy)
    # if the mx provided to SasGen is None then _vec(mx) will be [nan]
    if mx is not None and my is not None and mz is not None:
        magnetic_index = (mx != 0.) | (my != 0.) | (mz != 0.)
        is_magnetic = magnetic_index.any()
    else:
        is_magnetic = False
    if is_magnetic:
        index = (sld != 0.) | magnetic_index
        if not index.all():
            x, y, mx, my, mz, sld, vol \
                = (v[index] for v in (x, y, mx, my, mz, sld, vol))
        I_out = _calc_Iqxy_magnetic(
            qx, qy, x, y, sld, vol, (mx, my, mz),
            in_spin, out_spin, s_theta, s_phi)
    else:
        index = (sld != 0.)
        if not index.all():
            x, y, sld, vol = (v[index] for v in (x, y, sld, vol))
        I_out = _calc_Iqxy(sld*vol, x, y, qx.flatten(), qy.flatten())
        I_out = I_out.reshape(qx.shape)
    return I_out * (1.0E+8/np.sum(vol))

@njit('(f8[:], f8[:], f8[:], f8[:], f8[:])')
def _calc_Iq_avg(Iq, q, r, sld, vol):
    weight = sld * vol
    for i, qi in enumerate(q):
        # use q/pi since np.sinc = sin(pi x)/(pi x)
        bes = np.sinc((qi/np.pi)*r)
        Fq = np.sum(weight * bes)
        Iq[i] = Fq**2

def _calc_Iq(Iq, q, coords, sld, vol, worksize=1000000):
    """
    Compute Iq as sum rho_j rho_k j0(q ||x_j - x_k||)
    Chunk the calculation so that the q x r intermediate matrix has fewer
    than worksize elements.
    """
    Iq[:] = 0.
    q_pi = q/np.pi  # Precompute q/pi since np.sinc = sin(pi x)/(pi x).
    weight = sld * vol
    batch_size = worksize // coords.shape[0]
    for batch in range(0, len(q), batch_size):
        _calc_Iq_batch(Iq[batch:batch+batch_size], q_pi[batch:batch+batch_size],
                       coords, weight)

def _calc_Iq_batch(Iq, q_pi, coords, weight):
    """
    Helper function for _calc_Iq which operates on a batch of q values.
    *Iq* is accumulated within each batch, and should be initialized to zero.
    *q_pi* is q/pi, needed because np.sinc computes sin(pi x)/(pi x).
    *coords* are the sample points.
    *weights* is volume*rho for each point.
    """
    for j in range(len(weight)):
        # Compute dx for one row of the upper triangle matrix.
        dx = coords[:, j:] - coords[:, j:j+1]
        # Find the length of each dx vector.
        r = np.sqrt(np.sum(dx**2, axis=0))
        # Compute I_jk = rho_j rho_k j0(q ||x_j - x_k||) over all q in batch.
        bes = np.sinc(q_pi[:, None]*r[None, :])
        I_jk = (weight[j:] * weight[j])[None, :] * bes
        # Accumulate terms I(j,j), I(j, k+1..n) and by symmetry I(k+1..n, j).
        # Don't double-count the diagonal.
        Iq += 2*np.sum(I_jk, axis=1) - I_jk[:, 0]

@njit('(f8[:], f8[:], f8[:, :], f8[:], f8[:])')
def _calc_Iq_numba(Iq, q, coords, sld, vol):
    """
    **DEPRECATED**
    Numba version of the _calc_Iq since the pure numpy version is too
    difficult for numpy to handle.
    Even with with numba this code is slower than the pure numpy version.
    Without numba it is much much slower. Test for a few examples with
    smallish numbers of points.  The algorithm is O(n^2) which makes it
    unusable for a larger number of points.  A GPU implementation would
    help, maybe allowing 10x the number of points.
    """
    Iq[:] = 0.
    weight = sld * vol
    npoints = len(weight)
    for j in range(npoints):
        # Compute dx for one row of the upper triangle matrix
        dx = coords[:, j:] - coords[:, j:j+1]
        # Find the length of each dx vector
        r = np.sqrt(np.sum(dx**2, axis=0))
        # Compute I_jk = rho_j rho_k j0(q ||x_j - x_k||)
        for i, qi in enumerate(q):
            qi_pi = qi/np.pi  # precompute q/pi since np.sinc = sin(pi x)/(pi x)
            bes = np.sinc(qi_pi*r)
            I_jk = weight[j:] * weight[j] * bes
            # Accumulate terms I(j,j), I(j, k+1..n) and by symmetry I(k+1..n, j)
            Iq[i] += 2*np.sum(I_jk) - I_jk[0] # don't double-count the diagonal

if USE_NUMBA:
    sig = "f8[:](f8[:],f8[:],f8[:],f8[:],f8[:])"
    @njit(sig, parallel=True, fastmath=True)
    def _calc_Iqxy(scale, x, y, qx, qy):
        #print("calling numba for geni")
        Iq = np.empty_like(qx)
        for j in prange(len(Iq)):
            total = np.sum(scale * np.exp(1j*(qx[j]*x + qy[j]*y)))
            Iq[j] = abs(total)**2
        return Iq
else:
    def _calc_Iqxy(scale, x, y, qx, qy):
        Iq = [abs(np.sum(scale*np.exp(1j*(qx_k*x + qy_k*y))))**2
              for qx_k, qy_k in zip(qx.flat, qy.flat)]
        return np.asarray(Iq).reshape(qx.shape)
_calc_Iqxy.__doc__ = """
    Compute I(q) for a set of points (x, y).
    Uses::
        I(q) = |sum V(r) rho(r) e^(1j q.r)|^2 / sum V(r)
    Since qz is zero for SAS, only need 2D vectors q = (qx, qy) and r = (x, y).
    """


def _calc_Iqxy_magnetic(
        qx, qy, x, y, rho, vol, rho_m,
        up_frac_i=0, up_frac_f=0, up_angle=0., up_phi=0.):
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
   
    up_phi = np.radians(up_phi)
    cos_phi, sin_phi = np.cos(up_phi), np.sin(up_phi)
    mx, my, mz = rho_m
    ## NOTE: sasview calculator uses the opposite sign for mx, my, mz.
    ## Uncomment the following to match its output.
    #mx, my, mz = -mx, -my, -mz

    # Flatten arrays so everything is 1D
    shape = qx.shape
    qx, qy = (np.asarray(v, 'd').flatten() for v in (qx, qy))
    Iq = np.zeros(shape=qx.shape, dtype='d')
    #print("mag", [v.shape for v in (x, y, rho, vol, mx, my, mz)])
    _calc_Iqxy_magnetic_helper(
        Iq, qx, qy, x, y, rho, vol, mx, my, mz,
        cos_spin, sin_spin, cos_phi, sin_phi, dd, du, ud, uu)
    return Iq.reshape(shape)

@njit("(" + "f8[:], "*10 + "f8, "*6 + ")")
def _calc_Iqxy_magnetic_helper(
        Iq, qx, qy, x, y, rho, vol, mx, my, mz, cos_spin, sin_spin, cos_phi, sin_phi,
        dd, du, ud, uu):
    # Process each qx, qy
    # Note: enumerating a pair is slower than direct indexing in numba
    for k in range(len(qx)):
        qxk, qyk = qx[k], qy[k]
        # If q is near 0 then set px and py to zero.
        # Note: norm is computed as a separate scalar so that the numba jit
        # can figure out the proper type for perp even for q = 0
        qsq = qxk**2 + qyk**2
        norm = 1./qsq if qsq > 1e-16 else 0.
        
        px = sin_spin*cos_phi
        py = sin_spin*sin_phi
        pz = cos_spin  

        qvector = [qxk*norm, qyk*norm, 0]
        Mvector = [mx, my, mz]
        Pvector = [px, py, pz]

        
        Mperp = Mvector-norm*np.dot(Mvector, qvector)*qvector 
        MperpP = Mperp-np.dot(Mperp, Pvector)*Pvector
        MperpPperpQ = MperpP- norm * np.dot(MperpP, qvector) * qvector 



        ephase = vol*np.exp(1j*(qxk*x + qyk*y))
        if dd > 1e-10:
            Iq[k] += dd * abs(np.sum(rho-np.dot(Pvector,Mperp))*ephase)**2
        if uu > 1e-10:
            Iq[k] += uu * abs(np.sum(rho+np.dot(Pvector,Mperp))*ephase)**2
        if du > 1e-10:
            Iq[k] += du * abs(np.sum(np.sqrt(MperpPperpQ.dot(MperpPperpQ))-1j*np.dot(MperpP,qvector))*ephase)**2
        if ud > 1e-10:
            Iq[k] += ud * abs(np.sum(np.sqrt(MperpPperpQ.dot(MperpPperpQ))+1j*np.dot(MperpP,qvector))*ephase)**2

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
