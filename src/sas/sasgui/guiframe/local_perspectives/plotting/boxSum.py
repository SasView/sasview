"""
    Boxsum Class: determine 2 rectangular area to compute
    the sum of pixel of a Data.
"""
import math
import wx
from BaseInteractor import _BaseInteractor
from sas.sasgui.guiframe.events import SlicerParamUpdateEvent
from sas.sasgui.guiframe.events import EVT_SLICER_PARS
from sas.sasgui.guiframe.events import StatusEvent


class BoxSum(_BaseInteractor):
    """
        Boxsum Class: determine 2 rectangular area to compute
        the sum of pixel of a Data.
        Uses PointerInteractor , VerticalDoubleLine,HorizontalDoubleLine.
        @param zorder:  Artists with lower zorder values are drawn first.
        @param x_min: the minimum value of the x coordinate
        @param x_max: the maximum value of the x coordinate
        @param y_min: the minimum value of the y coordinate
        @param y_max: the maximum value of the y coordinate

    """
    def __init__(self, base, axes, color='black', zorder=3, x_min=0.008,
                 x_max=0.008, y_min=0.0025, y_max=0.0025):
        """
        """
        _BaseInteractor.__init__(self, base, axes, color=color)
        # # class initialization
        # # list of Boxsmun markers
        self.markers = []
        self.axes = axes
        # # connect the artist for the motion
        self.connect = self.base.connect
        # # when qmax is reached the selected line is reset the its previous value
        self.qmax = min(self.base.data2D.xmax, self.base.data2D.xmin)
        # # Define the boxsum limits
        self.xmin = -1 * 0.5 * min(math.fabs(self.base.data2D.xmax),
                                   math.fabs(self.base.data2D.xmin))
        self.ymin = -1 * 0.5 * min(math.fabs(self.base.data2D.xmax),
                                   math.fabs(self.base.data2D.xmin))
        self.xmax = 0.5 * min(math.fabs(self.base.data2D.xmax),
                              math.fabs(self.base.data2D.xmin))
        self.ymax = 0.5 * min(math.fabs(self.base.data2D.xmax),
                              math.fabs(self.base.data2D.xmin))
        # # center of the boxSum
        self.center_x = 0.0002
        self.center_y = 0.0003
        # # Number of points on the plot
        self.nbins = 20
        # # Define initial result the summation
        self.count = 0
        self.error = 0
        self.total = 0
        self.totalerror = 0
        self.points = 0
        # # Flag to determine if the current figure has moved
        # # set to False == no motion , set to True== motion
        self.has_move = False
        # # Create Boxsum edges
        self.horizontal_lines = HorizontalDoubleLine(self,
                                                     self.base.subplot,
                                                     color='blue',
                                                     zorder=zorder,
                                                     y=self.ymax,
                                                     x=self.xmax,
                                                     center_x=self.center_x,
                                                     center_y=self.center_y)
        self.horizontal_lines.qmax = self.qmax

        self.vertical_lines = VerticalDoubleLine(self,
                                                 self.base.subplot,
                                                 color='black',
                                                 zorder=zorder,
                                                 y=self.ymax,
                                                 x=self.xmax,
                                                 center_x=self.center_x,
                                                 center_y=self.center_y)
        self.vertical_lines.qmax = self.qmax

        self.center = PointInteractor(self,
                                      self.base.subplot, color='grey',
                                      zorder=zorder,
                                      center_x=self.center_x,
                                      center_y=self.center_y)
        # # Save the name of the slicer panel associate with this slicer
        self.panel_name = ""
        # # Update and post slicer parameters
        self.update()
        self._post_data()
        # # Bind to slice parameter events
        self.base.Bind(EVT_SLICER_PARS, self._onEVT_SLICER_PARS)

    def set_panel_name(self, name):
        """
            Store the name of the panel associated to this slicer
            @param name: the name of this panel
        """
        self.panel_name = name

    def _onEVT_SLICER_PARS(self, event):
        """
            receive an event containing parameters values to reset the slicer
            @param event: event of type SlicerParameterEvent with params as
            attribute
        """
        # # Post e message to declare what kind of event has being received
        wx.PostEvent(self.base.parent,
                     StatusEvent(status="Boxsum._onEVT_SLICER_PARS"))
        event.Skip()
        # # reset the slicer with the values contains the event.params dictionary
        if event.type == self.__class__.__name__:
            self.set_params(event.params)
            self.base.update()

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
        self.horizontal_lines.clear()
        self.vertical_lines.clear()
        self.center.clear()
        self.base.connect.clearall()
        self.base.Unbind(EVT_SLICER_PARS)

    def update(self):
        """
        Respond to changes in the model by recalculating the profiles and
        resetting the widgets.
        """
        # # check if the center point has moved and update the figure accordingly
        if self.center.has_move:
            self.center.update()
            self.horizontal_lines.update(center=self.center)
            self.vertical_lines.update(center=self.center)
        # # check if the horizontal lines have moved and
        # update the figure accordingly
        if self.horizontal_lines.has_move:
            self.horizontal_lines.update()
            self.vertical_lines.update(y1=self.horizontal_lines.y1,
                                       y2=self.horizontal_lines.y2,
                                       height=self.horizontal_lines.half_height)
        # # check if the vertical lines have moved and
        # update the figure accordingly
        if self.vertical_lines.has_move:
            self.vertical_lines.update()
            self.horizontal_lines.update(x1=self.vertical_lines.x1,
                                         x2=self.vertical_lines.x2,
                                         width=self.vertical_lines.half_width)

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.base.freeze_axes()
        self.horizontal_lines.save(ev)
        self.vertical_lines.save(ev)
        self.center.save(ev)

    def _post_data(self):
        """
        Get the limits of the boxsum and compute the sum of the pixel
        contained in that region and the error on that sum
        """
        # # the region of the summation
        x_min = self.horizontal_lines.x2
        x_max = self.horizontal_lines.x1
        y_min = self.vertical_lines.y2
        y_max = self.vertical_lines.y1
        # #computation of the sum and its error
        from sas.sascalc.dataloader.manipulations import Boxavg
        box = Boxavg(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)
        self.count, self.error = box(self.base.data2D)
        # Dig out number of points summed, SMK & PDB, 04/03/2013
        from sas.sascalc.dataloader.manipulations import Boxsum
        boxtotal = Boxsum(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)
        self.total, self.totalerror, self.points = boxtotal(self.base.data2D)

    def moveend(self, ev):
        """
            After a dragging motion this function is called to compute
            the error and the sum of pixel of a given data 2D
        """
        self.base.thaw_axes()
        # # compute error an d sum of data's pixel
        self._post_data()
        # # Create and event ( posted to guiframe)that  set the
        # #current slicer parameter to a panel of name self.panel_name
        self.type = self.__class__.__name__
        params = self.get_params()
        event = SlicerParamUpdateEvent(type=self.type,
                                       params=params,
                                       panel_name=self.panel_name)
        wx.PostEvent(self.base.parent, event)

    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.horizontal_lines.restore()
        self.vertical_lines.restore()
        self.center.restore()

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
        Store a copy of values of parameters of the slicer into a dictionary.
        :return params: the dictionary created
        """
        params = {}
        params["Width"] = math.fabs(self.vertical_lines.half_width) * 2
        params["Height"] = math.fabs(self.horizontal_lines.half_height) * 2
        params["center_x"] = self.center.x
        params["center_y"] = self.center.y
        params["num_points"] = self.points
        params["avg"] = self.count
        params["avg_error"] = self.error
        params["sum"] = self.total
        params["sum_error"] = self.totalerror
        return params

    def get_result(self):
        """
            return the result of box summation
        """
        result = {}
        result["num_points"] = self.points
        result["avg"] = self.count
        result["avg_error"] = self.error
        result["sum"] = self.total
        result["sum_error"] = self.totalerror
        return result

    def set_params(self, params):
        """
        Receive a dictionary and reset the slicer with values contained
        in the values of the dictionary.
        :param params: a dictionary containing name of slicer parameters and values the user assigned to the slicer.
        """
        x_max = math.fabs(params["Width"]) / 2
        y_max = math.fabs(params["Height"]) / 2

        self.center_x = params["center_x"]
        self.center_y = params["center_y"]
        # update the slicer given values of params
        self.center.update(center_x=self.center_x, center_y=self.center_y)
        self.horizontal_lines.update(center=self.center,
                                     width=x_max, height=y_max)
        self.vertical_lines.update(center=self.center,
                                   width=x_max, height=y_max)
        # compute the new error and sum given values of params
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



class PointInteractor(_BaseInteractor):
    """
    Draw a point that can be dragged with the marker.
    this class controls the motion the center of the BoxSum
    """
    def __init__(self, base, axes, color='black', zorder=5, center_x=0.0,
                 center_y=0.0):
        """
        """
        _BaseInteractor.__init__(self, base, axes, color=color)
        # # Initialization the class
        self.markers = []
        self.axes = axes
        # center coordinates
        self.x = center_x
        self.y = center_y
        # # saved value of the center coordinates
        self.save_x = center_x
        self.save_y = center_y
        # # Create a marker
        self.center_marker = self.axes.plot([self.x], [self.y], linestyle='',
                                            marker='s', markersize=10,
                                            color=self.color, alpha=0.6,
                                            pickradius=5, label="pick",
                                            zorder=zorder,
                                            visible=True)[0]
        # # Draw a point
        self.center = self.axes.plot([self.x], [self.y],
                                     linestyle='-', marker='',
                                     color=self.color,
                                     visible=True)[0]
        # # Flag to determine the motion this point
        self.has_move = False
        # # connecting the marker to allow them to move
        self.connect_markers([self.center_marker])
        # # Update the figure
        self.update()

    def set_layer(self, n):
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
        try:
            self.center.remove()
            self.center_marker.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]

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
        self.base.freeze_axes()

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

    def set_cursor(self, x, y):
        """
        """
        self.move(x, y, None)
        self.update()

class VerticalDoubleLine(_BaseInteractor):
    """
         Draw 2 vertical lines moving in opposite direction and centered on
         a point (PointInteractor)
    """
    def __init__(self, base, axes, color='black', zorder=5, x=0.5, y=0.5,
                 center_x=0.0, center_y=0.0):
        """
        """
        _BaseInteractor.__init__(self, base, axes, color=color)
        # # Initialization the class
        self.markers = []
        self.axes = axes
        # # Center coordinates
        self.center_x = center_x
        self.center_y = center_y
        # # defined end points vertical lignes and their saved values
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
        # # the height of the rectangle
        self.half_height = math.fabs(y)
        self.save_half_height = math.fabs(y)
        # # the with of the rectangle
        self.half_width = math.fabs(self.x1 - self.x2) / 2
        self.save_half_width = math.fabs(self.x1 - self.x2) / 2
        # # Create marker
        self.right_marker = self.axes.plot([self.x1], [0], linestyle='',
                                           marker='s', markersize=10,
                                           color=self.color, alpha=0.6,
                                           pickradius=5, label="pick",
                                           zorder=zorder, visible=True)[0]

        # # define the left and right lines of the rectangle
        self.right_line = self.axes.plot([self.x1, self.x1], [self.y1, self.y2],
                                         linestyle='-', marker='',
                                         color=self.color, visible=True)[0]
        self.left_line = self.axes.plot([self.x2, self.x2], [self.y1, self.y2],
                                        linestyle='-', marker='',
                                        color=self.color, visible=True)[0]
        # # Flag to determine if the lines have moved
        self.has_move = False
        # # connection the marker and draw the pictures
        self.connect_markers([self.right_marker])
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
        try:
            self.right_marker.remove()
            self.right_line.remove()
            self.left_line.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]

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
        # # save the new height, witdh of the rectangle if given as a param
        if width is not None:
            self.half_width = width
        if height is not None:
            self.half_height = height
        # # If new  center coordinates are given draw the rectangle
        # #given these value
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
        # # if x1, y1, y2, y3 are given draw the rectangle with this value
        if x1 is not None:
            self.x1 = x1
        if x2 is not None:
            self.x2 = x2
        if y1 is not None:
            self.y1 = y1
        if y2 is not None:
            self.y2 = y2
        # # Draw 2 vertical lines and a marker
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
        self.base.freeze_axes()

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
        self.half_width = math.fabs(self.x1 - self.x2) / 2
        self.has_move = True
        self.base.base.update()

    def set_cursor(self, x, y):
        """
            Update the figure given x and y
        """
        self.move(x, y, None)
        self.update()

class HorizontalDoubleLine(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self, base, axes, color='black', zorder=5, x=0.5, y=0.5,
                 center_x=0.0, center_y=0.0):

        _BaseInteractor.__init__(self, base, axes, color=color)
        # # Initialization the class
        self.markers = []
        self.axes = axes
        # # Center coordinates
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
        self.half_height = math.fabs(y)
        self.save_half_height = math.fabs(y)
        self.half_width = math.fabs(x)
        self.save_half_width = math.fabs(x)
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
        # # Flag to determine if the lines have moved
        self.has_move = False
        # # connection the marker and draw the pictures
        self.connect_markers([self.top_marker])
        self.update()

    def set_layer(self, n):
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
        try:
            self.top_marker.remove()
            self.bottom_line.remove()
            self.top_line.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]

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
        # # save the new height, witdh of the rectangle if given as a param
        if width is not None:
            self.half_width = width
        if height is not None:
            self.half_height = height
        # # If new  center coordinates are given draw the rectangle
        # #given these value
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
        # # if x1, y1, y2, y3 are given draw the rectangle with this value
        if x1 is not None:
            self.x1 = x1
        if x2 is not None:
            self.x2 = x2
        if y1 is not None:
            self.y1 = y1
        if y2 is not None:
            self.y2 = y2
        # # Draw 2 vertical lines and a marker
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
        self.base.freeze_axes()

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
        self.half_height = math.fabs(self.y1) - self.center_y
        self.has_move = True
        self.base.base.update()

    def set_cursor(self, x, y):
        """
            Update the figure given x and y
        """
        self.move(x, y, None)
        self.update()
