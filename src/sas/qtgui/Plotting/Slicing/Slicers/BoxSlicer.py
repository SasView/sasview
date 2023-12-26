import numpy

from typing import Optional

from matplotlib.axes import Axes
from sas.qtgui.Plotting.Plotter2D import Plotter2D


from sas.qtgui.Plotting.BaseInteractor import BaseInteractor
from sas.qtgui.Plotting.PlotterData import Data1D
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.Slicing.SlicerParameterWidget import SlicerParameterWidget

import logging
logger = logging.getLogger("BoxSlicer")

class BoxInteractor(BaseInteractor[Plotter2D], SlicerParameterWidget):
    """
    BoxInteractor plots a data1D average of a rectangular area defined in
    a Data2D object. The data1D averaging itself is performed in sasdata
    by manipulations.py

    This class uses two other classes, HorizontalLines and VerticalLines,
    to define the rectangle area: -x, x ,y, -y. It is subclassed by
    BoxInteractorX and BoxInteracgtorY which define the direction of the
    average. BoxInteractorX averages all the points from -y to +y as a
    function of Q_x and BoxInteractorY averages all the points from
    -x to +x as a function of Q_y
    """

    def __init__(self, base: Plotter2D, axes: Axes, item=None, color='black', zorder=3):
        BaseInteractor.__init__(self, base, axes, color=color)
        SlicerParameterWidget.__init__(self)
        # Class initialization
        self.markers = []
        self.axes = axes
        self._item = item
        # connecting artist
        self.connect = self.base.connect
        # which direction is the preferred interaction direction
        self.direction = None
        # determine x y  values
        self.x = 0.5 * min(numpy.fabs(self.data.xmax),
                           numpy.fabs(self.data.xmin))
        self.y = 0.5 * min(numpy.fabs(self.data.xmax),
                           numpy.fabs(self.data.xmin))
        # when reach qmax reset the graph
        self.qmax = max(self.data.xmax, self.data.xmin,
                        self.data.ymax, self.data.ymin)
        # Number of points on the plot
        self.nbins = 100
        # If True, I(|Q|) will be return, otherwise,
        # negative q-values are allowed
        self.fold = True
        # reference of the current  Slab averaging
        self.averager = None
        # Create vertical and horizaontal lines for the rectangle
        self.vertical_lines = VerticalLines(self,
                                            self.axes,
                                            color='blue',
                                            zorder=zorder,
                                            y=self.y,
                                            x=self.x)
        self.vertical_lines.qmax = self.qmax

        self.horizontal_lines = HorizontalLines(self,
                                                self.axes,
                                                color='green',
                                                zorder=zorder,
                                                x=self.x,
                                                y=self.y)
        self.horizontal_lines.qmax = self.qmax
        # draw the rectangle and plost the data 1D resulting
        # of averaging data2D
        self.update()
        self._post_data()
        self.draw()
        self.setModelFromParams()

    def update_and_post(self):
        """
        Update the slicer and plot the resulting data
        """
        self.update()
        self._post_data()
        self.draw()

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
        self.horizontal_lines.clear()
        self.vertical_lines.clear()
        self.base.connect.clearall()

    def update(self):
        """
        Respond to changes in the model by recalculating the profiles and
        resetting the widgets.
        """
        # #Update the slicer if an horizontal line is dragged
        if self.horizontal_lines.has_move:
            self.horizontal_lines.update()
            self.vertical_lines.update(y=self.horizontal_lines.y)
        # #Update the slicer if a vertical line is dragged
        if self.vertical_lines.has_move:
            self.vertical_lines.update()
            self.horizontal_lines.update(x=self.vertical_lines.x)

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.vertical_lines.save(ev)
        self.horizontal_lines.save(ev)

    def _post_data(self, new_slab: SlicerParameterWidget, nbins: Optional[int]=None, direction: Optional[str]=None):
        """
        post 1D data averaging in Qx or Qy given new_slab type

        :param new_slab: slicer that determine with direction to average
        :param nbins: the number of points plotted when averaging
        :param direction: the direction of averaging

        """
        if self.direction is None:
            self.direction = direction

        qx_min = -1 * numpy.fabs(self.vertical_lines.x)
        qx_max = numpy.fabs(self.vertical_lines.x)
        qy_min = -1 * numpy.fabs(self.horizontal_lines.y)
        qy_max = numpy.fabs(self.horizontal_lines.y)

        if nbins is not None:
            self.nbins = nbins

        if self.averager is None:
            if new_slab is None:
                msg = "post data:cannot average , averager is empty"
                raise ValueError(msg)
            self.averager = new_slab

        if self.direction not in ["X", "Y"]:
            msg = "post data:no Box Average direction was supplied"
            raise ValueError(msg)

        # # Average data2D given Qx or Qy
        box = self.averager(qx_min=qx_min, qx_max=qx_max, qy_min=qy_min,
                            qy_max=qy_max, nbins=self.nbins)

        box.fold = self.fold
        boxavg = box(self.data)
        # 3 Create Data1D to plot
        if hasattr(boxavg, "dxl"):
            dxl = boxavg.dxl
        else:
            dxl = None
        if hasattr(boxavg, "dxw"):
            dxw = boxavg.dxw
        else:
            dxw = None
        new_plot = Data1D(x=boxavg.x, y=boxavg.y, dy=boxavg.dy)
        new_plot.dxl = dxl
        new_plot.dxw = dxw

        new_plot.name = str(self.averager.__name__) + \
            "(" + self.data.name + ")"

        new_plot.title = str(self.averager.__name__) + \
            "(" + self.data.name + ")"

        new_plot.source = self.data.source
        new_plot.interactive = True
        new_plot.detector = self.data.detector

        # If the data file does not tell us what the axes are, just assume...
        new_plot.xaxis("\\rm{Q}", "A^{-1}")
        new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")

        data = self.data
        if hasattr(data, "scale") and data.scale == 'linear' and \
                self.data.name.count("Residuals") > 0:
            new_plot.ytransform = 'y'
            new_plot.yaxis("\\rm{Residuals} ", "/")

        new_plot.id = (self.averager.__name__) + self.data.name
        new_plot.group_id = new_plot.id
        new_plot.is_data = True
        item = self._item
        if self._item.parent() is not None:
            item = self._item.parent()
        GuiUtils.updateModelItemWithPlot(item, new_plot, new_plot.id)
        self.base.manager.communicator.forcePlotDisplaySignal.emit([item, new_plot])

        if self.update_model:
            self.setModelFromParams()

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
        self.horizontal_lines.restore(ev)
        self.vertical_lines.restore(ev)

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
        params["x_max"] = numpy.fabs(self.vertical_lines.x)
        params["y_max"] = numpy.fabs(self.horizontal_lines.y)
        params["nbins"] = self.nbins
        params["fold"] = self.fold
        return params

    def setParams(self, params):
        """
        Receive a dictionary and reset the slicer with values contained
        in the values of the dictionary.

        :param params: a dictionary containing name of slicer parameters and
            values the user assigned to the slicer.
        """
        self.x = float(numpy.fabs(params["x_max"]))
        self.y = float(numpy.fabs(params["qy_max"]))
        self.nbins = params["nbins"]
        self.fold = params["fold"]

        self.horizontal_lines.update(x=self.x, y=self.y)
        self.vertical_lines.update(x=self.x, y=self.y)
        self._post_data()
        self.draw()

    def draw(self):
        """
        Draws the Canvas using the canvas.draw from the calling class
        that instatiated this object.
        """
        self.base.draw()




class BoxInteractorX(BoxInteractor):
    """
    Average in Qx direction. The data for all Qy at a constant Qx are
    averaged together to provide a 1D array in Qx (to be plotted as a function
    of Qx)
    """

    def __init__(self, base: Plotter2D, axes: Axes, item=None, color='black', zorder=3):
        BoxInteractor.__init__(self, base, axes, item=item, color=color)

        super()._post_data()

    def _post_data(self, new_slab=None, nbins=None, direction=None):
        """
        Post data creating by averaging in Qx direction
        """
        from sasdata.data_util.averaging import SlabX
        super()._post_data(SlabX, direction="X")

    def validate(self, param_name, param_value):
        """
        Validate input from user.
        Values get checked at apply time.
        """
        isValid = True

        if param_name == 'nbins':
            # Can't be 0
            if param_value < 1:
                print("Number of bins cannot be less than or equal to 0. Please adjust.")
                isValid = False
        return isValid


class BoxInteractorY(BoxInteractor):
    """
    Average in Qy direction. The data for all Qx at a constant Qy are
    averaged together to provide a 1D array in Qy (to be plotted as a function
    of Qy)
    """

    def __init__(self, base: Plotter2D, axes: Axes, item=None, color='black', zorder=3):

        BoxInteractor.__init__(self, base, axes, item=item, color=color)


    def _post_data(self, new_slab=None, nbins: Optional[int]=None, direction: Optional[str]=None):
        """
        Post data creating by averaging in Qy direction
        """
        from sasdata.data_util.averaging import SlabY
        super()._post_data(SlabY, direction="Y")

    def validate(self, param_name, param_value):
        """
        Validate input from user
        Values get checked at apply time.
        """

        isValid = True

        if param_name == 'nbins':
            # Can't be 0
            if param_value < 1:
                logger.error("Number of bins cannot be less than or equal to 0. Please adjust.")
                isValid = False

        return isValid
