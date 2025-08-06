import numpy

from sas.qtgui.Plotting.Slicers.AnnulusSlicer import RingInteractor
from sas.qtgui.Plotting.Slicers.BaseInteractor import BaseInteractor


class CircularMask(BaseInteractor):
    """
     Draw a ring Given a radius
    """
    def __init__(self, base, axes, color='grey', zorder=3, side=None):
        """
        :param: the color of the line that defined the ring
        :param r: the radius of the ring
        :param sign: the direction of motion the the marker
        """
        BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.is_inside = side
        self.qmax = min(numpy.fabs(self.data.xmax),
                        numpy.fabs(self.data.xmin))  # must be positive
        self.connect = self.base.connect

        # Cursor position of Rings (Left(-1) or Right(1))
        self.xmaxd = self.data.xmax
        self.xmind = self.data.xmin

        if (self.xmaxd + self.xmind) > 0:
            self.sign = 1
        else:
            self.sign = -1
        # Inner circle
        self.outer_circle = RingInteractor(self, self.axes, 'blue',
                                           zorder=zorder + 1, r=self.qmax / 1.8,
                                           sign=self.sign)
        self.outer_circle.qmax = self.qmax * 1.2
        self.update()
        self._post_data()

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

    def update(self):
        """
        Respond to changes in the model by recalculating the profiles and
        resetting the widgets.
        """
        # Update locations
        self.outer_circle.update()
        self._post_data()
        out = self._post_data()
        return out

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.outer_circle.save(ev)

    def _post_data(self):
        """
        Uses annulus parameters to plot averaged data into 1D data.

        :param nbins: the number of points to plot

        """
        # Data to average
        data = self.data

        # If we have no data, just return
        if data is None:
            return
        mask = data.mask
        from sasdata.data_util.manipulations import Ringcut

        rmin = 0
        rmax = numpy.fabs(self.outer_circle.get_radius())

        # Create the data1D Q average of data2D
        mask = Ringcut(r_min=rmin, r_max=rmax)

        if self.is_inside:
            out = (mask(data) == False)
        else:
            out = (mask(data))
        return out


    def moveend(self, ev):
        """
        Called when any dragging motion ends.
        Post an event (type =SlicerParameterEvent)
        to plotter 2D with a copy  slicer parameters
        Call  _post_data method
        """
        #self.base.thaw_axes()
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

    def getParams(self):
        """
        Store a copy of values of parameters of the slicer into a dictionary.

        :return params: the dictionary created

        """
        params = {}
        params["outer_radius"] = numpy.fabs(self.outer_circle._inner_mouse_x)
        return params

    def setParams(self, params):
        """
        Receive a dictionary and reset the slicer with values contained
        in the values of the dictionary.

        :param params: a dictionary containing name of slicer parameters and
            values the user assigned to the slicer.
        """
        outer = numpy.fabs(params["outer_radius"])
        # Update the picture
        self.outer_circle.set_cursor(outer, self.outer_circle._inner_mouse_y)
        # Post the data given the nbins entered by the user
        self._post_data()

    def draw(self):
        self.base.update()

