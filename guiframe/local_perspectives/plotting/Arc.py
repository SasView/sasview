
import math
import wx 
from copy import deepcopy

from BaseInteractor import _BaseInteractor
from sans.guicomm.events import NewPlotEvent, StatusEvent,SlicerParameterEvent,EVT_SLICER_PARS
  
 
class ArcInteractor(_BaseInteractor):
    """
    Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=5, r=1.0,theta1=math.pi/8,
                 theta2=math.pi/4):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self._mouse_x = r
        self._mouse_y = 0
        
        self._save_x  = r
        self._save_y  = 0
        
        self.scale = 10.0
        
        self.theta1=theta1
        self.theta2=theta2
        self.radius= r
        [self.arc] = self.axes.plot([],[],
                                      linestyle='-', marker='',
                                      color=self.color)
        self.npts = 20
        self.has_move= False    
        self.connect_markers([self.arc])
        self.update()

    def set_layer(self, n):
        """
        """
        self.layernum = n
        self.update()
        
    def clear(self):
        """
        """
        self.clear_markers()
        try:
            self.marker.remove()
            self.arc.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]
        
    def get_radius(self):
        """
        """
        radius =math.sqrt(math.pow(self._mouse_x, 2)+math.pow(self._mouse_y, 2))
        return radius
        
    def update(self,theta1=None,theta2=None, nbins=None, r=None):
        """
        """
        # Plot inner circle
        x = []
        y = []
        if theta1 !=None:
            self.theta1= theta1
        if theta2 !=None:
            self.theta2= theta2
        
        print "ring update theta1 theta2", math.degrees(self.theta1), math.degrees(self.theta2)
        while self.theta2 < self.theta1: self.theta2 += 2*math.pi
        while self.theta2 >= self.theta1+2*math.pi: self.theta2 -= 2*math.pi

        npts = int((self.theta2 - self.theta1)/(math.pi/120))  
             
        if r ==None:
            self.radius=  math.sqrt(math.pow(self._mouse_x, 2)+math.pow(self._mouse_y, 2))
        else:
            self.radius= r
            
        for i in range(self.npts):
            
            phi =(self.theta2-self.theta1)/(self.npts-1)*i +self.theta1
            
            xval = 1.0*self.radius*math.cos(phi) 
            yval = 1.0*self.radius*math.sin(phi) 
            
            x.append(xval)
            y.append(yval)
        
        #self.marker.set(xdata=[self._mouse_x],ydata=[0])
        self.arc.set_data(x, y) 
        
      
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self._save_x = self._mouse_x
        self._save_y = self._mouse_y
        #self._save_x = ev.xdata
        #self._save_y = ev.ydata
        
        self.base.freeze_axes()

    def moveend(self, ev):
        """
        """
        self.has_move= False
        
        event = SlicerParameterEvent()
        event.type = self.__class__.__name__
        event.params = self.get_params()
        print "in arc moveend params",self.get_params()
        #wx.PostEvent(self.base.base.parent, event)
        
        self.base.moveend(ev)
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self._mouse_x = self._save_x
        self._mouse_y = self._save_y
       
    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        #print "ring move x, y", x,y
        self._mouse_x = x
        self._mouse_y = y
        self.has_move= True
        self.base.base.update()
        
    def set_cursor(self,radius, phi_min, phi_max,nbins):
        """
        """
        self.theta1= phi_min
        self.theta2= phi_max
        self.update(nbins=nbins, r=radius)
        
        
    def get_params(self):
        """
        """
        params = {}
        params["radius"] = self.radius
        params["theta1"] = self.theta1
        params["theta2"] = self.theta2
        return params
    
    def set_params(self, params):
        """
        """
        x = params["radius"] 
        self.set_cursor(x, self._mouse_y)
        
    