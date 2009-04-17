

import time
import sys
import wx

from calcthread import CalcThread


class SmearPlot(CalcThread):
    """
        Compute 2D model
        This calculation assumes a 2-fold symmetry of the model
        where points are computed for one half of the detector
        and I(qx, qy) = I(-qx, -qy) is assumed.
    """
    
    def __init__(self, enable_smearer=False,smearer=None,manager=None,
                 completefn = None,
                 updatefn   = None,
                 yieldtime  = 0.01,
                 worktime   = 0.01
                 ):
        CalcThread.__init__(self,completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        self.enable_smearer = enable_smearer
        self.smearer = smearer
        self.manager= manager
        self.starttime = 0  
        
    def compute(self):
        """
            Compute the data given a model function
        """
        ## set smearing value whether or not the data contain the smearing info
        self.manager.set_smearer(self.smearer, qmin= float(self.qmin_x),
                                      qmax= float(self.qmax_x)) 
        ##Calculate chi2
        self.compute_chisqr(smearer= temp_smearer)  
        elapsed = time.time()-self.starttime
       

