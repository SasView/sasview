import time
from calcthread import CalcThread
import sys
import numpy,math

class Calc2D_all(CalcThread):
    """
        Compute 2D model
        This calculation assumes a 2-fold symmetry of the model
        where points are computed for one half of the detector
        and I(qx, qy) = I(-qx, -qy) is assumed.
    """
    
    def __init__(self, x, y, model,
                 completefn = None,
                 updatefn   = None,
                 yieldtime  = 0.01,
                 worktime   = 0.01
                 ):
        CalcThread.__init__(self,completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        
        self.x = x
        self.y = y
        self.model = model
        self.starttime = 0
        
    def compute(self):
        x = self.x
        y = self.y
        output = numpy.zeros((len(x),len(y)))
            
        self.starttime = time.time()
        lx = len(self.x)
        
        #for i_x in range(int(len(self.x)/2)):
        for i_x in range(len(self.x)):
            if i_x%2==1:
                continue
            
            # Check whether we need to bail out
            self.update(output=output)
            self.isquit()
                
            for i_y in range(len(self.y)):
                value = self.model.runXY([self.x[i_x], self.y[i_y]])
                output[i_y][i_x] = value
                #output[lx-i_y-1][lx-i_x-1] = value
                
        if lx%2==1:
            i_x = int(len(self.x)/2)
            for i_y in range(len(self.y)):
                value = self.model.runXY([self.x[i_x], self.y[i_y]])
                output[i_y][i_x] = value
                
        #for i_x in range(int(len(self.x)/2)):
        for i_x in range(len(self.x)):
            if not i_x%2==1:
                continue

            # Check whether we need to bail out
            self.update(output=output)
            self.isquit()
            
            for i_y in range(len(self.y)):
                value = self.model.runXY([self.x[i_x], self.y[i_y]])
                output[i_y][i_x] = value
                #output[lx-i_y-1][lx-i_x-1] = value
            
        elapsed = time.time()-self.starttime
        self.complete(output=output, elapsed=elapsed)


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
        self.x = x
        self.y = y
        self.data= data
        ## the model on to calculate
        self.model = model
        self.starttime = 0  
        
    def compute(self):
        """
            Compute the data given a model function
        """
        x = self.x
        y = self.y
        output = numpy.zeros((len(x),len(y)))
        if self.qmin==None:
            self.qmin = 0
        if self.qmax== None:
            if self.data ==None:
                return
            newx= math.pow(max(math.fabs(self.data.xmax),math.fabs(self.data.xmin)),2)
            newy= math.pow(max(math.fabs(self.data.ymax),math.fabs(self.data.ymin)),2)
            self.qmax=math.sqrt( newx + newy )
        
        self.starttime = time.time()
        lx = len(self.x)
        for i_x in range(len(self.x)):
            # Check whether we need to bail out
            self.update(output=output )
            self.isquit()
       
            for i_y in range(int(len(self.y))):
                radius = math.sqrt(self.x[i_x]*self.x[i_x]+self.y[i_y]*self.y[i_y])
                
                if  self.qmin <= radius and radius<= self.qmax:
                    value = self.model.runXY( [self.x[i_x], self.y[i_y]] )
                    output[i_y][i_x] =value   
                else:
                    output[i_y][i_x] =0   
            
        elapsed = time.time()-self.starttime
        self.complete( image = output,
                       data = self.data , 
                       model = self.model,
                       elapsed = elapsed,
                       qmin = self.qmin,
                       qmax =self.qmax,
                       qstep = self.qstep )


class Calc2D_4fold(CalcThread):
    """
        Compute 2D model
        This calculation assumes a 4-fold symmetry of the model.
        Really is the same calculation time since we have to 
        calculate points for 0<phi<pi anyway.
    """
    
    def __init__(self, x, y, model,
                 completefn = None,
                 updatefn   = None,
                 yieldtime  = 0.01,
                 worktime   = 0.01
                 ):
        CalcThread.__init__(self,completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        self.x = x
        self.y = y
        self.model = model
        self.starttime = 0
        
    def compute(self):
        x = self.x
        y = self.y
        output = numpy.zeros((len(x),len(y)))
            
        self.starttime = time.time()
        lx = len(self.x)
        
        for i_x in range(int(len(self.x)/2)):
            if i_x%2==1:
                continue
            
            # Check whether we need to bail out
            self.update(output=output)
            self.isquit()
                
            for i_y in range(int(len(self.y)/2)):
                value1 = self.model.runXY([self.x[i_x], self.y[i_y]])
                value2 = self.model.runXY([self.x[i_x], self.y[lx-i_y-1]])
                output[i_y][i_x] = value1 + value2
                output[lx-i_y-1][lx-i_x-1] = value1 + value2
                output[lx-i_y-1][i_x] = value1 + value2
                output[i_y][lx-i_x-1] = value1 + value2
                
        if lx%2==1:
            i_x = int(len(self.x)/2)
            for i_y in range(int(len(self.y)/2)):
                value1 = self.model.runXY([self.x[i_x], self.y[i_y]])
                value2 = self.model.runXY([self.x[i_x], self.y[lx-i_y-1]])
                output[i_y][i_x] = value1 + value2
                output[lx-i_y-1][lx-i_x-1] = value1 + value2
                output[lx-i_y-1][i_x] = value1 + value2
                output[i_y][lx-i_x-1] = value1 + value2
                
        for i_x in range(int(len(self.x)/2)):
            if not i_x%2==1:
                continue

            # Check whether we need to bail out
            self.update(output=output)
            self.isquit()
            
            for i_y in range(int(len(self.y)/2)):
                value1 = self.model.runXY([self.x[i_x], self.y[i_y]])
                value2 = self.model.runXY([self.x[i_x], self.y[lx-i_y-1]])
                output[i_y][i_x] = value1 + value2
                output[lx-i_y-1][lx-i_x-1] = value1 + value2
                output[lx-i_y-1][i_x] = value1 + value2
                output[i_y][lx-i_x-1] = value1 + value2
            
        elapsed = time.time()-self.starttime
        self.complete(output=output, elapsed=elapsed)



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
        self.x = x
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
        output = numpy.zeros(len(self.x))
       
        self.starttime = time.time()
        
        for i_x in range(len(self.x)):
            self.update(x= self.x, output=output )
            # Check whether we need to bail out
            self.isquit()
            if self.qmin <= self.x[i_x] and self.x[i_x] <= self.qmax:
                value = self.model.run(self.x[i_x])
                output[i_x] = value
                
        if self.smearer!=None:
            output = self.smearer(output)
            
                      
        elapsed = time.time()-self.starttime
        self.complete(x= self.x, y= output, 
                      elapsed=elapsed, model= self.model, data=self.data)
        
        

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
   
