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
    x= ( b2- b1) /(a1- a2)
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
        
        self.bottom_line= HorizontalLine(self, self.base.subplot,color='gray', 
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
                                  ymax=self.ymax
                                  )
            self.right_line.update(
                                   xmin= self.xmax,
                                  xmax= self.xmax,
                                  ymin= self.ymin,
                                  ymax=self.ymax)
            self.top_line.update(xmin= self.right_line.x1,
                                 xmax= self.left_line.x1,
                                 ymin= self.right_line.y1,
                                 ymax= self.left_line.y1)
            self.bottom_line.update(xmin= self.right_line.x2,
                                 xmax= self.left_line.x2,
                                 ymin= self.right_line.y2,
                                 ymax= self.left_line.y2)
        if self.top_line.has_move:
            print "top has moved",self.left_line.slope, self.top_line.slope
            x2, y2= find_intersection(a1= self.left_line.slope,
                                     a2= self.top_line.slope,
                                     b1= self.left_line.b,
                                     b2= self.top_line.b )
            print "x, y max: ",x2,y2
            x1, y1= find_intersection(a1= self.right_line.slope,
                                     a2= self.top_line.slope,
                                     b1= self.right_line.b,
                                     b2= self.top_line.b )
            print "x, y min: ",x1 ,y1
            self.top_line.update(xmin= x2,
                                 ymin= y2,
                                 xmax= x1,
                                 ymax= y1)
            
            self.bottom_line.update(xmin= -x2,
                                    ymin= -y2,
                                    xmax= -x1,
                                    ymax= -y1)
            self.left_line.update(xmin= -x1,
                                  ymin= -y1,
                                  xmax= x2,
                                  ymax= y2,
                                  translation= True)
            self.right_line.update(
                                   xmin= -x2,
                                   ymin= -y2,
                                   xmax= x1,
                                   ymax= y1,
                                  translation= True)
            print "top has moved",self.left_line.slope, self.top_line.slope
            x2, y2= find_intersection(a1= self.main_line.slope,
                                     a2= self.top_line.slope,
                                     b1= self.main_line.b,
                                     b2= self.top_line.b )
            print "main x, y max: ",x2,y2
            x1, y1= find_intersection(a1= self.main_line.slope,
                                     a2= self.bottom_line.slope,
                                     b1= self.main_line.b,
                                     b2= self.bottom_line.b )
            print "main x, y min: ",x1,y1
            self.main_line.update(x1= -x2,
                                  y1= -y2,
                                  x2= x2,
                                  y2= y2,
                                  translation= True)
        if self.bottom_line.has_move:
            
            print "bottom has moved",self.left_line.slope, self.bottom_line.slope
            x2, y2= find_intersection(a1= self.left_line.slope,
                                     a2= self.bottom_line.slope,
                                     b1= self.left_line.b,
                                     b2= self.bottom_line.b )
            print "x, y max: ",x2,y2
            x1, y1= find_intersection(a1= self.right_line.slope,
                                     a2= self.bottom_line.slope,
                                     b1= self.right_line.b,
                                     b2= self.bottom_line.b )
            print "x, y min: ",x1 ,y1
            self.bottom_line.update(xmin= x2,
                                 ymin= y2,
                                 xmax= x1,
                                 ymax= y1)
            
            self.top_line.update(xmin= -x2,
                                    ymin= -y2,
                                    xmax= -x1,
                                    ymax= -y1)
            self.left_line.update(xmin= -x1,
                                  ymin= -y1,
                                  xmax= x2,
                                  ymax= y2,
                                  translation= True)
            self.right_line.update(
                                   xmin= -x2,
                                   ymin= -y2,
                                   xmax= x1,
                                   ymax= y1,
                                  translation= True)
            print "bottom has moved",self.left_line.slope, self.bottom_line.slope
            x2, y2= find_intersection(a1= self.main_line.slope,
                                     a2= self.bottom_line.slope,
                                     b1= self.main_line.b,
                                     b2= self.bottom_line.b )
            print "main x, y max: ",x2,y2
            x1, y1= find_intersection(a1= self.main_line.slope,
                                     a2= self.top_line.slope,
                                     b1= self.main_line.b,
                                     b2= self.top_line.b )
            print "main x, y min: ",x1,y1
            self.main_line.update(x1= -x2,
                                  y1= -y2,
                                  x2= x2,
                                  y2= y2,
                                  translation= True)
        if self.left_line.has_move:
            print "left_line has moved",self.left_line.slope, self.top_line.slope
            x2, y2= find_intersection(a1= self.left_line.slope,
                                     a2= self.top_line.slope,
                                     b1= self.left_line.b,
                                     b2= self.top_line.b )
            print "main x, y max: ",x2,y2
            x1, y1= find_intersection(a1= self.left_line.slope,
                                     a2= self.bottom_line.slope,
                                     b1= self.left_line.b,
                                     b2= self.bottom_line.b )
            self.left_line.update(xmin = x1,
                                   xmax = x2,
                                    ymin= y1, 
                                    ymax= y2,
                                   translation=True)
            
            self.right_line.update(xmin = -x1,
                                   xmax = -x2,
                                    ymin= -y1, 
                                    ymax= -y2,
                                   translation=True)
            
            self.bottom_line.update(xmin= x1,
                                 ymin= y1,
                                 xmax= -x2,
                                 ymax= -y2)
            
            self.top_line.update(xmin= x2,
                                    ymin= y2,
                                    xmax= -x1,
                                    ymax= -y1)
            print "initial xmin", self.xmin
            self.xmin= math.sqrt(math.pow((self.main_line.x2 - self.left_line.x2),2)\
                                 +math.pow((self.main_line.y2 - self.left_line.y2),2))
                                 
            print "new xmin ", self.xmin, self.main_line.x2 , self.left_line.x2
        if self.right_line.has_move:
            print "right_line has moved",self.right_line.slope, self.top_line.slope
            x2, y2= find_intersection(a1= self.right_line.slope,
                                     a2= self.top_line.slope,
                                     b1= self.right_line.b,
                                     b2= self.top_line.b )
            print "main x, y max: ",x2,y2
            x1, y1= find_intersection(a1= self.right_line.slope,
                                     a2= self.bottom_line.slope,
                                     b1= self.right_line.b,
                                     b2= self.bottom_line.b )
            self.right_line.update(xmin = x1,
                                   xmax = x2,
                                    ymin= y1, 
                                    ymax= y2,
                                   translation=True)
            
            self.left_line.update(xmin = -x1,
                                   xmax = -x2,
                                    ymin= -y1, 
                                    ymax= -y2,
                                   translation=True)
            
            self.bottom_line.update(xmin= x1,
                                 ymin= y1,
                                 xmax= -x2,
                                 ymax= -y2)
            
            self.top_line.update(xmin= x2,
                                    ymin= y2,
                                    xmax= -x1,
                                    ymax= -y1)
               
            print "initial xmax", self.xmax
            self.xmax= math.sqrt(math.pow((self.main_line.x2 - self.right_line.x2),2)\
                                 +math.pow((self.main_line.y2 - self.right_line.y2),2))
            print "new xmax",self.xmax
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
        params["x1"]= self.xmax
        params["y1"]= self.ymin
        params["x2"]= self.xmin
        params["y2"]= self.ymax
        params["phi"] = self.main_line.theta
        return params
    
    def set_params(self, params):
        self.xmax = params["x1"]
        self.ymin = params["y1"] 
        self.xmin = params["x2"]
        self.ymax = params["y2"]
        theta = params["theta"]
        print "theta setparams",theta
        self.main_line.update(radius1= math.fabs(self.ymax), radius2= math.fabs(self.ymin), theta= theta)
        self.left_line.update(xmin= -1*self.xmin)
        self.right_line.update(xmin= self.xmax)
        
        self.top_line.update(xmin= self.right_line.x1,
                                 xmax= self.left_line.x1,
                                 ymin= self.right_line.y1,
                                 ymax= self.left_line.y1)
        self.bottom_line.update(xmin= self.right_line.x2,
                                 xmax= self.left_line.x2,
                                 ymin= self.right_line.y2,
                                 ymax= self.left_line.y2)
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
        self.x1= xmax
        self.save_x1= xmax
        
        self.x2= xmin
        self.save_x2= xmin
        
        self.y1= ymax
        self.save_y1= ymax
        
        self.y2= ymin
        self.save_y2= ymin
        self.mline= mline
        self.line = self.axes.plot([self.x1,self.x2],
                                   [self.y1,self.y2],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
        
        self.slope= -1/math.tan(self.mline.theta)
        self.b= self.y1- self.slope* self.x1
        self.save_b= self.b
        print "slope from point",(self.y2- self.y1)/(self.x2- self.x1)
        print "my slope horizontal", self.slope
        print "b from point ", self.y2- self.slope*self.x2, self.b
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
        self.slope= -1/math.tan(self.mline.theta)
        if xmin !=None:
            self.x2 = xmin
        if xmax !=None:
            self.x1 = xmax
        if ymin !=None:
            self.y2 = ymin
        if ymax != None:
            self.y1 = ymax
        self.b= self.y1- self.slope * self.x1
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
        self.save_b= self.b
        
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
        self.b = self.save_b

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        print "horizontal move x y ", x, y
        self.b =  y - (-1/self.mline.slope) *x
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
        
        self.slope= math.tan(self.mline.theta)
        if translation:
            if xmin!=None:
                self.x2=xmin
                self.xmin= xmin
            if xmax!=None:
                self.x1=xmax
            if ymin!=None:
                self.y2=ymin
            if ymax!=None:
                self.y1=ymax
            self.line.set(xdata=[self.x1,self.x2],
                           ydata=[self.y1,self.y2]) 
            self.b= self.y1- self.slope * self.x1
            return 
        
        self.x1= self.mline.x1 + self.xmin*math.cos(math.pi/2 - self.mline.theta)
        self.x2= self.mline.x2 + self.xmin*math.cos(math.pi/2 - self.mline.theta)
        self.y1= self.mline.y1 - self.xmin*math.sin(math.pi/2 - self.mline.theta)
        self.y2= self.mline.y2 - self.xmin*math.sin(math.pi/2 - self.mline.theta)
        self.line.set(xdata=[self.x1,self.x2],
                           ydata=[self.y1,self.y2]) 
        print "update slope ", (self.y2-self.y1)/(self.x2- self.x1)
        #print "main slope", math.tan(self.mline.theta)
        
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
        self.y2= self.save_y2
      
        
    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.has_move=True
        
        # compute the b intercept of the vertical line
        self.b=y - self.mline.slope * x
        
        
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
        
        self.radius1 = math.fabs(ymax)
        self.radius2 = math.fabs(ymin)
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
        self.slope= math.tan(self.theta)
        self.b= math.fabs(self.y1- self.slope * self.x1)
        print "intercept main",math.fabs(self.y2- self.slope * self.x2),math.fabs(self.y1- self.slope * self.x1)
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
        
    def update(self,x1=None,
               y1=None,
               x2=None,
               y2=None,
               translation=False,
               xmin=None,vline=None, theta=None,radius1=None,radius2=None):
        """
            Draw a line given and angle relative to the x-axis and a radius
            @param  theta: the angle realtive to the x-axis
            @param radius: the distance between the center and one end of the line
        """
        if translation:
            if x1 !=None:
                self.x1= x1
            if x2 !=None:
                self.x2= x2
            if y1 !=None:
                self.y1= y1
            if y2 !=None:
                self.y2= y2
        
            self.line.set(xdata=[self.x1,self.x2], ydata=[self.y1,self.y2])
            self.radius1= math.fabs(self.x1/math.cos(self.theta))
            self.radius2= math.fabs(self.x2/math.cos(self.theta))
            print "radius 1, radius2", self.radius1, self.radius2
            return     
      
        if theta !=None:
            self.theta= theta
        if radius1 !=None:
            self.radius1 =radius1
        if radius2 !=None:
            self.radius2 =radius2
        #print "update main line", math.degrees(self.theta),self.radius1, self.radius2
        #print "smain radius 1 2", self.radius1, self.radius2
        self.x1= self.radius1*math.cos(self.theta)
        self.y1= self.radius1*math.sin(self.theta)
        self.x2= -1*self.radius2*math.cos(self.theta)
        self.y2= -1*self.radius2*math.sin(self.theta)
        print "init mainline sintercept ", self.y1 - math.tan(self.theta)*self.x1,\
         self.y2 - math.tan(self.theta)*self.x2
        #print "main line slope ", (self.y2- self.y1)/(self.x2- self.x1)
        #print "theta", math.tan(self.theta)
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
        self.slope= math.tan(self.theta)
        self.b=  y - self.slope *x
        
        print "main move slope , theta, b", self.slope, self.theta, self.b
        
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
        



        