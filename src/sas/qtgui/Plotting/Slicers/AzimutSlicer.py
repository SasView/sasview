# TODO: the line slicer should listen to all 2DREFRESH events, get the data and slice it
#       before pushing a new 1D data update.
#
# TODO: NEED MAJOR REFACTOR
#
import math
from .BaseInteractor import BaseInteractor

class SectorInteractor(BaseInteractor):
    """
    Select an annulus through a 2D plot
    """
    def __init__(self, base, axes, color='black', zorder=3):
        """
        """
        BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.qmax = self.base.data2D.xmax
        self.connect = self.base.connect

        # # Number of points on the plot
        self.nbins = 20
        theta1 = 2 * math.pi / 3
        theta2 = -2 * math.pi / 3

        # Inner circle
        from .Arc import ArcInteractor
        self.inner_circle = ArcInteractor(self, self.base.subplot,
                                          zorder=zorder,
                                          r=self.qmax / 2.0,
                                          theta1=theta1,
                                          theta2=theta2)
        self.inner_circle.qmax = self.qmax
        self.outer_circle = ArcInteractor(self, self.base.subplot,
                                          zorder=zorder + 1,
                                          r=self.qmax / 1.8,
                                          theta1=theta1,
                                          theta2=theta2)
        self.outer_circle.qmax = self.qmax * 1.2
        # self.outer_circle.set_cursor(self.base.qmax/1.8, 0)
        from Edge import RadiusInteractor
        self.right_edge = RadiusInteractor(self, self.base.subplot,
                                           zorder=zorder + 1,
                                           arc1=self.inner_circle,
                                           arc2=self.outer_circle,
                                           theta=theta1)
        self.left_edge = RadiusInteractor(self, self.base.subplot,
                                          zorder=zorder + 1,
                                          arc1=self.inner_circle,
                                          arc2=self.outer_circle,
                                          theta=theta2)
        self.update()
        self._post_data()

    def set_layer(self, n):
        """
        """
        self.layernum = n
        self.update()

    def clear(self):
        """
        """
        self.clear_markers()
        self.outer_circle.clear()
        self.inner_circle.clear()
        self.right_edge.clear()
        self.left_edge.clear()

    def update(self):
        """
        Respond to changes in the model by recalculating the profiles and
        resetting the widgets.
        """
        # Update locations
        if self.inner_circle.has_move:
            # print "inner circle has moved"
            self.inner_circle.update()
            r1 = self.inner_circle.get_radius()
            r2 = self.outer_circle.get_radius()
            self.right_edge.update(r1, r2)
            self.left_edge.update(r1, r2)
        if self.outer_circle.has_move:
            # print "outer circle has moved"
            self.outer_circle.update()
            r1 = self.inner_circle.get_radius()
            r2 = self.outer_circle.get_radius()
            self.left_edge.update(r1, r2)
            self.right_edge.update(r1, r2)
        if self.right_edge.has_move:
            # print "right edge has moved"
            self.right_edge.update()
            self.inner_circle.update(theta1=self.right_edge.get_angle(),
                                     theta2=None)
            self.outer_circle.update(theta1=self.right_edge.get_angle(),
                                     theta2=None)
        if  self.left_edge.has_move:
            # print "left Edge has moved"
            self.left_edge.update()
            self.inner_circle.update(theta1=None,
                                     theta2=self.left_edge.get_angle())
            self.outer_circle.update(theta1=None,
                                     theta2=self.left_edge.get_angle())

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.base.freeze_axes()
        self.inner_circle.save(ev)
        self.outer_circle.save(ev)
        self.right_edge.save(ev)
        self.left_edge.save(ev)

    def _post_data(self):
        pass

    def post_data(self, new_sector):
        """ post data averaging in Q"""
        if self.inner_circle.get_radius() < self.outer_circle.get_radius():
            rmin = self.inner_circle.get_radius()
            rmax = self.outer_circle.get_radius()
        else:
            rmin = self.outer_circle.get_radius()
            rmax = self.inner_circle.get_radius()
        if self.right_edge.get_angle() < self.left_edge.get_angle():
            phimin = self.right_edge.get_angle()
            phimax = self.left_edge.get_angle()
        else:
            phimin = self.left_edge.get_angle()
            phimax = self.right_edge.get_angle()
        # print "phimin, phimax, rmin ,rmax",math.degrees(phimin),
        # math.degrees(phimax), rmin ,rmax
        # from sas.sascalc.dataloader.manipulations import SectorQ

        sect = new_sector(r_min=rmin, r_max=rmax,
                          phi_min=phimin, phi_max=phimax)
        sector = sect(self.base.data2D)

        from sas.sasgui.guiframe.dataFitting import Data1D
        if hasattr(sector, "dxl"):
            dxl = sector.dxl
        else:
            dxl = None
        if hasattr(sector, "dxw"):
            dxw = sector.dxw
        else:
            dxw = None
        new_plot = Data1D(x=sector.x, y=sector.y, dy=sector.dy,
                          dxl=dxl, dxw=dxw)
        new_plot.name = str(new_sector.__name__) + \
                        "(" + self.base.data2D.name + ")"
        new_plot.source = self.base.data2D.source
        new_plot.interactive = True
        # print "loader output.detector",output.source
        new_plot.detector = self.base.data2D.detector
        # If the data file does not tell us what the axes are, just assume...
        new_plot.xaxis("\\rm{Q}", 'rad')
        new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")
        new_plot.group_id = str(new_sector.__name__) + self.base.data2D.name

    def validate(self, param_name, param_value):
        """
        Test the proposed new value "value" for row "row" of parameters
        """
        # Here, always return true
        return True

    def moveend(self, ev):
        #TODO: why is this empty?
        pass

    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.inner_circle.restore()
        self.outer_circle.restore()
        self.right_edge.restore()
        self.left_edge.restore()

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        pass

    def set_cursor(self, x, y):
        """
        """
        pass

    def get_params(self):
        """
        """
        params = {}
        params["r_min"] = self.inner_circle.get_radius()
        params["r_max"] = self.outer_circle.get_radius()
        params["phi_min"] = self.right_edge.get_angle()
        params["phi_max"] = self.left_edge.get_angle()
        params["nbins"] = self.nbins
        return params

    def set_params(self, params):
        """
        """
        # print "setparams on main slicer ",params
        inner = params["r_min"]
        outer = params["r_max"]
        phi_min = params["phi_min"]
        phi_max = params["phi_max"]
        self.nbins = int(params["nbins"])

        self.inner_circle.set_cursor(inner, phi_min, phi_max, self.nbins)
        self.outer_circle.set_cursor(outer, phi_min, phi_max, self.nbins)
        self.right_edge.set_cursor(inner, outer, phi_min)
        self.left_edge.set_cursor(inner, outer, phi_max)
        self._post_data()

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

class SectorInteractorQ(SectorInteractor):
    """
    """
    def __init__(self, base, axes, color='black', zorder=3):
        """
        """
        SectorInteractor.__init__(self, base, axes, color=color)
        self.base = base
        self._post_data()

    def _post_data(self):
        """
        """
        from sas.sascalc.dataloader.manipulations import SectorQ
        self.post_data(SectorQ)


class SectorInteractorPhi(SectorInteractor):
    """
    """
    def __init__(self, base, axes, color='black', zorder=3):
        """
        """
        SectorInteractor.__init__(self, base, axes, color=color)
        self.base = base
        self._post_data()

    def _post_data(self):
        """
        """
        from sas.sascalc.dataloader.manipulations import SectorPhi
        self.post_data(SectorPhi)

