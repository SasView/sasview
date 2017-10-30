import numpy

from .BaseInteractor import BaseInteractor
from sas.qtgui.Plotting.PlotterData import Data1D
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.SlicerModel import SlicerModel


class BoxInteractor(BaseInteractor, SlicerModel):
    """
    BoxInteractor define a rectangle that return data1D average of Data2D
    in a rectangle area defined by -x, x ,y, -y
    """
    def __init__(self, base, axes, item=None, color='black', zorder=3):
        BaseInteractor.__init__(self, base, axes, color=color)
        SlicerModel.__init__(self)
        # Class initialization
        self.markers = []
        self.axes = axes
        self._item = item
        #connecting artist
        self.connect = self.base.connect
        # which direction is the preferred interaction direction
        self.direction = None
        # determine x y  values
        self.x = 0.5 * min(numpy.fabs(self.base.data.xmax),
                           numpy.fabs(self.base.data.xmin))
        self.y = 0.5 * min(numpy.fabs(self.base.data.xmax),
                           numpy.fabs(self.base.data.xmin))
        # when reach qmax reset the graph
        self.qmax = max(self.base.data.xmax, self.base.data.xmin,
                        self.base.data.ymax, self.base.data.ymin)
        # Number of points on the plot
        self.nbins = 30
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
        self.setModelFromParams()

    def update_and_post(self):
        """
        Update the slicer and plot the resulting data
        """
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

    def _post_data(self):
        pass

    def post_data(self, new_slab=None, nbins=None, direction=None):
        """
        post data averaging in Qx or Qy given new_slab type

        :param new_slab: slicer that determine with direction to average
        :param nbins: the number of points plotted when averaging
        :param direction: the direction of averaging

        """
        if self.direction is None:
            self.direction = direction

        x_min = -1 * numpy.fabs(self.vertical_lines.x)
        x_max = numpy.fabs(self.vertical_lines.x)
        y_min = -1 * numpy.fabs(self.horizontal_lines.y)
        y_max = numpy.fabs(self.horizontal_lines.y)

        if nbins is not None:
            self.nbins = nbins
        if self.averager is None:
            if new_slab is None:
                msg = "post data:cannot average , averager is empty"
                raise ValueError(msg)
            self.averager = new_slab
        if self.direction == "X":
            if self.fold:
                x_low = 0
            else:
                x_low = numpy.fabs(x_min)
            bin_width = (x_max + x_low) / self.nbins
        elif self.direction == "Y":
            if self.fold:
                y_low = 0
            else:
                y_low = numpy.fabs(y_min)
            bin_width = (y_max + y_low) / self.nbins
        else:
            msg = "post data:no Box Average direction was supplied"
            raise ValueError(msg)
        # # Average data2D given Qx or Qy
        box = self.averager(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
                            bin_width=bin_width)
        box.fold = self.fold
        boxavg = box(self.base.data)
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
                        "(" + self.base.data.name + ")"
        new_plot.title = str(self.averager.__name__) + \
                        "(" + self.base.data.name + ")"
        new_plot.source = self.base.data.source
        new_plot.interactive = True
        new_plot.detector = self.base.data.detector
        # # If the data file does not tell us what the axes are, just assume...
        new_plot.xaxis("\\rm{Q}", "A^{-1}")
        new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")

        data = self.base.data
        if hasattr(data, "scale") and data.scale == 'linear' and \
                self.base.data.name.count("Residuals") > 0:
            new_plot.ytransform = 'y'
            new_plot.yaxis("\\rm{Residuals} ", "/")

        new_plot.group_id = "2daverage" + self.base.data.name
        new_plot.id = (self.averager.__name__) + self.base.data.name
        new_plot.is_data = True
        GuiUtils.updateModelItemWithPlot(self._item, new_plot, new_plot.id)

        if self.update_model:
            self.setModelFromParams()
        self.draw()

    def moveend(self, ev):
        """
        Called after a dragging event.
        Post the slicer new parameters and creates a new Data1D
        corresponding to the new average
        """
        self._post_data()

    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.horizontal_lines.restore()
        self.vertical_lines.restore()

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
        return params

    def setParams(self, params):
        """
        Receive a dictionary and reset the slicer with values contained
        in the values of the dictionary.

        :param params: a dictionary containing name of slicer parameters and
            values the user assigned to the slicer.
        """
        self.x = float(numpy.fabs(params["x_max"]))
        self.y = float(numpy.fabs(params["y_max"]))
        self.nbins = params["nbins"]

        self.horizontal_lines.update(x=self.x, y=self.y)
        self.vertical_lines.update(x=self.x, y=self.y)
        self.post_data(nbins=None)

    def draw(self):
        """
        """
        self.base.draw()


class HorizontalLines(BaseInteractor):
    """
    Draw 2 Horizontal lines centered on (0,0) that can move
    on the x- direction and in opposite direction
    """
    def __init__(self, base, axes, color='black', zorder=5, x=0.5, y=0.5):
        """
        """
        BaseInteractor.__init__(self, base, axes, color=color)
        # Class initialization
        self.markers = []
        self.axes = axes
        # Saving the end points of two lines
        self.x = x
        self.save_x = x

        self.y = y
        self.save_y = y
        # Creating a marker
        # Inner circle marker
        self.inner_marker = self.axes.plot([0], [self.y], linestyle='',
                                           marker='s', markersize=10,
                                           color=self.color, alpha=0.6,
                                           pickradius=5, label="pick",
                                           zorder=zorder,
                                           visible=True)[0]
        # Define 2 horizontal lines
        self.top_line = self.axes.plot([self.x, -self.x], [self.y, self.y],
                                       linestyle='-', marker='',
                                       color=self.color, visible=True)[0]
        self.bottom_line = self.axes.plot([self.x, -self.x], [-self.y, -self.y],
                                          linestyle='-', marker='',
                                          color=self.color, visible=True)[0]
        # Flag to check the motion of the lines
        self.has_move = False
        # Connecting markers to mouse events and draw
        self.connect_markers([self.top_line, self.inner_marker])
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
        Clear this slicer  and its markers
        """
        self.clear_markers()
        self.inner_marker.remove()
        self.top_line.remove()
        self.bottom_line.remove()

    def update(self, x=None, y=None):
        """
        Draw the new roughness on the graph.

        :param x: x-coordinates to reset current class x
        :param y: y-coordinates to reset current class y

        """
        # Reset x, y- coordinates if send as parameters
        if x is not None:
            self.x = numpy.sign(self.x) * numpy.fabs(x)
        if y is not None:
            self.y = numpy.sign(self.y) * numpy.fabs(y)
        # Draw lines and markers
        self.inner_marker.set(xdata=[0], ydata=[self.y])
        self.top_line.set(xdata=[self.x, -self.x], ydata=[self.y, self.y])
        self.bottom_line.set(xdata=[self.x, -self.x], ydata=[-self.y, -self.y])

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_x = self.x
        self.save_y = self.y

    def moveend(self, ev):
        """
        Called after a dragging this edge and set self.has_move to False
        to specify the end of dragging motion
        """
        self.has_move = False
        self.base.moveend(ev)

    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.x = self.save_x
        self.y = self.save_y

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.y = y
        self.has_move = True
        self.base.base.update()


class VerticalLines(BaseInteractor):
    """
    Select an annulus through a 2D plot
    """
    def __init__(self, base, axes, color='black', zorder=5, x=0.5, y=0.5):
        """
        """
        BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.x = numpy.fabs(x)
        self.save_x = self.x
        self.y = numpy.fabs(y)
        self.save_y = y
        # Inner circle marker
        self.inner_marker = self.axes.plot([self.x], [0], linestyle='',
                                           marker='s', markersize=10,
                                           color=self.color, alpha=0.6,
                                           pickradius=5, label="pick",
                                           zorder=zorder, visible=True)[0]
        self.right_line = self.axes.plot([self.x, self.x],
                                         [self.y, -self.y],
                                         linestyle='-', marker='',
                                         color=self.color, visible=True)[0]
        self.left_line = self.axes.plot([-self.x, -self.x],
                                        [self.y, -self.y],
                                        linestyle='-', marker='',
                                        color=self.color, visible=True)[0]
        self.has_move = False
        self.connect_markers([self.right_line, self.inner_marker])
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
        Clear this slicer  and its markers
        """
        self.clear_markers()
        self.inner_marker.remove()
        self.left_line.remove()
        self.right_line.remove()

    def update(self, x=None, y=None):
        """
        Draw the new roughness on the graph.

        :param x: x-coordinates to reset current class x
        :param y: y-coordinates to reset current class y

        """
        # Reset x, y -coordinates if given as parameters
        if x is not None:
            self.x = numpy.sign(self.x) * numpy.fabs(x)
        if y is not None:
            self.y = numpy.sign(self.y) * numpy.fabs(y)
        # Draw lines and markers
        self.inner_marker.set(xdata=[self.x], ydata=[0])
        self.left_line.set(xdata=[-self.x, -self.x], ydata=[self.y, -self.y])
        self.right_line.set(xdata=[self.x, self.x], ydata=[self.y, -self.y])

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_x = self.x
        self.save_y = self.y

    def moveend(self, ev):
        """
        Called after a dragging this edge and set self.has_move to False
        to specify the end of dragging motion
        """
        self.has_move = False
        self.base.moveend(ev)

    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.x = self.save_x
        self.y = self.save_y

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.has_move = True
        self.x = x
        self.base.base.update()


class BoxInteractorX(BoxInteractor):
    """
    Average in Qx direction
    """
    def __init__(self, base, axes, item=None, color='black', zorder=3):
        BoxInteractor.__init__(self, base, axes, item=item, color=color)
        self.base = base
        self._post_data()

    def _post_data(self):
        """
        Post data creating by averaging in Qx direction
        """
        from sas.sascalc.dataloader.manipulations import SlabX
        self.post_data(SlabX, direction="X")


class BoxInteractorY(BoxInteractor):
    """
    Average in Qy direction
    """
    def __init__(self, base, axes, item=None, color='black', zorder=3):
        BoxInteractor.__init__(self, base, axes, item=item, color=color)
        self.base = base
        self._post_data()

    def _post_data(self):
        """
        Post data creating by averaging in Qy direction
        """
        from sas.sascalc.dataloader.manipulations import SlabY
        self.post_data(SlabY, direction="Y")

