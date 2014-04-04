#__docformat__ = "restructuredtext en"
# ******NOTICE***************
# from optimize.py module by Travis E. Oliphant
#
# You may copy and use this module as you see fit with no
# guarantee implied provided you keep this notice in all copies.
# *****END NOTICE************
#
# Modified by Paul Kienzle to support bounded minimization
"""
Downhill simplex optimizer.
"""

__all__ = ['simplex']

__docformat__ = "restructuredtext en"

import numpy
__version__="0.7"

def wrap_function(function, bounds):
    ncalls = [0]
    if bounds is not None:
        lo, hi = [numpy.asarray(v) for v in bounds]
        def function_wrapper(x):
            ncalls[0] += 1
            if numpy.any((x<lo)|(x>hi)):
                return numpy.inf
            else:
                return function(x)
    else:
        def function_wrapper(x):
            ncalls[0] += 1
            return function(x)
    return ncalls, function_wrapper

class Result:
    """
    Results from the fit.
    
    x : ndarray
        Best parameter set
    fx : float
        Best value
    iters : int
        Number of iterations
    calls : int
        Number of function calls
    success : boolean
        True if the fit completed successful, false if terminated early
        because of too many iterations.
    """
    def __init__(self, x, fx, iters, calls, status):
        self.x,self.fx,self.iters,self.calls=x,fx,iters,calls
        self.status = status
    def __str__(self):
        return "Minimum %g at %s after %d calls"%(self.fx,self.x,self.calls)

def dont_abort(): return False

def simplex(f, x0=None, bounds=None, radius=0.05,
            xtol=1e-4, ftol=1e-4, maxiter=None,
            update_handler=None, abort_test=dont_abort):
    """
    Minimize a function using Nelder-Mead downhill simplex algorithm.

    This optimizer is also known as Amoeba (from Numerical Recipes) and
    the Nealder-Mead simplex algorithm.  This is not the simplex algorithm
    for solving constrained linear systems.

    Downhill simplex is a robust derivative free algorithm for finding
    minima.  It proceeds by choosing a set of points (the simplex) forming
    an n-dimensional triangle, and transforming that triangle so that the
    worst vertex is improved, either by stretching, shrinking or reflecting
    it about the center of the triangle.  This algorithm is not known for
    its speed, but for its simplicity and robustness, and is a good algorithm
    to start your problem with.

    *Parameters*:

        f : callable f(x,*args)
            The objective function to be minimized.
        x0 : ndarray
            Initial guess.
        bounds : (ndarray,ndarray) or None
            Bounds on the parameter values for the function.
        radius: float
            Size of the initial simplex.  For bounded parameters (those
            which have finite lower and upper bounds), radius is clipped
            to a value in (0,0.5] representing the portion of the 
            range to use as the size of the initial simplex.

    *Returns*: Result (`park.simplex.Result`)

        x : ndarray
            Parameter that minimizes function.
        fx : float
            Value of function at minimum: ``fopt = func(xopt)``.
        iters : int
            Number of iterations performed.
        calls : int
            Number of function calls made.
        success : boolean
            True if fit completed successfully.

    *Other Parameters*:

        xtol : float
            Relative error in xopt acceptable for convergence.
        ftol : number
            Relative error in func(xopt) acceptable for convergence.
        maxiter : int=200*N
            Maximum number of iterations to perform.  Defaults
        update_handler : callable
            Called after each iteration, as callback(xk,fxk), where xk
            is the current parameter vector and fxk is the function value.
            Returns True if the fit should continue.


    *Notes*

        Uses a Nelder-Mead simplex algorithm to find the minimum of
        function of one or more variables.

    """
    fcalls, func = wrap_function(f, bounds)
    x0 = numpy.asfarray(x0).flatten()
    #print "x0",x0
    N = len(x0)
    rank = len(x0.shape)
    if not -1 < rank < 2:
        raise ValueError, "Initial guess must be a scalar or rank-1 sequence."

    if maxiter is None:
        maxiter = N * 200

    rho = 1; chi = 2; psi = 0.5; sigma = 0.5;

    if rank == 0:
        sim = numpy.zeros((N+1,), dtype=x0.dtype)
    else:
        sim = numpy.zeros((N+1,N), dtype=x0.dtype)
    fsim = numpy.zeros((N+1,), float)
    sim[0] = x0
    fsim[0] = func(x0)

    # Metropolitan simplex: simplex has vertices at x0 and at
    # x0 + j*radius for each unit vector j.  Radius is a percentage 
    # change from the initial value, or just the radius if the initial
    # value is 0.  For bounded problems, the radius is a percentage of
    # the bounded range in dimension j.
    val = x0*(1+radius)
    val[val == 0] = radius
    if bounds is not None:
        radius = numpy.clip(radius,0,0.5)
        lo,hi = [numpy.asarray(v) for v in bounds]

        # Keep the initial simplex inside the bounds
        x0[x0<lo] = lo[x0<lo]
        x0[x0>hi] = hi[x0>hi]
        bounded = ~numpy.isinf(lo) & ~numpy.isinf(hi)
        val[bounded] = x0[bounded] + (hi[bounded]-lo[bounded])*radius
        val[val<lo] = lo[val<lo]
        val[val>hi] = hi[val>hi]
        
        # If the initial point was at or beyond an upper bound, then bounds
        # projection will put x0 and x0+j*radius at the same point.  We
        # need to detect these collisions and reverse the radius step
        # direction when such collisions occur.  The only time the collision
        # can occur at the lower bound is when upper and lower bound are
        # identical.  In that case, we are already done.
        collision = val==x0
        if numpy.any(collision):
            reverse = x0*(1-radius)
            reverse[reverse==0] = -radius
            reverse[bounded] = x0[bounded] - (hi[bounded]-lo[bounded])*radius
            val[collision] = reverse[collision]
        
        # Make tolerance relative for bounded parameters
        tol = numpy.ones(x0.shape)*xtol
        tol[bounded] = (hi[bounded]-lo[bounded])*xtol
        xtol = tol

    # Compute values at the simplex vertices
    for k in range(0,N):
        y = x0+0
        y[k] = val[k]
        sim[k+1] = y
        fsim[k+1] = func(y)

    #print sim
    ind = numpy.argsort(fsim)
    fsim = numpy.take(fsim,ind,0)
    # sort so sim[0,:] has the lowest function value
    sim = numpy.take(sim,ind,0)
    #print sim

    iterations = 1
    while iterations < maxiter:
        if numpy.all(abs(sim[1:]-sim[0]) <= xtol) \
            and max(abs(fsim[0]-fsim[1:])) <= ftol:
            #print abs(sim[1:]-sim[0])
            break

        xbar = numpy.sum(sim[:-1],0) / N
        xr = (1+rho)*xbar - rho*sim[-1]
        #print "xbar" ,xbar,rho,sim[-1],N
        #break
        fxr = func(xr)
        doshrink = 0

        if fxr < fsim[0]:
            xe = (1+rho*chi)*xbar - rho*chi*sim[-1]
            fxe = func(xe)

            if fxe < fxr:
                sim[-1] = xe
                fsim[-1] = fxe
            else:
                sim[-1] = xr
                fsim[-1] = fxr
        else: # fsim[0] <= fxr
            if fxr < fsim[-2]:
                sim[-1] = xr
                fsim[-1] = fxr
            else: # fxr >= fsim[-2]
                # Perform contraction
                if fxr < fsim[-1]:
                    xc = (1+psi*rho)*xbar - psi*rho*sim[-1]
                    fxc = func(xc)

                    if fxc <= fxr:
                        sim[-1] = xc
                        fsim[-1] = fxc
                    else:
                        doshrink=1
                else:
                    # Perform an inside contraction
                    xcc = (1-psi)*xbar + psi*sim[-1]
                    fxcc = func(xcc)

                    if fxcc < fsim[-1]:
                        sim[-1] = xcc
                        fsim[-1] = fxcc
                    else:
                        doshrink = 1

                if doshrink:
                    for j in xrange(1,N+1):
                        sim[j] = sim[0] + sigma*(sim[j] - sim[0])
                        fsim[j] = func(sim[j])

        ind = numpy.argsort(fsim)
        sim = numpy.take(sim,ind,0)
        fsim = numpy.take(fsim,ind,0)
        if update_handler is not None:
            update_handler(sim[0],fsim[0])
        iterations += 1
        if abort_test(): break

    status = 0 if iterations < maxiter else 1
    res = Result(sim[0],fsim[0],iterations,fcalls[0], status)
    return res

def main():
    import time
    def rosen(x):  # The Rosenbrock function
        return numpy.sum(100.0*(x[1:]-x[:-1]**2.0)**2.0 + (1-x[:-1])**2.0,axis=0)


    x0 = [0.8,1.2,0.7]
    print "Nelder-Mead Simplex"
    print "==================="
    start = time.time()
    x = simplex(rosen,x0)
    print x
    print "Time:",time.time() - start

    x0 = [0]*3
    print "Nelder-Mead Simplex"
    print "==================="
    print "starting at zero"
    start = time.time()
    x = simplex(rosen,x0)
    print x
    print "Time:",time.time() - start

    x0 = [0.8,1.2,0.7]
    lo,hi = [0]*3, [1]*3
    print "Bounded Nelder-Mead Simplex"
    print "==========================="
    start = time.time()
    x = simplex(rosen,x0,bounds=(lo,hi))
    print x
    print "Time:",time.time() - start


    x0 = [0.8,1.2,0.7]
    lo,hi = [0.999]*3, [1.001]*3
    print "Bounded Nelder-Mead Simplex"
    print "==========================="
    print "tight bounds"
    print "simplex is smaller than 1e-7 in every dimension, but you can't"
    print "see this without uncommenting the print statement simplex function"
    start = time.time()
    x = simplex(rosen,x0,bounds=(lo,hi),xtol=1e-4)
    print x
    print "Time:",time.time() - start


    x0 = [0]*3
    hi,lo = [-0.999]*3, [-1.001]*3
    print "Bounded Nelder-Mead Simplex"
    print "==========================="
    print "tight bounds, x0=0 outside bounds from above"
    start = time.time()
    x = simplex(lambda x:rosen(-x),x0,bounds=(lo,hi),xtol=1e-4)
    print x
    print "Time:",time.time() - start


    x0 = [0.8,1.2,0.7]
    lo,hi = [-numpy.inf]*3, [numpy.inf]*3
    print "Bounded Nelder-Mead Simplex"
    print "==========================="
    print "infinite bounds"
    start = time.time()
    x = simplex(rosen,x0,bounds=(lo,hi),xtol=1e-4)
    print x
    print "Time:",time.time() - start

if __name__ == "__main__":
    main()
