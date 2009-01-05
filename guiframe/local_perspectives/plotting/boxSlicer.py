#TODO: the line slicer should listen to all 2DREFRESH events, get the data and slice it
#      before pushing a new 1D data update.

#
#TODO: NEED MAJOR REFACTOR
#


# Debug printout
#from config import printEVT
from BaseInteractor import _BaseInteractor
from copy import deepcopy
import math

#from Plotter1D import AddPlotEvent
import SlicerParameters
import wx

class BoxInteractor(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=3, x_min=0.0025, x_max=0.0025, y_min=0.0025, y_max=0.0025):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.qmax = self.base.qmax
        self.connect = self.base.connect
        self.xmin= -1* x_min
        self.ymin= -1* y_min
        self.xmax= x_max
        self.ymax=  y_max
        
        self.theta2= math.pi/2
        ## Number of points on the plot
        self.nbins = 20
        self.count=0
        self.error=0
        self.main_line = LineInteractor(self, self.base.subplot,color='orange', zorder=zorder, r=self.qmax,
                                           theta= self.theta2)
        self.main_line.qmax = self.base.qmax
        
        self.left_line = VerticalLine(self, self.base.subplot,color='blue', zorder=zorder, 
                                        ymin= self.ymin, ymax= self.ymax,
                                        x= self.xmin,
                                        theta2= self.theta2)
        self.left_line.qmax = self.base.qmax
        
        self.right_line= VerticalLine(self, self.base.subplot,color='black', zorder=zorder,
                                     ymin= self.ymin, ymax= self.ymax,
                                     x=self.xmax,
                                      theta2= self.theta2)
        self.right_line.qmax = self.base.qmax
        
        self.top_line= HorizontalLine(self, self.base.subplot,color='green', zorder=zorder,
                                    y= self.ymax,
                                    xmin= self.xmin, xmax= self.xmax,
                                     theta2= self.theta2)
        self.top_line.qmax = self.base.qmax
        
        self.bottom_line= HorizontalLine(self, self.base.subplot,color='red', zorder=zorder,
                                    y =self.ymin,
                                    xmin= self.xmin, xmax= self.xmax,
                                     theta2= self.theta2)
        self.bottom_line.qmax = self.base.qmax
        #self.outer_circle.set_cursor(self.base.qmax/1.8, 0)
        
                      
        self.update()
        #self._post_data()
        
        # Bind to slice parameter events
        self.base.parent.Bind(SlicerParameters.EVT_SLICER_PARS, self._onEVT_SLICER_PARS)


    def _onEVT_SLICER_PARS(self, event):
        #printEVT("AnnulusSlicer._onEVT_SLICER_PARS")
        event.Skip()
        if event.type == self.__class__.__name__:
            #self.set_params(event.params)
            self.base.update()

    def update_and_post(self):
        self.update()
        self._post_data()

    def save_data(self, path, image, x, y):
        output = open(path, 'w')
        
        data_x, data_y = self.get_data(image, x, y)
        
        output.write("<phi>  <average>\n")
        for i in range(len(data_x)):
            output.write("%g  %g\n" % (data_x[i], data_y[i]))
        output.close()

    def set_layer(self, n):
        self.layernum = n
        self.update()
        
    def clear(self):
        self.clear_markers()
        self.left_line.clear()
        self.right_line.clear()
        self.top_line.clear()
        self.bottom_line.clear()
        self.main_line.clear()
        #self.base.connect.disconnect()
        self.base.parent.Unbind(SlicerParameters.EVT_SLICER_PARS)
        
    def update(self):
        """
        Respond to changes in the model by recalculating the profiles and
        resetting the widgets.
        """
        
        if self.main_line.has_move:
            print "main has move"
            self.main_line.update()
            self.left_line.update(mline= self.main_line)
            self.right_line.update(mline= self.main_line)
            self.top_line.update(mline= self.main_line)
            self.bottom_line.update(mline= self.main_line)
        
        if self.left_line.has_move:
            print "left has moved"
            self.left_line.update()
            self.right_line.update()
            #self.right_line.update(xmin= self.left_line.x ,xmax=-1*self.left_line.x)
            self.top_line.update( xmin= self.left_line.x ,xmax= self.right_line.x)
            self.bottom_line.update(xmin= self.left_line.x ,xmax= self.right_line.x)
        if self.right_line.has_move:
            print "right has moved"
            self.right_line.update()
            self.left_line.update()
            #self.left_line.update(xmin= self.right_line.x ,xmax=-1*self.right_line.x)
            self.top_line.update( xmin= self.left_line.x ,xmax= self.right_line.x)
            self.bottom_line.update(xmin= self.left_line.x ,xmax= self.right_line.x)
            
            
        if self.bottom_line.has_move:
            print "bottom has moved"
            self.bottom_line.update()
            self.top_line.update(y= -1*self.top_line.y)
            self.left_line.update( ymin= self.bottom_line.y ,ymax= self.top_line.y)
            self.right_line.update(ymin= self.bottom_line.y ,ymax= self.top_line.y)
            
        if self.top_line.has_move:
            print "top has moved"
            self.top_line.update()
            #self.bottom_line.update()xmin=None, xmax=None,y=None, mline=None):
            self.bottom_line.update(y= -1*self.top_line.y )
            self.left_line.update(ymin= self.bottom_line.y ,ymax= self.top_line.y)
            self.right_line.update(ymin= self.bottom_line.y ,ymax= self.top_line.y)
            
    
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.base.freeze_axes()
        self.inner_circle.save(ev)
        self.outer_circle.save(ev)

    def _post_data(self):
        # Compute data
        data = self.base.data2D
        from DataLoader.manipulations import  Boxavg
        radius = math.sqrt(math.pow(self.qmax,2)+math.pow(self.qmax,2))
        x_min= self.left_line.x 
        x_max= self.right_line.x 
        y_min= self.bottom_line.y
        y_max= self.top_line.y
        box =  Boxavg (x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)
       
        self.count, self.error= box(self.base.data2D)
        
        
              
                                       
    def moveend(self, ev):
        self.base.thaw_axes()
        
        # Post paramters
        event = SlicerParameters.SlicerParameterEvent()
        event.type = self.__class__.__name__
        #event.params = self.get_params()
        wx.PostEvent(self.base.parent, event)

        self._post_data()
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.inner_circle.restore()
        self.outer_circle.restore()

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        pass
        
    def set_cursor(self, x, y):
        pass
        
    def get_params(self):
        params = {}
        params["x_min"] = self.left_line.x 
        params["x_max"] = self.right_line.x 
        params["y_min"] = self.bottom_line.y
        params["y_max"] = self.top_line.y
        params["count"] = self.count
        params["error"] = self.error
        params["phi"] = self.main_line.theta
        return params
    
    def set_params(self, params):
        
        x_min = params["x_min"] 
        x_max = params["x_max"] 
        y_min = params["y_min"]
        y_max = params["y_max"] 
        theta = params["theta"]
        
        self.left_line.update(ymin= y_min ,ymax= y_max)
        self.right_line.update(ymin= y_min ,ymax= y_max)
        self.top_line.update( xmin= x_min ,xmax= xmax)
        self.bottom_line.update(xmin= xmin ,xmax= xmax)
        self.main_line.update(theta)
        
        self._post_data()
    def freeze_axes(self):
        self.base.freeze_axes()
        
    def thaw_axes(self):
        self.base.thaw_axes()

    def draw(self):
        self.base.draw()

class HorizontalLine(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=5, y=0.5,
                 xmin=0.0,xmax=0.5,
                 theta2= math.pi/3 ):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        
        self.y=y
        self.save_y=y
        
        self.xmin=xmin
        self.save_xmin=xmin
        self.xmax=xmax
        self.save_xmax=xmax
        self.theta2= theta2
        self.radius1= math.sqrt(math.pow(self.xmin, 2)+ math.pow(self.y, 2))
        self.radius2= math.sqrt(math.pow(self.xmax, 2)+ math.pow(self.y, 2))
        
       
        #print "phi and theta2", math.degrees(math.atan2(self.y, self.xmax))
        
        self.theta_right= math.atan2(self.y,self.xmin)
        self.theta_left= math.atan2(self.y,self.xmax)
        
        self.phi_left= self.theta_left - self.theta2
        self.phi_right=  self.theta_right -  self.theta2 
        #print "phi left right", math.degrees(self.phi_left),math.degrees(self.phi_right)
        print "theta left right ", math.degrees(self.theta_left),math.degrees(self.theta_right)
        
        self.line = self.axes.plot([self.xmin,self.xmax],[self.y,self.y],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
 

        self.npts = 20
        self.has_move=False
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
        
        return 0
   
    def update(self,xmin=None, xmax=None,y=None, mline=None):
        """
        Draw the new roughness on the graph.
        """
        #print "update main line", self.has_move
        if xmin !=None:
            self.xmin=xmin
        if xmax !=None:
            self.xmax=xmax
        if y !=None:
            self.y = y
        if mline !=None:
            self.theta2= mline.theta
            delta = mline.get_delta_angle()
            # rotation
            x1 = self.radius1 * math.cos(self.phi_left +  delta)
            y1= self.radius1 * math.sin(self.phi_left + delta)
                
            x2= -1*self.radius2 * math.cos( self.phi_right + delta)
            y2= -1*self.radius2 * math.sin(self.phi_right + delta)
            
            self.line.set(xdata=[x1,x2], ydata=[y1,y2]) 
            print "Horizontal: update ",math.degrees(self.phi_left +delta),math.degrees(self.phi_right+delta)
            print x1,x2,y1,y2
           
        else:
            self.line.set(xdata=[self.xmin,self.xmax], ydata=[self.y,self.y])
     
        
        
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_xmin= self.xmin
        self.save_xmax= self.xmax
       
        self.save_y= self.y
        self.base.freeze_axes()

    def moveend(self, ev):
        
        self.has_move=False
        self.base.moveend(ev)
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.ymin = self.save_ymin
        self.ymax = self.save_ymax

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.y=y
       
        
        self.has_move=True
        self.base.base.update()
        
    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()
        
        
    def get_params(self):
        params = {}
        params["radius"] = self.xmin
        params["theta"] = self.xmax
        return params
    
    def set_params(self, params):

        x = params["radius"] 
        self.set_cursor(x, self._inner_mouse_y)
        



class VerticalLine(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=5, ymin=0.0, 
                 ymax=0.5,x= 0.5,
                 theta2= math.pi/3 ):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        # x coordinate of the vertical line
        self.x = x
        self.save_x = x
        # minimum value of y coordinate of the vertical line 
        self.ymin = ymin
        self.save_ymin = ymin
        # maximum value of y coordinate of the vertical line 
        self.ymax=ymax
        self.save_ymax=ymax
        #insure rotation
        self.radius1= math.sqrt(math.pow(self.x, 2)+ math.pow(self.ymin, 2))
        self.radius2= math.sqrt(math.pow(self.x, 2)+ math.pow(self.ymax, 2))
        
        
        self.theta_down = math.atan2(self.ymin, self.x)
        self.theta_up = math.atan2(self.ymax, self.x)
        self.theta2= theta2
        
        self.phi_down= self.theta_down - self.theta2
        self.phi_up= self.theta_up - self.theta2
        print "phi up down", math.degrees(self.phi_up),math.degrees(self.phi_down)
        print "theta up down ", math.degrees(self.theta_up),math.degrees(self.theta_down)
        # Draw vertical line
        self.line = self.axes.plot([self.x,self.x],[self.ymin,self.ymax],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
      
        self.npts = 20
        # Check vertical line motion
        self.has_move=False
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
        return 0
    
    def update(self,x=None,ymin=None, ymax=None, mline=None):
        """
        Draw the new roughness on the graph.
        """
        if x!=None:
            self.x = x
        if ymin !=None:
            self.ymin = ymin
        if ymax !=None:
            self.ymax = ymax
        if mline !=None:
            self.theta2= mline.theta
            delta = mline.get_delta_angle()
            # rotation
            x1 = self.radius1 * math.cos(self.phi_down +  delta)
            y1= self.radius1 * math.sin(self.phi_down + delta)
                
            x2= -1*self.radius2 * math.cos( self.phi_up + delta)
            y2= -1*self.radius2 * math.sin(self.phi_up + delta)
            
            self.line.set(xdata=[x1,x2], ydata=[y1,y2])  
           
        else:
           self.line.set(xdata=[self.x,self.x], ydata=[self.ymin,self.ymax])
     
        
        
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_x= self.x
        self.save_ymin= self.ymin
        self.save_ymax= self.ymax
        
        self.base.freeze_axes()

    def moveend(self, ev):
        
        self.has_move=False
        self.base.moveend(ev)
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.x = self.save_x
        
        self.ymin=self.save_ymin
        self.ymax=self.save_ymax
    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.x = x
        self.has_move=True
        self.base.base.update()
        
        
    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()
        
        
    def get_params(self):
        params = {}
        params["x"] = self.xmin
        params["ymin"] = self.ymin
        params["ymax"] = self.ymax
        return params
    
    def set_params(self, params):
        """
            Draw a vertical line given some value of params
            @param params: a dictionary containing value for x, ymin , ymax to draw 
            a vertical line
        """
        x = params["x"] 
        ymin = params["ymin"] 
        ymax = params["ymax"] 
        #self.set_cursor(x, self._inner_mouse_y)
        self.update(self,x =x,ymin =ymin, ymax =ymax)
        

        
class LineInteractor(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=5, r=1.0,theta=math.pi/4):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        
        self.save_theta = theta 
        self.theta= theta
        
        self.radius = r
      
        self.scale = 10.0
            
        # Inner circle
        x1= self.radius*math.cos(self.theta)
        y1= self.radius*math.sin(self.theta)
        x2= -1*self.radius*math.cos(self.theta)
        y2= -1*self.radius*math.sin(self.theta)
       
        self.line = self.axes.plot([x1,x2],[y1,y2],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
      
        self.npts = 20
        self.has_move=False
        self.connect_markers([self.line])
        self.update()

    def set_layer(self, n):
        
        self.layernum = n
        self.update()
        
    def clear(self):
        """
            Remove the line of the plot
        """
        self.clear_markers()
        try:
            self.line.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]
        
        
        
    def get_delta_angle(self):
        """
            return difference between initial angle and the final angle during
            rotation
        """
        return self.theta - self.save_theta
        
    def update(self, theta=None,radius=None):
        """
            Draw a line given and angle relative to the x-axis and a radius
            @param  theta: the angle realtive to the x-axis
            @param radius: the distance between the center and one end of the line
        """
        
        if theta !=None:
            self.theta= theta
        if radius !=None:
            self.radius =radius
        print "update main line", math.degrees(self.theta)
        x1= self.radius*math.cos(self.theta)
        y1= self.radius*math.sin(self.theta)
        x2= -1*self.radius*math.cos(self.theta)
        y2= -1*self.radius*math.sin(self.theta)
      
        self.line.set(xdata=[x1,x2], ydata=[y1,y2])  
     
        
        
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_theta= self.theta
        self.base.freeze_axes()

    def moveend(self, ev):
        
        self.has_move=False
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
        #print "main_line previous theta --- next theta ",math.degrees(self.save_theta),math.degrees(self.theta)
        self.has_move=True
        self.base.base.update()
        
        
    def set_cursor(self, x, y):
        
        self.move(x, y, None)
        self.update()
        
        
    def get_params(self):
        """
            return params a dictionary containing values of paramters necessary to draw 
            this line
        """
        params = {}
        params["radius"] = self.radius
        params["theta"] = self.theta
        return params
    
    def set_params(self, params):
        """
            Draw the line given value contains by params
            @param params: dictionary containing name of parameters and their values
        """
        radius = params["radius"]
        theta = params["theta"]
        self.update(x, theta= theta , radius = radius )
        



        