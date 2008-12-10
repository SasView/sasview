#TODO: the line slicer should listen to all 2DREFRESH events, get the data and slice it
#      before pushing a new 1D data update.

#
#TODO: NEED MAJOR REFACTOR
#


# Debug printout

from BaseInteractor import _BaseInteractor
from copy import deepcopy
import math

from sans.guicomm.events import NewPlotEvent, StatusEvent
import SlicerParameters
import wx

class SectorInteractor(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=3):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.qmax = self.base.qmax
        self.connect = self.base.connect
        
        ## Number of points on the plot
        self.nbins = 20
        theta1=math.pi/8
        theta2=math.pi/2
        r1=self.qmax/2.0
        r2=self.qmax/1.8
        # Inner circle
        from Arc import ArcInteractor
        self.inner_circle = ArcInteractor(self, self.base.subplot, zorder=zorder, r=self.qmax/2.0,theta1= theta1,
                                           theta2=theta2)
        self.inner_circle.qmax = self.base.qmax
        self.outer_circle = ArcInteractor(self, self.base.subplot, zorder=zorder+1, r=self.qmax/1.8,theta1= theta1,
                                           theta2=theta2)
        self.outer_circle.qmax = self.base.qmax*1.2
        #self.outer_circle.set_cursor(self.base.qmax/1.8, 0)
        from Edge import RadiusInteractor
        self.inner_radius= RadiusInteractor(self, self.base.subplot, zorder=zorder+1,
                                             arc1=self.inner_circle,
                                             arc2=self.outer_circle,
                                            theta=math.pi/8)
        self.outer_radius= RadiusInteractor(self, self.base.subplot, zorder=zorder+1,
                                             arc1=self.inner_circle,
                                             arc2=self.outer_circle,
                                            theta=math.pi/2)
        self.update()
        self._post_data()
        
        # Bind to slice parameter events
        #self.base.parent.Bind(SlicerParameters.EVT_SLICER_PARS, self._onEVT_SLICER_PARS)


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
        self.outer_circle.clear()
        self.inner_circle.clear()
        #self.base.connect.disconnect()
        #self.base.parent.Unbind(SlicerParameters.EVT_SLICER_PARS)
        
    def update(self):
        """
        Respond to changes in the model by recalculating the profiles and
        resetting the widgets.
        """
        # Update locations        
        self.inner_circle.update()
        self.outer_circle.update()
        r1=self.inner_circle.get_radius()
        r2=self.outer_circle.get_radius()
        #print"annulus update",r1, r2
        if self.inner_radius.update(r1,r2)==1:
            #print "went here"
            self.inner_circle.update(theta1=self.inner_radius.get_radius(), theta2=None)
            self.outer_circle.update(theta1=self.inner_radius.get_radius(),theta2=None)
        
        if self.outer_radius.update(r1,r2)==1:#self.outer_circle.update(self.outer_radius.get_radius())
             self.inner_circle.update(theta1=None, theta2=self.outer_radius.get_radius())
             self.outer_circle.update(theta1=None,theta2=self.outer_radius.get_radius())
    

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.base.freeze_axes()
        self.inner_circle.save(ev)
        self.outer_circle.save(ev)

    def _post_data(self):
        """ post data"""
        rmin=self.inner_circle.get_radius()
        rmax=self.outer_circle.get_radius()
        phimin=self.inner_radius.get_radius()
        phimax=self.outer_radius.get_radius()
        from DataLoader.manipulations import SectorQ, SectorPhi
        sectQ = SectorQ(r_min=rmin, r_max=rmax, phi_min=phimin, phi_max=phimax)
        sectorQ = sectQ(self.base.data2D)
        
        sectPhi = SectorPhi(r_min=rmin, r_max=rmax, phi_min=phimin, phi_max=phimax)
        sectorPhi = sectPhi(self.base.data2D)
        from sans.guiframe.dataFitting import Data1D
        if hasattr(sectorQ,"dxl"):
            dxl= sectorQ.dxl
        else:
            dxl= None
        if hasattr(sectorQ,"dxw"):
            dxw= sectorQ.dxw
        else:
            dxw= None
            
        new_plot1 = Data1D(x=sectorQ.x,y=sectorQ.y,dy=sectorQ.dy,dxl=dxl,dxw=dxw)
        new_plot1.name = "SectorQ ("+ self.base.data2D.name+")"
        if hasattr(sectorPhi,"dxl"):
            dxl= sectorPhi.dxl
        else:
            dxl= None
        if hasattr(sectorPhi,"dxw"):
            dxw= sectorPhi.dxw
        else:
            dxw= None
        new_plot2 = Data1D(x=sectorPhi.x,y=sectorPhi.y,dy=sectorPhi.dy,dxl=dxl,dxw=dxw)
        new_plot2.name = "SectorPhi ("+ self.base.data2D.name+")"
        self.plot_data( new_plot1)
        self.plot_data( new_plot2)
        
        
    def plot_data(self, new_plot): 
        """
             plot a new data 1D corresponding to the phi and Q sector average
        """
        new_plot.source=self.base.data2D.source
        new_plot.info=self.base.data2D.info
        new_plot.interactive = True
        #print "loader output.detector",output.source
        new_plot.detector =self.base.data2D.detector
        # If the data file does not tell us what the axes are, just assume...
        new_plot.xaxis(self.base.data2D._xaxis,self.base.data2D._xunit)
        new_plot.yaxis(self.base.data2D._yaxis,self.base.data2D._yunit)
        new_plot.group_id = "sector"+self.base.data2D.name
        wx.PostEvent(self.base.parent, NewPlotEvent(plot=new_plot, title=new_plot.name))
        
        
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
        #self.outer_circle.restore()

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
        params["phi_min"] = self.inner_radious.get_radious()
        params["phi_max"] = self.inner_radious.get_radious()
        params["nbins"] = self.nbins
        return params
    
    def set_params(self, params):
        
        inner = params["inner_radius"] 
        outer = params["outer_radius"] 
        self.nbins = int(params["nbins"])
        self.inner_circle.set_cursor(inner, self.inner_circle._inner_mouse_y)
        self.outer_circle.set_cursor(outer, self.outer_circle._inner_mouse_y)
        self._post_data()
        
    def freeze_axes(self):
        self.base.freeze_axes()
        
    def thaw_axes(self):
        self.base.thaw_axes()

    def draw(self):
        self.base.draw()

    