#TODO: the line slicer should listen to all 2DREFRESH events, get the data and slice it
#      before pushing a new 1D data update.

#
#TODO: NEED MAJOR REFACTOR
#

import math
import wx
#from copy import deepcopy 
# Debug printout
from sans.guiframe.events import NewPlotEvent
from sans.guiframe.events import StatusEvent
from sans.guiframe.events import SlicerParameterEvent
from sans.guiframe.events import EVT_SLICER_PARS
from BaseInteractor import _BaseInteractor
from sans.guiframe.dataFitting import Data1D

class AnnulusInteractor(_BaseInteractor):
    """
    Select an annulus through a 2D plot.
    This interactor is used to average 2D data  with the region 
    defined by 2 radius.
    this class is defined by 2 Ringinterators.
    """
    def __init__(self, base, axes, color='black', zorder=3):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.base = base
        self.qmax = min(math.fabs(self.base.data2D.xmax),
                        math.fabs(self.base.data2D.xmin))  #must be positive
        self.connect = self.base.connect
    
        ## Number of points on the plot
        self.nbins = 20
        #Cursor position of Rings (Left(-1) or Right(1))
        self.xmaxd = self.base.data2D.xmax
        self.xmind = self.base.data2D.xmin

        if (self.xmaxd + self.xmind) > 0:
            self.sign = 1
        else:
            self.sign = -1
        # Inner circle
        self.inner_circle = RingInteractor(self, self.base.subplot,
                                            zorder=zorder,
                                            r=self.qmax/2.0, sign=self.sign)
        self.inner_circle.qmax = self.qmax
        self.outer_circle = RingInteractor(self, self.base.subplot,
                                           zorder=zorder+1, r=self.qmax/1.8,
                                           sign=self.sign)
        self.outer_circle.qmax = self.qmax * 1.2
        self.update()
        self._post_data()
        
        # Bind to slice parameter events
        self.base.Bind(EVT_SLICER_PARS, self._onEVT_SLICER_PARS)
        
    def _onEVT_SLICER_PARS(self, event):
        """
        receive an event containing parameters values to reset the slicer
        
        :param event: event of type SlicerParameterEvent with params as 
            attribute
            
        """
        wx.PostEvent(self.base,
                     StatusEvent(status="AnnulusSlicer._onEVT_SLICER_PARS"))
        event.Skip()
        if event.type == self.__class__.__name__:
            self.set_params(event.params)
            self.base.update()

    def set_layer(self, n):
        """
        Allow adding plot to the same panel
        
        :param n: the number of layer
        
        """
        self.layernum = n
        self.update()
        
    def clear(self):
        """
        Clear the slicer and all connected events related to this slicer
        """
        self.clear_markers()
        self.outer_circle.clear()
        self.inner_circle.clear()
        self.base.connect.clearall()
        self.base.Unbind(EVT_SLICER_PARS)
        
    def update(self):
        """
        Respond to changes in the model by recalculating the profiles and
        resetting the widgets.
        """
        # Update locations        
        self.inner_circle.update()
        self.outer_circle.update()
        
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.base.freeze_axes()
        self.inner_circle.save(ev)
        self.outer_circle.save(ev)

    def _post_data(self, nbins=None):
        """
        Uses annulus parameters to plot averaged data into 1D data.
        
        :param nbins: the number of points to plot 
        
        """
        #Data to average
        data = self.base.data2D
        # If we have no data, just return
        if data == None:
            return
        
        from sans.dataloader.manipulations import Ring
        rmin = min(math.fabs(self.inner_circle.get_radius()),
                  math.fabs(self.outer_circle.get_radius()))
        rmax = max(math.fabs(self.inner_circle.get_radius()),
                   math.fabs(self.outer_circle.get_radius()))
        #if the user does not specify the numbers of points to plot 
        # the default number will be nbins= 20
        if nbins == None:
            self.nbins = 20
        else:
            self.nbins = nbins
        ## create the data1D Q average of data2D    
        sect = Ring(r_min=rmin, r_max=rmax, nbins=self.nbins)
        sector = sect(self.base.data2D)
    
        if hasattr(sector, "dxl"):
            dxl = sector.dxl
        else:
            dxl = None
        if hasattr(sector, "dxw"):
            dxw = sector.dxw
        else:
            dxw = None
        new_plot = Data1D(x=(sector.x - math.pi) * 180/math.pi,
                          y=sector.y, dy=sector.dy)
        new_plot.dxl = dxl
        new_plot.dxw = dxw
        new_plot.name = "AnnulusPhi" +"("+ self.base.data2D.name+")"
        
        new_plot.source = self.base.data2D.source
        #new_plot.info=self.base.data2D.info
        new_plot.interactive = True
        new_plot.detector = self.base.data2D.detector
        # If the data file does not tell us what the axes are, just assume...
        new_plot.xaxis("\\rm{\phi}", 'degrees')
        new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")
        if hasattr(data, "scale") and data.scale == 'linear' and \
                self.base.data2D.name.count("Residuals") > 0:
            new_plot.ytransform = 'y'
            new_plot.yaxis("\\rm{Residuals} ", "/")

        new_plot.group_id = "AnnulusPhi" + self.base.data2D.name
        new_plot.id = "AnnulusPhi" + self.base.data2D.name
        new_plot.is_data= True
        new_plot.xtransform = "x"
        new_plot.ytransform = "y"
        self.base.parent.update_theory(data_id=data.id, theory=new_plot)
        wx.PostEvent(self.base.parent, NewPlotEvent(plot=new_plot,
                                                 title="AnnulusPhi"))
        
    def moveend(self, ev):
        """
        Called when any dragging motion ends.
        Post an event (type =SlicerParameterEvent)
        to plotter 2D with a copy  slicer parameters
        Call  _post_data method
        """
        self.base.thaw_axes()
        # Post parameters to plotter 2D
        event = SlicerParameterEvent()
        event.type = self.__class__.__name__
        event.params = self.get_params()
        wx.PostEvent(self.base, event)
        # create a 1D data plot
        #self._post_data()
            
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
        """
        Store a copy of values of parameters of the slicer into a dictionary.
        
        :return params: the dictionary created
        
        """
        params = {}
        params["inner_radius"] = math.fabs(self.inner_circle._inner_mouse_x)
        params["outer_radius"] = math.fabs(self.outer_circle._inner_mouse_x)
        params["nbins"] = self.nbins
        return params
    
    def set_params(self, params):
        """
        Receive a dictionary and reset the slicer with values contained 
        in the values of the dictionary.
        
        :param params: a dictionary containing name of slicer parameters and 
            values the user assigned to the slicer.
            
        """
        inner = math.fabs(params["inner_radius"])
        outer = math.fabs(params["outer_radius"])
        self.nbins = int(params["nbins"])
        ## Update the picture
        self.inner_circle.set_cursor(inner, self.inner_circle._inner_mouse_y)
        self.outer_circle.set_cursor(outer, self.outer_circle._inner_mouse_y)
        ## Post the data given the nbins entered by the user 
        self._post_data(self.nbins)
        
    def freeze_axes(self):
        """
        """
        self.base.freeze_axes()
        
    def thaw_axes(self):
        """
        """
        self.base.thaw_axes()

    def draw(self):
        """
        """
        self.base.draw()

        
class RingInteractor(_BaseInteractor):
    """
     Draw a ring Given a radius 
    """
    def __init__(self, base, axes, color='black', zorder=5, r=1.0, sign=1):
        """
        :param: the color of the line that defined the ring
        :param r: the radius of the ring
        :param sign: the direction of motion the the marker 
        
        """
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        # Current radius of the ring
        self._inner_mouse_x = r
        #Value of the center of the ring
        self._inner_mouse_y = 0
        # previous value of that radius
        self._inner_save_x  = r
        #Save value of the center of the ring
        self._inner_save_y  = 0
        #Class instantiating RingIterator class
        self.base = base
        #the direction of the motion of the marker
        self.sign = sign
        ## Create a marker 
        try:
            # Inner circle marker
            x_value = [self.sign * math.fabs(self._inner_mouse_x)]
            self.inner_marker = self.axes.plot(x_value,
                                               [0],
                                                linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          pickradius=5, label="pick", 
                                          zorder=zorder,
                                          visible=True)[0]
        except:
            x_value = [self.sign * math.fabs(self._inner_mouse_x)]
            self.inner_marker = self.axes.plot(x_value,
                                               [0], 
                                               linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          label="pick", 
                                          visible=True)[0]
            message  = "\nTHIS PROTOTYPE NEEDS THE LATEST"
            message += " VERSION OF MATPLOTLIB\n"
            message += "Get the SVN version that is at "
            message += " least as recent as June 1, 2007"
            
            owner = self.base.base.parent
            wx.PostEvent(owner, 
                         StatusEvent(status="AnnulusSlicer: %s" % message))
            
        # Draw a circle 
        [self.inner_circle] = self.axes.plot([], [],
                                      linestyle='-', marker='',
                                      color=self.color)
        # the number of points that make the ring line
        self.npts = 40
            
        self.connect_markers([self.inner_marker])
        self.update()

    def set_layer(self, n):
        """
        Allow adding plot to the same panel
         
        :param n: the number of layer
        
        """
        self.layernum = n
        self.update()
        
    def clear(self):
        """
        Clear the slicer and all connected events related to this slicer
        """
        self.clear_markers()
        try:
            self.inner_marker.remove()
            self.inner_circle.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]
        
    def get_radius(self):
        """
        :return self._inner_mouse_x: the current radius of the ring
        """
        return self._inner_mouse_x
        
    def update(self):
        """
        Draw the new roughness on the graph.
        """
        # Plot inner circle
        x = []
        y = []
        for i in range(self.npts):
            phi = 2.0 * math.pi / (self.npts - 1) * i
            
            xval = 1.0 * self._inner_mouse_x * math.cos(phi) 
            yval = 1.0 * self._inner_mouse_x * math.sin(phi) 
            
            x.append(xval)
            y.append(yval)
            
        self.inner_marker.set(xdata=[self.sign*math.fabs(self._inner_mouse_x)],
                              ydata=[0])
        self.inner_circle.set_data(x, y)        

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self._inner_save_x = self._inner_mouse_x
        self._inner_save_y = self._inner_mouse_y
        self.base.freeze_axes()

    def moveend(self, ev):
        """
        Called after a dragging motion
        """
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
        self._inner_mouse_x = x
        self._inner_mouse_y = y
        self.base.base.update()
        
    def set_cursor(self, x, y):
        """
        draw the ring given x, y value 
        """
        self.move(x, y, None)
        self.update()
        
        
    def get_params(self):
        """
        Store a copy of values of parameters of the slicer into a dictionary.
        
        :return params: the dictionary created
        
        """
        params = {}
        params["radius"] = math.fabs(self._inner_mouse_x)
        return params
    
    def set_params(self, params):
        """
        Receive a dictionary and reset the slicer with values contained 
        in the values of the dictionary.
        
        :param params: a dictionary containing name of slicer parameters and 
            values the user assigned to the slicer.
            
        """
        x = params["radius"] 
        self.set_cursor(x, self._inner_mouse_y)
        
class CircularMask(_BaseInteractor):
    """
     Draw a ring Given a radius 
    """
    def __init__(self, base, axes, color='grey', zorder=3, side=None):
        """
        
        :param: the color of the line that defined the ring
        :param r: the radius of the ring
        :param sign: the direction of motion the the marker 
        
        """
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.base = base
        self.is_inside = side
        self.qmax = min(math.fabs(self.base.data.xmax),
                        math.fabs(self.base.data.xmin))  #must be positive
        self.connect = self.base.connect
        
        #Cursor position of Rings (Left(-1) or Right(1))
        self.xmaxd = self.base.data.xmax
        self.xmind = self.base.data.xmin

        if (self.xmaxd + self.xmind) > 0:
            self.sign = 1
        else:
            self.sign = -1
        # Inner circle
        self.outer_circle = RingInteractor(self, self.base.subplot, 'blue',
                                            zorder=zorder+1, r=self.qmax/1.8,
                                            sign=self.sign)
        self.outer_circle.qmax = self.qmax * 1.2
        self.update()
        self._post_data()
        
        # Bind to slice parameter events
        #self.base.Bind(EVT_SLICER_PARS, self._onEVT_SLICER_PARS)
        
    def _onEVT_SLICER_PARS(self, event):
        """
        receive an event containing parameters values to reset the slicer
        
        :param event: event of type SlicerParameterEvent with params as 
            attribute
        """
        wx.PostEvent(self.base,
                     StatusEvent(status="AnnulusSlicer._onEVT_SLICER_PARS"))
        event.Skip()
        if event.type == self.__class__.__name__:
            self.set_params(event.params)
            self.base.update()

    def set_layer(self, n):
        """
        Allow adding plot to the same panel
         
        :param n: the number of layer
        
        """
        self.layernum = n
        self.update()
        
    def clear(self):
        """
        Clear the slicer and all connected events related to this slicer
        """
        self.clear_markers()
        self.outer_circle.clear()
        self.base.connect.clearall()
        #self.base.Unbind(EVT_SLICER_PARS)
        
    def update(self):
        """
        Respond to changes in the model by recalculating the profiles and
        resetting the widgets.
        """
        # Update locations        
        self.outer_circle.update()
        #if self.is_inside != None:
        out = self._post_data()
        return out

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.base.freeze_axes()
        self.outer_circle.save(ev)

    def _post_data(self):
        """
        Uses annulus parameters to plot averaged data into 1D data.
        
        :param nbins: the number of points to plot 
        
        """
        #Data to average
        data = self.base.data
              
        # If we have no data, just return
        if data == None:
            return
        mask = data.mask  
        from sans.dataloader.manipulations import Ringcut
    
        rmin = 0
        rmax = math.fabs(self.outer_circle.get_radius())

        ## create the data1D Q average of data2D    
        mask = Ringcut(r_min=rmin, r_max= rmax)

        if self.is_inside:
            out = (mask(data) == False)
        else:
            out = (mask(data))
        #self.base.data.mask=out
        return out                    

         
    def moveend(self, ev):
        """
        Called when any dragging motion ends.
        Post an event (type =SlicerParameterEvent)
        to plotter 2D with a copy  slicer parameters
        Call  _post_data method
        """
        self.base.thaw_axes()
        # create a 1D data plot
        self._post_data()
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.outer_circle.restore()

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        pass
        
    def set_cursor(self, x, y):
        pass
        
    def get_params(self):
        """
        Store a copy of values of parameters of the slicer into a dictionary.
        
        :return params: the dictionary created
        
        """
        params = {}
        params["outer_radius"] = math.fabs(self.outer_circle._inner_mouse_x)
        return params
    
    def set_params(self, params):
        """
        Receive a dictionary and reset the slicer with values contained 
        in the values of the dictionary.
        
        :param params: a dictionary containing name of slicer parameters and 
            values the user assigned to the slicer.
        """
        outer = math.fabs(params["outer_radius"] )
        ## Update the picture
        self.outer_circle.set_cursor(outer, self.outer_circle._inner_mouse_y)
        ## Post the data given the nbins entered by the user 
        self._post_data()
        
    def freeze_axes(self):
        self.base.freeze_axes()
        
    def thaw_axes(self):
        self.base.thaw_axes()

    def draw(self):
        self.base.update()
              