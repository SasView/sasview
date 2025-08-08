"""
Compute scattering from a set of points.
For 1-D scattering use *Iq(q, x, y, z, sld, vol, is_avg)*
"""
import logging
import os

import numpy as np
import periodictable

from sas.sascalc.calculator.sas_gen import OMF2SLD, MagSLD

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
    w = sld * vol

    if is_avg:
        r = np.linalg.norm(coords, axis=0)
        I_out = _calc_Iq_avg(q, r, w)
    else:
        from sas.sascalc.calculator.ausaxs.ausaxs_sans_debye import evaluate_sans_debye
        I_out = evaluate_sans_debye(q, coords, w)
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
                mx, my, mz, sld, elements, vol = (v[index] for v in (mx, my, mz, sld, elements, vol))
            I_out = _calc_Iqxy_magnetic_elements(
                qx, qy, x, y, z, sld, mx, my, mz, elements, vol,
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
                sld, elements, vol = (v[index] for v in (sld, elements, vol))
            I_out = _calc_Iqxy_elements(sld, x, y, z, elements, vol, qx.flatten(), qy.flatten())
            I_out = I_out.reshape(qx.shape)
        else:
            if not index.all():
                x, y, sld, vol = (v[index] for v in (x, y, sld, vol))
            I_out = _calc_Iqxy(sld*vol, x, y, qx.flatten(), qy.flatten())
            I_out = I_out.reshape(qx.shape)
    return I_out * (1.0E+8/np.sum(vol))

@njit('(f8[:], f8[:], f8[:])')
def _calc_Iq_avg(q, r, w):
    Iq = np.zeros_like(q)
    for i, qi in enumerate(q):
        # use q/pi since np.sinc = sin(pi x)/(pi x)
        bes = np.sinc((qi/np.pi)*r)
        Fq = np.sum(w * bes)
        Iq[i] = Fq**2
    return Iq

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
_calc_Iqxy.__doc__ = r"""
    Compute I(q) for a set of points (x, y).

    Uses: I(q) = \|sum V(r) rho(r) e^(1j q.r)\|^2 / sum V(r)
    Since qz is zero for SAS, only need 2D vectors q = (qx, qy) and r = (x, y).
    """

def _calc_Iqxy_elements(sld, x, y, z, elements, vol, qx, qy):
    """
    Compute I(q) for a set of elements, without magnetism.
    """
    # create the geometry as an array (elements x faces x vertices x coordinates)
    geometry = np.column_stack((x, y, z))[np.concatenate((elements, elements[:,:,:1]), axis=2)]
    # create normal vectors (elements x faces x normal_vector_coords)
    normals, geometry = _get_normal_vec(geometry)
    # extract the normal component of the displacement of the plane using the first point (elements x faces)
    rn_norm = np.sum(geometry[:,:,0] * normals, axis=-1)
    temp = element_transform(geometry, normals, rn_norm, vol, 0.5, 0)
    #temp = element_transform(geometry, normals, rn_norm, vol, 6.29259, -6.29259)
    #temp2 = np.sum(sld*temp)
    #temp3 = abs(temp2)**2*1e8/8
    Iq = [abs(np.sum(sld*element_transform(geometry, normals, rn_norm, vol, qx_k, qy_k)))**2
            for qx_k, qy_k in zip(qx.flat, qy.flat)]
    return np.asarray(Iq).reshape(qx.shape)

def _calc_Iqxy_magnetic(
        qx, qy, x, y, rho, vol, rho_m,
        up_frac_i=1, up_frac_f=1, up_theta=0., up_phi=0.):
    r"""Compute I(q) for a set of points (x, y), with magnetism on each point.

    Uses: I(q) = sum_xs w_xs \|sum V(r) rho(q, r, xs) e^(1j q.r)\|^2 / sum V(r)
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
    up_theta = np.radians(up_theta)
    cos_spin, sin_spin = np.cos(up_theta), np.sin(up_theta)

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

    p_hat = np.array([sin_spin * cos_phi, sin_spin * sin_phi, cos_spin ])
    #two unit vectors spanning up the plane perpendicular to polarisation for SF scattering
    perpy_hat = np.array([-sin_phi, cos_phi, 0 ])
    perpz_hat = np.array([-cos_spin * cos_phi, -cos_spin * sin_phi, sin_spin ])

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

        M_perp = orth(M, q_hat)

        perpx = p_hat @ M_perp
        # einsum is faster than sumsq in numpy but not supported in numba
        #perpy = np.sqrt(np.einsum('ji,ji->i', M_perpP_perpQ, M_perpP_perpQ))
        perpy = perpy_hat @ M_perp
        perpz = perpz_hat @ M_perp

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
    """return array of normal vectors of elements

    This function returns an array of unit normal vectors to faces, pointing out
    of the elements, as well as altering the geometry to ensure the vertices are ordered
    the correct way around

    .. warning:: This function alters geometry in place as well as returning it - so when this
                    function is called the geometry array will always be re-ordered.

    :param geometry: an array of the position data for the mesh which goes as
                        (elements x faces x vertices x coordinates)
    :type geometry: numpy.ndarray
    :return: normals, geometry - where geometry has been adjusted to ensure all vertices
            go anticlockwise around the unit normal vector, and the unit normal vectors
            are pointed out of the element.
    :rtype: tuple
    """
    v1 = geometry[:, :, 1] - geometry[:, :, 0]
    v2 = geometry[:, :, 2] - geometry[:, :, 0]
    # (elements x faces x coords)
    normals = np.cross(v1, v2)
    normals = normals / np.linalg.norm(normals, axis=-1)[..., None]
    disps = np.mean(geometry, axis=(1,2))[:, None, :] - geometry[:, :, 0]
    signs = np.sign(np.sum(disps*normals, axis=-1))
    normals = normals * (-signs)[..., None] # arrange normals outwards
    flips = signs == 1
    geometry[flips, :, :] = geometry[flips, ::-1, :]
    return normals, geometry

def _calc_Iqxy_magnetic_elements(
                qx, qy, x, y, z, sld, mx, my, mz, elements, vol,
                up_frac_i=1, up_frac_f=1, up_angle=0., up_phi=0.):
    """
    Compute I(q) for a set of elements, with magnetism.
    """
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
    normals, geometry = _get_normal_vec(geometry)
    # extract the normal component of the displacement of the plane using the first point (elements x faces)
    rn_norm = np.sum(geometry[:,:,0] * normals, axis=-1)
    # Flatten arrays so everything is 1D
    shape = qx.shape
    qx, qy = (np.asarray(v, 'd').flatten() for v in (qx, qy))
    Iq = np.zeros(shape=qx.shape, dtype='d')
    M = np.array([mx, my, mz])
    #print("mag", [v.shape for v in (x, y, rho, vol, mx, my, mz)])
    _calc_Iqxy_magnetic_elements_helper(
        Iq, qx, qy, geometry, normals, rn_norm, sld, M, vol,
        cos_spin, sin_spin, cos_phi, sin_phi, dd, du, ud, uu)
    return Iq.reshape(shape)

# TODO: currently doesn't use numba
def _calc_Iqxy_magnetic_elements_helper(
        Iq, qx, qy, geometry, normals, rn_norm, rho, M, vol,
        cos_spin, sin_spin, cos_phi, sin_phi, dd, du, ud, uu):
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

        ephase = element_transform(geometry, normals, rn_norm, vol, qxk, qyk)
        if dd > 1e-10:
            Iq[k] += dd * abs(np.sum((rho - perpx) * ephase))**2
        if uu > 1e-10:
            Iq[k] += uu * abs(np.sum((rho + perpx) * ephase))**2
        if du > 1e-10:
            Iq[k] += du * abs(np.sum((perpy - 1j * perpz) * ephase))**2
        if ud > 1e-10:
            Iq[k] += ud * abs(np.sum((perpy + 1j * perpz) * ephase))**2

def element_transform(geometry, normals, rn_norm, volumes, qx, qy):
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
    :param volumes: A 1D numpy array containing the volumes of the elements
    :type volumes: nump.ndarray
    :param qx: The x component of the Q vector which represents the position in fourier space.
    :type qx: float
    :param qy: The y component of the Q vector which represents the position in fourier space.
    :type qy: float
    :return: A 1D numpy array of the fourier transforms of each element at the given Q value
    :rtype: numpy.ndarray
    """
    # small value used in case where a fraction should limit to a finite answer with 0 on top and bottom
    # used in 2nd/3rd terms in sum over vertices
    eps = 1e-5
    # If Q is the zero vector then the fourier transform is just the volume of the subelements
    if abs(qx) < eps and abs(qy) < eps:
        return volumes

    # create the Q vector (elements x Q)
    Q = np.array([[qx, qy, 0]])*np.ones((len(geometry), 3))
    # create the Q normal vector as the dot product of Q with the normal vector * the normal vector:
    # separately store the component of the Qn vector for later use
    # np.dot: (elements x faces x normal_vector_coords) * (elements x 1 x Q_coords) -> (elements x faces)
    Qn_comp = np.sum(normals * Q[:, None, :], axis=-1)
    # Qn is the vector PARALLEL to the surface normal Q// in the referenced paper eq. (14)
    # np (*) (elements x faces x 1) * (elements x faces x normal_vector_coords) -> (elements x faces x Qn_coords)
    Qn = Qn_comp[..., None] * normals
    # extract the parallel component of the Q vector to the face i.e. PERPENDICULAR to the surface normal
    # (elements x 1 x Q_coords) - (elements x faces x Qn_coords) -> (elements x faces x Qp_coords)
    Qp = Q[:, None, :] - Qn
    # find any elements for which Qp is the 0 vector on one face and add an epsilon value
    # apply change to whole element becuase if Qp=0 on one face the other faces
    # will have one v vector which dots to 0 with it
    # seems to be very little difference to just using eps on the problematic face and letting
    # the Qp.v method sort out the other faces
    # ensure that epsilon lies within the plane of the face
    problem_elements = np.any(np.all(np.abs(Qp)<eps, axis=-1) , axis=-1)
    problem_faces = np.argmax(np.all(np.abs(Qp)<eps, axis=-1), axis=-1)
    vs = geometry[np.arange(len(geometry)), problem_faces, 1] - geometry[np.arange(len(geometry)), problem_faces, 0]
    vs = vs / np.sqrt(np.sum(vs*vs, axis=-1))[..., None]
    Qp[problem_elements, ...] += eps * vs[problem_elements, None, ...]
    Q[problem_elements, ...] += eps * vs[problem_elements, ...]
    # calculate the face-dependent prefactor for the sum over vertices (elements x faces)
    prefactor = (1j * Qn_comp * np.exp(1j * Qn_comp * rn_norm)) / np.sum(Q * Q, axis=-1)[..., None]
    # calculate the sum over vertices term
    # the sub sum over the vertices in eq (14) (elements x faces)
    sub_sum = np.zeros_like(prefactor, dtype="complex")
    for i in range(geometry.shape[2]-1):
        # calculate the separation vector and sum vector of the two vertices on each edge (elements x faces x vector_coords)
        v_diff = geometry[:,:,i+1] - geometry[:,:,i]
        v_sum = geometry[:,:,i+1] + geometry[:,:,i]
        # the terms in the expr (elements x faces)
        # WARNING: this uses the opposite sign convention as the article's code but agrees with the sign convention of the
        # main text - it takes line segment normals as pointing OUTWARDS from the surface - giving the 'standard' fourier transform
        # e.g. fourier transform of a box gives a *positive* sinc function
        term = (np.sum(Qp * np.cross(v_diff, normals), axis=-1)) / np.sum(Qp * Qp, axis=-1).astype(complex)
        dot_diff = np.sum(Qp * v_diff, axis=-1)/2.0
        dot_sum = np.sum(Qp * v_sum, axis=-1)/2.0
        term = term * 1j * np.sinc(dot_diff/np.pi) * np.exp(1j * dot_sum)
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


def radius_of_gyration(nuc_sl_data: MagSLD | OMF2SLD) -> tuple[str, str, float]:
    """Calculate parameters related to the radius of gyration using and SLD profile.

    :param nuc_sl_data: A scattering length object for a series of atomic points in space
    :return: A tuple of the string representation of the radius of gyration, Guinier slope, and Rg as a float.
    """
    # Calculate Center of Mass First
    c_o_m = center_of_mass(nuc_sl_data)

    x = nuc_sl_data.pos_x
    y = nuc_sl_data.pos_y
    z = nuc_sl_data.pos_z
    pix_symbol = nuc_sl_data.pix_symbol
    coordinates = np.array([x, y, z]).T
    coherent_sls, masses = np.empty(len(pix_symbol)), np.empty(len(pix_symbol))
    for i, sym in enumerate(pix_symbol):
        atom = periodictable.elements.symbol(sym)
        masses[i] = atom.mass
        coherent_sls[i] = atom.neutron.b_c
        # solvent_slds = atoms.volume() * 10**24 * float(self.txtSolventSLD.text()) * 10**5

    # TODO: Implement a scientifically sound method for obtaining protein volume - Current value is a imprecise
    #  approximation. Until then Solvent SLD does not impact RG - SLD.
    #  This method only calculates RG of proteins in vacuum. Implementing the RG calcuation in solvent needs
    #  the input of the solvent volume.
    contrast_sls = coherent_sls  # femtometer
    rsq = np.sum((c_o_m - coordinates)**2, axis=1)

    rog_num = np.sum(masses * rsq)
    rog_den = np.sum(masses)
    guinier_num = np.sum(contrast_sls * rsq)
    guinier_den = np.sum(contrast_sls)

    if rog_den <= 0: #Should never happen as there are no zero or negative mass atoms
        rog_mass = "NaN"
        r_g_mass = 0.0
        logging.warning("Atomic Mass is zero for all atoms in the system.")
    else:
        r_g_mass = np.sqrt(rog_num/rog_den)
        rog_mass = (str(round(np.sqrt(rog_num/rog_den),1)) + " Å")

    #Avoid division by zero - May occur through contrast matching
    if guinier_den == 0:
        guinier_value = "NaN"
        logging.warning("Effective Coherent Scattering Length is zero for all atoms in the system.")
    elif (guinier_num/guinier_den) < 0:
        guinier_value = (str(round(np.sqrt(-guinier_num/guinier_den), 1)) + " Å")
        logging.warning("Radius of Gyration Squared is negative. R(G)^2 is assumed to be |R(G)|* R(G).")
    else:
        guinier_value = (str(round(np.sqrt(guinier_num/guinier_den), 1)) + " Å")

    return rog_mass, guinier_value, r_g_mass  # (String, String, Float), float used for plugin model


def center_of_mass(nuc_sl_data: MagSLD | OMF2SLD) -> list[float]:
    """Calculate Center of Mass(CoM) of provided molecule using an SL profile

    :param nuc_sl_data: A coordinate data object (MagSLD or OMF2SLD)
    :return: A list of the calculated spatial center of mass, given as cartesian coordinates."""
    masses = np.asarray([0.0, 0.0, 0.0])
    densities = np.asarray([0.0, 0.0, 0.0])

    # Only call periodictable once per element -> minimizes calculation time
    coh_b_storage = {}

    for i in range(len(nuc_sl_data.pos_x)):
        coordinates = np.asarray([float(nuc_sl_data.pos_x[i]), float(nuc_sl_data.pos_y[i]), float(nuc_sl_data.pos_z[i])])

        #Coh b - Coherent Scattering Length(fm)
        symbol = nuc_sl_data.pix_symbol[i]
        coh_b = coh_b_storage.get(symbol, periodictable.elements.symbol(symbol).neutron.b_c)
        coh_b_storage[symbol] = coh_b

        masses += (coordinates*coh_b)
        densities += coh_b

    c_o_m = np.divide(masses, densities)

    return c_o_m


def create_beta_plot(q_x: np.ndarray, nuc_sl_data: MagSLD | OMF2SLD, form_factor: np.ndarray) -> np.ndarray:
    """Carry out the computation of beta Q using provided & calculated data

    :param q_x: The Q values where the beta will be calculated.
    :param nuc_sl_data: A coordinate data object (MagSLD or OMF2SLD)
    :param form_factor: The form factor calculated prior to applying the beta approximation.
    :return: An array of form factor values with the beta approximation applied."""
    f_q = f_of_q(q_x, nuc_sl_data)

    # Center Of Mass Calculation
    data_beta_q = (f_q**2) / form_factor

    # Scale Beta Q to 0-1
    scaling_factor = data_beta_q[0]
    data_beta_q = data_beta_q / scaling_factor

    return data_beta_q


def f_of_q(q_x: np.ndarray, nuc_sl_data: MagSLD | OMF2SLD) -> np.ndarray:
    """Compute the base F(Q) calculation based from the nuclear data.

    :param q_x: The Q values where the beta will be calculated.
    :param nuc_sl_data: A coordinate data object (MagSLD or OMF2SLD)
    :return: An array of form factor data."""
    c_o_m = center_of_mass(nuc_sl_data)
    r_x = np.subtract(nuc_sl_data.pos_x, c_o_m[0])
    r_y = np.subtract(nuc_sl_data.pos_y, c_o_m[1])
    r_z = np.subtract(nuc_sl_data.pos_z, c_o_m[2])
    magnitude_relative_coordinate = np.sqrt(np.power(r_x, 2) + np.power(r_y, 2) + np.power(r_z, 2))
    coh_b = np.asarray([periodictable.elements.symbol(atom).neutron.b_c for atom in nuc_sl_data.pix_symbol])

    f_of_q_list = [np.sum(coh_b * np.sinc(q_x[i] * magnitude_relative_coordinate / np.pi)) for i in range(len(q_x))]
    f_of_q_list = np.asarray(f_of_q_list) / abs(np.sum(coh_b))  # normalization
    return f_of_q_list


