#TODO: the line slicer should listen to all 2DREFRESH events, get the data and slice it
#      before pushing a new 1D data update.

#
#TODO: NEED MAJOR REFACTOR
#


# Debug printout
#from config import printEVT
from BaseInteractor import _BaseInteractor
from copy import deepcopy
import math, numpy

from sans.guicomm.events import NewPlotEvent, StatusEvent,SlicerParameterEvent,EVT_SLICER_PARS
import SlicerParameters
import wx


class BoxInteractor(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=3):
        _BaseInteractor.__init__(self, base, axes, color=color)
        
        self.markers = []
        self.axes = axes
        
        self.connect = self.base.connect
        
        self.x= 0.5*min(math.fabs(self.base.data2D.xmax),math.fabs( self.base.data2D.xmin))
        self.y= 0.5*min(math.fabs(self.base.data2D.xmax),math.fabs( self.base.data2D.xmin))        
        
        self.qmax = max(self.base.data2D.xmax,self.base.data2D.xmin,
                        self.base.data2D.ymax,self.base.data2D.ymin )   
        
        ## Number of points on the plot
        self.nbins = 30
        self.count=0
        self.error=0
        self.averager=None
        
        self.vertical_lines = VerticalLines(self, self.base.subplot,color='blue', 
                                      zorder=zorder,
                                        y= self.y ,
                                        x= self.x)
        self.vertical_lines.qmax = self.qmax
       
        self.horizontal_lines= HorizontalLines(self, self.base.subplot,color='green', 
                                      zorder=zorder,
                                      x= self.x,
                                      y= self.y)
        self.horizontal_lines.qmax= self.qmax
        
      
        
        self.update()
        self._post_data()
        
        # Bind to slice parameter events
        self.base.Bind(EVT_SLICER_PARS, self._onEVT_SLICER_PARS)


    def _onEVT_SLICER_PARS(self, event):
        wx.PostEvent(self.base.parent, StatusEvent(status="BoxSlicer._onEVT_SLICER_PARS"))
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
        self.averager=None
        self.clear_markers()
        self.horizontal_lines.clear()
        self.vertical_lines.clear()
        self.base.connect.clearall()
        
        self.base.Unbind(EVT_SLICER_PARS)
        
    def update(self):
        """
        Respond to changes in the model by recalculating the profiles and
        resetting the widgets.
        """
        if self.horizontal_lines.has_move:
            #print "top has moved"
            self.horizontal_lines.update()
            self.vertical_lines.update(y=self.horizontal_lines.y)
        if self.vertical_lines.has_move:
            #print "right has moved"
            self.vertical_lines.update()
            self.horizontal_lines.update(x=self.vertical_lines.x)
            
               
            
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.base.freeze_axes()
        self.vertical_lines.save(ev)
        self.horizontal_lines.save(ev)
    
    def _post_data(self):
        pass
        
    
    def post_data(self,new_slab=None , nbins=None):
        """ post data averaging in Q"""
        x_min= -1*math.fabs(self.vertical_lines.x)
        x_max= math.fabs(self.vertical_lines.x)
        
        y_min= -1*math.fabs(self.horizontal_lines.y)
        y_max= math.fabs(self.horizontal_lines.y)
        
        if nbins !=None:
            self.nbins
        if self.averager==None:
            if new_slab ==None:
                raise ValueError,"post data:cannot average , averager is empty"
            self.averager= new_slab
        bin_width= (x_max + math.fabs(x_min))/self.nbins
        
        box = self.averager( x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
                         bin_width=bin_width)
        
        boxavg = box(self.base.data2D)
        
        from sans.guiframe.dataFitting import Data1D
        if hasattr(boxavg,"dxl"):
            dxl= boxavg.dxl
        else:
            dxl= None
        if hasattr(boxavg,"dxw"):
            dxw=boxavg.dxw
        else:
            dxw= None
       
        new_plot = Data1D(x=boxavg.x,y=boxavg.y,dy=boxavg.dy,dxl=dxl,dxw=dxw)
        new_plot.name = str(self.averager.__name__) +"("+ self.base.data2D.name+")"
        
       

        new_plot.source=self.base.data2D.source
        new_plot.interactive = True
        #print "loader output.detector",output.source
        new_plot.detector =self.base.data2D.detector
        # If the data file does not tell us what the axes are, just assume...
        new_plot.xaxis("\\rm{Q}", 'rad')
        new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
        new_plot.group_id = str(self.averager.__name__)+self.base.data2D.name
        new_plot.id = str(self.averager.__name__)
        wx.PostEvent(self.base.parent, NewPlotEvent(plot=new_plot,
                                                 title=str(self.averager.__name__) ))
    
              
                                       
    def moveend(self, ev):
        self.base.thaw_axes()
        
        # Post paramters
        event = SlicerParameterEvent()
        event.type = self.__class__.__name__
        event.params = self.get_params()
        wx.PostEvent(self.base.parent, event)

        self._post_data()
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.horizontal_lines.restore()
        self.vertical_lines.restore()
       

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        pass
        
    def set_cursor(self, x, y):
        pass
        
    def get_params(self):
        params = {}
        params["x_max"]= math.fabs(self.vertical_lines.x)
        params["y_max"]= math.fabs(self.horizontal_lines.y)
        params["nbins"]= self.nbins
      
        return params
    
    def set_params(self, params):
        
        self.x = float(math.fabs(params["x_max"]))
        self.y = float(math.fabs(params["y_max"] ))
        self.nbins=params["nbins"]
        
        self.horizontal_lines.update(x= self.x, y=  self.y)
        self.vertical_lines.update(x= self.x, y=  self.y)
        self.post_data( nbins=None)
        
        
    def freeze_axes(self):
        self.base.freeze_axes()
        
    def thaw_axes(self):
        self.base.thaw_axes()

    def draw(self):
        self.base.draw()

class HorizontalLines(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=5,x=0.5, y=0.5):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.x= x
        self.save_x= x
        
        self.y= y
        self.save_y= y
       
        try:
            # Inner circle marker
            self.inner_marker = self.axes.plot([0],[self.y], linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          pickradius=5, label="pick", 
                                          zorder=zorder, # Prefer this to other lines
                                          visible=True)[0]
        except:
            self.inner_marker = self.axes.plot([0],[self.y], linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          label="pick", 
                                          visible=True)[0]
            message  = "\nTHIS PROTOTYPE NEEDS THE LATEST VERSION OF MATPLOTLIB\n"
            message += "Get the SVN version that is at least as recent as June 1, 2007"
            
        self.top_line = self.axes.plot([self.x,-self.x],
                                   [self.y,self.y],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
        self.bottom_line = self.axes.plot([self.x,-self.x],
                                   [-self.y,-self.y],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
        
        self.has_move=False
        self.connect_markers([self.top_line, self.inner_marker])
        self.update()

    def set_layer(self, n):
        self.layernum = n
        self.update()
        
    def clear(self):
        self.clear_markers()
        try:
            self.inner_marker.remove()
            self.top_line.remove() 
            self.bottom_line.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]
   
   
    def update(self,x=None,y=None):
        """
        Draw the new roughness on the graph.
        """
        if x!=None:
            self.x = numpy.sign(self.x)*math.fabs(x)
        if y !=None:
            self.y = numpy.sign(self.y)*math.fabs(y)
        self.inner_marker.set(xdata=[0],ydata=[self.y])
        
        self.top_line.set(xdata=[self.x,-self.x],
                       ydata=[self.y,self.y])
        self.bottom_line.set(xdata=[self.x,-self.x],
                       ydata=[-self.y, -self.y])
        
        
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
        self.x = self.save_x
        self.y = self.save_y
        

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        #print "horizontal move x y "
        self.y= y
        self.has_move=True
        self.base.base.update()
        
  
        
  
    
class VerticalLines(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black',zorder=5,x=0.5, y=0.5):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        
        self.x= math.fabs(x)
        self.save_x= self.x
        self.y= math.fabs(y)
        self.save_y= y
        
        try:
            # Inner circle marker
            self.inner_marker = self.axes.plot([self.x],[0], linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          pickradius=5, label="pick", 
                                          zorder=zorder, # Prefer this to other lines
                                          visible=True)[0]
        except:
            self.inner_marker = self.axes.plot([self.x],[0], linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          label="pick", 
                                          visible=True)[0]
            message  = "\nTHIS PROTOTYPE NEEDS THE LATEST VERSION OF MATPLOTLIB\n"
            message += "Get the SVN version that is at least as recent as June 1, 2007"
            
        self.right_line = self.axes.plot([self.x,self.x],[self.y,-self.y],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
        self.left_line = self.axes.plot([-self.x,-self.x],[self.y,-self.y],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
      
        self.has_move=False
        self.connect_markers([self.right_line, self.inner_marker])
        self.update()

    def set_layer(self, n):
        self.layernum = n
        self.update()
        
    def clear(self):
        self.clear_markers()
        try:
            self.inner_marker.remove()
            self.left_line.remove()
            self.right_line.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]

    def update(self,x=None,y=None):
        """
        Draw the new roughness on the graph.
        """

        if x!=None:
            self.x = numpy.sign(self.x)*math.fabs(x)
        if y !=None:
            self.y = numpy.sign(self.y)*math.fabs(y)
            
        self.inner_marker.set(xdata=[self.x],ydata=[0]) 
        self.left_line.set(xdata=[-self.x,-self.x],
                       ydata=[self.y,-self.y]) 
        self.right_line.set(xdata=[self.x,self.x],
                       ydata=[self.y,-self.y]) 
    
        
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
        self.x = self.save_x
        self.y = self.save_y
      
        
    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.has_move=True
        self.x= x
        self.base.base.update()
        
   
        

class BoxInteractorX(BoxInteractor):
    def __init__(self,base,axes,color='black', zorder=3):
        BoxInteractor.__init__(self, base, axes, color=color)
        self.base=base
        self._post_data()
    def _post_data(self):
        from DataLoader.manipulations import SlabX
        self.post_data(SlabX )   
        

class BoxInteractorY(BoxInteractor):
    def __init__(self,base,axes,color='black', zorder=3):
        BoxInteractor.__init__(self, base, axes, color=color)
        self.base=base
        self._post_data()
    def _post_data(self):
        from DataLoader.manipulations import SlabY
        self.post_data(SlabY )   
        
        