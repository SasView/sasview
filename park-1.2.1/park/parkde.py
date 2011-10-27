"""
"""
from __future__ import division
import thread
import numpy

import diffev

import fit,fitresult

__all__ = ['DiffEv']

class DiffEv(fit.Fitter):
    """
    Differential evolution optimizer

    This implements `park.fit.Fitter`.
    """

    maxiter=1000
    """Maximum number of iterations"""
    pop_scale=4
    """Number of active points per dimension"""
    crossover_rate=0.9
    """Amount of mixing in population"""
    Fscale=0.5
    """Step size along difference vector"""
    tolerance=1e-5
    """Fit tolerance"""

    def progress(self, k, n):
        self.handler.progress(k,n)
    def improvement(self, x, fx, ncalls=-1):
        self.handler.result.update(x,fx,-1)
        self.handler.improvement()

    def _call(self, objective, x0, bounds):
        x,fx,calls = diffev.diffev(objective, bounds,
                                   maxiter=self.maxiter,
                                   pop_scale=self.pop_scale,
                                   crossover_rate=self.crossover_rate,
                                   Fscale=self.Fscale,
                                   tolerance=self.tolerance,
                                   x0=x0, monitor=self)

        # Post the result
        self.handler.result.update(x, fx, calls)
        self.handler.result.calc_cov(objective)
        self.handler.done = True
        self.handler.finalize()

    def _fit(self, objective, x0, bounds):
        self._threaded(self._call, objective, x0, bounds)

if __name__ == "__main__":
    fit.demo2(fitter=DiffEv())
