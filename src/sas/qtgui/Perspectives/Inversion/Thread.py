import sys
import time

from sas.sascalc.data_util.calcthread import CalcThread
from sas.sascalc.pr.invertor import Invertor


class CalcPr(CalcThread):
    """
    Compute P(r)
    """

    def __init__(self, pr, nfunc=5, tab_id=None, error_func=None, completefn=None,
                 updatefn=None, yieldtime=0.01, worktime=0.01):
        """
        """
        CalcThread.__init__(self, completefn, updatefn, yieldtime, worktime)
        self.pr = pr
        self.tab_id = tab_id
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
        except Exception:
            if self.error_func is not None:
                self.error_func("CalcPr.compute: %s" % sys.exc_info()[1])

class CalcBatchPr(CalcThread):

    # A lot of these aren't type hinted but that can be future work as I'm trying to closely follow the pre-existing
    # structure, and I don't want to mess with anything.
    def __init__(self, prs: list[Invertor], nfuncs=None, tab_id=None, error_func=None, completefn=None,
                 updatefn=None, yieldtime=0.01, worktime=0.01):
        CalcThread.__init__(self, completefn, updatefn, yieldtime, worktime)
        self.prs = prs
        self.nfuncs = nfuncs
        self.error_func = error_func
        self.starttime = 0

    def compute(self):
        try:
            self.starttime = time.time()
            outputs = []
            for invertor, nfunc in zip(self.prs, self.nfuncs):
                outputs.append(invertor.invert(nfunc))
                self.isquit()
            elapsed = time.time() - self.starttime
            self.complete(totalElapsed=elapsed)
        except KeyboardInterrupt:
            pass
        except Exception:
            if self.error_func is not None:
                self.error_func("CalcBatchPr.compute: %s" % sys.exc_info()[1])


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
        except Exception:
            if self.error_func is not None:
                self.error_func("EstimatePr.compute: %s" % sys.exc_info()[1])


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
        except Exception:
            if self.error_func is not None:
                self.error_func("EstimatePr2.compute: %s" % sys.exc_info()[1])
