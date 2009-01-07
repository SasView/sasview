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
    def __init__(self,base,axes,color='black', zorder=3,
                  x_min=0.0025, x_max=0.0025, y_min=0.0025, y_max=0.0025):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.qmax = self.base.qmax
        self.connect = self.base.connect
        self.xmin= -1* x_min
        self.ymin= -1* y_min
        
        self.xmax= x_max
        self.ymax=  y_max
        
        self.theta2= math.pi/4
        ## Number of points on the plot
        self.nbins = 20
        self.count=0
        self.error=0
        self.main_line = LineInteractor(self, self.base.subplot,color='orange',
                                         zorder=zorder, ymin=y_min ,ymax=y_max,
                                           theta= self.theta2)
        self.main_line.qmax = self.base.qmax
        
        self.left_line = VerticalLine(self, self.base.subplot,color='blue', 
                                      zorder=zorder,
                                      mline= self.main_line, 
                                        ymin= self.ymin , 
                                        ymax= self.ymax ,
                                        xmin=self.xmin,
                                        xmax=self.xmin,
                                        theta2= self.theta2)
        self.left_line.qmax = self.base.qmax
        
        self.right_line= VerticalLine(self, self.base.subplot,color='black', 
                                      zorder=zorder,
                                      mline= self.main_line, 
                                     ymin= self.ymin , 
                                     ymax= self.ymax,
                                    xmin= self.xmax,
                                    xmax= self.xmax,
                                    theta2= self.theta2)
        self.right_line.qmax = self.base.qmax
        
        self.top_line= HorizontalLine(self, self.base.subplot,color='green', 
                                      zorder=zorder,
                                      mline= self.main_line,
                                      xmin=self.right_line.x1,
                                      xmax=self.left_line.x1,
                                      ymin=self.right_line.y1,
                                      ymax=self.left_line.y1)
        self.top_line.qmax= self.base.qmax
        
        self.bottom_line= HorizontalLine(self, self.base.subplot,color='grey', 
                                      zorder=zorder,
                                      mline= self.main_line,
                                      xmin=self.right_line.x2,
                                      xmax=self.left_line.x2,
                                      ymin=self.right_line.y2,
                                      ymax=self.left_line.y2)
        self.bottom_line.qmax= self.base.qmax
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
            
            self.main_line.update()
            self.left_line.update(
                                  xmin= self.xmin,
                                  xmax= self.xmin,
                                  ymin= self.ymin,
                                  ymax=self.ymax,
                                  translation=True)
            self.right_line.update(
                                   xmin= self.xmax,
                                  xmax= self.xmax,
                                  ymin= self.ymin,
                                  ymax=self.ymax,
                                  translation=True)
            self.top_line.update(xmin= self.right_line.x1,
                                 xmax= self.left_line.x1,
                                 ymin= self.right_line.y1,
                                 ymax= self.left_line.y1)
            self.bottom_line.update(xmin= self.right_line.x2,
                                 xmax= self.left_line.x2,
                                 ymin= self.right_line.y2,
                                 ymax= self.left_line.y2)
        if self.left_line.has_move:
            print "left has moved"
            self.left_line.update()
            self.right_line.update(opline= self.left_line )
            
            self.top_line.update(xmin= self.right_line.x2,
                                 xmax= self.left_line.x1,
                                 ymin= self.right_line.y2,
                                 ymax= self.left_line.y1)
            
            
            self.bottom_line.update(xmin= self.right_line.x1,
                                 xmax= self.left_line.x2,
                                 ymin= self.right_line.y1,
                                 ymax= self.left_line.y2)
           
        if self.right_line.has_move:
            print "right has moved"
            self.right_line.update()
            self.left_line.update(opline= self.right_line )
            
            self.top_line.update(xmin= self.right_line.x1,
                                 xmax= self.left_line.x2,
                                 ymin= self.right_line.y1,
                                 ymax= self.left_line.y2)
            
            self.bottom_line.update(xmin= self.right_line.x2,
                                 xmax= self.left_line.x1,
                                 ymin= self.right_line.y2,
                                 ymax= self.left_line.y1)
        if self.top_line.has_move:
            self.top_line.update(translation=True)
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
        #data = self.base.data2D
        #from DataLoader.manipulations import  Boxavg
        #radius = math.sqrt(math.pow(self.qmax,2)+math.pow(self.qmax,2))
        #x_min= self.left_line.xmin 
        #x_max= self.right_line.xmax 
        #y_min= self.bottom_line.y
        #y_max= self.top_line.y
        #box =  Boxavg (x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)
       
        #self.count, self.error= box(self.base.data2D)
        
        print "post data"
              
                                       
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
        params["x_min"] = self.left_line.L_width
        params["x_max"] = self.right_line.R_width
        #params["y_min"] = self.bottom_line.y
        #params["y_max"] = self.top_line.y
        params["count"] = self.count
        params["error"] = self.error
        params["phi"] = self.main_line.theta
        return params
    
    def set_params(self, params):
        
        x_min = params["x_min"] 
        x_max = params["x_max"] 
        #y_min = params["y_min"]
        #y_max = params["y_max"] 
        theta = params["theta"]
        
        self.left_line.update(ymin= y_min ,ymax= y_max)
        self.right_line.update(ymin= y_min ,ymax= y_max)
        #self.top_line.update( xmin= x_min ,xmax= xmax)
        #self.bottom_line.update(xmin= xmin ,xmax= xmax)
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
    def __init__(self,base,axes,color='black', zorder=5,mline=None,ymin=None, ymax=None, y=0.5,
                 xmin=0.0,xmax=0.5,
                 theta2= math.pi/3 ):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        
        self.ymin= ymin
        self.save_ymin = ymin
        self.mline = mline
        self.ymax= ymax
        self.save_ymax = ymax
        self.xmin = xmin
        self.save_xmin = xmin
        self.xmax = xmax
        self.save_xmax = xmax
        self.top_hight= self.ymax
        
        self.theta2 = theta2
        
        self.line = self.axes.plot([self.xmax,self.xmin],
                                   [self.ymax,self.ymin],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
 
        
        
        self.npts = 20
        self.has_move=False
        self.connect_markers([self.line])
        self.update(xmin= self.xmin,
                    xmax= self.xmax,
                    ymin= self.ymin,
                    ymax=  self.ymax)

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
   
    def update(self,xmin=None, xmax=None,ymin=None,ymax=None, mline=None,translation=False):
        """
        Draw the new roughness on the graph.
        """
        if translation :
            print "translation ",self.top_hight
            self.x1= self.xmax + self.top_hight*math.sin(math.pi/2 + self.mline.theta)
            self.x2= self.xmin + self.top_hight*math.sin(math.pi/2 + self.mline.theta)
            self.y1= self.ymin - self.top_hight*math.cos(math.pi/2 + self.mline.theta)
            self.y2= self.ymax -self.top_hight*math.cos(math.pi/2 + self.mline.theta)
            self.line.set(xdata=[self.x1,self.x2],
                       ydata=[self.y1,self.y2])
            return
        #print "update main line", self.has_move
        self.xmin=xmin
        self.xmax=xmax
        self.ymin=ymin
        self.ymax=ymax
        self.line.set(xdata=[self.xmin,self.xmax],
                       ydata=[self.ymin,self.ymax])
    
        
        
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_xmin= self.xmin
        self.save_xmax= self.xmax
       
        self.save_ymin= self.ymin
        self.save_ymax= self.ymax
        self.top_hight= self.ymax
        self.base.freeze_axes()

    def moveend(self, ev):
       
        self.has_move=False
        self.base.moveend(ev)
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.xmin = self.save_xmin
        self.xmax = self.save_xmax
        self.ymin = self.save_ymin
        self.ymax = self.save_ymax

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        
        self.top_hight= y
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
    def __init__(self,base,axes,color='black', zorder=5, mline=None, ymin=0.0, 
                 ymax=0.5,xmin=-0.5,xmax=0.5,
                 theta2= math.pi/3 ):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        
        self.L_width=xmin
        self.save_L_width=xmin
        
        self.save_xmin= xmin
        self.R_width=xmax
        self.save_xmax=xmax
        self.ymin=ymin
        self.save_ymin= ymin
        self.ymax=ymax
        self.save_ymax= ymax
        
        self.theta2= theta2
        
        self.mline= mline
      
        self.detax=0
        self.deltay=0
        
       
        self.clickxf=0
        self.clickyf=0
        self.x1= mline.x1 + xmin*math.cos(math.pi/2 - self.theta2)
        self.x2= mline.x2 + xmin*math.cos(math.pi/2 - self.theta2)
        self.y1= mline.y1 - xmin*math.sin(math.pi/2 - self.theta2)
        self.y2= mline.y2 - xmin*math.sin(math.pi/2 - self.theta2)
        
        self.line = self.axes.plot([self.x1,self.x2],[self.y1,self.y2],
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
    
    def update(self,xmin=None,xmax=None,ymin=None, ymax=None, opline=None,translation=False):
        """
        Draw the new roughness on the graph.
        """
        if opline !=None:
            self.x1= -1*opline.x1
            self.x2= -1*opline.x2
            self.y1= -1*opline.y1
            self.y2= -1*opline.y2
            self.line.set(xdata=[self.x1,self.x2],
                           ydata=[self.y1,self.y2]) 
            return
        if xmin== None:
            xmin= self.L_width
        if xmax== None:
            xmax= self.R_width
        #print "vertical line: xmin, xmax , ymin , ymax", xmin, self.mline.theta
        self.x1= self.mline.x1 + xmin*math.cos(math.pi/2 - self.mline.theta)
        self.x2= self.mline.x2 + xmin*math.cos(math.pi/2 - self.mline.theta)
        self.y1= self.mline.y1 - xmin*math.sin(math.pi/2 - self.mline.theta)
        self.y2= self.mline.y2 - xmin*math.sin(math.pi/2 - self.mline.theta)
        #print "vertical line: main line  value ", self.mline.x1, self.mline.x2, self.mline.y1,self.mline.y2
        #print "vertical line: new value ", self.x1, self.x2, self.y1,self.y2

        self.line.set(xdata=[self.x1,self.x2], ydata=[self.y1,self.y2])  
        if opline !=None:
            self.line.set(xdata=[-1*self.opline.x1,-1*self.opline.x2],
                           ydata=[self.opline.y1,self.opline.y2]) 
            return
        if translation:
            print "xmin L_width", xmin, self.L_width
            self.x1= self.mline.x1 + self.L_width*math.cos(math.pi/2 - self.mline.theta)
            self.x2= self.mline.x2 + self.L_width*math.cos(math.pi/2 - self.mline.theta)
            self.y1= self.mline.y1 - self.L_width*math.sin(math.pi/2 - self.mline.theta)
            self.y2= self.mline.y2 - self.L_width*math.sin(math.pi/2 - self.mline.theta)
            
            print"translation x1, x2,y1,y2",self.x1, self.x2,self.y1,self.y2
            self.line.set(xdata=[self.x1,self.x2], ydata=[self.y1,self.y2]) 
            
            
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_L_width= self.L_width
        self.save_xmin= self.x1
        self.save_xmax= self.x2
        self.save_ymin= self.y1
        self.save_ymax= self.y2
        
        self.base.freeze_axes()

    def moveend(self, ev):
        
        self.has_move=False
        self.base.moveend(ev)
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.xmin = self.save_xmin
        self.xmax = self.save_xmax
        self.ymin = self.save_ymin
        self.ymax = self.save_ymax
        self.L_width= self.save_L_width
        
    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.has_move=True
        self.L_width = x
        print "move L_width", self.L_width
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
    def __init__(self,base,axes,color='black', zorder=5, ymin=1.0,ymax=1.0,theta=math.pi/4):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        
        self.save_theta = theta 
        self.theta= theta
        
        self.radius1 = ymax
        self.radius2 = ymin
        self.scale = 10.0
            
        # Inner circle
        self.x1= self.radius1*math.cos(self.theta)
        self.y1= self.radius1*math.sin(self.theta)
        self.x2= -1*self.radius2*math.cos(self.theta)
        self.y2= -1*self.radius2*math.sin(self.theta)
       
        self.line = self.axes.plot([self.x1,self.x2],[self.y1,self.y2],
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
        
    def update(self, theta=None,radius1=None,radius2=None):
        """
            Draw a line given and angle relative to the x-axis and a radius
            @param  theta: the angle realtive to the x-axis
            @param radius: the distance between the center and one end of the line
        """
        
        if theta !=None:
            self.theta= theta
        if radius1 !=None:
            self.radius1 =radius1
        if radius2 !=None:
            self.radius2 =radius2
        print "update main line", math.degrees(self.theta),self.radius1, self.radius2
        self.x1= self.radius1*math.cos(self.theta)
        self.y1= self.radius1*math.sin(self.theta)
        self.x2= -1*self.radius2*math.cos(self.theta)
        self.y2= -1*self.radius2*math.sin(self.theta)
      
        self.line.set(xdata=[self.x1,self.x2], ydata=[self.y1,self.y2])  
     
        
        
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
        params["ymax"] = self.radius1
        params["ymin"] = self.radius2
        params["theta"] = self.theta
        return params
    
    def set_params(self, params):
        """
            Draw the line given value contains by params
            @param params: dictionary containing name of parameters and their values
        """
        radius1 = params["ymax"]
        radius2 = params["ymin"]
        theta = params["theta"]
        self.update(x, theta= theta , radius1 = radius1 ,radius2 = radius2)
        



        