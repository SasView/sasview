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

class BoxSum(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=3, x_min=0.008, x_max=0.008, y_min=0.0025, y_max=0.0025):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.qmax = self.base.data2D.xmax
        self.connect = self.base.connect
        
        self.xmin= -1* x_min
        self.ymin= -1* y_min
        self.xmax= x_max
        self.ymax=  y_max
        # center of the figure
        self.center_x= 0.002
        self.center_y= 0.003
       
        ## Number of points on the plot
        self.nbins = 20
        self.count=0
        self.error=0
        self.has_move= False
    
        self.horizontal_lines= Horizontal_DoubleLine(self, self.base.subplot,color='blue',
                                                      zorder=zorder,
                                    y= self.ymax,
                                    x= self.xmax,
                                    center_x= self.center_x,
                                    center_y= self.center_y)
        self.horizontal_lines.qmax = self.qmax
        
        self.vertical_lines= Vertical_DoubleLine(self, self.base.subplot,color='black',
                                                      zorder=zorder,
                                    y= self.ymax,
                                    x= self.xmax,
                                    center_x= self.center_x,
                                    center_y= self.center_y)
        self.vertical_lines.qmax = self.qmax
        self.center= PointInteractor(self, self.base.subplot,color='grey',
                                                      zorder=zorder,
                                    center_x= self.center_x,
                                    center_y= self.center_y)
      
            
        self.connect_markers([])
                      
        self.update()
        self._post_data()
        
        # Bind to slice parameter events
        self.base.parent.Bind(SlicerParameters.EVT_SLICER_PARS, self._onEVT_SLICER_PARS)


    def _onEVT_SLICER_PARS(self, event):
        #printEVT("AnnulusSlicer._onEVT_SLICER_PARS")
        event.Skip()
        if event.type == self.__class__.__name__:
            self.set_params(event.params)
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
        self.horizontal_lines.clear()
        self.vertical_lines.clear()
        self.center.clear()
        
        #self.base.connect.disconnect()
        self.base.parent.Unbind(SlicerParameters.EVT_SLICER_PARS)
        
    def update(self):
        """
        Respond to changes in the model by recalculating the profiles and
        resetting the widgets.
        """
        if self.center.has_move:
            print "center has move"
            self.center.update()
            self.horizontal_lines.update( center= self.center)
            self.vertical_lines.update( center= self.center)
            
        if self.horizontal_lines.has_move:
            print "top has moved"
            self.horizontal_lines.update()
            self.vertical_lines.update(y1=self.horizontal_lines.y1,
                                       y2=self.horizontal_lines.y2,
                                       height= self.horizontal_lines.half_height )
        if self.vertical_lines.has_move:
            print "right has moved"
            self.vertical_lines.update()
            self.horizontal_lines.update(x1=self.vertical_lines.x1,
                                         x2=self.vertical_lines.x2,
                                         width=self.vertical_lines.half_width)
            

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.base.freeze_axes()
        self.horizontal_lines.save(ev)
        self.vertical_lines.save(ev)
        self.center.save(ev)
        
    def _post_data(self):
        # Compute data
        print 
        """
        data = self.base.data2D
        from DataLoader.manipulations import  Boxavg
        radius = math.sqrt(math.pow(self.qmax,2)+math.pow(self.qmax,2))
        x_min= self.left_line.x 
        x_max= self.right_line.x 
        y_min= self.bottom_line.y
        y_max= self.top_line.y
        box =  Boxavg (x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)
        self.count, self.error = box(self.base.data2D)
        print "count, error",self.count, self.error
        """
                                       
    def moveend(self, ev):
        self.base.thaw_axes()
        
        # Post paramters
        event = SlicerParameters.SlicerParameterEvent()
        event.type = self.__class__.__name__
        print "event type boxsum: ", event.type
        event.params = self.get_params()
        
        wx.PostEvent(self.base.parent, event)
      
        self._post_data()
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.horizontal_lines.restore()
        self.vertical_lines.restore()
        self.center.restore()
    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        pass
    
    def set_cursor(self, x, y):
        pass
        
    def get_params(self):
        params = {}
       
        params["x"] = math.fabs(self.horizontal_lines.half_width)
        params["y"] = math.fabs(self.vertical_lines.half_height) 
        
        params["center_x"] = self.center.x
        params["center_y"] =self.center.y
        params["count"] = self.count
        params["errors"]= self.error
        
        return params
    
    
    def get_result(self):
        """
            return the result of box summation
        """
        result={}
        result["count"] = self.count
        result["error"] = self.error
        return result
        
        
    def set_params(self, params):
        
        x_max = math.fabs(params["x"] )
        y_max = math.fabs(params["y"] )
        
        self.center_x=params["center_x"] 
        self.center_y=params["center_y"]
        
        self.center.update(center_x=self.center_x,center_y=self.center_y)
       
        self.horizontal_lines.update(center= self.center,
                                     width=x_max,
                                     height=y_max)
        
        
        self.vertical_lines.update(center= self.center,
                                    width=x_max,
                                    height=y_max)
        
        self._post_data()
        
        
        
    def freeze_axes(self):
        self.base.freeze_axes()
        
    def thaw_axes(self):
        self.base.thaw_axes()

    def draw(self):
        self.base.draw()
class PointInteractor(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=5,
                 center_x= 0.0,
                 center_y= 0.0):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        # center
        self.x = center_x
        self.y = center_y
        
        self.save_x = center_x
        self.save_y = center_y
         
        
        try:
            self.center_marker = self.axes.plot([self.x],[self.y], linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          pickradius=5, label="pick", 
                                          zorder=zorder, # Prefer this to other lines
                                          visible=True)[0]
        except:
            self.center_marker = self.axes.plot([self.x],[self.y], linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          label="pick", 
                                          visible=True)[0]
            message  = "\nTHIS PROTOTYPE NEEDS THE LATEST VERSION OF MATPLOTLIB\n"
            message += "Get the SVN version that is at least as recent as June 1, 2007"
            
            #raise "Version error", message
            
        # line
        self.center = self.axes.plot([self.x],[self.y],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
    
        self.npts = 30
        self.has_move=False    
        self.connect_markers([self.center_marker])
        self.update()


    def set_layer(self, n):
        self.layernum = n
        self.update()
        
    def clear(self):
        self.clear_markers()
        try:
            self.center.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]
        
    def get_radius(self):
        
        return 0
   
    def update(self, center_x=None,center_y=None):
        """
        Draw the new roughness on the graph.
        """
        if center_x !=None: self.x= center_x
        if center_y !=None: self.y= center_y
   
        self.center_marker.set(xdata=[self.x], ydata=[self.y])
        self.center.set(xdata=[self.x], ydata=[self.y])
        
        
        
        
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_x= self.x
        self.save_y= self.y
        
        self.base.freeze_axes()

    def moveend(self, ev):
        
        self.has_move=False
        self.base.moveend(ev)
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.y= self.save_y
        self.x= self.save_x
        
    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.x= x
        self.y= y
       
        self.has_move=True
        self.base.base.update()
        
    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()
        
        
    def get_params(self):
        params = {}
        params["x"] = self.x
        params["y"] = self.y
        
        return params
    
    def set_params(self, params):
        center_x = params["x"] 
        center_y = params["y"] 
        self.update(center_x=center_x,center_y=center_y)
       
        
class Vertical_DoubleLine(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=5, x=0.5,y=0.5,
                 center_x= 0.0,
                 center_y= 0.0):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        # center
        self.center_x = center_x
        self.center_y = center_y
        
       
        
        self.y1     = y + self.center_y
        self.save_y1= self.y1
        
        delta= self.y1- self.center_y
        self.y2= self.center_y - delta
        self.save_y2= self.y2
        
        self.x1      = x + self.center_x
        self.save_x1 = self.x1
         
        delta= self.x1- self.center_x
        self.x2= self.center_x - delta
        self.save_x2 = self.x2
        
        self.color=color
        
        self.half_height= math.fabs(y)
        self.save_half_height= math.fabs(y)
        
        self.half_width= math.fabs(x)
        self.save_half_width=math.fabs(x)
        
        try:
            self.right_marker = self.axes.plot([self.x1],[0], linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          pickradius=5, label="pick", 
                                          zorder=zorder, # Prefer this to other lines
                                          visible=True)[0]
        except:
            self.right_marker = self.axes.plot([self.x1],[0], linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          label="pick", 
                                          visible=True)[0]
            message  = "\nTHIS PROTOTYPE NEEDS THE LATEST VERSION OF MATPLOTLIB\n"
            message += "Get the SVN version that is at least as recent as June 1, 2007"
            
            #raise "Version error", message
            
        # line
        self.right_line = self.axes.plot([self.x1,self.x1],[self.y1,self.y2],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
        self.left_line = self.axes.plot([self.x2,self.x2],[self.y1,self.y2],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
    
        self.npts = 30
        self.has_move=False    
        self.connect_markers([self.right_marker])
        self.update()


    def set_layer(self, n):
        self.layernum = n
        self.update()
        
    def clear(self):
        self.clear_markers()
        try:
            self.right_line.remove()
            self.left_line.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]
        
    def get_radius(self):
        
        return 0
   
    def update(self,x1=None,x2=None, y1=None,y2=None,width=None, height=None, center=None):
        """
        Draw the new roughness on the graph.
        """
        if width!=None:
            self.half_width= width
        if height!=None:
            self.half_height= height
        if center!=None:
            self.center_x= center.x
            self.center_y= center.y
            
            self.x1 = self.half_width + self.center_x
            self.x2= -self.half_width + self.center_x
            
            self.y1 = self.half_height + self.center_y
            self.y2= -self.half_height + self.center_y
         
            self.right_marker.set(xdata=[self.x1],ydata=[self.center_y])
            self.right_line.set(xdata=[self.x1,self.x1], ydata=[self.y1,self.y2])
            self.left_line.set(xdata=[self.x2,self.x2], ydata=[self.y1,self.y2])
            return 
        if x1 !=None: 
            self.x1= x1
        if x2 !=None: 
            self.x2= x2
        if y1 !=None: 
            self.y1= y1
        if y2 !=None: 
            self.y2= y2
        
       
       
        self.right_marker.set(xdata=[self.x1],ydata=[self.center_y])
        self.right_line.set(xdata=[self.x1,self.x1], ydata=[self.y1,self.y2])
        self.left_line.set(xdata=[self.x2,self.x2], ydata=[self.y1,self.y2])
        
        
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_x2= self.x2
        self.save_y2= self.y2
        
        self.save_x1= self.x1
        self.save_y1= self.y1
        
        self.save_half_height= self.half_height
        self.save_half_width =  self.half_width
        self.base.freeze_axes()

    def moveend(self, ev):
        
        self.has_move=False
        self.base.moveend(ev)
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.y2= self.save_y2
        self.x2= self.save_x2
        
        self.y1= self.save_y1
        self.x1= self.save_x1
        
        self.half_height= self.save_half_height
        self.half_width= self.save_half_width
       
    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.x1= x
        delta= self.x1- self.center_x
        self.x2= self.center_x - delta
        
        self.half_width= math.fabs(self.x1)-self.center_x
        self.has_move=True
        self.base.base.update()
        
    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()
        
        
    def get_params(self):
        params = {}
        params["x"] = self.x1
        params["y"] = self.y1
        
        return params
    
    def set_params(self, params):
        x = params["x"] 
        y = params["y"] 
        self.update(x=x, y=y, center_x=None,center_y=None)

class Horizontal_DoubleLine(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=5, x=0.5,y=0.5,
                 center_x= 0.0,
                 center_y= 0.0):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        # center
        self.center_x = center_x
        self.center_y = center_y
        
        self.y1     = y + self.center_y
        self.save_y1= self.y1
        
        delta= self.y1- self.center_y
        self.y2=  self.center_y - delta
        self.save_y2= self.y2
        
        self.x1      = x + self.center_x
        self.save_x1 = self.x1
        
        delta= self.x1- self.center_x
        self.x2=  self.center_x - delta
        self.save_x2 = self.x2
        
        self.color=color
        
        self.half_height= math.fabs(y)
        self.save_half_height= math.fabs(y)
        
        self.half_width= math.fabs(x)
        self.save_half_width=math.fabs(x)
    
        try:
            self.top_marker = self.axes.plot([0],[self.y1], linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          pickradius=5, label="pick", 
                                          zorder=zorder, # Prefer this to other lines
                                          visible=True)[0]
        except:
            self.top_marker = self.axes.plot([0],[self.y1], linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          label="pick", 
                                          visible=True)[0]
            message  = "\nTHIS PROTOTYPE NEEDS THE LATEST VERSION OF MATPLOTLIB\n"
            message += "Get the SVN version that is at least as recent as June 1, 2007"
            
            #raise "Version error", message
            
        # line
        self.top_line = self.axes.plot([self.x1,-self.x1],[self.y1,self.y1],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
        self.bottom_line = self.axes.plot([self.x1,-self.x1],[self.y2,self.y2],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
    
        self.npts = 30
        self.has_move=False    
        self.connect_markers([self.top_marker])
        self.update()


    def set_layer(self, n):
        self.layernum = n
        self.update()
        
    def clear(self):
        self.clear_markers()
        try:
            self.bottom_line.remove()
            self.top_line.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]
        
    def get_radius(self):
        
        return 0
   
    def update(self,x1=None,x2=None, y1=None,y2=None,width=None,height=None, center=None):
        """
        Draw the new roughness on the graph.
        """
        if width!=None:
            self.half_width= width
        if height!=None:
            self.half_height= height
        if center!=None:
            self.center_x= center.x
            self.center_y= center.y
            
            self.x1 = self.half_width + self.center_x
            self.x2= -self.half_width + self.center_x
            
            self.y1 = self.half_height + self.center_y
            self.y2= -self.half_height + self.center_y
            
            self.top_marker.set(xdata=[self.center_x],ydata=[self.y1])
            self.top_line.set(xdata=[self.x1,self.x2], ydata=[self.y1,self.y1])
            self.bottom_line.set(xdata=[self.x1,self.x2], ydata=[self.y2,self.y2])
            return 
        if x1 !=None: 
            self.x1= x1
        if x2 !=None: 
            self.x2= x2
        if y1 !=None: 
            self.y1= y1
        if y2 !=None: 
            self.y2= y2
       
             
        self.top_marker.set(xdata=[self.center_x],ydata=[self.y1])
        self.top_line.set(xdata=[self.x1,self.x2], ydata=[self.y1,self.y1])
        self.bottom_line.set(xdata=[self.x1,self.x2], ydata=[self.y2,self.y2])
       
        
        
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_x2= self.x2
        self.save_y2= self.y2
        
        self.save_x1= self.x1
        self.save_y1= self.y1
        
        self.save_half_height= self.half_height
        self.save_half_width =  self.half_width
        self.base.freeze_axes()


    def moveend(self, ev):
        
        self.has_move=False
        self.base.moveend(ev)
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.y2= self.save_y2
        self.x2= self.save_x2
        
        self.y1= self.save_y1
        self.x1= self.save_x1
        self.half_height= self.save_half_height
        self.half_width= self.save_half_width
        
    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.y1= y
        delta= self.y1- self.center_y
        self.y2=  self.center_y - delta
        self.half_height=  math.fabs(self.y1)-self.center_y
        self.has_move=True
        self.base.base.update()
        
    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()
        
        
    def get_params(self):
        params = {}
        params["x"] = self.x
        params["y"] = self.y
        
        return params
    
    def set_params(self, params):
        x = params["x"] 
        y = params["y"] 
        self.update(x=x, y=y, center_x=None,center_y=None)
         