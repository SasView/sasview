

import time
import numpy
import copy
import math
import sys
import wx

from data_util.calcthread import CalcThread
from sans.fit.AbstractFitEngine import FitData2D, FitData1D, SansAssembly


class CalcChisqr1D(CalcThread):
    """
       Compute chisqr
    """
    def __init__(self, data1d, model,
                 smearer=None,
                 qmin=None,
                 qmax=None,
                 completefn = None,
                 updatefn   = None,
                 yieldtime  = 0.01,
                 worktime   = 0.01
                 ):
        CalcThread.__init__(self,completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        
        if model ==None or data1d ==None:
            raise ValueError, "Need data and model to compute chisqr"
        
        if data1d.__class__.__name__ !="Data1D":
            msg= str(data1d.__class__.__name__)
            raise ValueError, "need Data1D to compute chisqr. Current class %s"%msg

        self.fitdata= FitData1D(x=data1d.x,y=data1d.y,dx=data1d.dx,dy=data1d.dy, smearer=smearer)
        self.fitdata.setFitRange(qmin=qmin,qmax=qmax)
        self.model = model
       
        self.starttime = 0  
        
    def isquit(self):
        """
             @raise KeyboardInterrupt: when the thread is interrupted
        """
        try:
            CalcThread.isquit(self)
        except KeyboardInterrupt:
            raise KeyboardInterrupt   
        
        
    def compute(self):
        """
            Compute the data given a model function
        """
        self.starttime = time.time()
       
        output= None
        res=[]
        try:
            res = self.fitdata.residuals(self.model.evalDistribution)
            sum=0
            for item in res:
                # Check whether we need to bail out
                self.isquit()  
                if numpy.isfinite(item):
                    sum +=item*item
            if len(res)>0:
                output = sum/ len(res)
            
            elapsed = time.time()-self.starttime
            self.complete(output= output,  elapsed=elapsed)
            
        except KeyboardInterrupt:
            # Thread was interrupted, just proceed and re-raise.
            # Real code should not print, but this is an example...
            raise
      
        
class CalcChisqr2D(CalcThread):
    """
       Compute chisqr
    """
    
    def __init__(self,data2d, model,
                 qmin,
                 qmax,
                 completefn = None,
                 updatefn   = None,
                 yieldtime  = 0.01,
                 worktime   = 0.01
                 ):
        CalcThread.__init__(self,completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        
        if model ==None or data2d ==None:
            raise ValueError, "Need data and model to compute chisqr"
        
        if data2d.__class__.__name__ !="Data2D":
            msg= str(data2d.__class__.__name__)
            raise ValueError, "need Data2D to compute chisqr. Current class %s"%msg
       
        self.fitdata = FitData2D(sans_data2d=data2d ,data=data2d.data, err_data=data2d.err_data)
        self.fitdata.setFitRange(qmin=qmin,qmax=qmax)
     
        self.model = model
      
        self.starttime = 0  
        
    def isquit(self):
        """
             @raise KeyboardInterrupt: when the thread is interrupted
        """
        try:
            CalcThread.isquit(self)
        except KeyboardInterrupt:
            raise KeyboardInterrupt   
        
        
    def compute(self):
        """
            Compute the data given a model function
        """
        self.starttime = time.time()
       
        output= None
        res=[]
        try:
            res = self.fitdata.residuals(self.model.evalDistribution)
            sum=0
            for item in res:
                # Check whether we need to bail out
                self.isquit()  
                if numpy.isfinite(item):
                    sum +=item*item
            if len(res)>0:
                output = sum/ len(res)
            
            elapsed = time.time()-self.starttime
            self.complete(output= output,  elapsed=elapsed)
            
        except KeyboardInterrupt:
            # Thread was interrupted, just proceed and re-raise.
            # Real code should not print, but this is an example...
            raise 
       