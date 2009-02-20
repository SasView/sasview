import time
from calcthread import CalcThread
from sans.guicomm.events import NewPlotEvent, StatusEvent  
import sys
import wx
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
        
    def isquit(self):
        try:
            CalcThread.isquit(self)
        except KeyboardInterrupt:
            #printEVT("Calc %s interrupted" % self.model.name)
            wx.PostEvent(self.parent, StatusEvent(status=\
                       "Calc %s interrupted" % self.model.name))
            raise KeyboardInterrupt
        
    def compute(self):
        import numpy
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
    
    def __init__(self,parent, x, y, model,qmin, qmax,qstep,
                 completefn = None,
                 updatefn   = None,
                 yieldtime  = 0.01,
                 worktime   = 0.01
                 ):
        CalcThread.__init__(self,completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        self.parent =parent
        self.qmin= qmin
        self.qmax=qmax
        self.qstep= qstep
        self.x = x
        self.y = y
        self.model = model
        self.starttime = 0
        wx.PostEvent(self.parent, StatusEvent(status=\
                    "Start Drawing model  ",curr_thread=self,type="start"))
        
    def isquit(self):
        try:
            CalcThread.isquit(self)
        except KeyboardInterrupt:
            #printEVT("Calc %s interrupted" % self.model.name)
            wx.PostEvent(self.parent, StatusEvent(status=\
                       "Calc %s interrupted" % self.model.name))
           
            raise KeyboardInterrupt
        
    def update(self, output=None):
        
        wx.PostEvent(self.parent, StatusEvent(status="Plot \
        #updating ... ",curr_thread=self,type="update"))
        
        
    def compute(self):
        import numpy
        x = self.x
        y = self.y
        output = numpy.zeros((len(x),len(y)))
      
        center_x=0
        center_y=0
        
        self.starttime = time.time()
        
        
        lx = len(self.x)
        wx.PostEvent(self.parent, StatusEvent(status=\
                       "Computing ",curr_thread=self,type="progress"))
        for i_x in range(len(self.x)):
            # Check whether we need to bail out
            self.update(output=output )
            self.isquit()
            
            for i_y in range(int(len(self.y))):
                try:
                    if (self.x[i_x]*self.x[i_x]+self.y[i_y]*self.y[i_y]) \
                        < self.qmin * self.qmin:
                        
                        output[i_x] [i_y]=0   
                    else:
                        value = self.model.runXY([self.x[i_x]-center_x, self.y[i_y]-center_y])
                        output[i_x] [i_y]=value   
                except:
                     wx.PostEvent(self.parent, StatusEvent(status=\
                       "Error computing %s at [%g,%g]" %(self.model.name, self.x[i_x],self.y[i_y])))
           
        elapsed = time.time()-self.starttime
        self.complete(
                      output=output, elapsed=elapsed,model= self.model,
                      qmin= self.qmin,
                      qmax=self.qmax,
                      qstep=self.qstep)

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
        
    def isquit(self):
        try:
            CalcThread.isquit(self)
        except KeyboardInterrupt:
            #printEVT("Calc %s interrupted" % self.model.name)
            wx.PostEvent(self.parent, StatusEvent(status=\
                       "Calc %s interrupted" % self.model.name))
           
            raise KeyboardInterrupt
        
    def compute(self):
        import numpy
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
        self.model = model
        self.starttime = 0
        
    def compute(self):
        import numpy
        x = self.x
        output = numpy.zeros(len(x))
            
        self.starttime = time.time()
        
        for i_x in range(len(self.x)):
             
            # Check whether we need to bail out
            self.isquit()
                
            try:
                value = self.model.run(self.x[i_x])
                output[i_x] = value
            except:
            
                wx.PostEvent(self.parent, StatusEvent(status=\
                       "Error computing %s at %g" %(self.model.name, self.x[i_x])))
           
        elapsed = time.time()-self.starttime
        self.complete(output=output, elapsed=elapsed)

class CalcCommandline:
    def __init__(self, n=20000):
        #print thread.get_ident()
        from sans.models.CylinderModel import CylinderModel
        from sans.models.DisperseModel import DisperseModel
        import Averager2D
        import pylab
        
        submodel = CylinderModel()
        #model = Averager2D.Averager2D()
        #model.set_model(submodel)
        #model.set_dispersity([['cyl_phi',0.2,10],
        #                      ['cyl_theta',0.2,10],
        #                      ['length',10,10],])
        
        model = DisperseModel(submodel, ['cyl_phi', 'cyl_theta', 'length'],
                                        [0.2, 0.2, 10.0])
        model.setParam('n_pts', 10)
         
        print model.runXY([0.01, 0.02])
        
        qmax = 0.01
        qstep = 0.0001
        self.done = False
        
        x = pylab.arange(-qmax, qmax+qstep*0.01, qstep)
        y = pylab.arange(-qmax, qmax+qstep*0.01, qstep)
    
        calc_thread_2D = Calc2D(x, y, model.clone(), 
                                        completefn=self.complete,
                                        updatefn=self.update,
                                        yieldtime=0.0)
     
        calc_thread_2D.queue()
        calc_thread_2D.ready(2.5)
        
        while not self.done:
            time.sleep(1)

    def update(self,output):
        print "update"

    def complete(self,output, elapsed=0.0):
        print "complete"
        self.done = True

if __name__ == "__main__":
    CalcCommandline()
   
