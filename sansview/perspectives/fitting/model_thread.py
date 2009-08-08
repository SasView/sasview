import time
from data_util.calcthread import CalcThread
import sys
import numpy,math

class Calc2D(CalcThread):
    """
        Compute 2D model
        This calculation assumes a 2-fold symmetry of the model
        where points are computed for one half of the detector
        and I(qx, qy) = I(-qx, -qy) is assumed.
    """
    
    def __init__(self, x, y, data,model,qmin, qmax,qstep,
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
        # Reshape dimensions of x and y to call evalDistribution
        self.x_array = numpy.reshape(x,[1,len(x)])
        self.y_array = numpy.reshape(y,[len(y),1])
        # Numpy array of dimensions 1 used for model.run method
        self.x= numpy.array(x)
        self.y= numpy.array(y)
        self.data= data
        # the model on to calculate
        self.model = model
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
        # Define matrix where data will be plotted        
        radius= numpy.sqrt(self.x_array**2 + self.y_array**2)
        index_data= (self.qmin<= radius)
        index_model = (self.qmin <= radius)&(radius<= self.qmax)
       
        ## receive only list of 2 numpy array 
        ## One must reshape to vertical and the other to horizontal
        value = self.model.evalDistribution([self.y_array,self.x_array] )
        ## for data ignore the qmax 
        if self.data == None:
            # Only qmin value will be consider for the detector
            output = value *index_data  
        else:
            # The user can define qmin and qmax for the detector
            output = value*index_model
        
        elapsed = time.time()-self.starttime
        self.complete( image = output,
                       data = self.data , 
                       model = self.model,
                       elapsed = elapsed,
                       qmin = self.qmin,
                       qmax =self.qmax,
                       qstep = self.qstep )
        
    def compute_point(self):
        """
            Compute the data given a model function. Loop through each point
            of x and y to compute the model
            @return output : is a matrix of size x*y
        """
        output = numpy.zeros((len(self.x),len(self.y)))
       
        for i_x in range(len(self.x)):
            # Check whether we need to bail out
            self.update(output=output )
            self.isquit()
       
            for i_y in range(int(len(self.y))):
                radius = math.sqrt(self.x[i_x]*self.x[i_x]+self.y[i_y]*self.y[i_y])
                ## for data ignore the qmax 
                if self.data == None:
                    if  self.qmin <= radius :
                        value = self.model.runXY( [self.x[i_x], self.y[i_y]] )
                        output[i_y][i_x] =value   
                    else:
                        output[i_y][i_x] =0   
                else:  
                    if  self.qmin <= radius and radius<= self.qmax:
                        value = self.model.runXY( [self.x[i_x], self.y[i_y]] )
                        output[i_y][i_x] =value   
                    else:
                        output[i_y][i_x] =0  
        return output 
     
    

class Calc1D(CalcThread):
    """Compute 1D data"""
    
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
        
        index= (self.qmin <= self.x)& (self.x <= self.qmax)
        output = self.model.evalDistribution(self.x[index])
 
        ##smearer the ouput of the plot    
        if self.smearer!=None:
            output = self.smearer(output) #Todo: Why always output[0]=0???
        
        ######Temp. FIX for Qrange w/ smear. #ToDo: Should not pass all the data to 'run' or 'smear'...
        new_index = (self.qmin > self.x) |(self.x > self.qmax)
        output[new_index] = None
                
        elapsed = time.time()-self.starttime
        
        self.complete(x= self.x, y= output, 
                      elapsed=elapsed, model= self.model, data=self.data)
        
    def compute_point(self):
        """
            Compute the data given a model function. Loop through each point
            of x  compute the model
            @return output : is a numpy vector of size x
        """  
        output = numpy.zeros(len(self.x))      
        # Loop through each q of data.x
        for i_x in range(len(self.x)):
            self.update(x= self.x, output=output )
            # Check whether we need to bail out
            self.isquit()
            if self.qmin <= self.x[i_x] and self.x[i_x] <= self.qmax:
                value = self.model.run(self.x[i_x])
                output[i_x] = value
                
        return output
                
                
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
    
    
        calc_thread_2D = Calc2D(x, y, None, model.clone(),-qmax, qmax,qstep,
                                        completefn=self.complete,
                                        updatefn=self.update ,
                                        yieldtime=0.0)
     
        calc_thread_2D.queue()
        calc_thread_2D.ready(2.5)
        
        while not self.done:
            time.sleep(1)

    def update(self,output):
        print "update"

    def complete(self, image, data, model, elapsed, qmin, qmax, qstep ):
        print "complete"
        self.done = True

if __name__ == "__main__":
    CalcCommandline()
   
