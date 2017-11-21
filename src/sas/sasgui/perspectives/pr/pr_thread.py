
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################

import sys
import time
from sas.sascalc.data_util.calcthread import CalcThread

class CalcPr(CalcThread):
    """
    Compute P(r)
    """

    def __init__(self, pr, nfunc=5, error_func=None, completefn=None,
                 updatefn=None, yieldtime=0.01, worktime=0.01):
        """
        """
        CalcThread.__init__(self, completefn, updatefn, yieldtime, worktime)
        self.pr = pr
        self.nfunc = nfunc
        self.error_func = error_func
        self.starttime = 0

    def compute(self):
        """
        Perform P(r) inversion
        """
        try:
            self.starttime = time.time()
            out, cov = self.pr.invert(self.nfunc)
            elapsed = time.time() - self.starttime
            self.complete(out=out, cov=cov, pr=self.pr, elapsed=elapsed)
        except KeyboardInterrupt:
            # Thread was interrupted, just proceed
            pass
        except Exception as ex:
            if self.error_func is not None:
                self.error_func("CalcPr.compute: %s" % ex)

class EstimatePr(CalcThread):
    """
    Estimate P(r)
    """

    def __init__(self, pr, nfunc=5, error_func=None, completefn=None,
                 updatefn=None, yieldtime=0.01, worktime=0.01):
        CalcThread.__init__(self, completefn, updatefn, yieldtime, worktime)
        self.pr = pr
        self.nfunc = nfunc
        self.error_func = error_func
        self.starttime = 0

    def compute(self):
        """
        Calculates the estimate
        """
        try:
            alpha, message, elapsed = self.pr.estimate_alpha(self.nfunc)
            self.isquit()
            self.complete(alpha=alpha, message=message, elapsed=elapsed)
        except KeyboardInterrupt:
            # Thread was interrupted, just proceed
            pass
        except Exception as ex:
            if self.error_func is not None:
                self.error_func("EstimatePr.compute: %s" % ex)

class EstimateNT(CalcThread):
    """
    """
    def __init__(self, pr, nfunc=5, error_func=None, completefn=None,
                 updatefn=None, yieldtime=0.01, worktime=0.01):
        CalcThread.__init__(self, completefn, updatefn, yieldtime, worktime)
        self.pr = pr
        self.nfunc = nfunc
        self.error_func = error_func
        self.starttime = 0
        self._time_for_sleep = 0
        self._sleep_delay = 1.0


    def isquit(self):
        """
        """
        CalcThread.isquit(self)
        if time.time() > self._time_for_sleep + self._sleep_delay:
            time.sleep(.2)
            self._time_for_sleep = time.time()

    def compute(self):
        """
        Calculates the estimate
        """
        try:
            t_0 = time.time()
            self._time_for_sleep = t_0
            nterms, alpha, message = self.pr.estimate_numterms(self.isquit)
            t_1 = time.time() - t_0
            self.isquit()
            self.complete(nterms=nterms, alpha=alpha, message=message, elapsed=t_1)
        except KeyboardInterrupt:
            # Thread was interrupted, just proceed
            pass
        except Exception as ex:
            if self.error_func is not None:
                self.error_func("EstimatePr2.compute: %s" % ex)
