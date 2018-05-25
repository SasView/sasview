"""
    Sector interactor
"""
import numpy
import logging

from .BaseInteractor import BaseInteractor
from sas.qtgui.Plotting.PlotterData import Data1D
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.SlicerModel import SlicerModel

MIN_PHI = 0.05

class SectorInteractor(BaseInteractor, SlicerModel):
    """
    Draw a sector slicer.Allow to performQ averaging on data 2D
    """
    def __init__(self, base, axes, item=None, color='black', zorder=3):

        BaseInteractor.__init__(self, base, axes, color=color)
        SlicerModel.__init__(self)
        # Class initialization
        self.markers = []
        self.axes = axes
        self._item = item
        # Connect the plot to event
        self.connect = self.base.connect

        # Compute qmax limit to reset the graph
        x = numpy.power(max(self.base.data.xmax,
                         numpy.fabs(self.base.data.xmin)), 2)
        y = numpy.power(max(self.base.data.ymax,
                         numpy.fabs(self.base.data.ymin)), 2)
        self.qmax = numpy.sqrt(x + y)
        # Number of points on the plot
        self.nbins = 20
        # Angle of the middle line
        self.theta2 = numpy.pi / 3
        # Absolute value of the Angle between the middle line and any side line
        self.phi = numpy.pi / 12
        # Middle line
        self.main_line = LineInteractor(self, self.axes, color='blue',
                                        zorder=zorder, r=self.qmax,
                                        theta=self.theta2)
        self.main_line.qmax = self.qmax
        # Right Side line
        self.right_line = SideInteractor(self, self.axes, color='black',
                                         zorder=zorder, r=self.qmax,
                                         phi=-1 * self.phi, theta2=self.theta2)
        self.right_line.qmax = self.qmax
        # Left Side line
        self.left_line = SideInteractor(self, self.axes, color='black',
                                        zorder=zorder, r=self.qmax,
                                        phi=self.phi, theta2=self.theta2)
        self.left_line.qmax = self.qmax
        # draw the sector
        self.update()
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
        self.clear_markers()
        self.main_line.clear()
        self.left_line.clear()
        self.right_line.clear()
        self.base.connect.clearall()

    def update(self):
        """
        Respond to changes in the model by recalculating the profiles and
        resetting the widgets.
        """
        # Update locations
        # Check if the middle line was dragged and
        # update the picture accordingly
        if self.main_line.has_move:
            self.main_line.update()
            self.right_line.update(delta=-self.left_line.phi / 2,
                                   mline=self.main_line.theta)
            self.left_line.update(delta=self.left_line.phi / 2,
                                  mline=self.main_line.theta)
        # Check if the left side has moved and update the slicer accordingly
        if self.left_line.has_move:
            self.main_line.update()
            self.left_line.update(phi=None, delta=None, mline=self.main_line,
                                  side=True, left=True)
            self.right_line.update(phi=self.left_line.phi, delta=None,
                                   mline=self.main_line, side=True,
                                   left=False, right=True)
        # Check if the right side line has moved and update the slicer accordingly
        if self.right_line.has_move:
            self.main_line.update()
            self.right_line.update(phi=None, delta=None, mline=self.main_line,
                                   side=True, left=False, right=True)
            self.left_line.update(phi=self.right_line.phi, delta=None,
                                  mline=self.main_line, side=True, left=False)

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.main_line.save(ev)
        self.right_line.save(ev)
        self.left_line.save(ev)

    def _post_data(self, nbins=None):
        """
        compute sector averaging of data2D into data1D
        :param nbins: the number of point to plot for the average 1D data
        """
        # Get the data2D to average
        data = self.base.data
        # If we have no data, just return
        if data is None:
            return
        # Averaging
        from sas.sascalc.dataloader.manipulations import SectorQ
        radius = self.qmax
        phimin = -self.left_line.phi + self.main_line.theta
        phimax = self.left_line.phi + self.main_line.theta
        if nbins is None:
            nbins = 20
        sect = SectorQ(r_min=0.0, r_max=radius,
                       phi_min=phimin + numpy.pi,
                       phi_max=phimax + numpy.pi, nbins=nbins)

        sector = sect(self.base.data)
        # Create 1D data resulting from average

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
        new_plot.name = "SectorQ" + "(" + self.base.data.name + ")"
        new_plot.title = "SectorQ" + "(" + self.base.data.name + ")"
        new_plot.source = self.base.data.source
        new_plot.interactive = True
        new_plot.detector = self.base.data.detector
        # If the data file does not tell us what the axes are, just assume them.
        new_plot.xaxis("\\rm{Q}", "A^{-1}")
        new_plot.yaxis("\\rm{Intensity}", "cm^{-1}")
        if hasattr(data, "scale") and data.scale == 'linear' and \
                self.base.data.name.count("Residuals") > 0:
            new_plot.ytransform = 'y'
            new_plot.yaxis("\\rm{Residuals} ", "/")

        new_plot.group_id = "2daverage" + self.base.data.name
        new_plot.id = "SectorQ" + self.base.data.name
        new_plot.is_data = True
        GuiUtils.updateModelItemWithPlot(self._item, new_plot, new_plot.id)

        self.base.manager.communicator.plotUpdateSignal.emit([new_plot])

        if self.update_model:
            self.setModelFromParams()
        self.draw()

    def validate(self, param_name, param_value):
        """
        Test the proposed new value "value" for row "row" of parameters
        """
        MIN_DIFFERENCE = 0.01
        isValid = True

        if param_name == 'Delta_Phi [deg]':
            # First, check the closeness
            if numpy.fabs(param_value) < MIN_DIFFERENCE:
                print("Sector angles too close. Please adjust.")
                isValid = False
        elif param_name == 'nbins':
            # Can't be 0
            if param_value < 1:
                print("Number of bins cannot be less than or equal to 0. Please adjust.")
                isValid = False
        return isValid

    def moveend(self, ev):
        """
        Called a dragging motion ends.Get slicer event
        """
        # Post parameters
        self._post_data(self.nbins)

    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.main_line.restore()
        self.left_line.restore()
        self.right_line.restore()

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
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
        # Always make sure that the left and the right line are at phi
        # angle of the middle line
        if numpy.fabs(self.left_line.phi) != numpy.fabs(self.right_line.phi):
            msg = "Phi left and phi right are different"
            msg += " %f, %f" % (self.left_line.phi, self.right_line.phi)
            raise ValueError(msg)
        params["Phi [deg]"] = self.main_line.theta * 180 / numpy.pi
        params["Delta_Phi [deg]"] = numpy.fabs(self.left_line.phi * 180 / numpy.pi)
        params["nbins"] = self.nbins
        return params

    def setParams(self, params):
        """
        Receive a dictionary and reset the slicer with values contained
        in the values of the dictionary.

        :param params: a dictionary containing name of slicer parameters and
            values the user assigned to the slicer.
        """
        main = params["Phi [deg]"] * numpy.pi / 180
        phi = numpy.fabs(params["Delta_Phi [deg]"] * numpy.pi / 180)

        # phi should not be too close.
        if numpy.fabs(phi) < MIN_PHI:
            phi = MIN_PHI
            params["Delta_Phi [deg]"] = MIN_PHI

        self.nbins = int(params["nbins"])
        self.main_line.theta = main
        # Reset the slicer parameters
        self.main_line.update()
        self.right_line.update(phi=phi, delta=None, mline=self.main_line,
                               side=True, right=True)
        self.left_line.update(phi=phi, delta=None,
                              mline=self.main_line, side=True)
        # Post the new corresponding data
        self._post_data(nbins=self.nbins)

    def draw(self):
        """
        Redraw canvas
        """
        self.base.draw()


class SideInteractor(BaseInteractor):
    """
    Draw an oblique line

    :param phi: the phase between the middle line and one side line
    :param theta2: the angle between the middle line and x- axis

    """
    def __init__(self, base, axes, color='black', zorder=5, r=1.0,
                 phi=numpy.pi / 4, theta2=numpy.pi / 3):
        BaseInteractor.__init__(self, base, axes, color=color)
        # Initialize the class
        self.markers = []
        self.axes = axes
        # compute the value of the angle between the current line and
        # the x-axis
        self.save_theta = theta2 + phi
        self.theta = theta2 + phi
        # the value of the middle line angle with respect to the x-axis
        self.theta2 = theta2
        # Radius to find polar coordinates this line's endpoints
        self.radius = r
        # phi is the phase between the current line and the middle line
        self.phi = phi
        # End points polar coordinates
        x1 = self.radius * numpy.cos(self.theta)
        y1 = self.radius * numpy.sin(self.theta)
        x2 = -1 * self.radius * numpy.cos(self.theta)
        y2 = -1 * self.radius * numpy.sin(self.theta)
        # Defining a new marker
        self.inner_marker = self.axes.plot([x1 / 2.5], [y1 / 2.5], linestyle='',
                                           marker='s', markersize=10,
                                           color=self.color, alpha=0.6,
                                           pickradius=5, label="pick",
                                           zorder=zorder, visible=True)[0]

        # Defining the current line
        self.line = self.axes.plot([x1, x2], [y1, y2],
                                   linestyle='-', marker='',
                                   color=self.color, visible=True)[0]
        # Flag to differentiate the left line from the right line motion
        self.left_moving = False
        # Flag to define a motion
        self.has_move = False
        # connecting markers and draw the picture
        self.connect_markers([self.inner_marker, self.line])

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
            self.line.remove()
            self.inner_marker.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]

    def update(self, phi=None, delta=None, mline=None,
               side=False, left=False, right=False):
        """
        Draw oblique line

        :param phi: the phase between the middle line and the current line
        :param delta: phi/2 applied only when the mline was moved

        """
        self.left_moving = left
        theta3 = 0
        if phi is not None:
            self.phi = phi
        if delta is None:
            delta = 0
        if  right:
            self.phi = -1 * numpy.fabs(self.phi)
            #delta=-delta
        else:
            self.phi = numpy.fabs(self.phi)
        if side:
            self.theta = mline.theta + self.phi

        if mline is not None:
            if delta != 0:
                self.theta2 = mline + delta
            else:
                self.theta2 = mline.theta
        if delta == 0:
            theta3 = self.theta + delta
        else:
            theta3 = self.theta2 + delta
        x1 = self.radius * numpy.cos(theta3)
        y1 = self.radius * numpy.sin(theta3)
        x2 = -1 * self.radius * numpy.cos(theta3)
        y2 = -1 * self.radius * numpy.sin(theta3)
        self.inner_marker.set(xdata=[x1 / 2.5], ydata=[y1 / 2.5])
        self.line.set(xdata=[x1, x2], ydata=[y1, y2])

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_theta = self.theta

    def moveend(self, ev):
        self.has_move = False
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
        self.theta = numpy.arctan2(y, x)
        self.has_move = True
        if not self.left_moving:
            if  self.theta2 - self.theta <= 0 and self.theta2 > 0:
                self.restore()
                return
            elif self.theta2 < 0 and self.theta < 0 and \
                self.theta - self.theta2 >= 0:
                self.restore()
                return
            elif  self.theta2 < 0 and self.theta > 0 and \
                (self.theta2 + 2 * numpy.pi - self.theta) >= numpy.pi / 2:
                self.restore()
                return
            elif  self.theta2 < 0 and self.theta < 0 and \
                (self.theta2 - self.theta) >= numpy.pi / 2:
                self.restore()
                return
            elif self.theta2 > 0 and (self.theta2 - self.theta >= numpy.pi / 2 or \
                (self.theta2 - self.theta >= numpy.pi / 2)):
                self.restore()
                return
        else:
            if  self.theta < 0 and (self.theta + numpy.pi * 2 - self.theta2) <= 0:
                self.restore()
                return
            elif self.theta2 < 0 and (self.theta - self.theta2) <= 0:
                self.restore()
                return
            elif  self.theta > 0 and self.theta - self.theta2 <= 0:
                self.restore()
                return
            elif self.theta - self.theta2 >= numpy.pi / 2 or  \
                ((self.theta + numpy.pi * 2 - self.theta2) >= numpy.pi / 2 and \
                 self.theta < 0 and self.theta2 > 0):
                self.restore()
                return

        self.phi = numpy.fabs(self.theta2 - self.theta)
        if self.phi > numpy.pi:
            self.phi = 2 * numpy.pi - numpy.fabs(self.theta2 - self.theta)
        self.base.base.update()

    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()

    def getParams(self):
        params = {}
        params["radius"] = self.radius
        params["theta"] = self.theta
        return params

    def setParams(self, params):
        x = params["radius"]
        self.set_cursor(x, None)


class LineInteractor(BaseInteractor):
    """
    Select an annulus through a 2D plot
    """
    def __init__(self, base, axes, color='black',
                 zorder=5, r=1.0, theta=numpy.pi / 4):
        BaseInteractor.__init__(self, base, axes, color=color)

        self.markers = []
        self.axes = axes
        self.save_theta = theta
        self.theta = theta
        self.radius = r
        self.scale = 10.0
        # Inner circle
        x1 = self.radius * numpy.cos(self.theta)
        y1 = self.radius * numpy.sin(self.theta)
        x2 = -1 * self.radius * numpy.cos(self.theta)
        y2 = -1 * self.radius * numpy.sin(self.theta)
        # Inner circle marker
        self.inner_marker = self.axes.plot([x1 / 2.5], [y1 / 2.5], linestyle='',
                                           marker='s', markersize=10,
                                           color=self.color, alpha=0.6,
                                           pickradius=5, label="pick",
                                           zorder=zorder,
                                           visible=True)[0]
        self.line = self.axes.plot([x1, x2], [y1, y2],
                                   linestyle='-', marker='',
                                   color=self.color, visible=True)[0]
        self.npts = 20
        self.has_move = False
        self.connect_markers([self.inner_marker, self.line])
        self.update()

    def set_layer(self, n):
        self.layernum = n
        self.update()

    def clear(self):
        self.clear_markers()
        try:
            self.inner_marker.remove()
            self.line.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]

    def update(self, theta=None):
        """
        Draw the new roughness on the graph.
        """

        if theta is not None:
            self.theta = theta
        x1 = self.radius * numpy.cos(self.theta)
        y1 = self.radius * numpy.sin(self.theta)
        x2 = -1 * self.radius * numpy.cos(self.theta)
        y2 = -1 * self.radius * numpy.sin(self.theta)

        self.inner_marker.set(xdata=[x1 / 2.5], ydata=[y1 / 2.5])
        self.line.set(xdata=[x1, x2], ydata=[y1, y2])

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_theta = self.theta

    def moveend(self, ev):
        self.has_move = False
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
        self.theta = numpy.arctan2(y, x)
        self.has_move = True
        self.base.base.update()

    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()

    def getParams(self):
        params = {}
        params["radius"] = self.radius
        params["theta"] = self.theta
        return params

    def setParams(self, params):
        x = params["radius"]
        self.set_cursor(x, None)
