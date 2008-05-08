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
            
            print "Alpha  Oscill"
            
            self.starttime = time.time()
            # If the current alpha is zero, try
            # another value
            if self.pr.alpha<=0:
                self.pr.alpha = 0.0001
                 
            out, cov = self.pr.lstsq(self.nfunc)
            elapsed = time.time()-self.starttime
            

            # Take the default and try to find 
            # a better value
            best_alpha = self.pr.alpha
            best_osc   = self.pr.oscillations(out) 
            
            print best_alpha, best_osc
            
            alpha = self.pr.suggested_alpha
            print "initial:", alpha

            # Look at smaller values
            for i in range(5):
                self.pr.alpha = (0.1)**(i)*alpha
                out, cov = self.pr.lstsq(self.nfunc)
                osc = self.pr.oscillations(out) 
                print self.pr.alpha, osc
                if  osc < best_osc:
                    best_osc = osc
                    best_alpha = alpha
            
            ## Look at larger values
            #for i in range(4):
            #    self.pr.alpha = (10.0)**(i+1)*alpha
            #    out, cov = self.pr.lstsq(self.nfunc)
            #    osc = self.pr.oscillations(out) 
            #    print self.pr.alpha, osc
            #    if  osc < best_osc:
            #        best_osc = osc
            #        best_alpha = alpha
            
            
            self.complete(alpha=best_alpha, elapsed=elapsed)
            
            
            
            
        except:
            if not self.error_func==None:
                printEVT("EstimatePr.compute: %s" % sys.exc_value)

    