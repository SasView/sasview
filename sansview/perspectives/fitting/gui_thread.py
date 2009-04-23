

import time
import numpy
import copy
import math
import sys
import wx

from calcthread import CalcThread

class CalcChisqr1D(CalcThread):
    """
       Compute chisqr
    """
    def __init__(self, x, y,dy, model,
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
        self.smearer =smearer
        self.y = numpy.array(y)
        self.x = numpy.array(x)
        self.dy= copy.deepcopy(dy)
        self.model = model
        self.qmin = qmin
        self.qmax = qmax
        self.smearer = smearer
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
        x,y = [numpy.asarray(v) for v in (self.x,self.y)]
        if self.dy==None or self.dy==[]:
            self.dy= numpy.zeros(len(self.y))
        self.dy[self.dy==0]=1
        
        if self.qmin==None:
            self.qmin= min(self.x)
        
        if self.qmax==None:
            self.qmax= max(self.x)
            
        fx = numpy.zeros(len(self.x)) 
        
        output= None
        res=[]
        try: 
            
            for i_x in range(len(self.x)):
               
                # Check whether we need to bail out
                self.isquit()   
                fx[i_x]=self.model.run(i_x)
                
            if self.smearer!=None:
                fx= self.smearer(fx)
            for i_y in range(len(fx)):
                # Check whether we need to bail out
                self.isquit()   
                temp=(self.y[i_y] - fx[i_y])/self.dy[i_y]
                res.append(temp*temp)
            #sum of residuals
            sum=0
            for item in res:
                # Check whether we need to bail out
                self.isquit()  
                if numpy.isfinite(item):
                    sum +=item
            output = sum/ len(res)
            elapsed = time.time()-self.starttime
            self.complete(output= output,  elapsed=elapsed)
            
        except KeyboardInterrupt:
            # Thread was interrupted, just proceed and re-raise.
            # Real code should not print, but this is an example...
            raise
        except:
            raise
        
class CalcChisqr2D(CalcThread):
    """
       Compute chisqr
    """
    
    def __init__(self, x_bins, y_bins,data,err_data, model,
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
      
        self.y_bins = y_bins
        self.x_bins = x_bins
        self.data= data
        self.err_data= copy.deepcopy(err_data)
        self.model = model
        self.qmin = qmin
        self.qmax = qmax
      
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
        if self.err_data==None or self.err_data==[]:
            self.err_data= numpy.zeros(len(self.x_bins),len(self.y_bins))
            
        self.err_data[self.err_data==0]=1
            
        output= None
        res=[]
        try:
          
            for i in range(len(self.x_bins)):
                # Check whether we need to bail out
                self.isquit()   
                for j in range(len(self.y_bins)):
                    #Check the range containing data between self.qmin_x and self.qmax_x
                    value =  math.pow(self.x_bins[i],2)+ math.pow(self.y_bins[j],2)
                    if value >= math.pow(self.qmin,2) and value <= math.pow(self.qmax,2):
                        
                        temp = [self.x_bins[i],self.y_bins[j]]
                        error= self.err_data[j][i]
                        chisqrji = (self.data[j][i]- self.model.runXY(temp ))/error
                        #Vector containing residuals
                        res.append( math.pow(chisqrji,2) )
 
            sum=0
            for item in res:
                # Check whether we need to bail out
                self.isquit()  
                if numpy.isfinite(item):
                    sum +=item
            output = sum/ len(res)
            elapsed = time.time()-self.starttime
            self.complete(output= output,  elapsed=elapsed)
            
        except KeyboardInterrupt:
            # Thread was interrupted, just proceed and re-raise.
            # Real code should not print, but this is an example...
            raise