"""
"""
from __future__ import division
import thread
import numpy

from snobfit.snobfit import snobfit

import fit,fitresult

__all__ = ['Snobfit']

class Snobfit(fit.Fitter):
    """
    Response surface optimizer

    This implements `park.fit.Fitter`.
    """

    p=0.5
    """Locality: 1.0 for completely global, 0. for local"""
    dn=5
    """Number of surplus points in quadratic fit; increase for noisy functions"""
    maxiter=1000
    """Maximum number of iterations"""
    maxfun=1000
    """Maximum number of function evaluations"""
    nstop=50
    """Number of times no improvement is tolerated"""

    def _monitor(self, k, x, fx, improved):
        self.handler.progress(k,self.maxiter)
        if improved:
            self.handler.result.update(x,fx,-1)
            self.handler.improvement()

    def _call_snobfit(self, objective, x0, bounds):
        x,fx,calls = snobfit(objective, x0, bounds, fglob=0,
                             callback=self._monitor)

        # Post the result
        self.handler.result.update(x, fx, calls)
        self.handler.result.calc_cov(objective)
        self.handler.done = True
        self.handler.finalize()

    def _fit(self, objective, x0, bounds):
        self._threaded(self._call_snobfit, objective, x0, bounds)

if __name__ == "__main__":
    fit.demo2(fitter=Snobfit())
