import math
from BaseInteractor import _BaseInteractor
from boxSum import PointInteractor
from boxSum import VerticalDoubleLine
from boxSum import HorizontalDoubleLine


class BoxMask(_BaseInteractor):
    """
    BoxMask Class: determine 2 rectangular area to find the pixel of
    a Data inside of box.

    Uses PointerInteractor , VerticalDoubleLine,HorizontalDoubleLine.

    :param zorder:  Artists with lower zorder values are drawn first.
    :param x_min: the minimum value of the x coordinate
    :param x_max: the maximum value of the x coordinate
    :param y_min: the minimum value of the y coordinate
    :param y_max: the maximum value of the y coordinate

    """
    def __init__(self, base, axes, color='black', zorder=3, side=None,
                 x_min=0.008, x_max=0.008, y_min=0.0025, y_max=0.0025):
        """
        """
        _BaseInteractor.__init__(self, base, axes, color=color)
        # # class initialization
        # # list of Boxmask markers
        self.markers = []
        self.axes = axes
        self.mask = None
        self.is_inside = side
        # # connect the artist for the motion
        self.connect = self.base.connect
        # # when qmax is reached the selected line is reset
        # the its previous value
        self.qmax = min(self.base.data.xmax, self.base.data.xmin)
        # # Define the box limits
        self.xmin = -1 * 0.5 * min(math.fabs(self.base.data.xmax),
                                   math.fabs(self.base.data.xmin))
        self.ymin = -1 * 0.5 * min(math.fabs(self.base.data.xmax),
                                   math.fabs(self.base.data.xmin))
        self.xmax = 0.5 * min(math.fabs(self.base.data.xmax),
                              math.fabs(self.base.data.xmin))
        self.ymax = 0.5 * min(math.fabs(self.base.data.xmax),
                              math.fabs(self.base.data.xmin))
        # # center of the box
        self.center_x = 0.0002
        self.center_y = 0.0003
        # # Number of points on the plot
        self.nbins = 20
        # # Define initial result the summation
        self.count = 0
        self.error = 0
        self.data = self.base.data
        # # Flag to determine if the current figure has moved
        # # set to False == no motion , set to True== motion
        self.has_move = False
        # # Create Box edges
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
                                                 color='grey',
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

    def clear(self):
        """
        Clear the slicer and all connected events related to this slicer
        """
        self.clear_markers()
        self.horizontal_lines.clear()
        self.vertical_lines.clear()
        self.center.clear()
        self.base.connect.clearall()

    def update(self):
        """
        Respond to changes in the model by recalculating the profiles and
        resetting the widgets.
        """
        # check if the center point has moved and update the figure accordingly
        if self.center.has_move:
            self.center.update()
            self.horizontal_lines.update(center=self.center)
            self.vertical_lines.update(center=self.center)
        # # check if the horizontal lines have moved and update
        # the figure accordingly
        if self.horizontal_lines.has_move:
            self.horizontal_lines.update()
            self.vertical_lines.update(y1=self.horizontal_lines.y1,
                                       y2=self.horizontal_lines.y2,
                                       height=self.horizontal_lines.half_height)
        # # check if the vertical lines have moved and update
        # the figure accordingly
        if self.vertical_lines.has_move:
            self.vertical_lines.update()
            self.horizontal_lines.update(x1=self.vertical_lines.x1,
                                         x2=self.vertical_lines.x2,
                                         width=self.vertical_lines.half_width)
        # if self.is_inside != None:
        out = self._post_data()
        return out

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
        from sas.dataloader.manipulations import Boxcut
        # # Data 2D for which the pixel will be summed
        data = self.base.data
        mask = data.mask
        # # the region of the summation
        x_min = self.horizontal_lines.x2
        x_max = self.horizontal_lines.x1
        y_min = self.vertical_lines.y2
        y_max = self.vertical_lines.y1
        mask = Boxcut(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)

        if self.is_inside:
            out = (mask(data) == False)
        else:
            out = (mask(data))
        # self.base.data.mask=out
        self.mask = mask
        return out

    def moveend(self, ev):
        """
        After a dragging motion this function is called to compute
        the error and the sum of pixel of a given data 2D
        """
        self.base.thaw_axes()
        # # post
        self._post_data()

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
        return params

    def get_mask(self):
        """
        return mask as a result of boxcut
        """
        mask = self.mask
        return mask

    def set_params(self, params):
        """
        Receive a dictionary and reset the slicer with values contained
        in the values of the dictionary.

        :param params: a dictionary containing name of slicer parameters and
           values the user assigned to the slicer.
        """
        x_max = math.fabs(params["Width"]) / 2
        y_max = math.fabs(params["Height"]) / 2

        self.center_x = params["center_x"]
        self.center_y = params["center_y"]
        # update the slicer given values of params
        self.center.update(center_x=self.center_x, center_y=self.center_y)
        self.horizontal_lines.update(center=self.center, width=x_max, height=y_max)
        self.vertical_lines.update(center=self.center, width=x_max, height=y_max)
        # compute the new error and sum given values of params
        self._post_data()

    def freeze_axes(self):
        self.base.freeze_axes()

    def thaw_axes(self):
        self.base.thaw_axes()

    def draw(self):
        self.base.update()

class inner_BoxMask(BoxMask):
    def __call__(self):
        self.base.data.mask = (self._post_data() == False)
