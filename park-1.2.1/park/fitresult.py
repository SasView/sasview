import sys, math, time
import numpy

from formatnum import format_uncertainty

class FitHandler(object):
    """
    Abstract interface for fit thread handler.

    The methods in this class are called by the optimizer as the fit
    progresses.

    Note that it is up to the optimizer to call the fit handler correctly,
    reporting all status changes and maintaining the 'done' flag.
    """
    done = False
    """True when the fit job is complete"""
    result = None
    """The current best result of the fit"""

    def improvement(self):
        """
        Called when a result is observed which is better than previous
        results from the fit.

        result is a FitResult object, with parameters, #calls and fitness.
        """
    def error(self, msg):
        """
        Model had an error; print traceback
        """
    def progress(self, current, expected):
        """
        Called each cycle of the fit, reporting the current and the
        expected amount of work.   The meaning of these values is
        optimizer dependent, but they can be converted into a percent
        complete using (100*current)//expected.

        Progress is updated each iteration of the fit, whatever that
        means for the particular optimization algorithm.  It is called
        after any calls to improvement for the iteration so that the
        update handler can control I/O bandwidth by suppressing
        intermediate improvements until the fit is complete.
        """
    def finalize(self):
        """
        Fit is complete; best results are reported
        """
    def abort(self):
        """
        Fit was aborted.
        """

class ConsoleUpdate(FitHandler):
    """
    Print progress to the console.
    """
    isbetter = False
    """Record whether results improved since last update"""
    progress_delta =  60
    """Number of seconds between progress updates"""
    improvement_delta = 5
    """Number of seconds between improvement updates"""
    def __init__(self,quiet=False,progress_delta=60,improvement_delta=5):
        """
        If quiet is true, only print out final summary, not progress and
        improvements.
        """
        #import traceback; traceback.print_stack()
        self.progress_time = time.time()
        self.progress_percent = 0
        self.improvement_time = self.progress_time
        self.isbetter = False
        self.quiet = quiet
        self.progress_delta = progress_delta
        self.improvement_delta = improvement_delta

    def progress(self, k, n):
        """
        Report on progress.
        """
        if self.quiet: return
        t = time.time()
        p = int((100*k)//n)

        # Show improvements if there are any
        dt = t - self.improvement_time
        if self.isbetter and dt > self.improvement_delta:
            self.result.print_summary()
            self.isbetter = False
            self.improvement_time = t

        # Update percent complete
        dp = p-self.progress_percent
        if dp < 1: return
        dt = t - self.progress_time
        if dt > self.progress_delta:
            if 1 <= dp <= 2:
                print "%d%% complete"%p
                self.progress_percent = p
                self.progress_time = t
            elif 2 < dp <= 5:
                if p//5 != self.progress_percent//5:
                    print "%d%% complete"%(5*(p//5))
                    self.progress_percent = p
                    self.progress_time = t
            else:
                if p//10 != self.progress_percent//10:
                    print "%d%% complete"%(10*(p//10))
                    self.progress_percent = p
                    self.progress_time = t

    def improvement(self):
        """
        Called when a result is observed which is better than previous
        results from the fit.
        """
        self.isbetter = True

    def error(self, msg):
        """
        Model had an error; print traceback
        """
        if self.isbetter:
            self.result.print_summary()
        print msg

    def finalize(self):
        if self.isbetter:
            self.result.print_summary()
        print "Total function calls:",self.result.calls

    def abort(self):
        if self.isbetter:
            self.result.print_summary()


class FitParameter(object):
    """
    Fit result for an individual parameter.
    """
    def __init__(self, name, range, value):
        self.name = name
        self.range = range
        self.value = value
        self.stderr = None
    def summarize(self):
        """
        Return parameter range string.

        E.g.,  "       Gold .....|.... 5.2043 in [2,7]"
        """
        bar = ['.']*10
        lo,hi = self.range
        if numpy.isfinite(lo)and numpy.isfinite(hi):
            portion = (self.value-lo)/(hi-lo)
            if portion < 0: portion = 0.
            elif portion >= 1: portion = 0.99999999
            barpos = int(math.floor(portion*len(bar)))
            bar[barpos] = '|'
        bar = "".join(bar)
        lostr = "[%g"%lo if numpy.isfinite(lo) else "(-inf"
        histr = "%g]"%hi if numpy.isfinite(hi) else "inf)"
        valstr = format_uncertainty(self.value, self.stderr)
        return "%25s %s %s in %s,%s"  % (self.name,bar,valstr,lostr,histr)
    def __repr__(self):
        return "FitParameter('%s')"%self.name

class FitResult(object):
    """
    Container for reporting fit results.
    """
    def __init__(self, parameters, calls, fitness):
        self.parameters = parameters
        """Fit parameter list, each with name, range and value attributes."""
        self.calls = calls
        """Number of function calls"""
        self.fitness = fitness
        """Value of the goodness of fit metric"""
        self.pvec = numpy.array([p.value for p in self.parameters])
        """Parameter vector"""
        self.stderr = None
        """Parameter uncertainties"""
        self.cov = None
        """Covariance matrix"""

    def update(self, pvec, fitness, calls):
        self.calls = calls
        self.fitness = fitness
        self.pvec = pvec.copy()
        for i,p in enumerate(self.parameters):
            p.value = pvec[i]

    def calc_cov(self, fn):
        """
        Return the covariance matrix inv(J'J) at point p.
        """
        if hasattr(fn, 'jacobian'):
            # Find cov of f at p
            #     cov(f,p) = inv(J'J)
            # Use SVD
            #     J = U S V'
            #     J'J = (U S V')' (U S V')
            #         = V S' U' U S V'
            #         = V S S V'
            #     inv(J'J) = inv(V S S V')
            #              = inv(V') inv(S S) inv(V)
            #              = V inv (S S) V'
            J = fn.jacobian(self.pvec)
            u,s,vh = numpy.linalg.svd(J,0)
            JTJinv = numpy.dot(vh.T.conj()/s**2,vh)
            self.set_cov(JTJinv)

    def set_cov(self, cov):
        """
        Return the covariance matrix inv(J'J) at point p.
        """
        self.cov = cov
        if cov is not None:
            self.stderr = numpy.sqrt(numpy.diag(self.cov))
            # Set the uncertainties on the individual parameters
            for k,p in enumerate(self.parameters):
                p.stderr = self.stderr[k]
        else:
            self.stderr = None
            # Reset the uncertainties on the individual parameters
            for k,p in enumerate(self.parameters):
                p.stderr = None

    def __str__(self):
        #import traceback; traceback.print_stack()
        if self.parameters == None: return "No results"
        L = ["P%-3d %s"%(n+1,p.summarize()) for n,p in enumerate(self.parameters)]
        L.append("=== goodness of fit: %g"%(self.fitness))
        return "\n".join(L)

    def print_summary(self, fid=sys.stdout):
        print >>fid, self

