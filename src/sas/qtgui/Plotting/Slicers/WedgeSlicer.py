import numpy as np

from sas.qtgui.Plotting.Slicers.BaseInteractor import BaseInteractor
from sas.qtgui.Plotting.SlicerModel import SlicerModel
from sas.qtgui.Plotting.PlotterData import Data1D
import sas.qtgui.Utilities.GuiUtils as GuiUtils

from sas.qtgui.Plotting.Slicers.ArcInteractor import ArcInteractor
from sas.qtgui.Plotting.Slicers.RadiusInteractor import RadiusInteractor
from sas.qtgui.Plotting.Slicers.SectorSlicer import LineInteractor

class WedgeInteractor(BaseInteractor, SlicerModel):
    """
    This WedgeInteractor is a cross between the SectorInteractor and the
    AnnulusInteractor. It plots a data1D average of a wedge area defined in a
    Data2D object, in either the Q direction or the Phi direction. The data1D
    averaging itself is performed in sasdata by manipulations.py.

    This class uses three other classes, ArcInteractor (in ArcInteractor.py),
    RadiusInteractor (in RadiusInteractor.py), and LineInteractor
    (in SectorSlicer.py), to define a wedge area contained
    between two radial lines running through (0,0) defining the left and right
    edges of the wedge (similar to the sector), and two rings at Q1 and Q2
    (similar to the annulus). The wedge is centred on the line defined by
    LineInteractor, which the radial lines move symmetrically around.
    This class is itself subclassed by SectorInteractorPhi and
    SectorInteractorQ which define the direction of the averaging.
    SectorInteractorPhi averages all Q points at constant Phi (as for the
    AnnulusSlicer) and SectorInteractorQ averages all phi points at constant Q
    (as for the SectorSlicer).
    """
    def __init__(self, base, axes, item=None, color='black', zorder=3):

        BaseInteractor.__init__(self, base, axes, color=color)
        SlicerModel.__init__(self)

        self.markers = []
        self.axes = axes
        self._item = item
        self.qmax = max(self.data.xmax, np.fabs(self.data.xmin),
                        self.data.ymax, np.fabs(self.data.ymin))
        self.dqmin = min(np.fabs(self.data.qx_data))
        self.connect = self.base.connect

        # Number of points on the plot
        self.nbins = 100
        # Radius of the inner edge of the wedge
        self.r1 = self.qmax / 2.0
        # Radius of the outer edge of the wedge
        self.r2 = self.qmax / 1.6
        # Angle of the central line
        self.theta = np.pi / 3
        # Angle between the central line and the radial lines either side of it
        self.phi = np.pi / 8
        # reference of the current data averager
        self.averager = None

        self.inner_arc = ArcInteractor(self, self.axes, color='black',
                                       zorder=zorder, r=self.r1,
                                       theta=self.theta, phi=self.phi)
        self.inner_arc.qmax = self.qmax
        self.outer_arc = ArcInteractor(self, self.axes, color='black',
                                       zorder=zorder + 1, r=self.r2,
                                       theta=self.theta, phi=self.phi)
        self.outer_arc.qmax = self.qmax * 1.2
        self.radial_lines = RadiusInteractor(self, self.axes, color='black',
                                             zorder=zorder + 1,
                                             r1=self.r1, r2=self.r2,
                                             theta=self.theta, phi=self.phi)
        self.radial_lines.qmax = self.qmax * 1.2
        self.central_line = LineInteractor(self, self.axes, color='black',
                                           zorder=zorder, r=self.qmax * 1.414,
                                           theta=self.theta, half_length=True)
        self.central_line.qmax = self.qmax * 1.414
        self.update()
        self.draw()
        self._post_data()
        self.setModelFromParams()

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
        self.averager = None
        self.clear_markers()
        self.outer_arc.clear()
        self.inner_arc.clear()
        self.radial_lines.clear()
        self.central_line.clear()
        self.base.connect.clearall()

    def update(self):
        """
        If one of the interactors has been moved, update it and the parameter
        it controls, then update the other interactors accordingly
        """
        if self.inner_arc.has_move:
            self.inner_arc.update()
            self.r1 = self.inner_arc.radius
            self.radial_lines.update(r1=self.r1)
        if self.outer_arc.has_move:
            self.outer_arc.update()
            self.r2 = self.outer_arc.radius
            self.radial_lines.update(r2=self.r2)
        if self.radial_lines.has_move:
            self.radial_lines.update()
            self.phi = self.radial_lines.phi
            self.inner_arc.update(phi=self.phi)
            self.outer_arc.update(phi=self.phi)
        if  self.central_line.has_move:
            self.central_line.update()
            self.theta = self.central_line.theta
            self.inner_arc.update(theta=self.theta)
            self.outer_arc.update(theta=self.theta)
            self.radial_lines.update(theta=self.theta)

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.inner_arc.save(ev)
        self.outer_arc.save(ev)
        self.radial_lines.save(ev)
        self.central_line.save(ev)

    def _post_data(self):
        pass

    def post_data(self, new_sector=None, nbins=None):
        """
        post 1D data averagin in Q or Phi given new_sector type

        :param new_sector: slicer used for directional averaging in Q or Phi
        :param nbins: the number of point plotted when averaging
        """
        # Data to average
        data = self.data
        if data is None:
            return

        if self.inner_arc.radius < self.outer_arc.radius:
            rmin = self.inner_arc.radius
            rmax = self.outer_arc.radius
        else:
            rmin = self.outer_arc.radius
            rmax = self.inner_arc.radius
        phimin = self.central_line.theta - self.radial_lines.phi
        phimax = self.central_line.theta + self.radial_lines.phi

        if nbins is not None:
            self.nbins = nbins
        if self.averager is None:
            if new_sector is None:
                msg = "post data:cannot average , averager is empty"
                raise ValueError(msg)
            self.averager = new_sector

        # Why do I have to add pi to the angles for it to work properly?
        sect = self.averager(r_min=rmin, r_max=rmax, phi_min=phimin + np.pi,
                             phi_max=phimax + np.pi, nbins=self.nbins)
        sect.fold = False
        sector = sect(self.data)

        if hasattr(sector, "dxl"):
            dxl = sector.dxl
        else:
            dxl = None
        if hasattr(sector, "dxw"):
            dxw = sector.dxw
        else:
            dxw = None
        new_plot = Data1D(x=sector.x, y=sector.y, dy=sector.dy, dx=sector.dx)
        new_plot.dxl = dxl
        new_plot.dxw = dxw
        new_plot.name = str(self.averager.__name__) + \
                        "(" + self.data.name + ")"
        new_plot.source = self.data.source
        new_plot.interactive = True
        new_plot.detector = self.data.detector
        # If the data file does not tell us what the axes are, just assume...
        if self.averager.__name__ == 'SectorPhi':
            new_plot.xaxis("\\rm{\phi}", "degrees")
        else:
            new_plot.xaxis("\\rm{Q}", 'A^{-1}')
        new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")

        if hasattr(data, "scale") and data.scale == 'linear' and \
                self.data.name.count("Residuals") > 0:
            new_plot.ytransform = 'y'
            new_plot.yaxis("\\rm{Residuals} ", "/")

        new_plot.id = str(self.averager.__name__) + self.data.name
        new_plot.group_id = new_plot.id
        new_plot.is_data = True
        item = self._item
        if self._item.parent() is not None:
            item = self._item.parent()
        GuiUtils.updateModelItemWithPlot(item, new_plot, new_plot.id)

        self.base.manager.communicator.plotUpdateSignal.emit([new_plot])
        self.base.manager.communicator.forcePlotDisplaySignal.emit([item, new_plot])

        if self.update_model:
            self.setModelFromParams()

    def validate(self, param_name, param_value):
        """
        Validate input from user
        Values get checked at apply time.
        """
        MIN_Q_DIFFERENCE = self.dqmin
        MIN_PHI_DIFFERENCE = 0.01
        isValid = True

        # Stitched together from other slicers. There could be a neater way.
        if param_name == 'r_min':
            if np.fabs(param_value - self.getParams()['r_max']) < MIN_Q_DIFFERENCE:
                print("Inner and outer radii too close. Please adjust.")
                isValid = False
            elif param_value > self.qmax:
                print("Inner radius exceeds maximum range. Please adjust.")
                isValid = False
        elif param_name == 'r_max':
            if np.fabs(param_value - self.getParams()['r_min']) < MIN_Q_DIFFERENCE:
                print("Inner and outer radii too close. Please adjust.")
                isValid = False
            elif param_value > self.qmax:
                print("Outer radius exceeds maximum range. Please adjust.")
                isValid = False
        elif param_name == 'delta_phi [deg]':
            if np.fabs(param_value) < MIN_PHI_DIFFERENCE:
                print("Sector angles too close. Please adjust.")
                isValid = False
        elif param_name == 'nbins':
            # Can't be 0
            if param_value < 1:
                print("Number of bins cannot be <= 0. Please adjust.")
                isValid = False
        return isValid

    def moveend(self, ev):
        """
        Called after a dragging event.
        Post the slicer new parameters and creates a new Data1D
        corresponding to the new average
        """
        self._post_data()

    def restore(self, ev):
        """
        Restore the roughness for this layer.
        """
        self.inner_arc.restore(ev)
        self.outer_arc.restore(ev)
        self.radial_lines.restore(ev)
        self.central_line.restore(ev)

    def move(self, x, y, ev):
        """
        Process move to a new position.
        """
        pass

    def set_cursor(self, x, y):
        pass

    def getParams(self):
        """
        Store a copy of values of parameters of the slicer into a dictionary.
        :return params: the dictionary created
        """
        params = {}
        params["r_min"] = self.inner_arc.radius
        params["r_max"] = self.outer_arc.radius
        params["phi [deg]"] = self.central_line.theta * 180 / np.pi
        params["delta_phi [deg]"] = self.radial_lines.phi * 180 / np.pi
        params["nbins"] = self.nbins
        return params

    def setParams(self, params):
        """
        Receive a dictionary and reset the slicer with values contained
        in the values of the dictionary.

        :param params: a dictionary containing name of slicer parameters and
            values the user assigned to the slicer.
        """
        self.r1 = params["r_min"]
        self.r2 = params["r_max"]
        self.theta = params["phi [deg]"] * np.pi / 180
        self.phi = params["delta_phi [deg]"] * np.pi / 180
        self.nbins = int(params["nbins"])

        self.inner_arc.update(theta=self.theta, phi=self.phi, r=self.r1)
        self.outer_arc.update(theta=self.theta, phi=self.phi, r=self.r2)
        self.radial_lines.update(r1=self.r1, r2=self.r2,
                                 theta=self.theta, phi=self.phi)
        self.central_line.update(theta=self.theta)
        self.post_data()
        self.draw()

    def draw(self):
        """
        Draws the Canvas using the canvas.draw from the calling class
        that instantiated this object.
        """
        self.base.draw()

class WedgeInteractorQ(WedgeInteractor):
    """
    Average in Q direction. The data for all phi at a constant Q are
    averaged together to provide a 1D array in Q (to be plotted as a function
     of Q)
    """
    def __init__(self, base, axes, item=None, color='black', zorder=3):
        WedgeInteractor.__init__(self, base, axes, item=item, color=color)
        self.base = base
        self._post_data()

    def _post_data(self):
        """
        """
        from sasdata.data_util.manipulations import SectorQ
        self.post_data(SectorQ)


class WedgeInteractorPhi(WedgeInteractor):
    """
    Average in phi direction. The data for all Q at a constant phi are
    averaged together to provide a 1D array in phi (to be plotted as a function
     of phi)
    """
    def __init__(self, base, axes, item=None, color='black', zorder=3):
        WedgeInteractor.__init__(self, base, axes, item=item, color=color)
        self.base = base
        self._post_data()

    def _post_data(self):
        from sasdata.data_util.manipulations import SectorPhi
        self.post_data(SectorPhi)

