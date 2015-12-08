"""
Define the resolution functions for the data.

This defines classes for 1D and 2D resolution calculations.
"""
from __future__ import division
from scipy.special import erf
from numpy import sqrt, log, log10
import numpy as np

MINIMUM_RESOLUTION = 1e-8


# When extrapolating to -q, what is the minimum positive q relative to q_min
# that we wish to calculate?
MIN_Q_SCALE_FOR_NEGATIVE_Q_EXTRAPOLATION = 0.01

class Resolution(object):
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


class Perfect1D(Resolution):
    """
    Resolution function to use when there is no actual resolution smearing
    to be applied.  It has the same interface as the other resolution
    functions, but returns the identity function.
    """
    def __init__(self, q):
        self.q_calc = self.q = q

    def apply(self, theory):
        return theory


class Pinhole1D(Resolution):
    r"""
    Pinhole aperture with q-dependent gaussian resolution.

    *q* points at which the data is measured.

    *q_width* gaussian 1-sigma resolution at each data point.

    *q_calc* is the list of points to calculate, or None if this should
    be estimated from the *q* and *q_width*.
    """
    def __init__(self, q, q_width, q_calc=None, nsigma=3):
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
        self.q_calc = pinhole_extend_q(q, q_width, nsigma=nsigma) \
            if q_calc is None else np.sort(q_calc)
        self.weight_matrix = pinhole_resolution(self.q_calc,
                self.q, np.maximum(q_width, MINIMUM_RESOLUTION))

    def apply(self, theory):
        return apply_resolution_matrix(self.weight_matrix, theory)


class Slit1D(Resolution):
    """
    Slit aperture with a complicated resolution function.

    *q* points at which the data is measured.

    *qx_width* slit width

    *qy_height* slit height

    *q_calc* is the list of points to calculate, or None if this should
    be estimated from the *q* and *q_width*.

    The *weight_matrix* is computed by :func:`slit1d_resolution`
    """
    def __init__(self, q, width, height=0., q_calc=None):
        # Remember what width/height was used even though we won't need them
        # after the weight matrix is constructed
        self.width, self.height = width, height

        # Allow independent resolution on each point even though it is not
        # needed in practice.
        if np.isscalar(width):
            width = np.ones(len(q))*width
        else:
            width = np.asarray(width)
        if np.isscalar(height):
            height = np.ones(len(q))*height
        else:
            height = np.asarray(height)

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


def slit_resolution(q_calc, q, width, height, n_height=30):
    r"""
    Build a weight matrix to compute *I_s(q)* from *I(q_calc)*, given
    $q_\perp$ = *width* and $q_\parallel$ = *height*.  *n_height* is
    is the number of steps to use in the integration over $q_\parallel$
    when both $q_\perp$ and $q_\parallel$ are non-zero.

    Each $q$ can have an independent width and height value even though
    current instruments use the same slit setting for all measured points.

    If slit height is large relative to width, use:

    .. math::

        I_s(q_i) = \frac{1}{\Delta q_\perp}
            \int_0^{\Delta q_\perp} I(\sqrt{q_i^2 + q_\perp^2} dq_\perp

    If slit width is large relative to height, use:

    .. math::

        I_s(q_i) = \frac{1}{2 \Delta q_\parallel}
            \int_{-\Delta q_\parallel}^{\Delta q_\parallel}
                I(|q_i + q_\parallel|) dq_\parallel

    For a mixture of slit width and height use:

    .. math::

        I_s(q_i) = \frac{1}{2 \Delta q_\parallel \Delta q_\perp}
            \int_{-\Delta q_\parallel)^{\Delta q_parallel}
            \int_0^[\Delta q_\perp}
                I(\sqrt{(q_i + q_\parallel)^2 + q_\perp^2})
                dq_\perp dq_\parallel


    Algorithm
    ---------

    We are using the mid-point integration rule to assign weights to each
    element of a weight matrix $W$ so that

    .. math::

        I_s(q) = W I(q_\text{calc})

    If *q_calc* is at the mid-point, we can infer the bin edges from the
    pairwise averages of *q_calc*, adding the missing edges before
    *q_calc[0]* and after *q_calc[-1]*.

    For $q_\parallel = 0$, the smeared value can be computed numerically
    using the $u$ substitution

    .. math::

        u_j = \sqrt{q_j^2 - q^2}

    This gives

    .. math::

        I_s(q) \approx \sum_j I(u_j) \Delta u_j

    where $I(u_j)$ is the value at the mid-point, and $\Delta u_j$ is the
    difference between consecutive edges which have been first converted
    to $u$.  Only $u_j \in [0, \Delta q_\perp]$ are used, which corresponds
    to $q_j \in [q, \sqrt{q^2 + \Delta q_\perp}]$, so

    .. math::

        W_{ij} = \frac{1}{\Delta q_\perp} \Delta u_j
               = \frac{1}{\Delta q_\perp}
                    \sqrt{q_{j+1}^2 - q_i^2} - \sqrt{q_j^2 - q_i^2}
            \text{if} q_j \in [q_i, \sqrt{q_i^2 + q_\perp^2}]

    where $I_s(q_i)$ is the theory function being computed and $q_j$ are the
    mid-points between the calculated values in *q_calc*.  We tweak the
    edges of the initial and final intervals so that they lie on integration
    limits.

    (To be precise, the transformed midpoint $u(q_j)$ is not necessarily the
    midpoint of the edges $u((q_{j-1}+q_j)/2)$ and $u((q_j + q_{j+1})/2)$,
    but it is at least in the interval, so the approximation is going to be
    a little better than the left or right Riemann sum, and should be
    good enough for our purposes.)

    For $q_\perp = 0$, the $u$ substitution is simpler:

    .. math::

        u_j = |q_j - q|

    so

    .. math::

        W_ij = \frac{1}{2 \Delta q_\parallel} \Delta u_j
            = \frac{1}{2 \Delta q_\parallel} (q_{j+1} - q_j)
            \text{if} q_j \in [q-\Delta q_\parallel, q+\Delta q_\parallel]

    However, we need to support cases were $u_j < 0$, which means using
    $2 (q_{j+1} - q_j)$ when $q_j \in [0, q_\parallel-q_i]$.  This is not
    an issue for $q_i > q_\parallel$.

    For bot $q_\perp > 0$ and $q_\parallel > 0$ we perform a 2 dimensional
    integration with

    .. math::

        u_jk = \sqrt{q_j^2 - (q + (k\Delta q_\parallel/L))^2}
            \text{for} k = -L \ldots L

    for $L$ = *n_height*.  This gives

    .. math::

        W_{ij} = \frac{1}{2 \Delta q_\perp q_\parallel}
            \sum_{k=-L}^L \Delta u_jk (\frac{\Delta q_\parallel}{2 L + 1}


    """
    #np.set_printoptions(precision=6, linewidth=10000)

    # The current algorithm is a midpoint rectangle rule.
    q_edges = bin_edges(q_calc) # Note: requires q > 0
    q_edges[q_edges<0.0] = 0.0 # clip edges below zero
    weights = np.zeros((len(q), len(q_calc)), 'd')

    #print q_calc
    for i, (qi, w, h) in enumerate(zip(q, width, height)):
        if w == 0. and h == 0.:
            # Perfect resolution, so return the theory value directly.
            # Note: assumes that q is a subset of q_calc.  If qi need not be
            # in q_calc, then we can do a weighted interpolation by looking
            # up qi in q_calc, then weighting the result by the relative
            # distance to the neighbouring points.
            weights[i, :] = (q_calc == qi)
        elif h == 0:
            weights[i, :] = _q_perp_weights(q_edges, qi, w)
        elif w == 0:
            in_x = 1.0 * ((q_calc >= qi-h) & (q_calc <= qi+h))
            abs_x = 1.0*(q_calc < abs(qi - h)) if qi < h else 0.
            #print qi - h, qi + h
            #print in_x + abs_x
            weights[i,:] = (in_x + abs_x) * np.diff(q_edges) / (2*h)
        else:
            L = n_height
            for k in range(-L, L+1):
                weights[i,:] += _q_perp_weights(q_edges, qi+k*h/L, w)
            weights[i,:] /= 2*L + 1

    return weights.T


def _q_perp_weights(q_edges, qi, w):
    # Convert bin edges from q to u
    u_limit = np.sqrt(qi**2 + w**2)
    u_edges = q_edges**2 - qi**2
    u_edges[q_edges < abs(qi)] = 0.
    u_edges[q_edges > u_limit] = u_limit**2 - qi**2
    weights = np.diff(np.sqrt(u_edges))/w
    #print "i, qi",i,qi,qi+width
    #print q_calc
    #print weights
    return weights


def pinhole_extend_q(q, q_width, nsigma=3):
    """
    Given *q* and *q_width*, find a set of sampling points *q_calc* so
    that each point I(q) has sufficient support from the underlying
    function.
    """
    q_min, q_max = np.min(q - nsigma*q_width), np.max(q + nsigma*q_width)
    return linear_extrapolation(q, q_min, q_max)


def slit_extend_q(q, width, height):
    """
    Given *q*, *width* and *height*, find a set of sampling points *q_calc* so
    that each point I(q) has sufficient support from the underlying
    function.
    """
    q_min, q_max = np.min(q-height), np.max(np.sqrt((q+height)**2 + width**2))

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
    a guide.  Extrapolation below uses about the same size as the first
    interval.  Extrapolation above uses about the same size as the final
    interval.

    if *q_min* is zero or less then *q[0]/10* is used instead.
    """
    q = np.sort(q)
    if q_min < q[0]:
        if q_min <= 0: q_min = q_min*MIN_Q_SCALE_FOR_NEGATIVE_Q_EXTRAPOLATION
        n_low = np.ceil((q[0]-q_min) / (q[1]-q[0])) if q[1]>q[0] else 15
        q_low = np.linspace(q_min, q[0], n_low+1)[:-1]
    else:
        q_low = []
    if q_max > q[-1]:
        n_high = np.ceil((q_max-q[-1]) / (q[-1]-q[-2])) if q[-1]>q[-2] else 15
        q_high = np.linspace(q[-1], q_max, n_high+1)[1:]
    else:
        q_high = []
    return np.concatenate([q_low, q, q_high])


def geometric_extrapolation(q, q_min, q_max, points_per_decade=None):
    r"""
    Extrapolate *q* to [*q_min*, *q_max*] using geometric steps, with the
    average geometric step size in *q* as the step size.

    if *q_min* is zero or less then *q[0]/10* is used instead.

    *points_per_decade* sets the ratio between consecutive steps such
    that there will be $n$ points used for every factor of 10 increase
    in *q*.

    If *points_per_decade* is not given, it will be estimated as follows.
    Starting at $q_1$ and stepping geometrically by $\Delta q$ to $q_n$
    in $n$ points gives a geometric average of:

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
    if points_per_decade is None:
        log_delta_q = (len(q) - 1) / (log(q[-1]) - log(q[0]))
    else:
        log_delta_q = log(10.) / points_per_decade
    if q_min < q[0]:
        if q_min < 0: q_min = q[0]*MIN_Q_SCALE_FOR_NEGATIVE_Q_EXTRAPOLATION
        n_low = log_delta_q * (log(q[0])-log(q_min))
        q_low  = np.logspace(log10(q_min), log10(q[0]), np.ceil(n_low)+1)[:-1]
    else:
        q_low = []
    if q_max > q[-1]:
        n_high = log_delta_q * (log(q_max)-log(q[-1]))
        q_high = np.logspace(log10(q[-1]), log10(q_max), np.ceil(n_high)+1)[1:]
    else:
        q_high = []
    return np.concatenate([q_low, q, q_high])


############################################################################
# unit tests
############################################################################
import unittest


def eval_form(q, form, pars):
    from sasmodels import core
    kernel = core.make_kernel(form, [q])
    theory = core.call_kernel(kernel, pars)
    kernel.release()
    return theory


def gaussian(q, q0, dq):
    from numpy import exp, pi
    return exp(-0.5*((q-q0)/dq)**2)/(sqrt(2*pi)*dq)


def romberg_slit_1d(q, width, height, form, pars):
    """
    Romberg integration for slit resolution.

    This is an adaptive integration technique.  It is called with settings
    that make it slow to evaluate but give it good accuracy.
    """
    from scipy.integrate import romberg, dblquad

    if any(k not in form.info['defaults'] for k in pars.keys()):
        keys = set(form.info['defaults'].keys())
        extra = set(pars.keys()) - keys
        raise ValueError("bad parameters: [%s] not in [%s]"%
                         (", ".join(sorted(extra)), ", ".join(sorted(keys))))

    if np.isscalar(width):
        width = [width]*len(q)
    if np.isscalar(height):
        height = [height]*len(q)
    _int_w = lambda w, qi: eval_form(sqrt(qi**2 + w**2), form, pars)
    _int_h = lambda h, qi: eval_form(abs(qi+h), form, pars)
    # If both width and height are defined, then it is too slow to use dblquad.
    # Instead use trapz on a fixed grid, interpolated into the I(Q) for
    # the extended Q range.
    #_int_wh = lambda w, h, qi: eval_form(sqrt((qi+h)**2 + w**2), form, pars)
    q_calc = slit_extend_q(q, np.asarray(width), np.asarray(height))
    Iq = eval_form(q_calc, form, pars)
    result = np.empty(len(q))
    for i, (qi, w, h) in enumerate(zip(q, width, height)):
        if h == 0.:
            r = romberg(_int_w, 0, w, args=(qi,),
                        divmax=100, vec_func=True, tol=0, rtol=1e-8)
            result[i] = r/w
        elif w == 0.:
            r = romberg(_int_h, -h, h, args=(qi,),
                        divmax=100, vec_func=True, tol=0, rtol=1e-8)
            result[i] = r/(2*h)
        else:
            w_grid = np.linspace(0, w, 21)[None,:]
            h_grid = np.linspace(-h, h, 23)[:,None]
            u = sqrt((qi+h_grid)**2 + w_grid**2)
            Iu = np.interp(u, q_calc, Iq)
            #print np.trapz(Iu, w_grid, axis=1)
            Is = np.trapz(np.trapz(Iu, w_grid, axis=1), h_grid[:,0])
            result[i] = Is / (2*h*w)
            """
            r, err = dblquad(_int_wh, -h, h, lambda h: 0., lambda h: w,
                             args=(qi,))
            result[i] = r/(w*2*h)
            """

    # r should be [float, ...], but it is [array([float]), array([float]),...]
    return result


def romberg_pinhole_1d(q, q_width, form, pars, nsigma=5):
    """
    Romberg integration for pinhole resolution.

    This is an adaptive integration technique.  It is called with settings
    that make it slow to evaluate but give it good accuracy.
    """
    from scipy.integrate import romberg

    if any(k not in form.info['defaults'] for k in pars.keys()):
        keys = set(form.info['defaults'].keys())
        extra = set(pars.keys()) - keys
        raise ValueError("bad parameters: [%s] not in [%s]"%
                         (", ".join(sorted(extra)), ", ".join(sorted(keys))))

    _fn = lambda q, q0, dq: eval_form(q, form, pars)*gaussian(q, q0, dq)
    r = [romberg(_fn, max(qi-nsigma*dqi,1e-10*q[0]), qi+nsigma*dqi, args=(qi, dqi),
                 divmax=100, vec_func=True, tol=0, rtol=1e-8)
         for qi,dqi in zip(q,q_width)]
    return np.asarray(r).flatten()


class ResolutionTest(unittest.TestCase):

    def setUp(self):
        self.x = 0.001*np.arange(1, 11)
        self.y = self.Iq(self.x)

    def Iq(self, q):
        "Linear function for resolution unit test"
        return 12.0 - 1000.0*q

    def test_perfect(self):
        """
        Perfect resolution and no smearing.
        """
        resolution = Perfect1D(self.x)
        theory = self.Iq(resolution.q_calc)
        output = resolution.apply(theory)
        np.testing.assert_equal(output, self.y)

    def test_slit_zero(self):
        """
        Slit smearing with perfect resolution.
        """
        resolution = Slit1D(self.x, width=0, height=0, q_calc=self.x)
        theory = self.Iq(resolution.q_calc)
        output = resolution.apply(theory)
        np.testing.assert_equal(output, self.y)

    @unittest.skip("not yet supported")
    def test_slit_high(self):
        """
        Slit smearing with height 0.005
        """
        resolution = Slit1D(self.x, width=0, height=0.005, q_calc=self.x)
        theory = self.Iq(resolution.q_calc)
        output = resolution.apply(theory)
        answer = [ 9.0618, 8.6402, 8.1187, 7.1392, 6.1528,
                   5.5555, 4.5584, 3.5606, 2.5623, 2.0000 ]
        np.testing.assert_allclose(output, answer, atol=1e-4)

    @unittest.skip("not yet supported")
    def test_slit_both_high(self):
        """
        Slit smearing with width < 100*height.
        """
        q = np.logspace(-4, -1, 10)
        resolution = Slit1D(q, width=0.2, height=np.inf)
        theory = 1000*self.Iq(resolution.q_calc**4)
        output = resolution.apply(theory)
        answer = [ 8.85785, 8.43012, 7.92687, 6.94566, 6.03660,
                   5.40363, 4.40655, 3.40880, 2.41058, 2.00000 ]
        np.testing.assert_allclose(output, answer, atol=1e-4)

    @unittest.skip("not yet supported")
    def test_slit_wide(self):
        """
        Slit smearing with width 0.0002
        """
        resolution = Slit1D(self.x, width=0.0002, height=0, q_calc=self.x)
        theory = self.Iq(resolution.q_calc)
        output = resolution.apply(theory)
        answer = [ 11.0, 10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0 ]
        np.testing.assert_allclose(output, answer, atol=1e-4)

    @unittest.skip("not yet supported")
    def test_slit_both_wide(self):
        """
        Slit smearing with width > 100*height.
        """
        resolution = Slit1D(self.x, width=0.0002, height=0.000001,
                            q_calc=self.x)
        theory = self.Iq(resolution.q_calc)
        output = resolution.apply(theory)
        answer = [ 11.0, 10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0 ]
        np.testing.assert_allclose(output, answer, atol=1e-4)

    def test_pinhole_zero(self):
        """
        Pinhole smearing with perfect resolution
        """
        resolution = Pinhole1D(self.x, 0.0*self.x)
        theory = self.Iq(resolution.q_calc)
        output = resolution.apply(theory)
        np.testing.assert_equal(output, self.y)

    def test_pinhole(self):
        """
        Pinhole smearing with dQ = 0.001 [Note: not dQ/Q = 0.001]
        """
        resolution = Pinhole1D(self.x, 0.001*np.ones_like(self.x),
                               q_calc=self.x)
        theory = 12.0-1000.0*resolution.q_calc
        output = resolution.apply(theory)
        answer = [ 10.44785079, 9.84991299, 8.98101708,
                  7.99906585, 6.99998311, 6.00001689,
                  5.00093415, 4.01898292, 3.15008701, 2.55214921]
        np.testing.assert_allclose(output, answer, atol=1e-8)


class IgorComparisonTest(unittest.TestCase):

    def setUp(self):
        self.pars = TEST_PARS_PINHOLE_SPHERE
        from sasmodels import core
        from sasmodels.models import sphere
        self.model = core.load_model(sphere, dtype='double')

    def Iq_sphere(self, pars, resolution):
        from sasmodels import core
        kernel = core.make_kernel(self.model, [resolution.q_calc])
        theory = core.call_kernel(kernel, pars)
        result = resolution.apply(theory)
        kernel.release()
        return result

    def compare(self, q, output, answer, tolerance):
        #err = (output - answer)/answer
        #idx = abs(err) >= tolerance
        #problem = zip(q[idx], output[idx], answer[idx], err[idx])
        #print "\n".join(str(v) for v in problem)
        np.testing.assert_allclose(output, answer, rtol=tolerance)

    def test_perfect(self):
        """
        Compare sphere model with NIST Igor SANS, no resolution smearing.
        """
        pars = TEST_PARS_SLIT_SPHERE
        data_string = TEST_DATA_SLIT_SPHERE

        data = np.loadtxt(data_string.split('\n')).T
        q, width, answer, _ = data
        resolution = Perfect1D(q)
        output = self.Iq_sphere(pars, resolution)
        self.compare(q, output, answer, 1e-6)

    def test_pinhole(self):
        """
        Compare pinhole resolution smearing with NIST Igor SANS
        """
        pars = TEST_PARS_PINHOLE_SPHERE
        data_string = TEST_DATA_PINHOLE_SPHERE

        data = np.loadtxt(data_string.split('\n')).T
        q, q_width, answer = data
        resolution = Pinhole1D(q, q_width)
        output = self.Iq_sphere(pars, resolution)
        # TODO: relative error should be lower
        self.compare(q, output, answer, 3e-4)

    def test_pinhole_romberg(self):
        """
        Compare pinhole resolution smearing with romberg integration result.
        """
        pars = TEST_PARS_PINHOLE_SPHERE
        data_string = TEST_DATA_PINHOLE_SPHERE
        pars['radius'] *= 5
        radius = pars['radius']

        data = np.loadtxt(data_string.split('\n')).T
        q, q_width, answer = data
        answer = romberg_pinhole_1d(q, q_width, self.model, pars)
        ## Getting 0.1% requires 5 sigma and 200 points per fringe
        #q_calc = interpolate(pinhole_extend_q(q, q_width, nsigma=5),
        #                     2*np.pi/radius/200)
        #tol = 0.001
        ## The default 3 sigma and no extra points gets 1%
        q_calc, tol = None, 0.01
        resolution = Pinhole1D(q, q_width, q_calc=q_calc)
        output = self.Iq_sphere(pars, resolution)
        if 0: # debug plot
            import matplotlib.pyplot as plt
            resolution = Perfect1D(q)
            source = self.Iq_sphere(pars, resolution)
            plt.loglog(q, source, '.')
            plt.loglog(q, answer, '-', hold=True)
            plt.loglog(q, output, '-', hold=True)
            plt.show()
        self.compare(q, output, answer, tol)

    def test_slit(self):
        """
        Compare slit resolution smearing with NIST Igor SANS
        """
        pars = TEST_PARS_SLIT_SPHERE
        data_string = TEST_DATA_SLIT_SPHERE

        data = np.loadtxt(data_string.split('\n')).T
        q, delta_qv, _, answer = data
        resolution = Slit1D(q, width=delta_qv, height=0)
        output = self.Iq_sphere(pars, resolution)
        # TODO: eliminate Igor test since it is too inaccurate to be useful.
        # This means we can eliminate the test data as well, and instead
        # use a generated q vector.
        self.compare(q, output, answer, 0.5)

    def test_slit_romberg(self):
        """
        Compare slit resolution smearing with romberg integration result.
        """
        pars = TEST_PARS_SLIT_SPHERE
        data_string = TEST_DATA_SLIT_SPHERE
        radius = pars['radius']

        data = np.loadtxt(data_string.split('\n')).T
        q, delta_qv, _, answer = data
        answer = romberg_slit_1d(q, delta_qv, 0., self.model, pars)
        q_calc = slit_extend_q(interpolate(q, 2*np.pi/radius/20),
                               delta_qv[0], 0.)
        resolution = Slit1D(q, width=delta_qv, height=0, q_calc=q_calc)
        output = self.Iq_sphere(pars, resolution)
        # TODO: relative error should be lower
        self.compare(q, output, answer, 0.025)

    def test_ellipsoid(self):
        """
        Compare romberg integration for ellipsoid model.
        """
        from .core import load_model
        pars = {
            'scale':0.05,
            'rpolar':500, 'requatorial':15000,
            'sld':6, 'solvent_sld': 1,
            }
        form = load_model('ellipsoid', dtype='double')
        q = np.logspace(log10(4e-5),log10(2.5e-2), 68)
        width, height = 0.117, 0.
        resolution = Slit1D(q, width=width, height=height)
        answer = romberg_slit_1d(q, width, height, form, pars)
        output = resolution.apply(eval_form(resolution.q_calc, form, pars))
        # TODO: 10% is too much error; use better algorithm
        #print np.max(abs(answer-output)/answer)
        self.compare(q, output, answer, 0.1)

    #TODO: can sas q spacing be too sparse for the resolution calculation?
    @unittest.skip("suppress sparse data test; not supported by current code")
    def test_pinhole_sparse(self):
        """
        Compare pinhole resolution smearing with NIST Igor SANS on sparse data
        """
        pars = TEST_PARS_PINHOLE_SPHERE
        data_string = TEST_DATA_PINHOLE_SPHERE

        data = np.loadtxt(data_string.split('\n')).T
        q, q_width, answer = data[:, ::20] # Take every nth point
        resolution = Pinhole1D(q, q_width)
        output = self.Iq_sphere(pars, resolution)
        self.compare(q, output, answer, 1e-6)


# pinhole sphere parameters
TEST_PARS_PINHOLE_SPHERE = {
    'scale': 1.0, 'background': 0.01,
    'radius': 60.0, 'sld': 1, 'solvent_sld': 6.3,
    }
# Q, dQ, I(Q) calculated by NIST Igor SANS package
TEST_DATA_PINHOLE_SPHERE = """\
0.001278 0.0002847 2538.41176383
0.001562 0.0002905 2536.91820405
0.001846 0.0002956 2535.13182479
0.002130 0.0003017 2533.06217813
0.002414 0.0003087 2530.70378586
0.002698 0.0003165 2528.05024192
0.002982 0.0003249 2525.10408349
0.003266 0.0003340 2521.86667499
0.003550 0.0003437 2518.33907750
0.003834 0.0003539 2514.52246995
0.004118 0.0003646 2510.41798319
0.004402 0.0003757 2506.02690988
0.004686 0.0003872 2501.35067884
0.004970 0.0003990 2496.38678318
0.005253 0.0004112 2491.16237596
0.005537 0.0004237 2485.63911673
0.005821 0.0004365 2479.83657083
0.006105 0.0004495 2473.75676948
0.006389 0.0004628 2467.40145990
0.006673 0.0004762 2460.77293372
0.006957 0.0004899 2453.86724627
0.007241 0.0005037 2446.69623838
0.007525 0.0005177 2439.25775219
0.007809 0.0005318 2431.55421398
0.008093 0.0005461 2423.58785521
0.008377 0.0005605 2415.36158137
0.008661 0.0005750 2406.87009473
0.008945 0.0005896 2398.12841186
0.009229 0.0006044 2389.13360806
0.009513 0.0006192 2379.88958042
0.009797 0.0006341 2370.39776774
0.010080 0.0006491 2360.69528793
0.010360 0.0006641 2350.85169027
0.010650 0.0006793 2340.42023633
0.010930 0.0006945 2330.11206013
0.011220 0.0007097 2319.20109972
0.011500 0.0007251 2308.43503981
0.011780 0.0007404 2297.44820179
0.012070 0.0007558 2285.83853677
0.012350 0.0007713 2274.41290746
0.012640 0.0007868 2262.36219581
0.012920 0.0008024 2250.51169731
0.013200 0.0008180 2238.45596231
0.013490 0.0008336 2225.76495666
0.013770 0.0008493 2213.29618391
0.014060 0.0008650 2200.19110751
0.014340 0.0008807 2187.34050325
0.014620 0.0008965 2174.30529864
0.014910 0.0009123 2160.61632548
0.015190 0.0009281 2147.21038112
0.015470 0.0009440 2133.62023580
0.015760 0.0009598 2119.37907426
0.016040 0.0009757 2105.45234903
0.016330 0.0009916 2090.86319102
0.016610 0.0010080 2076.60576032
0.016890 0.0010240 2062.19214565
0.017180 0.0010390 2047.10550219
0.017460 0.0010550 2032.38715621
0.017740 0.0010710 2017.52560123
0.018030 0.0010880 2001.99124318
0.018310 0.0011040 1986.84662060
0.018600 0.0011200 1971.03389745
0.018880 0.0011360 1955.61395119
0.019160 0.0011520 1940.08291563
0.019450 0.0011680 1923.87672225
0.019730 0.0011840 1908.10656374
0.020020 0.0012000 1891.66297192
0.020300 0.0012160 1875.66789021
0.020580 0.0012320 1859.56357196
0.020870 0.0012490 1842.79468290
0.021150 0.0012650 1826.50064489
0.021430 0.0012810 1810.11533702
0.021720 0.0012970 1793.06840882
0.022000 0.0013130 1776.51153580
0.022280 0.0013290 1759.87201249
0.022570 0.0013460 1742.57354412
0.022850 0.0013620 1725.79397319
0.023140 0.0013780 1708.35831550
0.023420 0.0013940 1691.45256069
0.023700 0.0014110 1674.48561783
0.023990 0.0014270 1656.86525366
0.024270 0.0014430 1639.79847285
0.024550 0.0014590 1622.68887088
0.024840 0.0014760 1604.96421100
0.025120 0.0014920 1587.85768129
0.025410 0.0015080 1569.99297335
0.025690 0.0015240 1552.84580279
0.025970 0.0015410 1535.54074115
0.026260 0.0015570 1517.75249337
0.026540 0.0015730 1500.40115023
0.026820 0.0015900 1483.03632237
0.027110 0.0016060 1465.05942429
0.027390 0.0016220 1447.67682181
0.027670 0.0016390 1430.46495191
0.027960 0.0016550 1412.49232282
0.028240 0.0016710 1395.13182318
0.028520 0.0016880 1377.93439837
0.028810 0.0017040 1359.99528971
0.029090 0.0017200 1342.67274512
0.029370 0.0017370 1325.55375609
"""

# Slit sphere parameters
TEST_PARS_SLIT_SPHERE = {
    'scale': 0.01, 'background': 0.01,
    'radius': 60000, 'sld': 1, 'solvent_sld': 4,
    }
# Q dQ I(Q) I_smeared(Q)
TEST_DATA_SLIT_SPHERE = """\
2.26097e-05 0.117 5.5781372896e+09 1.4626077708e+06
2.53847e-05 0.117 5.0363141458e+09 1.3117318023e+06
2.81597e-05 0.117 4.4850108103e+09 1.1594863713e+06
3.09347e-05 0.117 3.9364658459e+09 1.0094881630e+06
3.37097e-05 0.117 3.4019975074e+09 8.6518941303e+05
3.92597e-05 0.117 2.4139519814e+09 6.0232158311e+05
4.48097e-05 0.117 1.5816877820e+09 3.8739994090e+05
5.03597e-05 0.117 9.3715407224e+08 2.2745304775e+05
5.59097e-05 0.117 4.8387917428e+08 1.2101295768e+05
6.14597e-05 0.117 2.0193586928e+08 6.0055107771e+04
6.70097e-05 0.117 5.5886110911e+07 3.2749521065e+04
7.25597e-05 0.117 3.7782348010e+06 2.6350963616e+04
7.81097e-05 0.117 5.3407817904e+06 2.9624963314e+04
8.36597e-05 0.117 2.7975485523e+07 3.4403962254e+04
8.92097e-05 0.117 4.9845448282e+07 3.6130017903e+04
9.47597e-05 0.117 6.0092588905e+07 3.3495107849e+04
1.00310e-04 0.117 5.6823430831e+07 2.7475726279e+04
1.05860e-04 0.117 4.3857024036e+07 2.0144282226e+04
1.11410e-04 0.117 2.7277144760e+07 1.3647403260e+04
1.22510e-04 0.117 3.3119334113e+06 6.6519711526e+03
1.33610e-04 0.117 1.4412859402e+06 6.9726212813e+03
1.44710e-04 0.117 8.5620162463e+06 8.1441335775e+03
1.55810e-04 0.117 9.6957429033e+06 6.4559996521e+03
1.66910e-04 0.117 4.3818341914e+06 3.6252154156e+03
1.78010e-04 0.117 2.7448997387e+05 2.4006505342e+03
1.89110e-04 0.117 8.0472009936e+05 2.8187789089e+03
2.00210e-04 0.117 2.8149552834e+06 3.0915662855e+03
2.11310e-04 0.117 2.7510907861e+06 2.3722530293e+03
2.22410e-04 0.117 1.0053133293e+06 1.4473468311e+03
2.33510e-04 0.117 5.8428305052e+03 1.2048540556e+03
2.44610e-04 0.117 5.1699305004e+05 1.4625670042e+03
2.55710e-04 0.117 1.2120227268e+06 1.5010705973e+03
2.66810e-04 0.117 9.7896842846e+05 1.1336343426e+03
2.77910e-04 0.117 2.5507264791e+05 8.1848818080e+02
3.05660e-04 0.117 5.2403101181e+05 7.4913374357e+02
3.33410e-04 0.117 5.8699343809e+04 4.4669964560e+02
3.61160e-04 0.117 3.0844327150e+05 4.6774007542e+02
3.88910e-04 0.117 8.3360142970e+03 2.7169550220e+02
4.16660e-04 0.117 1.8630080583e+05 3.0710983679e+02
4.44410e-04 0.117 3.1616804732e-01 1.7959006831e+02
4.72160e-04 0.117 1.1299016314e+05 2.0763952339e+02
4.99910e-04 0.117 2.9952522747e+03 1.2536542765e+02
5.27660e-04 0.117 6.7625695649e+04 1.4013969777e+02
5.55410e-04 0.117 7.6927460089e+03 8.2145593180e+01
6.10910e-04 0.117 1.1229057779e+04 8.4519745643e+01
6.66410e-04 0.117 1.3035567943e+04 8.1554625609e+01
7.21910e-04 0.117 1.3309931343e+04 7.4437319172e+01
7.77410e-04 0.117 1.2462626212e+04 6.4697088261e+01
8.32910e-04 0.117 1.0912927143e+04 5.3773301044e+01
8.88410e-04 0.117 9.0172597469e+03 4.2843375753e+01
9.43910e-04 0.117 7.0496495917e+03 3.2771032724e+01
9.99410e-04 0.117 5.2030483682e+03 2.4113557144e+01
1.05491e-03 0.117 3.5988976711e+03 1.7160773658e+01
1.11041e-03 0.117 2.2996060652e+03 1.2016626459e+01
1.22141e-03 0.117 6.4766590598e+02 6.0373017740e+00
1.33241e-03 0.117 4.1963483264e+01 4.5215452974e+00
1.44341e-03 0.117 6.3370708246e+01 5.1054681903e+00
1.55441e-03 0.117 3.0736750577e+02 5.9176165298e+00
1.66541e-03 0.117 5.0327682399e+02 5.9815000189e+00
1.77641e-03 0.117 5.4084331454e+02 5.1634639625e+00
1.88741e-03 0.117 4.3488671756e+02 3.8535158148e+00
1.99841e-03 0.117 2.6322287860e+02 2.5824997753e+00
2.10941e-03 0.117 1.0793633150e+02 1.7315517194e+00
2.22041e-03 0.117 1.8474448850e+01 1.4077213604e+00
2.33141e-03 0.117 1.5864062279e+00 1.4771560682e+00
2.44241e-03 0.117 3.2267213848e+01 1.6916253448e+00
2.55341e-03 0.117 7.4289116207e+01 1.8274751193e+00
2.66441e-03 0.117 9.9000521929e+01 1.7706812289e+00
"""

def main():
    """
    Run tests given is sys.argv.

    Returns 0 if success or 1 if any tests fail.
    """
    import sys
    import xmlrunner

    suite = unittest.TestSuite()
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))

    runner = xmlrunner.XMLTestRunner(output='logs')
    result = runner.run(suite)
    return 1 if result.failures or result.errors else 0


############################################################################
# usage demo
############################################################################

def _eval_demo_1d(resolution, title):
    import sys
    from sasmodels import core
    name = sys.argv[1] if len(sys.argv) > 1 else 'cylinder'

    if name == 'cylinder':
        pars = {'length':210, 'radius':500}
    elif name == 'teubner_strey':
        pars = {'a2':0.003, 'c1':-1e4, 'c2':1e10, 'background':0.312643}
    elif name == 'sphere' or name == 'spherepy':
        pars = TEST_PARS_SLIT_SPHERE
    elif name == 'ellipsoid':
        pars = {
            'scale':0.05,
            'rpolar':500, 'requatorial':15000,
            'sld':6, 'solvent_sld': 1,
            }
    else:
        pars = {}
    defn = core.load_model_definition(name)
    model = core.load_model(defn)

    kernel = core.make_kernel(model, [resolution.q_calc])
    theory = core.call_kernel(kernel, pars)
    Iq = resolution.apply(theory)

    if isinstance(resolution, Slit1D):
        width, height = resolution.width, resolution.height
        Iq_romb = romberg_slit_1d(resolution.q, width, height, model, pars)
    else:
        dq = resolution.q_width
        Iq_romb = romberg_pinhole_1d(resolution.q, dq, model, pars)

    import matplotlib.pyplot as plt
    plt.loglog(resolution.q_calc, theory, label='unsmeared')
    plt.loglog(resolution.q, Iq, label='smeared', hold=True)
    plt.loglog(resolution.q, Iq_romb, label='romberg smeared', hold=True)
    plt.legend()
    plt.title(title)
    plt.xlabel("Q (1/Ang)")
    plt.ylabel("I(Q) (1/cm)")

def demo_pinhole_1d():
    q = np.logspace(-4, np.log10(0.2), 400)
    q_width = 0.1*q
    resolution = Pinhole1D(q, q_width)
    _eval_demo_1d(resolution, title="10% dQ/Q Pinhole Resolution")

def demo_slit_1d():
    q = np.logspace(-4, np.log10(0.2), 100)
    w = h = 0.
    #w = 0.000000277790
    w = 0.0277790
    #h = 0.00277790
    #h = 0.0277790
    resolution = Slit1D(q, w, h)
    _eval_demo_1d(resolution, title="(%g,%g) Slit Resolution"%(w,h))

def demo():
    import matplotlib.pyplot as plt
    plt.subplot(121)
    demo_pinhole_1d()
    #plt.yscale('linear')
    plt.subplot(122)
    demo_slit_1d()
    #plt.yscale('linear')
    plt.show()


if __name__ == "__main__":
    demo()
    #main()