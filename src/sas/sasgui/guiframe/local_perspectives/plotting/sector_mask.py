"""
    Sector mask interactor
"""
import math
import wx
#from copy import deepcopy
from BaseInteractor import _BaseInteractor
from SectorSlicer import SideInteractor
from SectorSlicer import LineInteractor
from sas.sasgui.guiframe.events import SlicerParameterEvent

class SectorMask(_BaseInteractor):
    """
    Draw a sector slicer.Allow to find the data 2D inside of the sector lines
    """
    def __init__(self, base, axes, color='gray', zorder=3, side=False):
        """
        """
        _BaseInteractor.__init__(self, base, axes, color=color)
        ## Class initialization
        self.markers = []
        self.axes = axes
        self.is_inside = side
        ## connect the plot to event
        self.connect = self.base.connect

        ## compute qmax limit to reset the graph
        x = math.pow(max(self.base.data.xmax,
                         math.fabs(self.base.data.xmin)), 2)
        y = math.pow(max(self.base.data.ymax,
                         math.fabs(self.base.data.ymin)), 2)
        self.qmax = math.sqrt(x + y)
        ## Number of points on the plot
        self.nbins = 20
        ## Angle of the middle line
        self.theta2 = math.pi / 3
        ## Absolute value of the Angle between the middle line and any side line
        self.phi = math.pi / 12

        ## Middle line
        self.main_line = LineInteractor(self, self.base.subplot, color='blue',
                                        zorder=zorder, r=self.qmax, theta=self.theta2)
        self.main_line.qmax = self.qmax
        ## Right Side line
        self.right_line = SideInteractor(self, self.base.subplot, color='gray',
                                         zorder=zorder, r=self.qmax, phi=-1 * self.phi,
                                         theta2=self.theta2)
        self.right_line.qmax = self.qmax
        ## Left Side line
        self.left_line = SideInteractor(self, self.base.subplot, color='gray',
                                        zorder=zorder, r=self.qmax, phi=self.phi,
                                        theta2=self.theta2)
        self.left_line.qmax = self.qmax
        ## draw the sector
        self.update()
        self._post_data()

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
        ## Check if the middle line was dragged and
        #update the picture accordingly
        if self.main_line.has_move:
            self.main_line.update()
            self.right_line.update(delta=-self.left_line.phi / 2,
                                   mline=self.main_line.theta)
            self.left_line.update(delta=self.left_line.phi / 2,
                                  mline=self.main_line.theta)
        ## Check if the left side has moved and update the slicer accordingly
        if self.left_line.has_move:
            self.main_line.update()
            self.left_line.update(phi=None, delta=None, mline=self.main_line,
                                  side=True, left=True)
            self.right_line.update(phi=self.left_line.phi, delta=None,
                                   mline=self.main_line, side=True,
                                   left=False, right=True)
        ## Check if the right side line has moved and
        #update the slicer accordingly
        if self.right_line.has_move:
            self.main_line.update()
            self.right_line.update(phi=None, delta=None, mline=self.main_line,
                                   side=True, left=False, right=True)
            self.left_line.update(phi=self.right_line.phi, delta=None,
                                  mline=self.main_line, side=True, left=False)
        #if self.is_inside is not None:
        out = self._post_data()
        return out

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.base.freeze_axes()
        self.main_line.save(ev)
        self.right_line.save(ev)
        self.left_line.save(ev)

    def _post_data(self):
        """
        compute sector averaging of data into data1D
        """
        ## get the data to average
        data = self.base.data
        # If we have no data, just return
        if data is None:
            return
        ## Averaging
        from sas.sascalc.dataloader.manipulations import Sectorcut
        phimin = -self.left_line.phi + self.main_line.theta
        phimax = self.left_line.phi + self.main_line.theta

        mask = Sectorcut(phi_min=phimin, phi_max=phimax)
        if self.is_inside:
            out = (mask(data) == False)
        else:
            out = (mask(data))
        return out

    def moveend(self, ev):
        """
        Called a dragging motion ends.Get slicer event
        """
        self.base.thaw_axes()
        ## Post parameters
        event = SlicerParameterEvent()
        event.type = self.__class__.__name__
        event.params = self.get_params()
        ## Send slicer paramers to plotter2D
        wx.PostEvent(self.base, event)
        self._post_data()

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

    def get_params(self):
        """
        Store a copy of values of parameters of the slicer into a dictionary.

        :return params: the dictionary created

        """
        params = {}
        ## Always make sure that the left and the right line are at phi
        ## angle of the middle line
        if math.fabs(self.left_line.phi) != math.fabs(self.right_line.phi):
            msg = "Phi left and phi right are "
            msg += "different %f, %f" % (self.left_line.phi,
                                         self.right_line.phi)
            raise (ValueError, msg)
        params["Phi"] = self.main_line.theta
        params["Delta_Phi"] = math.fabs(self.left_line.phi)
        return params

    def set_params(self, params):
        """
        Receive a dictionary and reset the slicer with values contained
        in the values of the dictionary.

        :param params: a dictionary containing name of slicer parameters and
            values the user assigned to the slicer.
        """
        main = params["Phi"]
        phi = math.fabs(params["Delta_Phi"])

        self.main_line.theta = main
        ## Reset the slicer parameters
        self.main_line.update()
        self.right_line.update(phi=phi, delta=None, mline=self.main_line,
                               side=True, right=True)
        self.left_line.update(phi=phi, delta=None,
                              mline=self.main_line, side=True)
        ## post the new corresponding data
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
        self.base.update()
