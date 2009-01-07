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
                                         zorder=zorder, r=self.qmax,
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
        """
        self.left_line = VerticalLine(self, self.base.subplot,color='blue', 
                                      zorder=zorder, 
                                        ymin= self.main_line.y2 , 
                                        ymax= self.main_line.y1 ,
                                        xmin=self.main_line.x2 +self.xmin,
                                        xmax=self.main_line.x1 +self.xmin,
                                        theta2= self.theta2)
        self.left_line.qmax = self.base.qmax
        
        self.right_line= VerticalLine(self, self.base.subplot,color='black', 
                                      zorder=zorder,
                                     ymin= self.main_line.y2 , 
                                     ymax= self.main_line.y1 ,
                                    xmin=self.main_line.x2 +self.xmax,
                                    xmax=self.main_line.x1 +self.xmax,
                                    theta2= self.theta2)
        self.right_line.qmax = self.base.qmax
        self.top_line= HorizontalLine(self, self.base.subplot,color='green', 
                                      zorder=zorder,
                                    y= self.ymax,
                                    xmin= self.xmin, xmax= self.xmax,
                                     theta2= self.theta2)
        self.top_line.qmax = self.base.qmax
        
        self.bottom_line= HorizontalLine(self, self.base.subplot,color='red',
                                          zorder=zorder,
                                    y =self.ymin,
                                    xmin= self.xmin, xmax= self.xmax,
                                     theta2= self.theta2)
        self.bottom_line.qmax = self.base.qmax
        #self.outer_circle.set_cursor(self.base.qmax/1.8, 0)
        
           """           
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
        #self.top_line.clear()
        #self.bottom_line.clear()
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
            self.left_line.update(mline= self.main_line,
                                  xmin= self.xmin,
                                  xmax= self.xmin,
                                  ymin= self.ymin,
                                  ymax=self.ymax,
                                  translation=True)
            self.right_line.update(mline= self.main_line,
                                   xmin= self.xmax,
                                  xmax= self.xmax,
                                  ymin= self.ymin,
                                  ymax=self.ymax,
                                  translation=True)
            #self.top_line.update(mline= self.main_line)
            #self.bottom_line.update(mline= self.main_line)
        
        if self.left_line.has_move:
            print "left has moved"
            self.left_line.update(mline= self.main_line,
                                  xmin= self.xmin,
                                  translation=True)
            self.right_line.update(mline= self.main_line,
                                   xmin=-1*self.xmin,
                                   translation=True)
            """
            self.top_line.update( xmin= self.left_line.xmax ,xmax= self.right_line.xmax,
                                  translation=True)
            self.bottom_line.update(xmin= self.left_line.xmin ,xmax= self.right_line.xmin,
                                    translation=True)
            """
        if self.right_line.has_move:
            print "right has moved"
            self.right_line.update(mline= self.main_line,
                                  xmin= self.xmax,
                                  translation=True)
            self.left_line.update(mline= self.main_line,
                                   xmin=-1*self.xmax,
                                   translation=True)
            """
            self.top_line.update( xmin= self.left_line.xmax ,xmax= self.right_line.xmax,
                                  translation=True)
            self.bottom_line.update(xmin= self.left_line.xmin ,xmax= self.right_line.xmin,
                                    translation=True)
            """
            
        """   
        if self.bottom_line.has_move:
            print "bottom has moved"
            self.bottom_line.update(translation=True)
            self.top_line.update(ymin= -1*self.bottom_line.ymin,
                                 ymax =-1*self.bottom_line.ymax,
                                 translation=True)
            self.left_line.update( ymin= self.bottom_line.ymin ,ymax= self.top_line.ymax,
                                   translation=True)
            self.right_line.update(ymin= self.bottom_line.ymin,ymax= self.top_line.ymax,
                                   translation=True)
            
        if self.top_line.has_move:
            print "top has moved"
            self.top_line.update(mline= self.main_line,translation=True)
            self.bottom_line.update(ymin= -1*self.top_line.ymin,
                                    ymax=-1*self.top_line.ymax,
                                    translation=True )
            self.left_line.update(ymin= self.bottom_line.ymin ,ymax= self.top_line.ymax,
                                  translation=True)
            self.right_line.update(ymin= self.bottom_line.ymin ,ymax= self.top_line.ymax,
                                   translation=True)
        """
    
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
    def __init__(self,base,axes,color='black', zorder=5, y=0.5,
                 xmin=0.0,xmax=0.5,
                 theta2= math.pi/3 ):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        
        self.y= y
        self.save_y = y 
        
        self.xmin = xmin
        self.save_xmin = xmin
        self.xmax = xmax
        self.save_xmax = xmax
        
        self.theta2 = theta2
        
        self.clickx=self.xmin
        self.clicky=self.y
        self.clickxf=self.xmin
        self.clickyf=self.y
        self.deltax=0
        self.deltay=0
        
        x1= self.xmin*math.cos(self.theta2)- self.y*math.sin(self.theta2)
        self.ymin= self.xmin*math.sin(self.theta2)+ self.y*math.sin(self.theta2)
        
        x2= self.xmax*math.cos(self.theta2)- self.y*math.sin(self.theta2)
        self.ymax= self.xmax*math.sin(self.theta2)+ self.y*math.sin(self.theta2)
        #print "x1, y1", x1, y1, x2,y2
        self.line = self.axes.plot([x1,x2],[self.ymin,self.ymax],
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
    def onClick(self, ev):
        """
        Prepare to move the artist.  Calls save() to preserve the state for
        later restore().
        """
        self.clickx,self.clicky = ev.xdata,ev.ydata
        print "onclick",self.clickx,self.clicky
        
       
        #self.save(ev)
        return True   
    def get_radius(self):
        
        return 0
   
    def update(self,xmin=None, xmax=None,ymin=None,ymax=None, mline=None,translation=False):
        """
        Draw the new roughness on the graph.
        """
        #print "update main line", self.has_move
        
        if translation :
            self.deltax = self.clickxf- self.clickx
            self.deltay = self.clickyf-self.clicky
            
            self.xmin= self.xmin +self.deltax
            self.xmax=self.xmax+self.deltax
            self.ymin= self.ymin +self.deltay
            self.ymax=self.ymax+self.deltay
            
            if xmin !=None:
                self.xmin=xmin
            if xmax !=None:
                self.xmax=xmax
            if ymin !=None:
                self.ymin = ymin
            if ymax !=None:
                self.ymax = ymax
            self.line.set(xdata=[self.xmin, self.xmax],
                          ydata=[self.ymin, self.ymax])
        if mline !=None:
            self.theta2= mline.theta
            
            x1= self.xmin*math.cos(self.theta2)- self.y*math.sin(self.theta2)
            y1= self.xmin*math.sin(self.theta2)+ self.y*math.sin(self.theta2)
        
            x2= self.xmax*math.cos(self.theta2)- self.y*math.sin(self.theta2)
            y2= self.xmax*math.sin(self.theta2)+ self.y*math.sin(self.theta2)
            
            self.line.set(xdata=[x1,x2], ydata=[y1,y2]) 
            print x1,x2,y1,y2
           
        #else:
        #    self.line.set(xdata=[self.xmin,self.xmax], ydata=[self.y,self.y])
     
        
        
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
        self.clickxf,self.clickyf = ev.xdata,ev.ydata
        print "move end ",self.clickxf,self.clickyf
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
        """
        a=(1,1)
        transform = self.base.connect._hasclick.artist.get_transform()
        print "transform", self.base.connect.rotation_matrix(angle=math.pi/4, direction=(1, 0, 0), point=a)
        """
        
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
        self.save_xmin= xmin
        self.R_width=xmax
        self.save_xmax=xmax
        self.ymin=ymin
        self.save_ymin= ymin
        self.ymax=ymax
        self.save_ymax= ymax
        self.theta2= theta2
        self.mline= mline
        """
        x1= self.xmin*math.cos(self.theta2)- self.y*math.sin(self.theta2)
        self.ymin= self.xmin*math.sin(self.theta2)+ self.y*math.sin(self.theta2)
        
        x2= self.xmax*math.cos(self.theta2)- self.y*math.sin(self.theta2)
        self.ymax= self.xmax*math.sin(self.theta2)+ self.y*math.sin(self.theta2)
        """
        self.detax=0
        self.deltay=0
        
        self.clickx=0
        self.clicky=0
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
   
    #def onClick(self, ev):
    #    """
        #Prepare to move the artist.  Calls save() to preserve the state for
        #later restore().
        #"""
    #    self.clickx,self.clicky = ev.xdata,ev.ydata
    #    print "onclick",self.clickx,self.clicky
    #    self.save(ev)
    #    return True   
    
    def get_radius(self):
        return 0
    
    def update(self,xmin=None,xmax=None,ymin=None, ymax=None, mline=None,translation=False):
        """
        Draw the new roughness on the graph.
        """
        
        if xmin== None:
            xmin= self.L_width
        if xmax== None:
            xmax= self.R_width
        print "vertical line: xmin, xmax , ymin , ymax", xmin, self.mline.theta
        self.x1= self.mline.x1 + xmin*math.cos(math.pi/2 - self.mline.theta)
        self.x2= self.mline.x2 + xmin*math.cos(math.pi/2 - self.mline.theta)
        self.y1= self.mline.y1 - xmin*math.sin(math.pi/2 - self.mline.theta)
        self.y2= self.mline.y2 - xmin*math.sin(math.pi/2 - self.mline.theta)
        print "vertical line: main line  value ", self.mline.x1, self.mline.x2, self.mline.y1,self.mline.y2
        print "vertical line: new value ", self.x1, self.x2, self.y1,self.y2

        self.line.set(xdata=[self.x1,self.x2], ydata=[self.y1,self.y2])  
           
        if translation:
            self.deltax= self.clickxf +self.clickx
            self.deltay= self.clickyf +self.clicky
            print"translation deltax deltay", self.deltax, self.deltay
            self.x1=self.x1 +self.deltax
            self.y1=self.y1+ self.deltay
            self.x2=self.x2+ self.deltax
            self.y2=self.y2+self.deltay
            self.line.set(xdata=[self.x1,self.x2], ydata=[self.y1,self.y2]) 
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        #self.save_x= self.x
        self.save_xmin= self.x1
        self.save_xmax= self.x2
        self.save_ymin= self.y1
        self.save_ymax= self.y2
        
        self.base.freeze_axes()

    def moveend(self, ev):
        self.clickxf,self.clickyf = ev.xdata,ev.ydata
        print "move end ",self.clickxf,self.clickyf
        self.has_move=False
        self.base.moveend(ev)
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.xmin = self.save_xmin
        self.xmax = self.save_xmax
        self.ymin=self.save_ymin
        self.ymax=self.save_ymax
        
        
    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        
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
        self.x1= self.radius*math.cos(self.theta)
        self.y1= self.radius*math.sin(self.theta)
        self.x2= -1*self.radius*math.cos(self.theta)
        self.y2= -1*self.radius*math.sin(self.theta)
       
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
        self.x1= self.radius*math.cos(self.theta)
        self.y1= self.radius*math.sin(self.theta)
        self.x2= -1*self.radius*math.cos(self.theta)
        self.y2= -1*self.radius*math.sin(self.theta)
      
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
        



        