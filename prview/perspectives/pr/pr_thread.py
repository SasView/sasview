import sys, time
from calcthread import CalcThread
from sans.pr.invertor import Invertor
import numpy
from config import printEVT

class CalcPr(CalcThread):
    """
        Compute 2D model
        This calculation assumes a 2-fold symmetry of the model
        where points are computed for one half of the detector
        and I(qx, qy) = I(-qx, -qy) is assumed.
    """
    
    def __init__(self, pr, nfunc=5, error_func=None,
                 completefn = None,
                 updatefn   = None,
                 yieldtime  = 0.01,
                 worktime   = 0.01
                 ):
        CalcThread.__init__(self,completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        self.pr = pr
        self.nfunc = nfunc
        self.error_func = error_func
        self.starttime = 0
        
    def isquit(self):
        try:
            CalcThread.isquit(self)
        except KeyboardInterrupt:
            printEVT("P(r) calc interrupted")
            raise KeyboardInterrupt
        
    def compute(self):
        import time
        try:
            self.starttime = time.time()
            #out, cov = self.pr.invert(self.nfunc)
            out, cov = self.pr.lstsq(self.nfunc)
            elapsed = time.time()-self.starttime
            self.complete(out=out, cov=cov, pr=self.pr, elapsed=elapsed)
        except:
            if not self.error_func==None:
                self.error_func("CalcPr.compute: %s" % sys.exc_value)

class EstimatePr(CalcThread):
    """
        Compute 2D model
        This calculation assumes a 2-fold symmetry of the model
        where points are computed for one half of the detector
        and I(qx, qy) = I(-qx, -qy) is assumed.
    """
    
    def __init__(self, pr, nfunc=5, error_func=None,
                 completefn = None,
                 updatefn   = None,
                 yieldtime  = 0.01,
                 worktime   = 0.01
                 ):
        CalcThread.__init__(self,completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        self.pr = pr
        self.nfunc = nfunc
        self.error_func = error_func
        self.starttime = 0
        
    def isquit(self):
        try:
            CalcThread.isquit(self)
        except KeyboardInterrupt:
            printEVT("P(r) calc interrupted")
            raise KeyboardInterrupt    
        
    def compute(self):
        import time
        try:            
            self.starttime = time.time()
            # If the current alpha is zero, try
            # another value
            if self.pr.alpha<=0:
                self.pr.alpha = 0.0001
                 
            # Perform inversion to find the largest alpha
            out, cov = self.pr.lstsq(self.nfunc)
            elapsed = time.time()-self.starttime
            initial_alpha = self.pr.alpha
            initial_peaks = self.pr.get_peaks(out)

            # Try the inversion with the estimated alpha
            self.pr.alpha = self.pr.suggested_alpha
            out, cov = self.pr.lstsq(self.nfunc)

            npeaks = self.pr.get_peaks(out)
            # if more than one peak to start with
            # just return the estimate
            if npeaks>1:
                message = "Your P(r) is not smooth, please check your inversion parameters"
                self.complete(alpha=self.pr.suggested_alpha, message=message, elapsed=elapsed)
            else:
                
                # Look at smaller values
                # We assume that for the suggested alpha, we have 1 peak
                # if not, send a message to change parameters
                alpha = self.pr.suggested_alpha
                best_alpha = self.pr.suggested_alpha
                found = False
                for i in range(10):
                    self.pr.alpha = (0.33)**(i+1)*alpha
                    out, cov = self.pr.lstsq(self.nfunc)
                    #osc = self.pr.oscillations(out) 
                    #print self.pr.alpha, osc
                    
                    peaks = self.pr.get_peaks(out)
                    print self.pr.alpha, peaks
                    if peaks>1:
                        found = True
                        break
                    best_alpha = self.pr.alpha
                    
                # If we didn't find a turning point for alpha and
                # the initial alpha already had only one peak,
                # just return that
                if not found and initial_peaks==1 and initial_alpha<best_alpha:
                    best_alpha = initial_alpha
                    
                # Check whether the size makes sense
                message=None
                
                if not found:
                    message = "None"
                elif best_alpha>=0.5*self.pr.suggested_alpha:
                    # best alpha is too big, return a 
                    # reasonable value
                    message  = "The estimated alpha for your system is too large. "
                    message += "Try increasing your maximum distance."
                
                self.complete(alpha=best_alpha, message=None, elapsed=elapsed)

        except:
            if not self.error_func==None:
                printEVT("EstimatePr.compute: %s" % sys.exc_value)

    