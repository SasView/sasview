"""
Define the resolution functions for the data.

This defines classes for 1D and 2D resolution calculations.
"""
from __future__ import division
from scipy.special import erf
from numpy import sqrt, log, log10
import numpy as np

MINIMUM_RESOLUTION = 1e-8

class Resolution1D(object):
    """
    Abstract base class defining a 1D resolution function.

    *q* is the set of q values at which the data is measured.

    *q_calc* is the set of q values at which the theory needs to be evaluated.
    This may extend and interpolate the q values.

    *apply* is the method to call with I(q_calc) to compute the resolution
    smeared theory I(q).
    """
    q = None
    q_calc = None
    def apply(self, theory):
        """
        Smear *theory* by the resolution function, returning *Iq*.
        """
        raise NotImplementedError("Subclass does not define the apply function")


class Perfect1D(Resolution1D):
    """
    Resolution function to use when there is no actual resolution smearing
    to be applied.  It has the same interface as the other resolution
    functions, but returns the identity function.
    """
    def __init__(self, q):
        self.q_calc = self.q = q

    def apply(self, theory):
        return theory


class Pinhole1D(Resolution1D):
    r"""
    Pinhole aperture with q-dependent gaussian resolution.

    *q* points at which the data is measured.

    *q_width* gaussian 1-sigma resolution at each data point.

    *q_calc* is the list of points to calculate, or None if this should
    be estimated from the *q* and *q_width*.
    """
    def __init__(self, q, q_width, q_calc=None):
        #*min_step* is the minimum point spacing to use when computing the
        #underlying model.  It should be on the order of
        #$\tfrac{1}{10}\tfrac{2\pi}{d_\text{max}}$ to make sure that fringes
        #are computed with sufficient density to avoid aliasing effects.

        # Protect against calls with q_width=0.  The extend_q function will
        # not extend the q if q_width is 0, but q_width must be non-zero when
        # constructing the weight matrix to avoid division by zero errors.
        # In practice this should never be needed, since resolution should
        # default to Perfect1D if the pinhole geometry is not defined.
        self.q, self.q_width = q, q_width
        self.q_calc = pinhole_extend_q(q, q_width) \
            if q_calc is None else np.sort(q_calc)
        self.weight_matrix = pinhole_resolution(self.q_calc,
                self.q, np.maximum(q_width, MINIMUM_RESOLUTION))

    def apply(self, theory):
        return apply_resolution_matrix(self.weight_matrix, theory)


class Slit1D(Resolution1D):
    """
    Slit aperture with a complicated resolution function.

    *q* points at which the data is measured.

    *qx_width* slit width

    *qy_height* slit height

    *q_calc* is the list of points to calculate, or None if this should
    be estimated from the *q* and *q_width*.

    The *weight_matrix* is computed by :func:`slit1d_resolution`
    """
    def __init__(self, q, width, height, q_calc=None):
        # TODO: maybe issue warnings rather than raising errors
        if not np.isscalar(width):
            if np.any(np.diff(width) > 0.0):
                raise ValueError("Slit resolution requires fixed width slits")
            width = width[0]
        if not np.isscalar(height):
            if np.any(np.diff(height) > 0.0):
                raise ValueError("Slit resolution requires fixed height slits")
            height = height[0]

        # Remember what width/height was used even though we won't need them
        # after the weight matrix is constructed
        self.width, self.height = width, height

        self.q = q.flatten()
        self.q_calc = slit_extend_q(q, width, height) \
            if q_calc is None else np.sort(q_calc)
        self.weight_matrix = \
            slit_resolution(self.q_calc, self.q, width, height)

    def apply(self, theory):
        return apply_resolution_matrix(self.weight_matrix, theory)


def apply_resolution_matrix(weight_matrix, theory):
    """
    Apply the resolution weight matrix to the computed theory function.
    """
    #print "apply shapes", theory.shape, weight_matrix.shape
    Iq = np.dot(theory[None,:], weight_matrix)
    #print "result shape",Iq.shape
    return Iq.flatten()


def pinhole_resolution(q_calc, q, q_width):
    """
    Compute the convolution matrix *W* for pinhole resolution 1-D data.

    Each row *W[i]* determines the normalized weight that the corresponding
    points *q_calc* contribute to the resolution smeared point *q[i]*.  Given
    *W*, the resolution smearing can be computed using *dot(W,q)*.

    *q_calc* must be increasing.  *q_width* must be greater than zero.
    """
    # The current algorithm is a midpoint rectangle rule.  In the test case,
    # neither trapezoid nor Simpson's rule improved the accuracy.
    edges = bin_edges(q_calc)
    edges[edges<0.0] = 0.0 # clip edges below zero
    G = erf( (edges[:,None] - q[None,:]) / (sqrt(2.0)*q_width)[None,:] )
    weights = G[1:] - G[:-1]
    weights /= np.sum(weights, axis=0)[None,:]
    return weights


def slit_resolution(q_calc, q, width, height):
    r"""
    Build a weight matrix to compute *I_s(q)* from *I(q_calc)*, given
    $q_v$ = *width* and $q_h$ = *height*.

    *width* and *height* are scalars since current instruments use the
    same slit settings for all measurement points.

    If slit height is large relative to width, use:

    .. math::

        I_s(q_o) = \frac{1}{\Delta q_v}
            \int_0^{\Delta q_v} I(\sqrt{q_o^2 + u^2} du

    If slit width is large relative to height, use:

    .. math::

        I_s(q_o) = \frac{1}{2 \Delta q_v}
            \int_{-\Delta q_v}^{\Delta q_v} I(u) du
    """
    if width == 0.0 and height == 0.0:
        #print "condition zero"
        return 1

    q_edges = bin_edges(q_calc) # Note: requires q > 0
    q_edges[q_edges<0.0] = 0.0 # clip edges below zero

    #np.set_printoptions(linewidth=10000)
    if width <= 100.0 * height or height == 0:
        # The current algorithm is a midpoint rectangle rule.  In the test case,
        # neither trapezoid nor Simpson's rule improved the accuracy.
        #print "condition h", q_edges.shape, q.shape, q_calc.shape
        weights = np.zeros((len(q), len(q_calc)), 'd')
        for i, qi in enumerate(q):
            weights[i, :] = np.diff(q_to_u(q_edges, qi))
        weights /= width
        weights = weights.T
    else:
        #print "condition w"
        # Make q_calc into a row vector, and q into a column vector
        q, q_calc = q[None,:], q_calc[:,None]
        in_x = (q_calc >= q-width) * (q_calc <= q+width)
        weights = np.diff(q_edges)[:,None] * in_x

    return weights


def pinhole_extend_q(q, q_width, nsigma=3):
    """
    Given *q* and *q_width*, find a set of sampling points *q_calc* so
    that each point I(q) has sufficient support from the underlying
    function.
    """
    q_min, q_max = np.min(q - nsigma*q_width), np.max(q + nsigma*q_width)
    return geometric_extrapolation(q, q_min, q_max)


def slit_extend_q(q, width, height):
    """
    Given *q*, *width* and *height*, find a set of sampling points *q_calc* so
    that each point I(q) has sufficient support from the underlying
    function.
    """
    height # keep lint happy
    q_min, q_max = np.min(q), np.max(np.sqrt(q**2 + width**2))
    return geometric_extrapolation(q, q_min, q_max)


def bin_edges(x):
    """
    Determine bin edges from bin centers, assuming that edges are centered
    between the bins.

    Note: this uses the arithmetic mean, which may not be appropriate for
    log-scaled data.
    """
    if len(x) < 2 or (np.diff(x)<0).any():
        raise ValueError("Expected bins to be an increasing set")
    edges = np.hstack([
        x[0]  - 0.5*(x[1]  - x[0]),  # first point minus half first interval
        0.5*(x[1:] + x[:-1]),        # mid points of all central intervals
        x[-1] + 0.5*(x[-1] - x[-2]), # last point plus half last interval
        ])
    return edges


def q_to_u(q, q0):
    """
    Convert *q* values to *u* values for the integral computed at *q0*.
    """
    # array([value])**2 - value**2 is not always zero
    qpsq = q**2 - q0**2
    qpsq[qpsq<0] = 0
    return sqrt(qpsq)


def interpolate(q, max_step):
    """
    Returns *q_calc* with points spaced at most max_step apart.
    """
    step = np.diff(q)
    index = step>max_step
    if np.any(index):
        inserts = []
        for q_i,step_i in zip(q[:-1][index],step[index]):
            n = np.ceil(step_i/max_step)
            inserts.extend(q_i + np.arange(1,n)*(step_i/n))
        # Extend a couple of fringes beyond the end of the data
        inserts.extend(q[-1] + np.arange(1,8)*max_step)
        q_calc = np.sort(np.hstack((q,inserts)))
    else:
        q_calc = q
    return q_calc


def linear_extrapolation(q, q_min, q_max):
    """
    Extrapolate *q* out to [*q_min*, *q_max*] using the step size in *q* as
    a guide.  Extrapolation below uses steps the same size as the first
    interval.  Extrapolation above uses steps the same size as the final
    interval.

    if *q_min* is zero or less then *q[0]/10* is used instead.
    """
    q = np.sort(q)
    if q_min < q[0]:
        if q_min <= 0: q_min = q[0]/10
        delta = q[1] - q[0]
        q_low = np.arange(q_min, q[0], delta)
    else:
        q_low = []
    if q_max > q[-1]:
        delta = q[-1] - q[-2]
        q_high = np.arange(q[-1]+delta, q_max, delta)
    else:
        q_high = []
    return np.concatenate([q_low, q, q_high])


def geometric_extrapolation(q, q_min, q_max):
    r"""
    Extrapolate *q* to [*q_min*, *q_max*] using geometric steps, with the
    average geometric step size in *q* as the step size.

    if *q_min* is zero or less then *q[0]/10* is used instead.

    Starting at $q_1$ and stepping geometrically by $\Delta q$
    to $q_n$ in $n$ points gives a geometric average of:

    .. math::

         \log \Delta q = (\log q_n - log q_1) / (n - 1)

    From this we can compute the number of steps required to extend $q$
    from $q_n$ to $q_\text{max}$ by $\Delta q$ as:

    .. math::

         n_\text{extend} = (\log q_\text{max} - \log q_n) / \log \Delta q

    Substituting:

        n_\text{extend} = (n-1) (\log q_\text{max} - \log q_n)
            / (\log q_n - log q_1)
    """
    q = np.sort(q)
    delta_q = (len(q)-1)/(log(q[-1]) - log(q[0]))
    if q_min < q[0]:
        if q_min < 0: q_min = q[0]/10
        n_low = delta_q * (log(q[0])-log(q_min))
        q_low  = np.logspace(log10(q_min), log10(q[0]), np.ceil(n_low)+1)[:-1]
    else:
        q_low = []
    if q_max > q[-1]:
        n_high = delta_q * (log(q_max)-log(q[-1]))
        q_high = np.logspace(log10(q[-1]), log10(q_max), np.ceil(n_high)+1)[1:]
    else:
        q_high = []
    return np.concatenate([q_low, q, q_high])

