"""
Defines transformations between the a fit space and the parameter space.

The parameter space maps a set of possibly bounded dimensions into a
real-valued fitness::

    f: [a,b]**n |-> R

The fit space is constrained to map values in the unit box::

    f': [0,1]**n |-> R 

Here we can define f' using the zero-one mapper::

    f' = ZeroOneMapper(f,a,b)
    f'(v) = f(x)

An asymptote function maps x to [0,1], preserving at least 12 digits of
precision.

Using this mapping, the optimizer can operate in a well known space
independent of parameter precision.  This allows the use of reasonable
constants for items such as a step size and initial value.

Note: we do not yet support fitness functions with analytic derivatives.
Given df/dp and mapping function f'(v) = f(M(v)) then df'/dv = df/dM dM/dv.
So the derivatives need to be multiplied by the derivative of the
parameter mapper.  Not difficult computationally, but the definition of
the fitness function does not currently support this organization.
"""


class FitCobyla(LocalFit):
    """
    Local minimizer using COBYLA, Constrained Optimization by Linear
    Approximation.
    
    COBYLA minimizes an objective function F(X) subject to M inequality 
    constraints on X, where X is a vector of variables that has N components. 
    The algorithm employs linear approximations to the objective and 
    constraint functions, the approximations being formed by linear 
    interpolation at N+1 points in the space of the variables.  These 
    interpolation points can be regarded as vertices of a simplex. The
    parameter rho controls the size of the simplex and it is reduced
    automatically from radius to xtol. For each RHO the subroutine tries
    to achieve a good vector of variables for the current size, and then
    RHO is reduced until the value xtol is reached. Therefore radius and
    xtol should be set to reasonable initial changes to and the required   
    accuracy in the variables respectively, but this accuracy should be
    viewed as a subject for experimentation because it is not guaranteed.

    Basic bounds constraints are built into the interface.  These bounds
    map the space into the n-D unit cube, so values values for radius
    and xtol should be chosen accordingly.  Regardless of xtol, the
    fit is stopped after maxiter function evaluations.
    """
    radius = 0.05
    """Size of the initial simplex; this is a portion between 0 and 1"""
    xtol = 1e-4
    """Stop when simplex vertices are within xtol of each other"""
    maxiter = 1000
    def __call__(self):
        from scipy.optimize.cobyla import fmin_cobyla as cobyla

class ArctanAsymptote(object):
    """
    Arctan asymptote function for mapping (-inf,inf) to [0,1].

    With all attributes constant, either the class or an instance can be used.

    An asymptote function is monotonically increasing and finite everywhere.
    Assuming the function is a at -inf and b at +inf, scale is 1/(b-a) and
    offset is a.  Together with an inverse function, this allows us to
    transform between an infinite range and the range [0,1].  Semidefinite
    map to (-inf,0] and [0,inf).

    ArctanAsymptote is approximately linear in [-0.5,0.5], and is useful 
    out to the range [-1e15,1e15],  though with much reduced precision 
    for larger values.
    """
    scale = 1/numpy.pi
    offset = -numpy.pi/2
    forward = numpy.arctan
    inverse = numpy.tan

def fp_forward(x):
    """
    Linearize floating point values using an exponential scale.
    
    Convert sign*m*2^e to sign*(e+1023+m), yielding a value in [-2047,2047]
    """
    (m,e) = numpy.frexp(x)
    s = numpy.sign(x)
    v = (e+1023+m*s)*s
    return v
def fp_inverse(v):
    """
    Restore floating point value from linear form on an exponential scale.
    
    Convert sign*(e+1023+m) to sign*m*2^e, yielding a value in [-1e308,1e308]
    """
    s = sign(v)
    v *= s
    m = floor(v)
    e = v-m
    x = ldexp(s*m,e)
    return x
fp_min, fp_max = -(1024+1023), (1024+1023)
class Asymptote:
    """
    Logarithmic asymptote function.
    
    This is an asymptote function which follows the floating point 
    representation, using the following mapping::
    
        [-1e308,-1e-308] -> [0,0.5)
        0 -> 0.5
        [1e-308,1e308] -> (0.5+eps,1]

    With 11 bits of the 53 bits of available precision for the exponent, 
    this leaves a tolerance of 1e-12 on the fitting parameters, which is 
    easily good enough for any real unbounded fitting problem.  The user 
    can increased the precision on the bounded parameters by using tighter 
    bounds.
    """
    scale = 1/(fp_max-fp_min)
    offset = fp_min
    forward = fp_forward
    inverse = fp_inverse

class ZeroOneMapper(object):
    """
    Map function range into [0,1]**n.

    Given f: [a,b] -> R
    Defines f': [0,1] -> R
    
    The method encode(x) returns a value in [0,1]
    The method decode(v) returns a value in [a,b]
    The method __call__(v) returns f(decode(v))
    
    For indefinite and semidefinte ranges, an asymptote transformation
    is needed.  Normally this is `park.rangemap.Asymptote` which supports
    the full floating point range of values, but is limited to about
    12 digits of precision.  The arctan function can also be used
    (see `park.rangemap.ArctanAsymptote`).
    
    Range is determined by the bounds low and high.  Each dimension may be 
    unbounded, semi-definite or bounded. Bounded functions use a linear 
    mapping between low and high.  Unbounded functions use an asymptote 
    function, which should be -1 at -inf, 0 at 0 and 1 at +inf, and 
    approximate the identity function between [-0.5,0.5].
    
    This can be used to turn any unconstrained optimizer into a [0,1]
    bounded optimizer by sending infeasible points to infinity.

    Note: Newton-style optimizers will not work in this regime, but 
    instead require a hint about the direction of the unconstrained
    region.
    """
    def __init__(self, base_function, low, high, asymptote=Asymptote,
                 range_check=False):
        """
        Function range mapper.  See `park.rangemap.ZeroOneMapper` for details.

        base_function is the function being wrapped.
        
        low[k],high[k] is the range of values for each fitting parameter k.
        
        range_check is True if calls to the mapper may include out of range
        values.  In this case, f(v) returns inf for out of range values and
        encode/decode raise exceptions.

        asymptote is the asymptote function to use when linearizing
        indefinite ranges.
        """

        unbounded_low = numpy.isinf(low)
        unbounded_high = numpy.isinf(high)
        unbounded = unbounded_low|unbounded_high
    
        # Determine linear scale and offset for v = (x-offset)/scale
        # For semi-infinite ranges, use the known bound as the offset.  This 
        # transforms [a,inf) to [0.5,1] and (-inf,b] to [0,0.5].
        # Infinite ranges should use offset 0.
        scale = (high-low)
        offset = -low
        scale[unbounded_low | unbounded_high] = 0.
        offset[unbounded_low] = high[unbounded_low]
        offset[unbounded_high] = low[unbounded_high]
        offset[unbounded_low & unbounded_high] = 0. # low&high must be last

        # Determine transformed scale and offset
        # If the value is unbounded, then use asymptote directly.
        # If bounded below, then transform [0.5,1] to [0,1] using (v-0.5)/0.5
        # If bounded above, then transform [0,0.5] to [0,1] using v/0.5
        a_scale = numpy.ones(scale.shape)*asymptote.scale
        a_scale[unbounded_low ^ unbounded_high] *= 0.5
        a_offset = numpy.zeros(offset.shape)+asymptote.offset
        a_offset[unbounded_high & ~unbounded_low] += 0.5*asymptote.scale
        a_forward = asymptote.forward
        a_inverse = asymptote.inverse

        # Preselect the relevant elements
        a_scale = a_scale[unbounded]
        a_offset = a_offset[unbounded]

        # Remember the transformation parameters
        self.low,self.high = low,high
        self.base_function = base_function
        self.scale,self.offset = scale,offset
        self.a_scale,self.a_offset = a_scale,a_offset
        self.a_forward,self.a_inverse = a_forward,a_inverse
        
        # To minimize function call overhead, use only the linear bounds
        # tranform if the problem is completely bounded.
        if numpy.any(unbounded):
            self.__call__ = self._indefinite
        else:
            self.__call__ = self._definite    

    def _indefinite(self, v):
        """Use this function if some bounds are indefinite"""
        x = v.copy()
        x[unbounded] = self.a_inverse(x[unbounded])*self.a_scale + self.a_offset
        x = x*self.scale+self.offset
        return self.base_function(x)
    def _definite(self, v):
        """Use this function if all bounds are definite"""
        return self.base_function(v*self.scale+self.offset)
    def _indefinite_checked(self, v):
        """Use this function if some bounds are indefinite and ranges need
        to be checked"""
        if numpy.any(v<0|v>1): return numpy.inf
        x = v.copy()
        x[unbounded] = self.a_inverse(x[unbounded])*self.a_scale + self.a_offset
        x = x*self.scale+self.offset
        return self.base_function(x)
    def _definite_checked(self, v):
        """Use this function if all bounds are definite, but ranges need
        to be checked"""
        if numpy.any(v<0|v>1): return numpy.inf
        return self.base_function(v*self.scale+self.offset)

    def decode(v):
        """Transform from range [0,1] to [a,b]."""
        if numpy.any(v<0|v>1): 
            raise RuntimeError("value out of range [0,1]")
        x = v.copy()
        x[unbounded] = self.a_forward(x[unbounded])*a_scale + a_offset
        x = x*scale+offset
        return x
    def encode(x):
        """Transform from range [a,b] to [0,1]."""
        if numpy.any(x<self.low|x>self.high): 
            raise RuntimeError("value out of range [a,b]")
        v = (x-offset)/scale
        v[unbounded] = (self.a_inverse(v[unbounded])-a_offset)/a_scale
        return v

# Functional implementation: return transformation functions.
# This is faster but less pythonic
def zero_one_mapper(base_function, low, high, asymptote=ArctanAsymptote):
    """
    Map function range into [0,1]**n.   
    
    Returns a pair of functions f and inv.  The function f takes an
    encoded value in 
     encode, which takes x and returns a value 
    in [0,1] and decode, which takes a value in [0,1] and returns x.
    
    Range is determined by the bounds low and high.  Each dimension may be 
    unbounded, semi-definite or bounded. Bounded functions use a linear 
    mapping between low and high.  Unbounded functions use an asymptote 
    function, which should be -1 at -inf, 0 at 0 and 1 at +inf, and 
    approximate the identity function between [-0.5,0.5].
    
    This can be used to turn any unconstrained optimizer into a [0,1]
    bounded optimizer by sending infeasible points to infinity.

    Note: Newton-style optimizers will not work in this regime, but 
    instead require a hint about the direction of the unconstrained
    region.
    """

    unbounded_low = numpy.isinf(low)
    unbounded_high = numpy.isinf(high)
    unbounded = unbounded_low|unbounded_high
    
    # Determine linear scale and offset for v = (x-offset)/scale
    # For semi-infinite ranges, use the known bound as the offset.  This 
    # transforms [a,inf) to [0.5,1] and (-inf,b] to [0,0.5].
    # Infinite ranges should use offset 0.
    scale = (high-low)
    offset = -low
    scale[unbounded_low | unbounded_high] = 0.
    offset[unbounded_low] = high[unbounded_low]
    offset[unbounded_high] = low[unbounded_high]
    offset[unbounded_low & unbounded_high] = 0. # low&high must be last

    # Determine transformed scale and offset
    # If the value is unbounded, then use asymptote directly.
    # If bounded below, then transform [0.5,1] to [0,1] using (v-0.5)/0.5
    # If bounded above, then transform [0,0.5] to [0,1] using v/0.5
    a_scale = numpy.ones(scale.shape)*asymptote.scale
    a_scale[unbounded_low ^ unbounded_high] *= 0.5
    a_offset = numpy.zeros(offset.shape)+asymptote.offset
    a_offset[unbounded_high & ~unbounded_low] += 0.5*asymptote.scale

    # Preselect the relevant elements
    a_scale = a_scale[unbounded]
    a_offset = a_offset[unbounded]
    

    if numpy.any(unbounded):
        def function(v):
            x = v.copy()
            x[unbounded] = asymptote.inverse(x[unbounded])*a_scale + a_offset
            x = x*scale+offset
            return base_function(x)
        def decode(v):
            x = v.copy()
            x[unbounded] = asymptote.inverse(x[unbounded])*a_scale + a_offset
            x = x*scale+offset
            return x
        def encode(x):
            v = (x-offset)/scale
            v[unbounded] = (asymptote.function(v[unbounded])-a_offset)/a_scale
            return v
    else:
        def function(v):  return base_function( (x-offset)/scale )
        def decode(v):  return (v*scale+offset)
        def function(x):  return base_function( (x-offset)/scale )
        def decode(v):  return (v*scale+offset)

    return function, encode, decode


def bounded(function, low, high):
    """
    Evaluate a function with bounds checking.
    
    This can be used to turn any unconstrained optimizer into a
    constrained optimizer by sending infeasible points to infinity.

    Note: Newton-style optimizers will not work in this regime, but 
    instead require a hint about the direction of the unconstrained
    region.
    
    Note: unused function which may be removed in future versions.
    """
    def function_wrapper(x):
        if  numpy.any((x<low) | (x>high)):
            return numpy.Inf
        else:
            return function(x)
    function_wrapper.__doc__ = function.__doc__
    return function_wrapper

