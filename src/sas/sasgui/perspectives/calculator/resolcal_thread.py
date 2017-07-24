"""
Thread for Resolution computation
"""
import time
from sas.sascalc.data_util.calcthread import CalcThread

class CalcRes(CalcThread):
    """
    Compute Resolution
    """
    def __init__(self,
                 id= -1,
                 func=None,
                 qx=None,
                 qy=None,
                 qx_min=None,
                 qx_max=None,
                 qy_min=None,
                 qy_max=None,
                 image=None,
                 completefn=None,
                 updatefn=None,
                 elapsed=0,
                 yieldtime=0.01,
                 worktime=0.01
                 ):
        """
        """
        CalcThread.__init__(self, completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        self.starttime = 0
        self.id = id
        self.func = func
        self.qx = qx
        self.qy = qy
        self.qx_min = qx_min
        self.qx_max = qx_max
        self.qy_min = qy_min
        self.qy_max = qy_max
        self.image = image

    def compute(self):
        """
        excuting computation
        """
        self.image = map(self.func, self.qx, self.qy,
                        self.qx_min, self.qx_max,
                        self.qy_min, self.qy_max)[0]
        elapsed = time.time() - self.starttime

        self.complete(image=self.image,
                      elapsed=elapsed)