import sys
import time
from collections.abc import Callable

from sas.sascalc.data_util.calcthread import CalcThread
from sas.sascalc.pr.invertor import Invertor


class CalcPr(CalcThread):
    """Compute P(r) inversion in a background thread."""

    def __init__(
        self,
        pr: Invertor,
        nfunc: int = 5,
        tab_id: int | None = None,
        error_func: Callable | None = None,
        completefn: Callable | None = None,
        updatefn: Callable | None = None,
        yieldtime: float = 0.01,
        worktime: float = 0.01,
    ):
        CalcThread.__init__(self, completefn, updatefn, yieldtime, worktime)
        self.pr: Invertor = pr
        self.tab_id: int | None = tab_id
        self.nfunc: int = nfunc
        self.error_func: Callable | None = error_func
        self.starttime: float = 0

    def compute(self) -> None:
        """Perform P(r) inversion."""
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
    """Compute P(r) inversion for a batch of data sets in a background thread."""

    def __init__(
        self,
        prs: list[Invertor],
        nfuncs: list[int] | None = None,
        tab_id: int | None = None,
        error_func: Callable | None = None,
        completefn: Callable | None = None,
        updatefn: Callable | None = None,
        yieldtime: float = 0.01,
        worktime: float = 0.01,
    ):
        CalcThread.__init__(self, completefn, updatefn, yieldtime, worktime)
        self.prs: list[Invertor] = prs
        self.nfuncs: list[int] | None = nfuncs
        self.error_func: Callable | None = error_func
        self.starttime: float = 0

    def compute(self) -> None:
        """Perform P(r) inversion for each invertor in the batch."""
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
    """Estimate the regularisation parameter alpha for P(r) in a background thread."""

    def __init__(
        self,
        pr: Invertor,
        nfunc: int = 5,
        error_func: Callable | None = None,
        completefn: Callable | None = None,
        updatefn: Callable | None = None,
        yieldtime: float = 0.01,
        worktime: float = 0.01,
    ):
        CalcThread.__init__(self, completefn, updatefn, yieldtime, worktime)
        self.pr: Invertor = pr
        self.nfunc: int = nfunc
        self.error_func: Callable | None = error_func
        self.starttime: float = 0

    def compute(self) -> None:
        """Calculate the alpha estimate."""
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
    """Estimate the number of terms for P(r) inversion in a background thread."""

    def __init__(
        self,
        pr: Invertor,
        nfunc: int = 5,
        error_func: Callable | None = None,
        completefn: Callable | None = None,
        updatefn: Callable | None = None,
        yieldtime: float = 0.01,
        worktime: float = 0.01,
    ):
        CalcThread.__init__(self, completefn, updatefn, yieldtime, worktime)
        self.pr: Invertor = pr
        self.nfunc: int = nfunc
        self.error_func: Callable | None = error_func
        self.starttime: float = 0
        self._time_for_sleep: float = 0
        self._sleep_delay: float = 1.0

    def isquit(self) -> None:
        """Check for quit signal and throttle with a short sleep if needed."""
        CalcThread.isquit(self)
        if time.time() > self._time_for_sleep + self._sleep_delay:
            time.sleep(0.2)
            self._time_for_sleep = time.time()

    def compute(self) -> None:
        """Calculate the estimated number of terms and optimal alpha."""
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
