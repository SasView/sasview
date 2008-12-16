#from config import printEVT
from BaseInteractor import _BaseInteractor
from copy import deepcopy
import math

#from Plotter1D import AddPlotEvent
import SlicerParameters
import wx   
#import radii 
#(FunctionRadiusEvent, EVT_FUNC_RAD) = wx.lib.newevent.NewEvent()      
class ArcInteractor(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=5, r=1.0,theta1=math.pi/8,
                 theta2=math.pi/4):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self._inner_mouse_x = r
        self._inner_mouse_y = 0
        
        self._inner_save_x  = r
        self._inner_save_y  = 0
        
        self.scale = 10.0
        
        self.theta1=theta1
        self.theta2=theta2
        self.radius= r
        [self.inner_circle] = self.axes.plot([],[],
                                      linestyle='-', marker='',
                                      color=self.color)
        self.npts = 20
        self.has_move= False    
        self.connect_markers([self.inner_circle])
        self.update()

    def set_layer(self, n):
        self.layernum = n
        self.update()
        
    def clear(self):
        self.clear_markers()
        try:
            self.inner_marker.remove()
            self.inner_circle.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]
        
        
        
    def get_radius(self):
        radius =math.sqrt(math.pow(self._inner_mouse_x, 2)+math.pow(self._inner_mouse_y, 2))
        return radius
        
    def update(self,theta1=None,theta2=None, nbins=None, r=None):
        """
        Draw the new roughness on the graph.
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
        
        
        
            
        if nbins!=None:
            self.npts =nbins
        else:
            npts = int((self.theta2 - self.theta1)/(math.pi/120))   
        for i in range(self.npts):
            
            phi =(self.theta2-self.theta1)/(self.npts-1)*i +self.theta1
            #delta= phi1-phi
            if r ==None:
                self.radius=  math.sqrt(math.pow(self._inner_mouse_x, 2)+math.pow(self._inner_mouse_y, 2))
            else:
                self.radius= r
            
            xval = 1.0*self.radius*math.cos(phi) 
            yval = 1.0*self.radius*math.sin(phi) 
            
            x.append(xval)
            y.append(yval)
        
        #self.inner_marker.set(xdata=[self._inner_mouse_x],ydata=[0])
        self.inner_circle.set_data(x, y) 
        
      
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self._inner_save_x = self._inner_mouse_x
        self._inner_save_y = self._inner_mouse_y
        #self._inner_save_x = ev.xdata
        #self._inner_save_y = ev.ydata
        
        self.base.freeze_axes()

    def moveend(self, ev):
        self.has_move= False
        
        event = SlicerParameters.SlicerParameterEvent()
        event.type = self.__class__.__name__
        event.params = self.get_params()
        print "in arc moveend params",self.get_params()
        #wx.PostEvent(self.base.base.parent, event)
        
        self.base.moveend(ev)
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self._inner_mouse_x = self._inner_save_x
        self._inner_mouse_y = self._inner_save_y
       
    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        #print "ring move x, y", x,y
        self._inner_mouse_x = x
        self._inner_mouse_y = y
        self.has_move= True
        self.base.base.update()
        
    def set_cursor(self,radius, phi_min, phi_max,nbins):
        
        self.theta1= phi_min
        self.theta2= phi_max
        self.update(nbins=nbins, r=radius)
        
        
    def get_params(self):
        params = {}
        params["radius"] = self.radius
        params["theta1"] = self.theta1
        params["theta2"] = self.theta2
        return params
    
    def set_params(self, params):

        x = params["radius"] 
        self.set_cursor(x, self._inner_mouse_y)
        
    