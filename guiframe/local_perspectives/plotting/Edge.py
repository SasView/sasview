#from config import printEVT
from BaseInteractor import _BaseInteractor
from copy import deepcopy
import math

#from Plotter1D import AddPlotEvent
import SlicerParameters
import wx     

import wx.lib.newevent
       
class RadiusInteractor(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=5, arc1=None,arc2=None,
                 theta=math.pi/8):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        
        self.r1 = arc1.get_radius()
        self.r2 = arc2.get_radius()
        #print "radius init", self.r1, self.r2
        self.theta=theta
        self.save_theta= theta
        #self.scale = 10.0
        
        self.arc1= arc1
        self.arc2=arc2
        #raise "Version error", message
        x1= self.r1*math.cos(self.theta)
        y1= self.r1*math.sin(self.theta)
        x2= self.r2*math.cos(self.theta)
        y2= self.r2*math.sin(self.theta)
        self.line = self.axes.plot([x1,x2],[y1,y2],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
       
        self.npts = 20
        self.has_move= False
        self.connect_markers([self.line])
        self.update()
        
        
    def set_layer(self, n):
        self.layernum = n
        self.update()
        
    def clear(self):
        self.clear_markers()
        try:
            self.line.remove()
          
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]
        
        
        
    def get_radius(self):
        return self.theta
        
    def update(self,r1=None, r2=None):
        """
        Draw the new roughness on the graph.
        """
        # Plot inner circle
        if r1 !=None:
            self.r1=r1
        if r2!=None:
            self.r2=r2
        #print "update line ",self.r1,self.r2
        #if self.theta <0:
        #    self.theta= 2*math.pi + self.theta
        x1= self.r1*math.cos(self.theta)
        y1= self.r1*math.sin(self.theta)
        x2= self.r2*math.cos(self.theta)
        y2= self.r2*math.sin(self.theta)  
             
        self.line.set(xdata=[x1,x2], ydata=[y1,y2])
        return 1
 
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_theta= self.theta
        self.base.freeze_axes()
   
    def moveend(self, ev):
        self.has_move= False
        self.base.moveend(ev)
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.theta = self.save_theta

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.theta= math.atan2(y,x)
        
        self.has_move= True
        self.base.base.update()
        
    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()
        
        
    def get_params(self):
        params = {}
        params["radius1"] = self.r1
        params["radius2"] = self.r2
        return params
    
    def set_params(self, params):

        x1 = params["radius1"] 
        x2 = params["radius2"] 
        self.set_cursor(x, self._inner_mouse_y)
        
    