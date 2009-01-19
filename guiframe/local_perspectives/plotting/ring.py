#TODO: the line slicer should listen to all 2DREFRESH events, get the data and slice it
#      before pushing a new 1D data update.

#
#TODO: NEED MAJOR REFACTOR
#


# Debug printout
from config import printEVT
from BaseInteractor import _BaseInteractor
from copy import deepcopy
import math

from Plotter1D import AddPlotEvent
import SlicerParameters
import wx

class AnnulusInteractor(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=3):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.qmax = self.base.data2D.xmax
        self.connect = self.base.connect
        
        ## Number of points on the plot
        self.nbins = 20

        # Inner circle
        self.inner_circle = RingInteractor(self, self.base.subplot, zorder=zorder, r=self.qmax/2.0)
        self.inner_circle.qmax = self.qmax
      
        #self.outer_circle.set_cursor(self.base.qmax/1.8, 0)
        
                      
        self.update()
        self._post_data()
        
        # Bind to slice parameter events
        self.base.parent.Bind(SlicerParameters.EVT_SLICER_PARS, self._onEVT_SLICER_PARS)


    def _onEVT_SLICER_PARS(self, event):
        printEVT("AnnulusSlicer._onEVT_SLICER_PARS")
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
       
        self.inner_circle.clear()
        #self.base.connect.disconnect()
        self.base.parent.Unbind(SlicerParameters.EVT_SLICER_PARS)
        
    def update(self):
        """
        Respond to changes in the model by recalculating the profiles and
        resetting the widgets.
        """
        # Update locations        
        self.inner_circle.update()
       
        
        
    def get_data(self, image, x, y):
        """ 
            Return a 1D vector corresponding to the slice
            @param image: data matrix
            @param x: x matrix
            @param y: y matrix
        """
        # If we have no data, just return
        if image == None:
            return        
        
        nbins = self.nbins
        
        data_x = nbins*[0]
        data_y = nbins*[0]
        counts = nbins*[0]
        length = len(image)
        print "length x , y , image", len(x), len(y), length
        
        for i_x in range(length):
            for i_y in range(length):
                        
                q = math.sqrt(x[i_x]*x[i_x] + y[i_y]*y[i_y])
                if (q>self.inner_circle._inner_mouse_x \
                    and q<self.outer_circle._inner_mouse_x) \
                    or (q<self.inner_circle._inner_mouse_x \
                    and q>self.outer_circle._inner_mouse_x):
                            
                    i_bin = int(math.ceil(nbins*(math.atan2(y[i_y], x[i_x])+math.pi)/(2.0*math.pi)) - 1)
                    
                    
                    #data_y[i_bin] += math.exp(image[i_x][i_y])
                    data_y[i_bin] += image[i_y][i_x]
                    counts[i_bin] += 1.0
                    
        for i in range(nbins):
            data_x[i] = (1.0*i+0.5)*2.0*math.pi/nbins
            if counts[i]>0:
                data_y[i] = data_y[i]/counts[i]
        
        return data_x, data_y

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.base.freeze_axes()
        self.inner_circle.save(ev)
       

    def _post_data(self):
        # Compute data
        data = self.base.get_corrected_data()
        # If we have no data, just return
        if data == None:
            return

        data_x, data_y = self.get_data(data, self.base.x, self.base.y)
        
        name = "Ring"
        if hasattr(self.base, "name"):
            name += " %s" % self.base.name
        
        wx.PostEvent(self.base.parent, AddPlotEvent(name=name,
                                               x = data_x,
                                               y = data_y,
                                               qmin = self.inner_circle._inner_mouse_x,
                                               qmax = self.outer_circle._inner_mouse_x,
                                               yscale = 'log',
                                               variable = 'ANGLE',
                                               ylabel = "\\rm{Intensity} ",
                                               yunits = "cm^{-1}",
                                               xlabel = "\\rm{\phi}",
                                               xunits = "rad",
                                               parent = self.base.__class__.__name__))
                                               
        
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
        self.inner_circle.restore()
      

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        pass
        
    def set_cursor(self, x, y):
        pass
        
    def get_params(self):
        params = {}
        params["inner_radius"] = self.inner_circle._inner_mouse_x
       
        params["nbins"] = self.nbins
        return params
    
    def set_params(self, params):
        
        inner = params["inner_radius"] 
        
        self.nbins = int(params["nbins"])
        self.inner_circle.set_cursor(inner, self.inner_circle._inner_mouse_y)
       
        self._post_data()
        
    def freeze_axes(self):
        self.base.freeze_axes()
        
    def thaw_axes(self):
        self.base.thaw_axes()

    def draw(self):
        self.base.draw()

        
class RingInteractor(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=5, r=1.0):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self._inner_mouse_x = r
        self._inner_mouse_y = 0
        self._inner_save_x  = r
        self._inner_save_y  = 0
        self.scale = 10.0
        
        try:
            # Inner circle marker
            self.inner_marker = self.axes.plot([self._inner_mouse_x],[0], linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          pickradius=5, label="pick", 
                                          zorder=zorder, # Prefer this to other lines
                                          visible=True)[0]
        except:
            self.inner_marker = self.axes.plot([self._inner_mouse_x],[0], linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          label="pick", 
                                          visible=True)[0]
            message  = "\nTHIS PROTOTYPE NEEDS THE LATEST VERSION OF MATPLOTLIB\n"
            message += "Get the SVN version that is at least as recent as June 1, 2007"
            
            #raise "Version error", message
            
        # Inner circle

           
        [self.inner_circle] = self.axes.plot([],[],
                                      linestyle='-', marker='',
                                      color=self.color)
        self.npts = 20
            
        self.connect_markers([self.inner_marker])
        self.update()

    def set_layer(self, n):
        self.layernum = n
        self.update()
        
    def clear(self):
        self.clear_markers()
        try:
            self.inner_marker.remove()
            self.inner_circle.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]
        
        
        
    def get_radius(self):
        return self._inner_mouse_x
        
    def update(self):
        """
        Draw the new roughness on the graph.
        """
        # Plot inner circle
        x = []
        y = []
        for i in range(self.npts):
            phi = 2.0*math.pi/(self.npts-1)*i
            
            xval = 1.0*self._inner_mouse_x*math.cos(phi) 
            yval = 1.0*self._inner_mouse_x*math.sin(phi) 
            
            x.append(xval)
            y.append(yval)
        
        self.inner_marker.set(xdata=[self._inner_mouse_x],ydata=[0])
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
        self.move(x, y, None)
        self.update()
        
        
    def get_params(self):
        params = {}
        params["radius"] = self._inner_mouse_x
        return params
    
    def set_params(self, params):

        x = params["radius"] 
        self.set_cursor(x, self._inner_mouse_y)
        
        