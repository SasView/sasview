import numpy

from sas.qtgui.Plotting.Slicers.BaseInteractor import BaseInteractor
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
        self.xmin = -1 * 0.5 * min(numpy.fabs(self.data.xmax),
                                   numpy.fabs(self.data.xmin))
        self.ymin = -1 * 0.5 * min(numpy.fabs(self.data.xmax),
                                   numpy.fabs(self.data.xmin))
        self.xmax = 0.5 * min(numpy.fabs(self.data.xmax),
                              numpy.fabs(self.data.xmin))
        self.ymax = 0.5 * min(numpy.fabs(self.data.xmax),
                              numpy.fabs(self.data.xmin))

        # when reach qmax reset the graph
        self.qmax = max(self.data.xmax, self.data.xmin,
                        self.data.ymax, self.data.ymin)

        # center of the box
        # puts the center of box at the middle of the q-range (??)
        self.center_x = self.qmax/2
        self.center_y = self.qmax/2

        # Number of points on the plot
        self.nbins = 30
        # If True, I(|Q|) will be return, otherwise,
        # negative q-values are allowed
        # Should this be set to True??
        self.fold = True
        # reference of the current  Slab averaging
        self.averager = None
        # Create vertical and horizaontal lines for the rectangle
        self.horizontal_lines = HorizontalDoubleLine(self,
                                                     self.axes,
                                                     color='blue',
                                                     zorder=zorder,
                                                     y=self.ymax,
                                                     x=self.xmax,
                                                     center_x=self.center_x,
                                                     center_y=self.center_y)
        self.horizontal_lines.qmax = self.qmax

        self.vertical_lines = VerticalDoubleLine(self,
                                                 self.axes,
                                                 color='black',
                                                 zorder=zorder,
                                                 y=self.ymax,
                                                 x=self.xmax,
                                                 center_x=self.center_x,
                                                 center_y=self.center_y)
        self.vertical_lines.qmax = self.qmax

        # PointINteractor determins the center of the box
        self.center = PointInteractor(self,
                                      self.axes, color='grey',
                                      zorder=zorder,
                                      center_x=self.center_x,
                                      center_y=self.center_y)

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
        # # If the data file does not tell us what the axes are, just assume...
        new_plot.xaxis("\\rm{Q}", "A^{-1}")
        new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")

        data = self.data
        if hasattr(data, "scale") and data.scale == 'linear' and \
                self.data.name.count("Residuals") > 0:
            new_plot.ytransform = 'y'
            new_plot.yaxis("\\rm{Residuals} ", "/")

        #new_plot. = "2daverage" + self.data.name
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



class PointInteractor(BaseInteractor):
    """
    Draw a point that can be dragged with the marker.
    this class controls the motion the center of the BoxSum
    """
    def __init__(self, base, axes, color='black', zorder=5, center_x=0.0,
                 center_y=0.0):
        BaseInteractor.__init__(self, base, axes, color=color)
        # Initialization the class
        self.markers = []
        self.axes = axes
        # center coordinates
        self.x = center_x
        self.y = center_y
        # saved value of the center coordinates
        self.save_x = center_x
        self.save_y = center_y
        # Create a marker
        self.center_marker = self.axes.plot([self.x], [self.y], linestyle='',
                                            marker='s', markersize=10,
                                            color=self.color, alpha=0.6,
                                            pickradius=5, label="pick",
                                            zorder=zorder,
                                            visible=True)[0]
        # Draw a point
        self.center = self.axes.plot([self.x], [self.y],
                                     linestyle='-', marker='',
                                     color=self.color,
                                     visible=True)[0]
        # Flag to determine the motion this point
        self.has_move = False
        # connecting the marker to allow them to move
        self.connect_markers([self.center_marker])
        # Update the figure
        self.update()

    def setLayer(self, n):
        """
        Allow adding plot to the same panel
        @param n: the number of layer
        """
        self.layernum = n
        self.update()

    def clear(self):
        """
        Clear this figure and its markers
        """
        self.clear_markers()
        self.center.remove()
        self.center_marker.remove()

    def update(self, center_x=None, center_y=None):
        """
        Draw the new roughness on the graph.
        """
        if center_x is not None:
            self.x = center_x
        if center_y is not None:
            self.y = center_y
        self.center_marker.set(xdata=[self.x], ydata=[self.y])
        self.center.set(xdata=[self.x], ydata=[self.y])

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_x = self.x
        self.save_y = self.y

    def moveend(self, ev):
        """
        """
        self.has_move = False
        self.base.moveend(ev)

    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.y = self.save_y
        self.x = self.save_x

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.x = x
        self.y = y
        self.has_move = True
        self.base.base.update()

    def setCursor(self, x, y):
        """
        """
        self.move(x, y, None)
        self.update()

class VerticalDoubleLine(BaseInteractor):
    """
    Draw 2 vertical lines moving in opposite direction and centered on
    a point (PointInteractor)
    """
    def __init__(self, base, axes, color='black', zorder=5, x=0.5, y=0.5,
                 center_x=0.0, center_y=0.0):
        BaseInteractor.__init__(self, base, axes, color=color)
        # Initialization the class
        self.markers = []
        self.axes = axes
        # Center coordinates
        self.center_x = center_x
        self.center_y = center_y
        # defined end points vertical lignes and their saved values
        self.y1 = y + self.center_y
        self.save_y1 = self.y1

        delta = self.y1 - self.center_y
        self.y2 = self.center_y - delta
        self.save_y2 = self.y2

        self.x1 = x + self.center_x
        self.save_x1 = self.x1

        delta = self.x1 - self.center_x
        self.x2 = self.center_x - delta
        self.save_x2 = self.x2
        # # save the color of the line
        self.color = color
        # the height of the rectangle
        self.half_height = numpy.fabs(y)
        self.save_half_height = numpy.fabs(y)
        # the with of the rectangle
        self.half_width = numpy.fabs(self.x1 - self.x2) / 2
        self.save_half_width = numpy.fabs(self.x1 - self.x2) / 2
        # Create marker
        self.right_marker = self.axes.plot([self.x1], [0], linestyle='',
                                           marker='s', markersize=10,
                                           color=self.color, alpha=0.6,
                                           pickradius=5, label="pick",
                                           zorder=zorder, visible=True)[0]

        # Define the left and right lines of the rectangle
        self.right_line = self.axes.plot([self.x1, self.x1], [self.y1, self.y2],
                                         linestyle='-', marker='',
                                         color=self.color, visible=True)[0]
        self.left_line = self.axes.plot([self.x2, self.x2], [self.y1, self.y2],
                                        linestyle='-', marker='',
                                        color=self.color, visible=True)[0]
        # Flag to determine if the lines have moved
        self.has_move = False
        # Connection the marker and draw the pictures
        self.connect_markers([self.right_marker])
        self.update()

    def setLayer(self, n):
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
        self.right_marker.remove()
        self.right_line.remove()
        self.left_line.remove()

    def update(self, x1=None, x2=None, y1=None, y2=None, width=None,
               height=None, center=None):
        """
        Draw the new roughness on the graph.
        :param x1: new maximum value of x coordinates
        :param x2: new minimum value of x coordinates
        :param y1: new maximum value of y coordinates
        :param y2: new minimum value of y coordinates
        :param width: is the width of the new rectangle
        :param height: is the height of the new rectangle
        :param center: provided x, y  coordinates of the center point
        """
        # Save the new height, witdh of the rectangle if given as a param
        if width is not None:
            self.half_width = width
        if height is not None:
            self.half_height = height
        # If new  center coordinates are given draw the rectangle
        # given these value
        if center is not None:
            self.center_x = center.x
            self.center_y = center.y
            self.x1 = self.half_width + self.center_x
            self.x2 = -self.half_width + self.center_x
            self.y1 = self.half_height + self.center_y
            self.y2 = -self.half_height + self.center_y

            self.right_marker.set(xdata=[self.x1], ydata=[self.center_y])
            self.right_line.set(xdata=[self.x1, self.x1],
                                ydata=[self.y1, self.y2])
            self.left_line.set(xdata=[self.x2, self.x2],
                               ydata=[self.y1, self.y2])
            return
        # if x1, y1, y2, y3 are given draw the rectangle with this value
        if x1 is not None:
            self.x1 = x1
        if x2 is not None:
            self.x2 = x2
        if y1 is not None:
            self.y1 = y1
        if y2 is not None:
            self.y2 = y2
        # Draw 2 vertical lines and a marker
        self.right_marker.set(xdata=[self.x1], ydata=[self.center_y])
        self.right_line.set(xdata=[self.x1, self.x1], ydata=[self.y1, self.y2])
        self.left_line.set(xdata=[self.x2, self.x2], ydata=[self.y1, self.y2])

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_x2 = self.x2
        self.save_y2 = self.y2
        self.save_x1 = self.x1
        self.save_y1 = self.y1
        self.save_half_height = self.half_height
        self.save_half_width = self.half_width

    def moveend(self, ev):
        """
        After a dragging motion reset the flag self.has_move to False
        """
        self.has_move = False
        self.base.moveend(ev)

    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.y2 = self.save_y2
        self.x2 = self.save_x2
        self.y1 = self.save_y1
        self.x1 = self.save_x1
        self.half_height = self.save_half_height
        self.half_width = self.save_half_width

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.x1 = x
        delta = self.x1 - self.center_x
        self.x2 = self.center_x - delta
        self.half_width = numpy.fabs(self.x1 - self.x2) / 2
        self.has_move = True
        self.base.base.update()

    def setCursor(self, x, y):
        """
        Update the figure given x and y
        """
        self.move(x, y, None)
        self.update()

class HorizontalDoubleLine(BaseInteractor):
    """
    Select an annulus through a 2D plot
    """
    def __init__(self, base, axes, color='black', zorder=5, x=0.5, y=0.5,
                 center_x=0.0, center_y=0.0):

        BaseInteractor.__init__(self, base, axes, color=color)
        # Initialization the class
        self.markers = []
        self.axes = axes
        # Center coordinates
        self.center_x = center_x
        self.center_y = center_y
        self.y1 = y + self.center_y
        self.save_y1 = self.y1
        delta = self.y1 - self.center_y
        self.y2 = self.center_y - delta
        self.save_y2 = self.y2
        self.x1 = x + self.center_x
        self.save_x1 = self.x1
        delta = self.x1 - self.center_x
        self.x2 = self.center_x - delta
        self.save_x2 = self.x2
        self.color = color
        self.half_height = numpy.fabs(y)
        self.save_half_height = numpy.fabs(y)
        self.half_width = numpy.fabs(x)
        self.save_half_width = numpy.fabs(x)
        self.top_marker = self.axes.plot([0], [self.y1], linestyle='',
                                         marker='s', markersize=10,
                                         color=self.color, alpha=0.6,
                                         pickradius=5, label="pick",
                                         zorder=zorder, visible=True)[0]

        # Define 2 horizotnal lines
        self.top_line = self.axes.plot([self.x1, -self.x1], [self.y1, self.y1],
                                       linestyle='-', marker='',
                                       color=self.color, visible=True)[0]
        self.bottom_line = self.axes.plot([self.x1, -self.x1],
                                          [self.y2, self.y2],
                                          linestyle='-', marker='',
                                          color=self.color, visible=True)[0]
        # Flag to determine if the lines have moved
        self.has_move = False
        # connection the marker and draw the pictures
        self.connect_markers([self.top_marker])
        self.update()

    def setLayer(self, n):
        """
        Allow adding plot to the same panel
        @param n: the number of layer
        """
        self.layernum = n
        self.update()

    def clear(self):
        """
        Clear this figure and its markers
        """
        self.clear_markers()
        self.top_marker.remove()
        self.bottom_line.remove()
        self.top_line.remove()

    def update(self, x1=None, x2=None, y1=None, y2=None,
               width=None, height=None, center=None):
        """
        Draw the new roughness on the graph.
        :param x1: new maximum value of x coordinates
        :param x2: new minimum value of x coordinates
        :param y1: new maximum value of y coordinates
        :param y2: new minimum value of y coordinates
        :param width: is the width of the new rectangle
        :param height: is the height of the new rectangle
        :param center: provided x, y  coordinates of the center point
        """
        # Save the new height, witdh of the rectangle if given as a param
        if width is not None:
            self.half_width = width
        if height is not None:
            self.half_height = height
        # If new  center coordinates are given draw the rectangle
        # given these value
        if center is not None:
            self.center_x = center.x
            self.center_y = center.y
            self.x1 = self.half_width + self.center_x
            self.x2 = -self.half_width + self.center_x

            self.y1 = self.half_height + self.center_y
            self.y2 = -self.half_height + self.center_y

            self.top_marker.set(xdata=[self.center_x], ydata=[self.y1])
            self.top_line.set(xdata=[self.x1, self.x2],
                              ydata=[self.y1, self.y1])
            self.bottom_line.set(xdata=[self.x1, self.x2],
                                 ydata=[self.y2, self.y2])
            return
        # if x1, y1, y2, y3 are given draw the rectangle with this value
        if x1 is not None:
            self.x1 = x1
        if x2 is not None:
            self.x2 = x2
        if y1 is not None:
            self.y1 = y1
        if y2 is not None:
            self.y2 = y2
        # Draw 2 vertical lines and a marker
        self.top_marker.set(xdata=[self.center_x], ydata=[self.y1])
        self.top_line.set(xdata=[self.x1, self.x2], ydata=[self.y1, self.y1])
        self.bottom_line.set(xdata=[self.x1, self.x2], ydata=[self.y2, self.y2])

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_x2 = self.x2
        self.save_y2 = self.y2
        self.save_x1 = self.x1
        self.save_y1 = self.y1
        self.save_half_height = self.half_height
        self.save_half_width = self.half_width

    def moveend(self, ev):
        """
        After a dragging motion reset the flag self.has_move to False
        """
        self.has_move = False
        self.base.moveend(ev)

    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.y2 = self.save_y2
        self.x2 = self.save_x2
        self.y1 = self.save_y1
        self.x1 = self.save_x1
        self.half_height = self.save_half_height
        self.half_width = self.save_half_width

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.y1 = y
        delta = self.y1 - self.center_y
        self.y2 = self.center_y - delta
        self.half_height = numpy.fabs(self.y1) - self.center_y
        self.has_move = True
        self.base.base.update()

    def setCursor(self, x, y):
        """
        Update the figure given x and y
        """
        self.move(x, y, None)
        self.update()



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

