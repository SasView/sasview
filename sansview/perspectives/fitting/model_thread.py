

import time
from data_util.calcthread import CalcThread
import sys
import numpy,math
from DataLoader.smearing_2d import Smearer2D

class Calc2D(CalcThread):
    """
    Compute 2D model
    This calculation assumes a 2-fold symmetry of the model
    where points are computed for one half of the detector
    and I(qx, qy) = I(-qx, -qy) is assumed.
    """
    def __init__(self, x, y, data,model,smearer,qmin, qmax,qstep,
                 completefn = None,
                 updatefn   = None,
                 yieldtime  = 0.01,
                 worktime   = 0.01
                 ):
        CalcThread.__init__(self,completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        self.qmin= qmin
        self.qmax= qmax
        self.qstep= qstep

        self.x = x
        self.y = y
        self.data= data
        # the model on to calculate
        self.model = model
        self.smearer = smearer#(data=self.data,model=self.model)
        self.starttime = 0  
        
    def compute(self):
        """
        Compute the data given a model function
        """
        self.starttime = time.time()
        # Determine appropriate q range
        if self.qmin==None:
            self.qmin = 0
        if self.qmax== None:
            if self.data !=None:
                newx= math.pow(max(math.fabs(self.data.xmax),math.fabs(self.data.xmin)),2)
                newy= math.pow(max(math.fabs(self.data.ymax),math.fabs(self.data.ymin)),2)
                self.qmax=math.sqrt( newx + newy )
        
        if self.data != None:
            self.I_data = self.data.data
            self.qx_data = self.data.qx_data
            self.qy_data = self.data.qy_data
            self.dqx_data = self.data.dqx_data
            self.dqy_data = self.data.dqy_data
            self.mask    = self.data.mask
        else:          
            xbin =  numpy.linspace(start= -1*self.qmax,
                                   stop= self.qmax,
                                   num= self.qstep,
                                   endpoint=True )  
            ybin = numpy.linspace(start= -1*self.qmax,
                                   stop= self.qmax,
                                   num= self.qstep,
                                   endpoint=True )            
            
            new_xbin = numpy.tile(xbin, (len(ybin),1))
            new_ybin = numpy.tile(ybin, (len(xbin),1))
            new_ybin = new_ybin.swapaxes(0,1)
            new_xbin = new_xbin.flatten()
            new_ybin = new_ybin.flatten()
            self.qy_data = new_ybin
            self.qx_data = new_xbin
            # fake data
            self.I_data = numpy.ones(len(self.qx_data))
           
            self.mask = numpy.ones(len(self.qx_data),dtype=bool)
            
        # Define matrix where data will be plotted    
        radius= numpy.sqrt( self.qx_data*self.qx_data + self.qy_data*self.qy_data )
        index_data= (self.qmin<= radius)&(self.mask)

        # For theory, qmax is based on 1d qmax 
        # so that must be mulitified by sqrt(2) to get actual max for 2d
        index_model = ((self.qmin <= radius)&(radius<= self.qmax))
        index_model = (index_model)&(self.mask)
        index_model = (index_model)&(numpy.isfinite(self.I_data))
        if self.data ==None:
            # Only qmin value will be consider for the detector
            index_model = index_data  

        if self.smearer != None:
            # Set smearer w/ data, model and index.
            fn = self.smearer
            fn.set_model(self.model)
            fn.set_index(index_model)
            # Get necessary data from self.data and set the data for smearing
            fn.get_data()
            # Calculate smeared Intensity (by Gaussian averaging): DataLoader/smearing2d/Smearer2D()
            value = fn.get_value()

        else:    
            # calculation w/o smearing
            value =  self.model.evalDistribution([self.qx_data[index_model],self.qy_data[index_model]])

        output = numpy.zeros(len(self.qx_data))
        
        # output default is None
        # This method is to distinguish between masked point(nan) and data point = 0.
        output = output/output
        # set value for self.mask==True, else still None to Plottools
        output[index_model] = value 

        elapsed = time.time()-self.starttime
        self.complete( image = output,
                       data = self.data , 
                       model = self.model,
                       elapsed = elapsed,
                       index = index_model,
                       qmin = self.qmin,
                       qmax = self.qmax,
                       qstep = self.qstep )
        

class Calc1D(CalcThread):
    """
    Compute 1D data
    """
    def __init__(self, x, model,
                 data=None,
                 qmin=None,
                 qmax=None,
                 smearer=None,
                 completefn = None,
                 updatefn   = None,
                 yieldtime  = 0.01,
                 worktime   = 0.01
                 ):
        """
        """
        CalcThread.__init__(self,completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        self.x = numpy.array(x)
        self.data= data
        self.qmin= qmin
        self.qmax= qmax
        self.model = model
        self.smearer= smearer
        self.starttime = 0
        
    def compute(self):
        """
        Compute model 1d value given qmin , qmax , x value 
        """
        self.starttime = time.time()
        output = numpy.zeros((len(self.x)))
        index= (self.qmin <= self.x)& (self.x <= self.qmax)
     
        ##smearer the ouput of the plot    
        if self.smearer!=None:
            first_bin, last_bin = self.smearer.get_bin_range(self.qmin, self.qmax)
            output[first_bin:last_bin] = self.model.evalDistribution(self.x[first_bin:last_bin])
            output = self.smearer(output, first_bin, last_bin) 
        else:
            output[index] = self.model.evalDistribution(self.x[index])
         
        elapsed = time.time() - self.starttime
       
        self.complete(x=self.x[index], y=output[index], 
                      elapsed=elapsed,index=index, model=self.model,
                                        data=self.data)
        
    def results(self):
        """
        Send resuts of the computation
        """
        return [self.out, self.index]

"""
Example: ::
                     
    class CalcCommandline:
        def __init__(self, n=20000):
            #print thread.get_ident()
            from sans.models.CylinderModel import CylinderModel
            
            model = CylinderModel()
            
             
            print model.runXY([0.01, 0.02])
            
            qmax = 0.01
            qstep = 0.0001
            self.done = False
            
            x = numpy.arange(-qmax, qmax+qstep*0.01, qstep)
            y = numpy.arange(-qmax, qmax+qstep*0.01, qstep)
        
        
            calc_thread_2D = Calc2D(x, y, None, model.clone(),None,
                                    -qmax, qmax,qstep,
                                            completefn=self.complete,
                                            updatefn=self.update ,
                                            yieldtime=0.0)
         
            calc_thread_2D.queue()
            calc_thread_2D.ready(2.5)
            
            while not self.done:
                time.sleep(1)
    
        def update(self,output):
            print "update"
    
        def complete(self, image, data, model, elapsed, qmin, qmax,index, qstep ):
            print "complete"
            self.done = True
    
    if __name__ == "__main__":
        CalcCommandline()
"""   
