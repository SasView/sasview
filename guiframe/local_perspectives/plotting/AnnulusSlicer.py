#TODO: the line slicer should listen to all 2DREFRESH events, get the data and slice it
#      before pushing a new 1D data update.

#
#TODO: NEED MAJOR REFACTOR
#

import math
import wx
from copy import deepcopy 
# Debug printout
from sans.guicomm.events import NewPlotEvent, StatusEvent,SlicerParameterEvent,EVT_SLICER_PARS
from BaseInteractor import _BaseInteractor


class AnnulusInteractor(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=3):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.base= base
        self.qmax = min(math.fabs(self.base.data2D.xmax),math.fabs(self.base.data2D.xmin))  #must be positive
        self.connect = self.base.connect
        

        ## Number of points on the plot
        self.nbins = 20
        
        #Cursor position of Rings (Left(-1) or Right(1))
        self.xmaxd=self.base.data2D.xmax
        self.xmind=self.base.data2D.xmin

        #self.sign=1
        
        if (self.xmaxd+self.xmind)>0:
            self.sign=1
        else:
            self.sign=-1
                 
        # Inner circle
        self.inner_circle = RingInteractor(self, self.base.subplot, zorder=zorder, r=self.qmax/2.0,sign=self.sign)
        self.inner_circle.qmax = self.qmax
        self.outer_circle = RingInteractor(self, self.base.subplot, zorder=zorder+1, r=self.qmax/1.8,sign=self.sign)
        self.outer_circle.qmax = self.qmax*1.2
        #self.outer_circle.set_cursor(self.base.qmax/1.8, 0)
        
                      
        self.update()
        self._post_data()
        
        # Bind to slice parameter events
        self.base.parent.Bind(EVT_SLICER_PARS, self._onEVT_SLICER_PARS)
        

    def _onEVT_SLICER_PARS(self, event):
        wx.PostEvent(self.base.parent, StatusEvent(status="AnnulusSlicer._onEVT_SLICER_PARS"))
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
        self.outer_circle.clear()
        self.inner_circle.clear()
        #self.base.connect.disconnect()
        self.base.parent.Unbind(EVT_SLICER_PARS)
        
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

    def _post_data(self,nbins=None):
         # Compute data
        data = self.base.data2D
        # If we have no data, just return
        if data == None:
            return
        
        from DataLoader.manipulations import SectorPhi
        radius = self.qmax#math.sqrt(math.pow(self.qmax,2)+math.pow(self.qmax,2))
        rmin= math.fabs(self.inner_circle.get_radius())
        rmax = math.fabs(self.outer_circle.get_radius())
        phi_min=-math.pi
        phi_max=math.pi
        phimi=phi_min+math.pi
        phima=phi_max+math.pi
        sect = SectorPhi(r_min=rmin , r_max= rmax, phi_min=phimi, phi_max=phima)
        if nbins!=None:
            sect.nbins = nbins
        
        sector = sect(self.base.data2D)
        
        from sans.guiframe.dataFitting import Data1D
        if hasattr(sector,"dxl"):
            dxl= sector.dxl
        else:
            dxl= None
        if hasattr(sector,"dxw"):
            dxw= sector.dxw
        else:
            dxw= None
       
        new_plot = Data1D(x=sector.x,y=sector.y,dy=sector.dy,dxl=dxl,dxw=dxw)
        new_plot.name = "SectorPhi" +"("+ self.base.data2D.name+")"
        
       
        
        new_plot.source=self.base.data2D.source
        #new_plot.info=self.base.data2D.info
        new_plot.interactive = True
        #print "loader output.detector",output.source
        new_plot.detector =self.base.data2D.detector
        # If the data file does not tell us what the axes are, just assume...
        new_plot.xaxis("\\rm{\phi}", 'rad')
        new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
        new_plot.group_id = "SectorPhi"+self.base.data2D.name
        new_plot.xtransform="x"
        new_plot.ytransform="y"
        wx.PostEvent(self.base.parent, NewPlotEvent(plot=new_plot,
                                                 title="SectorPhi" ))
        
         
        
        
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
        params["inner_radius"] = self.inner_circle._inner_mouse_x
        params["outer_radius"] = self.outer_circle._inner_mouse_x
        params["nbins"] = self.nbins
        return params
    
    def set_params(self, params):
        
        inner = params["inner_radius"] 
        outer = params["outer_radius"] 
        self.nbins = int(params["nbins"])
        self.inner_circle.set_cursor(inner, self.inner_circle._inner_mouse_y)
        self.outer_circle.set_cursor(outer, self.outer_circle._inner_mouse_y)
        self._post_data(self.nbins)
        
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
    def __init__(self,base,axes,color='black', zorder=5, r=1.0,sign=1):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self._inner_mouse_x = r
        self._inner_mouse_y = 0
        self._inner_save_x  = r
        self._inner_save_y  = 0
        self.scale = 10.0
        self.base= base
        self.sign=sign
         
        
        print "sign",self.sign,self.sign*math.fabs(self._inner_mouse_x)
                                                    
        try:
            # Inner circle marker
            self.inner_marker = self.axes.plot([self.sign*math.fabs(self._inner_mouse_x)],[0], linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          pickradius=5, label="pick", 
                                          zorder=zorder, # Prefer this to other lines
                                          visible=True)[0]
        except:
            self.inner_marker = self.axes.plot([self.sign*math.fabs(self._inner_mouse_x)],[0], linestyle='',
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
        self.npts = 40
            
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
            
        self.inner_marker.set(xdata=[self.sign*math.fabs(self._inner_mouse_x)],ydata=[0])
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
        params["radius"] = math.fabs(self._inner_mouse_x)
        return params
    
    def set_params(self, params):

        x = params["radius"] 
        self.set_cursor(x, self._inner_mouse_y)
        
        