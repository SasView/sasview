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

def find_intersection(a1= 2, a2= -0.5,b1= 1,b2= 1 ):
    """ @ return x, y  coordinates of an intersection between 2 lines
        @param a1: the slope of the first line
        @param a2 : the slope of the 2nd line
        @param b1 : line intercept of the 1 st line
        @param b2 : line intercept of the 2 nd ligne
        @note 1st line equation  is y= a1*x +b1 ; 2nd line equation  is y= a2*x +b2 
    """
    x= ( b2- b1) /(a1- a1)
    y= ( -a2*b1 + a1*b2 )/(a1 -a2)
    return x, y
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
        
        self.theta2= math.pi/3
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
       
        params["phi"] = self.main_line.theta
        return params
    
    def set_params(self, params):
        
       
        theta = params["theta"]
        print "theta setparams",theta
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
        self.x1= self.xmax
        self.save_x1= self.xmax
        
        self.x2= self.xmin
        self.save_x2= self.xmin
        
        self.y1= self.ymax
        self.save_y1= self.ymax
        
        self.y2= self.ymin
        self.save_y2= self.ymin
        self.mline= mline
        self.line = self.axes.plot([self.x1,self.x2],
                                   [self.y1,self.y2],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
        
        self.slope= -1*math.tan(self.mline.theta)
        self.b= self.y1- self.slope* self.x1
        
        print "slope from point",(self.y2- self.y1)/(self.x2- self.x1)
        print "my slope horizontal", self.slope
        print "b from point ", self.y2- self.slope*self.x1, self.b
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
   
    def update(self,xmin=None, xmax=None,ymin=None,ymax=None, mline=None,translation=False):
        """
        Draw the new roughness on the graph.
        """
        if translation :
            print "translation ",self.top_hight
            self.x1= self.xmax +_self.top_hight*math.sin(math.pi/2 + self.mline.theta)
            self.x2= self.xmin +self.top_hight*math.sin(math.pi/2 + self.mline.theta)
            self.y1= self.ymin - self.top_hight*math.sin(math.pi/2 + self.mline.theta)
            self.y2= self.ymax -self.top_hight*math.sin(math.pi/2 + self.mline.theta)
            self.line.set(xdata=[self.x1,self.x2],
                       ydata=[self.y1,self.y2])
            return
        if xmin !=None:
            self.x2 = xmin
        if xmax !=None:
            self.x1 = xmax
        if ymin !=None:
            self.y2 = ymin
        if ymax != None:
            self.y1 = ymax
        self.line.set(xdata=[self.x1,self.x2],
                       ydata=[self.y1,self.y2])
    
        
        
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_x1= self.x1
        self.save_x2= self.x2
       
        self.save_y1= self.y1
        self.save_y2= self.y2
        
        self.base.freeze_axes()

    def moveend(self, ev):
       
        self.has_move=False
        self.base.moveend(ev)
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.x1 = self.save_x1
        self.x2 = self.save_x2
        self.y1 = self.save_y1
        self.y2 = self.save_y2

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.b = - self.slope.x
        self.has_move=True
        self.base.base.update()
        
    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()
        
        
    def get_params(self):
        params = {}
        params["radius"] = self.x1
        #params["theta"] = self.xmax
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
        
        self.theta2 = mline.theta
        self.mline =mline
        self.xmin= xmin
        self.x1= mline.x1 + xmin*math.cos(math.pi/2 - self.theta2)
        self.x2= mline.x2 + xmin*math.cos(math.pi/2 - self.theta2)
        self.y1= mline.y1 - xmin*math.sin(math.pi/2 - self.theta2)
        self.y2= mline.y2 - xmin*math.sin(math.pi/2 - self.theta2)
        self.line = self.axes.plot([self.x1,self.x2],[self.y1,self.y2],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
      
        
        self.slope= math.tan(self.mline.theta)
        print "vertical line intercetp ",self.y2- self.slope*self.x2, self.y1- self.slope* self.x1 
       
        self.b = self.y1- self.slope* self.x1 
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
        self.x1= self.mline.x1 + self.xmin*math.cos(math.pi/2 - self.mline.theta)
        self.x2= self.mline.x2 + self.xmin*math.cos(math.pi/2 - self.mline.theta)
        self.y1= self.mline.y1 - self.xmin*math.sin(math.pi/2 - self.mline.theta)
        self.y2= self.mline.y2 - self.xmin*math.sin(math.pi/2 - self.mline.theta)
        self.line.set(xdata=[self.x1,self.x2],
                           ydata=[self.y1,self.y2]) 
        #print "update slope ", (self.y2-self.y1)/(self.x2- self.x1)
        #print "main slope", math.tan(self.mline.theta)
        
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
        self.x1 = self.save_x1
        self.x2 = self.save_x2
        self.y1 = self.save_y1
        self.y2= self.save_y2
      
        
    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.has_move=True
        
        # compute the b intercept of the vertical line
        self.b= math.fabs( y - self.mline.theta * x)
        
        
        print "move L_width", self.L_width, self.L_hight
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
        print "init mainline sintercept ", self.y1 - math.tan(self.theta)*self.x1,\
         self.y2 - math.tan(self.theta)*self.x2
        print "main line slope ", (self.y2- self.y1)/(self.x2- self.x1)
        print "theta", math.tan(self.theta)
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
        



        