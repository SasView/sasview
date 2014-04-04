
# The job queue needs to be in a transaction/rollback protected database.
# If the server is rebooted, long running jobs should continue to work.
#
from __future__ import division
import numpy

import simplex

import fitresult, pmap, fit

__all__ = ['fitmc', 'FitMCJob']

class LocalFit(object):
    """
    Abstract interface for a local minimizer

    See `park.fitmc.FitSimplex` for a concrete implementation.
    """
    def fit(self, objective, x0):
        """
        Minimize the value of a fitness function.

        See `park.fitmc.Fitness` for the definition of the goodness of fit
        object.  x0 is a vector containing the initial value for the fit.
        """
    def abort(self):
        """
        Cancel the fit.  This will be called from a separate execution
        thread.  The fit should terminate as soon as possible after this
        function has been called.  Ideally this would interrupt the
        cur
        """

class FitSimplex(LocalFit):
    """
    Local minimizer using Nelder-Mead simplex algorithm.

    Simplex is robust and derivative free, though not very efficient.

    This class wraps the bounds contrained Nelder-Mead simplex
    implementation for `park.simplex.simplex`.
    """
    radius = 0.05
    """Size of the initial simplex; this is a portion between 0 and 1"""
    xtol = 1
    #xtol = 1e-4
    """Stop when simplex vertices are within xtol of each other"""
    ftol = 1e-4
    """Stop when vertex values are within ftol of each other"""
    maxiter = None
    """Maximum number of iterations before fit terminates"""
    def fit(self, fitness, x0):
        """Run the fit"""
        self.cancel = False
        pars = fitness.fit_parameters()
        bounds = numpy.array([p.range for p in pars]).T
        result = simplex.simplex(fitness, x0, bounds=bounds,
                                 radius=self.radius, xtol=self.xtol,
                                 ftol=self.ftol, maxiter=self.maxiter,
                                 abort_test=self._iscancelled)
        #print "calls:",result.calls
        #print "simplex returned",result.x,result.fx
        # Need to make our own copy of the fit results so that the
        # values don't get stomped on by the next fit iteration.
        fitpars = [fitresult.FitParameter(pars[i].name,pars[i].range,v)
                   for i,v in enumerate(result.x)]
        res = fitresult.FitResult(fitpars, result.calls, result.fx)
        # Compute the parameter uncertainties from the jacobian
        res.calc_cov(fitness)
        return res

    def abort(self):
        """Cancel the fit in progress from another thread of execution"""
        # Effectively an atomic operation; rely on GIL to protect it.
        self.cancel = True
        # Abort the current function evaluation if possible.
        if hasattr(fitness,'abort'): self.fitness.abort()

    def _iscancelled(self): return self.cancel

class MapMC(object):
    """
    Evaluate a local fit at a particular start point.

    This is the function to be mapped across a set of start points for the
    monte carlo map-reduce implementation.

    See `park.pmap.Mapper` for required interface.
    """
    def __init__(self, minimizer, fitness):
        self.minimizer, self.fitness = minimizer, fitness
    def __call__(self, x0):
        return self.minimizer.fit(self.fitness,x0)
    def abort(self):
        self.minimizer.abort()

class CollectMC(object):
    """
    Collect the results from multiple start points in a Monte Carlo fit engine.

    See `park.pmap.Collector` for required interface.
    """
    def __init__(self, number_expected, handler):
        self.number_expected = number_expected
        """Number of starting points to check with local optimizer"""
        self.iterations = 0
        self.best = None
        self.calls = 0
        self.handler = handler
        self.handler.done = False
    def __call__(self, result):
        # Keep track of the amount of work done
        self.iterations += 1
        self.calls += result.calls
        if self.best is None or result.fitness < self.best.fitness:
            self.best = result
            self.handler.result = result
            self.handler.improvement()
        # Progress should go after improvement in case the fit handler
        # wants to suppress intermediate improvements
        self.handler.progress(self.iterations, self.number_expected)
    def abort(self):
        self.handler.done = True
        self.handler.abort()
    def finalize(self):
        self.handler.result.calls = self.calls
        self.handler.done = True
        self.handler.finalize()
    def error(self, msg):
        self.handler.done = True
        self.handler.error(msg)

def fitmc(fitness, x0, bounds, localfit, n, handler):
    """
    Run a monte carlo fit.

    This procedure maps a local optimizer across a set of n initial points.
    The initial parameter value defined by the fitness parameters defines
    one initial point.  The remainder are randomly generated within the
    bounds of the problem.

    localfit is the local optimizer to use.  It should be a bounded
    optimizer following the `park.fitmc.LocalFit` interface.

    handler accepts updates to the current best set of fit parameters.
    See `park.fitresult.FitHandler` for details.
    """
    # Generate random number within bounds.  If bounds are indefinite, use [0,1]
    # If bounds are semi-definite, use [low,low+1] or [high-1,high], depending
    # on which limit is unbounded.
    lo,hi = bounds
    inf_lo = numpy.isinf(lo)
    inf_hi = numpy.isinf(hi)
    delta = hi-lo
    delta[inf_lo|inf_hi] = 1.0
    lo[inf_lo] = hi[inf_lo] - 1.0
    lo[inf_lo&inf_hi] = 0.0
    P = numpy.random.rand(n,len(x0))*delta+lo
    #print "Population",P
    P[0] = x0

    pmap.pmapreduce(MapMC(localfit,fitness),
                    CollectMC(n,handler),
                    P)

class FitMC(fit.Fitter):
    """
    Monte Carlo optimizer.

    This implements `park.fit.Fitter`.
    """
    localfit = FitSimplex()
    start_points = 10

    def _fit(self, objective, x0, bounds):
        """
        Run a monte carlo fit.

        This procedure maps a local optimizer across a set of initial points.
        """
        fitmc(objective, x0, bounds, self.localfit,
              self.start_points, self.handler)

if __name__ == "__main__":
    fit.demo2(FitMC(localfit=FitSimplex(),start_points=10))
