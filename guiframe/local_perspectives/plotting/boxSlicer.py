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

from sans.guicomm.events import NewPlotEvent, StatusEvent
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
        self.qmax = self.base.data2D.xmax
        self.connect = self.base.connect
        self.x= x_max
        self.y= y_max
                
        self.theta2= math.pi/3
        ## Number of points on the plot
        self.nbins = 30
        self.count=0
        self.error=0
        self.averager=None
        self.left_line = VerticalLine(self, self.base.subplot,color='blue', 
                                      zorder=zorder,
                                        ymin= -self.y , 
                                        ymax= self.y ,
                                        xmin= -self.x,
                                        xmax= -self.x)
        self.left_line.qmax = self.qmax
        
        self.right_line= VerticalLine(self, self.base.subplot,color='black', 
                                      zorder=zorder,
                                     ymin= -self.y , 
                                     ymax= self.y,
                                     xmin= self.x,
                                     xmax= self.x)
        self.right_line.qmax = self.qmax
        
        self.top_line= HorizontalLine(self, self.base.subplot,color='green', 
                                      zorder=zorder,
                                      xmin= -self.x,
                                      xmax= self.x,
                                      ymin= self.y,
                                      ymax= self.y)
        self.top_line.qmax= self.qmax
        
        self.bottom_line= HorizontalLine(self, self.base.subplot,color='gray', 
                                      zorder=zorder,
                                      xmin= -self.x,
                                      xmax= self.x,
                                      ymin= -self.y,
                                      ymax= -self.y)
        self.bottom_line.qmax= self.qmax
        
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
        self.averager=None
        self.clear_markers()
        self.left_line.clear()
        self.right_line.clear()
        self.top_line.clear()
        self.bottom_line.clear()
        #self.base.connect.disconnect()
        self.base.parent.Unbind(SlicerParameters.EVT_SLICER_PARS)
        
    def update(self):
        """
        Respond to changes in the model by recalculating the profiles and
        resetting the widgets.
        """
        
        if self.top_line.has_move:
            print"top has moved"
            self.top_line.update()
            self.bottom_line.update(ymin= -self.top_line.y1,
                                    ymax= -self.top_line.y2)
            self.left_line.update(ymin= -self.top_line.y1,
                                    ymax= -self.top_line.y2)
            self.right_line.update(ymin= -self.top_line.y1,
                                    ymax= -self.top_line.y2)
           
        if self.bottom_line.has_move:
            print "bottom has move"
            self.bottom_line.update()
            self.top_line.update(ymin= -self.bottom_line.y1,
                                    ymax= -self.bottom_line.y2)
            self.left_line.update(ymin= self.bottom_line.y1,
                                    ymax= self.top_line.y1)
            self.right_line.update(ymin= self.bottom_line.y1,
                                    ymax=self.top_line.y1)
           
        if self.left_line.has_move:
           
            self.left_line.update()
            self.right_line.update(xmin = - self.left_line.x1,
                                   xmax = - self.left_line.x1)
            self.bottom_line.update(xmin=  self.left_line.x1,
                                     xmax= self.right_line.x1)
            self.top_line.update(xmin= self.left_line.x1,
                                    xmax= self.right_line.x1)
           
        if self.right_line.has_move:
           
            self.right_line.update()
            self.left_line.update(xmin = -self.right_line.x1,
                                   xmax = -self.right_line.x1)
            
            self.bottom_line.update(xmin= self.left_line.x1,
                                 xmax= self.right_line.x1)
            
            self.top_line.update(xmin= self.left_line.x1,
                                    xmax= self.right_line.x1)
               
            
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.base.freeze_axes()
        self.left_line.save(ev)
        self.right_line.save(ev)
        self.top_line.save(ev)
        self.bottom_line.save(ev)
    def _post_data(self):
        pass
        
    
    def post_data(self,new_slab=None , nbins=None):
        """ post data averaging in Q"""
        x_min= min(self.left_line.x1, self.right_line.x1)
        x_max= max(self.left_line.x1, self.right_line.x1)
        
        y_min= min(self.top_line.y1, self.bottom_line.y1)
        y_max= max(self.top_line.y1, self.bottom_line.y1)  
        
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
        new_plot.info=self.base.data2D.info
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
        
        
    def _post_data(self):
        # Compute data
        data = self.base.data2D
        from DataLoader.manipulations import  Boxavg
        radius = math.sqrt(math.pow(self.qmax,2)+math.pow(self.qmax,2))
        self.x= math.fabs(self.right_line.x1)
        self.y= math.fabs(self.top_line.y1 )
       
        box =  Boxavg (x_min=-self.x, x_max=self.x, y_min=-self.y, y_max=self.y)
       
        self.count, self.error= box(self.base.data2D)
        
        #print "post data"
              
                                       
    def moveend(self, ev):
        self.base.thaw_axes()
        
        # Post paramters
        event = SlicerParameters.SlicerParameterEvent()
        event.type = self.__class__.__name__
        event.params = self.get_params()
        wx.PostEvent(self.base.parent, event)

        self._post_data()
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.left_line.restore()
        self.right_line.restore()
        self.top_line.restore()
        self.bottom_line.restore()

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        pass
        
    def set_cursor(self, x, y):
        pass
        
    def get_params(self):
        params = {}
        params["x_max"]= math.fabs(self.right_line.x1)
        params["y_max"]= math.fabs(self.top_line.y1)
        params["nbins"]= self.nbins
        params["errors"] = self.error
        params["count"]= self.count
        return params
    
    def set_params(self, params):
        
        self.x = float(math.fabs(params["x_max"]))
        self.y = float(math.fabs(params["y_max"] ))
        self.nbins=params["nbins"]
        self.left_line.update(xmin= -1*self.x,
                              xmax = -1*self.x,
                              ymin= -self.y,
                              ymax=  self.y, 
                              )
        self.right_line.update(xmin= self.x,
                              xmax = self.x,
                              ymin= -self.y,
                              ymax=  self.y, 
                              )
        self.top_line.update(xmin= -1*self.x,
                             xmax= self.x,
                             ymin= self.y,
                             ymax= self.y)
        self.bottom_line.update(xmin= -1*self.x,
                                 xmax= self.x,
                                 ymin= -1*self.y,
                                 ymax= -1*self.y)
       
        self.post_data( nbins=None)
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
                 xmin=0.0,xmax=0.5):
        
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
        self.line = self.axes.plot([self.x1,-self.x1],
                                   [self.y1,self.y2],
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
   
    def update(self,xmin=None, xmax=None,ymin=None,ymax=None, mline=None,translation=False):
        """
        Draw the new roughness on the graph.
        """
        if xmin !=None:
            self.x1 = xmin
        if ymin !=None:
            self.y1 = ymin
        self.line.set(xdata=[self.x1,-self.x1],
                       ydata=[self.y1,self.y1])
    
        
        
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
        print "horizontal move x y "
        self.y1= y
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
                 ymax=0.5,xmin=-0.5,xmax=0.5
                 ):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        
        self.x1= xmax
        self.x2= xmin
        self.y1= ymax
        self.y2= ymin
        self.line = self.axes.plot([self.x1,self.x2],[self.y1,self.y2],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
      
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

   
        if xmin!=None:
            self.x1=xmin
        if ymin!=None:
            self.y1=ymin
        self.line.set(xdata=[self.x1,self.x1],
                       ydata=[self.y1,-self.y1]) 
        
    
        
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
        self.x1= x
        
        
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
        
        