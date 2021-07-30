"""
Compute scattering from a set of points.
For 1-D scattering use *Iq(q, x, y, z, sld, vol, is_avg)*
"""
import os

import numpy as np

try:
    if os.environ.get('SAS_NUMBA', '1').lower() in ('1', 'yes', 'true', 't'):
        from numba import njit, prange
        # Suppress numba debug info
        import logging
        numba_logger = logging.getLogger('numba')
        numba_logger.setLevel(logging.WARNING)
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

def Iqxy(qx, qy, x, y, z, sld, vol, mx, my, mz, in_spin, out_spin, s_theta, s_phi, elements=None, is_elements=False):
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
        if is_elements:
            if not index.all():
                mx, my, mz, sld, elements = (v[index] for v in (mx, my, mz, sld, elements))
            I_out = _calc_Iqxy_magnetic_elements(
                qx, qy, x, y, z, sld, mx, my, mz, elements,
                in_spin, out_spin, s_theta, s_phi)
        else:
            if not index.all():
                x, y, mx, my, mz, sld, vol \
                    = (v[index] for v in (x, y, mx, my, mz, sld, vol))
            I_out = _calc_Iqxy_magnetic(
                qx, qy, x, y, sld, vol, (mx, my, mz),
                in_spin, out_spin, s_theta, s_phi)
    else:
        index = (sld != 0.)
        if is_elements:
            if not index.all():
                sld, elements = (v[index] for v in (sld, elements))
            I_out = _calc_Iqxy_elements(sld, x, y, z, elements, qx.flatten(), qy.flatten())
            I_out = I_out.reshape(qx.shape)
        else:
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

def _calc_Iqxy_elements(sld, x, y, z, elements, qx, qy):
    # create the geometry as an array (elements x faces x vertices x coordinates)
    geometry = np.column_stack((x, y, z))[np.concatenate((elements, elements[:,:,:1]), axis=2)]
    # create normal vectors (elements x faces x normal_vector_coords)
    normals = _get_normal_vec(geometry)
    # extract the normal component of the displacement of the plane using the first point (elements x faces)
    rn_norm = np.sum(geometry[:,:,0] * normals, axis=-1)
    Iq = [abs(np.sum(sld*element_transform(geometry, normals, rn_norm, qx_k, qy_k)))**2
            for qx_k, qy_k in zip(qx.flat, qy.flat)]
    return np.asarray(Iq).reshape(qx.shape)

def _calc_Iqxy_magnetic(
        qx, qy, x, y, rho, vol, rho_m,
        up_frac_i=1, up_frac_f=1, up_angle=0., up_phi=0.):
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
    cos_spin, sin_spin = np.cos(up_angle), np.sin(up_angle)

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
    M = np.array([mx, my, mz])
    #print("mag", [v.shape for v in (x, y, rho, vol, mx, my, mz)])
    _calc_Iqxy_magnetic_helper(
        Iq, qx, qy, x, y, rho, vol, M,
        cos_spin, sin_spin, cos_phi, sin_phi, dd, du, ud, uu)
    return Iq.reshape(shape)

@njit
def orth(A, b): # A = 3 x n, and b_hat unit vector
    return A - np.outer(b, b)@A

@njit("(" + "f8[:], "*7 + "f8[:,::1], "+ "f8, "*8 + ")")
def _calc_Iqxy_magnetic_helper(
        Iq, qx, qy, x, y, rho, vol, M, cos_spin, sin_spin, cos_phi, sin_phi,
        dd, du, ud, uu):
    # Process each qx, qy
    # Note: enumerating a pair is slower than direct indexing in numba
    for k in range(len(qx)):
        qxk, qyk = qx[k], qy[k]

        if abs(qxk) > 1.e-16 or abs(qyk) > 1.e-16:
            norm = 1/np.sqrt(qxk**2 + qyk**2)
            q_hat = np.array([qxk, qyk, 0]) * norm
        else:
            # For homogeneously magnetised disc Mperp can be associated to the
            # magnetsation corrected for demag factorfield q->0, i.e. M-Nij M
            # with Nij the demagnetisation tensor (Belleggia JMMM 263, L1, 2003).
            q_hat = np.sqrt(np.array([0.5, 0.5, 0]))

        p_hat = np.array([sin_spin * cos_phi, sin_spin * sin_phi, cos_spin ])

        M_perp = orth(M, q_hat)
        M_perpP = orth(M_perp, p_hat)
        M_perpP_perpQ = orth(M_perpP, q_hat)

        perpx = p_hat @ M_perp
        # einsum is faster than sumsq in numpy but not supported in numba
        #perpy = np.sqrt(np.einsum('ji,ji->i', M_perpP_perpQ, M_perpP_perpQ))
        perpy = np.sqrt(np.sum(M_perpP_perpQ**2, axis=0))
        perpz = q_hat @ M_perpP

        ephase = vol * np.exp(1j * (qxk * x + qyk * y))
        if dd > 1e-10:
            Iq[k] += dd * abs(np.sum((rho - perpx) * ephase))**2
        if uu > 1e-10:
            Iq[k] += uu * abs(np.sum((rho + perpx) * ephase))**2
        if du > 1e-10:
            Iq[k] += du * abs(np.sum((perpy - 1j * perpz) * ephase))**2
        if ud > 1e-10:
            Iq[k] += ud * abs(np.sum((perpy + 1j * perpz) * ephase))**2

def _get_normal_vec(geometry):
    """return array of normal vectors of elements"""
    v1 = geometry[:, :, 1] - geometry[:, :, 0]
    v2 = geometry[:, :, 2] - geometry[:, :, 0]
    normals = np.cross(v1, v2)
    temp = np.linalg.norm(normals, axis=-1)
    normals = normals / np.linalg.norm(normals, axis=-1)[..., None]
    return normals

def _calc_Iqxy_magnetic_elements(
                qx, qy, x, y, z, sld, mx, my, mz, elements,
                up_frac_i=1, up_frac_f=1, up_angle=0., up_phi=0.):
    # Determine contribution from each cross section
    dd, du, ud, uu = _spin_weights(up_frac_i, up_frac_f)

    # Precompute helper values
    up_angle = np.radians(up_angle)
    cos_spin, sin_spin = np.cos(up_angle), np.sin(up_angle)

    up_phi = np.radians(up_phi)
    cos_phi, sin_phi = np.cos(up_phi), np.sin(up_phi)
    ## NOTE: sasview calculator uses the opposite sign for mx, my, mz.
    ## Uncomment the following to match its output.
    #mx, my, mz = -mx, -my, -mz
    # create the geometry as an array (elements x faces x vertices x coordinates)
    geometry = np.column_stack((x, y, z))[np.concatenate((elements, elements[:,:,:1]), axis=2)]
    # create normal vectors (elements x faces x normal_vector_coords)
    normals = _get_normal_vec(geometry)
    # extract the normal component of the displacement of the plane using the first point (elements x faces)
    rn_norm = np.sum(geometry[:,:,0] * normals, axis=-1)
    # Flatten arrays so everything is 1D
    shape = qx.shape
    qx, qy = (np.asarray(v, 'd').flatten() for v in (qx, qy))
    Iq = np.zeros(shape=qx.shape, dtype='d')
    M = np.array([mx, my, mz])
    #print("mag", [v.shape for v in (x, y, rho, vol, mx, my, mz)])
    _calc_Iqxy_magnetic_elements_helper(
        Iq, qx, qy, geometry, normals, rn_norm, sld, M, elements,
        cos_spin, sin_spin, cos_phi, sin_phi, dd, du, ud, uu)
    return Iq.reshape(shape)

# TODO: currently doesn't use numba - can this be integrated with fourier transform method
def _calc_Iqxy_magnetic_elements_helper(
        Iq, qx, qy, geometry, normals, rn_norm, rho, M, elements, cos_spin, sin_spin, cos_phi, sin_phi,
        dd, du, ud, uu):
    # Process each qx, qy
    # Note: enumerating a pair is slower than direct indexing in numba
    for k in range(len(qx)):
        qxk, qyk = qx[k], qy[k]

        if abs(qxk) > 1.e-16 or abs(qyk) > 1.e-16:
            norm = 1/np.sqrt(qxk**2 + qyk**2)
            q_hat = np.array([qxk, qyk, 0]) * norm
        else:
            # For homogeneously magnetised disc Mperp can be associated to the
            # magnetsation corrected for demag factorfield q->0, i.e. M-Nij M
            # with Nij the demagnetisation tensor (Belleggia JMMM 263, L1, 2003).
            q_hat = np.sqrt(np.array([0.5, 0.5, 0]))

        p_hat = np.array([sin_spin * cos_phi, sin_spin * sin_phi, cos_spin ])

        M_perp = orth(M, q_hat)
        M_perpP = orth(M_perp, p_hat)
        M_perpP_perpQ = orth(M_perpP, q_hat)

        perpx = p_hat @ M_perp
        # einsum is faster than sumsq in numpy but not supported in numba
        #perpy = np.sqrt(np.einsum('ji,ji->i', M_perpP_perpQ, M_perpP_perpQ))
        perpy = np.sqrt(np.sum(M_perpP_perpQ**2, axis=0))
        perpz = q_hat @ M_perpP

        ephase = element_transform(geometry, normals, rn_norm, qxk, qyk)
        if dd > 1e-10:
            Iq[k] += dd * abs(np.sum((rho - perpx) * ephase))**2
        if uu > 1e-10:
            Iq[k] += uu * abs(np.sum((rho + perpx) * ephase))**2
        if du > 1e-10:
            Iq[k] += du * abs(np.sum((perpy - 1j * perpz) * ephase))**2
        if ud > 1e-10:
            Iq[k] += ud * abs(np.sum((perpy + 1j * perpz) * ephase))**2

def element_transform(geometry, normals, rn_norm, qx, qy):
    """carries out fourier transform on elements
    
    This function carries out the polyhedral transformation on the elements that make up the mesh.
    This algorithm only works on meshes where all the elements have the same number of faces, and
    each face has the same number of vertices. It is heavily based on the algorithm in:

    An implementation of an efficient direct Fourier transform of polygonal areas and volumes.
    Brian B. Maranville.
    https://arxiv.org/abs/2104.08309

    :param geometry: A 4D numpy array of the form elements x faces x vertices x vertex_coordinates.
    :type geometry: numpy.ndarray
    :param normals: A 3D numpy array of the form elements x faces x normal_coordinates. The normals
                    provided should be normalised.
    :type normals: numpy.ndarray
    :param rn_normals: A 2D numpy array of the form elements x faces containing the perpendicular
                        distances from each face to the origin of the co-ordinate system.
    :type rn_norm: numpy.ndarray
    :param qx: the x component of the Q vector which represents the position in fourier space.
    :type qx: float
    :param qy: the y component of the Q vector which represents the position in fourier space.
    :type qy: float
    """
    # small value used in case where a fraction should limit to a finite answer with 0 on top and bottom
    # used in 2nd/3rd terms in sum over vertices
    eps = 1e-6

    # create the Q vector
    Q = np.array([qx+eps, qy+eps, 0+eps])
    # create the Q normal vector as the dot product of Q with the normal vector * the normal vector:
    # separately store the component of the Qn vector for later use
    # np.dot: (elements x faces x normal_vector_coords) * (Q_coords) -> (elements x faces)
    Qn_comp = np.dot(normals, Q)
    # Qn is the vector PARALLEL to the surface normal Q// in the referenced paper eq. (14)
    # np (*) (elements x faces x 1) * (elements x faces x normal_vector_coords) -> (elements x faces x Qn_coords)
    Qn = Qn_comp[..., None] * normals
    # extract the parallel component of the Q vector
    # (1 x 1 x Q_coords) - (elements x faces x Qn_coords)
    Qp = Q[None, None, :] - Qn
    # calculate the face-dependent prefactor for the sum over vertices (elements x faces) 
    # TODO: divide by zero error - can nan and inf handle this?
    prefactor = (1j * Qn_comp * np.exp(1j * Qn_comp * rn_norm)) / np.sum(Q * Q)
    # calculate the sum over vertices term
    # TODO: divide by zero error - can nan and inf handle this?
    # the sub sum over the vertices in eq (14) (elements x faces)
    sub_sum = np.zeros_like(prefactor, dtype="complex")
    for i in range(geometry.shape[2]-1):
        # calculate the separation vector (elements x faces x vector_coords)
        v = geometry[:,:,i+1] - geometry[:,:,i]
        # the terms in the expr (elements x faces)
        # WARNING: this uses the opposite sign convention as the article's code but agrees with the sign convention of the
        # main text - it takes line segment normals as pointing OUTWARDS from the surface - giving the 'standard' fourier transform
        # e.g. fourier transform of a box gives a *positive* sinc function
        term = (np.sum(Qp * np.cross(v, normals), axis=-1)) / np.sum(Qp * Qp, axis=-1)
        term = term * (np.exp(1j * np.sum(Qp * geometry[:,:,i+1], axis=-1)) - np.exp(1j * np.sum(Qp * geometry[:,:,i], axis=-1)))
        term = term / np.sum(Qp*v, axis=-1)
        sub_sum += term
    # sum over all the faces in each subvolume to return an array of transforms of sub_volumes
    return np.sum(prefactor*sub_sum, axis=-1)

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


