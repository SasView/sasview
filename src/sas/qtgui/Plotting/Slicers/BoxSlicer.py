import logging

import numpy

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.SlicerModel import SlicerModel
from sas.qtgui.Plotting.Slicers.BaseInteractor import BaseInteractor


class BoxInteractor(BaseInteractor, SlicerModel):
    """
    BoxInteractor plots a data1D average of a rectangular area defined in
    a Data2D object. The data1D averaging itself is performed in sasdata
    by manipulations.py

    This class uses two other classes, HorizontalLines and VerticalLines,
    to define the rectangle area: x1, x2 ,y1, y2. It is subclassed by
    BoxInteractorX and BoxInteracgtorY which define the direction of the
    average. BoxInteractorX averages all the points from y1 to y2 as a
    function of Q_x and BoxInteractorY averages all the points from
    x1 to x2 as a function of Q_y
    """

    def __init__(self, base, axes, item=None, color='black', zorder=3, direction=None):
        BaseInteractor.__init__(self, base, axes, color=color)
        SlicerModel.__init__(self)
        # Class initialization
        self.markers = []
        self.axes = axes
        self._item = item
        # connecting artist
        self.connect = self.base.connect
        # which direction is the preferred interaction direction
        self.direction = direction
        # determine x y  values
        if self.direction == "Y":
            self.half_width = 0.1 * (self.data.xmax - self.data.xmin) / 2
            self.half_height = 1.0 * (self.data.ymax - self.data.ymin) / 2
        elif self.direction == "X":
            self.half_width = 1.0 * (self.data.xmax - self.data.xmin) / 2
            self.half_height = 0.1 * (self.data.ymax - self.data.ymin) / 2
        else:
            msg = "post data:no Box Average direction was supplied"
            raise ValueError(msg)

        # center of the box
        # puts the center of box at the middle of the data q-range
        self.center_x = (self.data.xmin + self.data.xmax) /2
        self.center_y = (self.data.ymin + self.data.ymax) /2

        # Number of points on the plot
        self.nbins = 100
        # If True, I(|Q|) will be return, otherwise,
        # negative q-values are allowed
        # Default to true on initialize
        self.fold = True
        # reference of the current  Slab averaging
        self.averager = None
        # Flag to determine if the current figure has moved
        # set to False == no motion , set to True== motion
        # NOTE: This is not currently ever used. All moves happen in the
        # individual interactors not the whole slicker. Thus the move(ev)
        # currently does a pass. Default to False at initialize anyway
        # (nothing has moved yet) for possible future implementation.
        self.has_move = False
        # Create vertical and horizontal lines for the rectangle
        self.horizontal_lines = HorizontalDoubleLine(self,
                                                     self.axes,
                                                     color='blue',
                                                     zorder=zorder,
                                                     half_height=self.half_height,
                                                     half_width=self.half_width,
                                                     center_x=self.center_x,
                                                     center_y=self.center_y)

        self.vertical_lines = VerticalDoubleLine(self,
                                                 self.axes,
                                                 color='black',
                                                 zorder=zorder,
                                                 half_height=self.half_height,
                                                 half_width=self.half_width,
                                                 center_x=self.center_x,
                                                 center_y=self.center_y)

        # PointInteractor determines the center of the box
        self.center = PointInteractor(self,
                                      self.axes, color='grey',
                                      zorder=zorder,
                                      center_x=self.center_x,
                                      center_y=self.center_y)

        # draw the rectangle and plot the data 1D resulting
        # from averaging of the data2D
        self.update_and_post()
        # Set up the default slicer parameters for the parameter editor
        # window (in SlicerModel.py)
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
        self.center.clear()


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

        # check if the horizontal lines have moved and
        # update the figure accordingly
        if self.horizontal_lines.has_move:
            self.horizontal_lines.update()
            self.vertical_lines.update(y1=self.horizontal_lines.y1,
                                       y2=self.horizontal_lines.y2,
                                       half_height=self.horizontal_lines.half_height)
        # check if the vertical lines have moved and
        # update the figure accordingly
        if self.vertical_lines.has_move:
            self.vertical_lines.update()
            self.horizontal_lines.update(x1=self.vertical_lines.x1,
                                         x2=self.vertical_lines.x2,
                                         half_width=self.vertical_lines.half_width)

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.vertical_lines.save(ev)
        self.horizontal_lines.save(ev)
        self.center.save(ev)

    def _post_data(self, new_slab=None, nbins=None, direction=None):
        """
        post 1D data averaging in Qx or Qy given new_slab type

        :param new_slab: slicer that determine with direction to average
        :param nbins: the number of points plotted when averaging
        :param direction: the direction of averaging

        """
        if self.direction is None:
            self.direction = direction

        x_min = self.vertical_lines.x2
        x_max = self.vertical_lines.x1
        y_min = self.horizontal_lines.y2
        y_max = self.horizontal_lines.y1

        if nbins is not None:
            self.nbins = nbins
        if self.averager is None:
            if new_slab is None:
                msg = "post data:cannot average , averager is empty"
                raise ValueError(msg)
            self.averager = new_slab
        # Calculate the bin width from number of points. The only tricky part
        # is when the box stradles 0 but 0 is not the center.
        #
        # todo: This should probably NOT be calculated here. Instead it should
        #       be calculated as part of manipulations.py which already does
        #       almost the same math to calculate the bins anyway. See for
        #       example under "Build array of Q intervals" in the _avg method
        #       of the _Slab class. Moreover, scripts would more likely prefer
        #       to pass number of points than bin width anyway. This will
        #       however be an API change!
        #            Added by PDB -- 3/31/2024
        if self.direction == "X":
            if self.fold and (x_max * x_min <= 0):
                x_low = 0
                x_high = max(abs(x_min),abs(x_max))
            else:
                x_low = x_min
                x_high = x_max
            bin_width = (x_high - x_low) / self.nbins
        elif self.direction == "Y":
            if self.fold and (y_max * y_min >= 0):
                y_low = 0
                y_high = max(abs(y_min),abs(y_max))
            else:
                y_low = y_min
                y_high = y_max
            bin_width = (y_high - y_low) / self.nbins
        else:
            msg = "post data:no Box Average direction was supplied"
            raise ValueError(msg)

        # Average data2D given Qx or Qy
        box = self.averager(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
                            bin_width=bin_width)
        box.fold = self.fold
        # Check for data inside ROI. A bit of a kludge but faster than
        # checking twice: once to check and once to do the calculation
        # Adding a function to manipulations.py that returns the maksed data
        # set as an object which can then be checked for not being empty before
        # being passed back to the calculation in manipulations.py?
        #
        # Note that it no simple way to ensure that data is in the ROI without
        # checking (unless one can guarantee a perfect grid in x,y).
        try:
            boxavg = box(self.data)
        except ValueError as ve:
            logging.warning(str(ve))
            self.restore(ev=None)
            self.update()
            self.draw()
            self.setModelFromParams()
            return

        # Now that we know the move valid, update the half_width and half_height
        self.half_width = numpy.fabs(x_max - x_min)/2
        self.half_height = numpy.fabs(y_max - y_min)/2

        # Create Data1D to plot
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
        if self.direction == "X":
            new_plot.xaxis("\\rm{Q_x}", "A^{-1}")
        elif self.direction == "Y":
            new_plot.xaxis("\\rm{Q_y}", "A^{-1}")
        else:
            new_plot.xaxis("\\rm{Q}", "A^{-1}")
        new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")

        data = self.data
        if hasattr(data, "scale") and data.scale == 'linear' and \
                self.data.name.count("Residuals") > 0:
            new_plot.ytransform = 'y'
            new_plot.yaxis("\\rm{Residuals} ", "/")

        new_plot.id = (self.averager.__name__) + self.data.name
        # Create id to remove plots after changing slicer so they don't keep
        # showing up after being closed
        new_plot.type_id = "Slicer" + self.data.name
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
        Restore the roughness for this layer. Only restores things that have
        moved. Otherwise you are restoring too far back.

        Save is only done when the mouse is clicked not when it is released.
        Thus, if vertical lines have changed, they will move horizontal lines
        also, but the original state of those horizontal lines has not been
        saved (there was no click event on the horizontal lines). However,
        restoring the vertical lines and then doing an updated will take care
        of the related values in horizontal lines.
        """
        if self.horizontal_lines.has_move:
            self.horizontal_lines.restore(ev)
        if self.vertical_lines.has_move:
            self.vertical_lines.restore(ev)
        if self.center.has_move:
            self.center.restore(ev)

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
        params["half_width"] = self.vertical_lines.half_width
        params["half_height"] = self.horizontal_lines.half_height
        params["nbins"] = self.nbins
        params["center_x"] = self.center.x
        params["center_y"] = self.center.y
        params["fold"] = self.fold
        return params

    def setParams(self, params):
        """
        Receive a dictionary and reset the slicer with values contained
        in the values of the dictionary.

        :param params: a dictionary containing name of slicer parameters and
            values the user assigned to the slicer.
        """
        self.half_width = params["half_width"]
        self.half_height = params["half_height"]
        self.nbins = params["nbins"]
        self.fold = params["fold"]
        self.center_x = params["center_x"]
        self.center_y = params["center_y"]

        # save current state of the ROI in case the change leaves no data in
        # the ROI and thus a disallowed move. Also set the has_move flags to
        # true in case we have to restore this saved state.
        self.save(ev=None)
        self.center.has_move = True
        self.horizontal_lines.has_move = True
        self.vertical_lines.has_move = True
        # Now update the ROI based on the change
        self.center.update(center_x=self.center_x, center_y=self.center_y)
        self.horizontal_lines.update(center=self.center,
                                     half_width=self.half_width, half_height=self.half_height)
        self.vertical_lines.update(center=self.center,
                                   half_width=self.half_width, half_height=self.half_height)
        # Compute and plot the 1D average based on these parameters
        self._post_data()
        # Now move is over so turn off flags
        self.center.has_move = False
        self.horizontal_lines.has_move = False
        self.vertical_lines.has_move = False
        self.draw()

    def validate(self, param_name, param_value):
        """
        Validate input from user.
        Values get checked at apply time.
        * nbins cannot be zero or samller
        * The full ROI should stay within the data. thus center_x and center_y
          are restricted such that the center +/- width (or height) cannot be
          greate or smaller than data max/min.
        * The width/height should not be set so small as to leave no data in
          the ROI. Here we only make sure that the width/height is not zero
          as done when dragging the vertical or horizontal lines. We let the
          call to _post_data capture the ValueError of no points in ROI
          raised by manipulations.py, log the message and negate the entry
          at that point.
        """
        isValid = True

        if param_name =='half_width':
            # Can't be negative for sure. Also, it should not be so small that
            # there remains no points to average in the ROI. We leave this
            # second check to manipulations.py
            if param_value <= 0:
                logging.warning("The box width is too small. Please adjust.")
                isValid = False
        elif param_name =='half_height':
            # Can't be negative for sure. Also, it should not be so small that
            # there remains no points to average in the ROI. We leave this
            # second check to manipulations.py
            if param_value <= 0:
                logging.warning("The box height is too small. Please adjust.")
                isValid = False
        elif param_name == 'nbins':
            # Can't be negative or 0
            if param_value < 1:
                logging.warning("Number of bins cannot be less than or equal"\
                                 "to 0. Please adjust.")
                isValid = False
        elif param_name == 'center_x':
            # Keep the full ROI box within the data (only moving x here)
            if (param_value + self.half_width) >= self.data.xmax or \
                    (param_value- self.half_width) <= self.data.xmin:
                logging.warning("The ROI must be fully contained within the"\
                                "2D data. Please adjust")
                isValid = False
        elif param_name == 'center_y':
            # Keep the full ROI box within the data (only moving y here)
            if (param_value + self.half_height) >= self.data.ymax or \
                    (param_value - self.half_height) <= self.data.ymin:
                logging.warning("The ROI must be fully contained within the"\
                                "2D data. Please adjust")
                isValid = False
        return isValid

    def draw(self):
        """
        Draws the Canvas using the canvas.Draw from the calling class
        that instantiated this object.
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
        # Flag to determine if this point has moved
        self.has_move = False
        # Flag to verify if the last move was valid
        self.valid_move = True
        # connecting the marker to allow it to be moved
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

    def restore(self, ev):
        """
        Restore the roughness for this layer.
        """
        self.y = self.save_y
        self.x = self.save_x

    def move(self, x, y, ev):
        """
        Process move to a new position. BaseInteractor checks that the center
        is within the data. Here we check to make sure that the center move
        does not cause any part of the ROI box to move outside the data.
        """
        if x - self.base.half_width < self.base.data.xmin:
            self.x = self.base.data.xmin + self.base.half_width
        elif x + self.base.half_width > self.base.data.xmax:
            self.x = self.base.data.xmax - self.base.half_width
        else:
            self.x = x
        if y - self.base.half_height < self.base.data.ymin:
            self.y = self.base.data.ymin + self.base.half_height
        elif y + self.base.half_height > self.base.data.ymax:
            self.y = self.base.data.ymax - self.base.half_height
        else:
            self.y = y
        self.has_move = True
        self.base.update()
        self.base.draw()

    def setCursor(self, x, y):
        """
        ..todo:: the cursor moves are currently being captured somewhere upstream
                 of BaseInteractor so this never gets called.
        """
        self.move(x, y, None)
        self.update()

class VerticalDoubleLine(BaseInteractor):
    """
    Draw 2 vertical lines that can move symmetrically in opposite directions in x and centered on
    a point (PointInteractor). It also defines the top and bottom y positions of a box.
    """
    def __init__(self, base, axes, color='black', zorder=5, half_width=0.5, half_height=0.5,
                 center_x=0.0, center_y=0.0):
        BaseInteractor.__init__(self, base, axes, color=color)
        # Initialization of the class
        self.markers = []
        self.axes = axes
        # the height of the rectangle
        self.half_height = half_height
        self.save_half_height = self.half_height
        # the width of the rectangle
        self.half_width = half_width
        self.save_half_width = self.half_width
        # Center coordinates
        self.center_x = center_x
        self.center_y = center_y
        # defined end points vertical and horizontal lines and their saved values
        self.y1 = self.center_y + self.half_height
        self.save_y1 = self.y1
        self.y2 = self.center_y - self.half_height
        self.save_y2 = self.y2
        self.x1 = self.center_x + self.half_width
        self.save_x1 = self.x1
        self.x2 = self.center_x - self.half_width
        self.save_x2 = self.x2
        # save the color of the line
        self.color = color
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
        # Flag to verify if the last move was valid
        self.valid_move = True
        # Connect the marker and draw the picture
        self.connect_markers([self.right_marker, self.right_line])
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

    def update(self, x1=None, x2=None, y1=None, y2=None, half_width=None,
               half_height=None, center=None):
        """
        Draw the new roughness on the graph.
        :param x1: new maximum value of x coordinates
        :param x2: new minimum value of x coordinates
        :param y1: new maximum value of y coordinates
        :param y2: new minimum value of y coordinates
        :param half_ width: is the half width of the new rectangle
        :param half_height: is the half height of the new rectangle
        :param center: provided x, y  coordinates of the center point
        """
        # Save the new height, width of the rectangle if given as a param
        if half_width is not None:
            self.half_width = half_width
        if half_height is not None:
            self.half_height = half_height
        # If new center coordinates are given draw the rectangle
        # given these value
        if center is not None:
            self.center_x = center.x
            self.center_y = center.y
            self.x1 = self.center_x + self.half_width
            self.x2 = self.center_x - self.half_width
            self.y1 = self.center_y + self.half_height
            self.y2 = self.center_y - self.half_height

            self.right_marker.set(xdata=[self.x1], ydata=[self.center_y])
            self.right_line.set(xdata=[self.x1, self.x1],
                                ydata=[self.y1, self.y2])
            self.left_line.set(xdata=[self.x2, self.x2],
                               ydata=[self.y1, self.y2])
            return
        # if x1, y1, x2, y2 are given draw the rectangle with these values
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
        can restore on Esc. This save is run on mouse click (not a drag event)
        by BaseInteractor
        """
        self.save_x2 = self.x2
        self.save_y2 = self.y2
        self.save_x1 = self.x1
        self.save_y1 = self.y1
        self.save_half_height = self.half_height
        self.save_half_width = self.half_width

    def moveend(self, ev):
        """
        After a dragging motion update the 1D average plot and then reset the
        flag self.has_move to False.
        """
        self.base.moveend(ev)
        self.has_move = False

    def restore(self, ev):
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
        In principle, the move must not create a box without any data points
        in it. For the dragging (continuous move), we make sure that the width
        or height are not negative and that the entire ROI resides withing the
        data. We leave the check of whether there are any data in that ROI to
        the manipulations.py which is called from _post_data, itself being
        called on moveend(ev).
        """
        if x - self.center_x > 0:
            self.valid_move = True
            if self.center_x - (x - self.center_x) < self.base.data.xmin:
                self.x1 = self.center_x - (self.base.data.xmin - self.center_x)
            else:
                self.x1 = x
            self.half_width = self.x1 - self.center_x
            self.x2 = self.center_x - self.half_width
            self.has_move = True
            self.base.update()
            self.base.draw()
        else:
            if self.valid_move:
                self.valid_move = False
                logging.warning("the ROI cannot be negative")

    def setCursor(self, x, y):
        """
        Update the figure given x and y
        """
        self.move(x, y, None)
        self.update()

class HorizontalDoubleLine(BaseInteractor):
    """
    Draw 2 vertical lines that can move symmetrically in opposite directions in y and centered on
    a point (PointInteractor). It also defines the left and right x positions of a box.
    """
    def __init__(self, base, axes, color='black', zorder=5, half_width=0.5, half_height=0.5,
                 center_x=0.0, center_y=0.0):

        BaseInteractor.__init__(self, base, axes, color=color)
        # Initialization of the class
        self.markers = []
        self.axes = axes
        # Center coordinates
        self.center_x = center_x
        self.center_y = center_y
        # Box half width and height and  horizontal and vertical limits
        self.half_height = half_height
        self.save_half_height = self.half_height
        self.half_width = half_width
        self.save_half_width = self.half_width
        self.y1 = self.center_y + half_height
        self.save_y1 = self.y1
        self.y2 = self.center_y - half_height
        self.save_y2 = self.y2
        self.x1 = self.center_x + self.half_width
        self.save_x1 = self.x1
        self.x2 = self.center_x - self.half_width
        self.save_x2 = self.x2
        # Color
        self.color = color
        self.top_marker = self.axes.plot([0], [self.y1], linestyle='',
                                         marker='s', markersize=10,
                                         color=self.color, alpha=0.6,
                                         pickradius=5, label="pick",
                                         zorder=zorder, visible=True)[0]

        # Define 2 horizontal lines
        self.top_line = self.axes.plot([self.x1, -self.x1], [self.y1, self.y1],
                                       linestyle='-', marker='',
                                       color=self.color, visible=True)[0]
        self.bottom_line = self.axes.plot([self.x1, -self.x1],
                                          [self.y2, self.y2],
                                          linestyle='-', marker='',
                                          color=self.color, visible=True)[0]
        # Flag to determine if the lines have moved
        self.has_move = False
        # Flag to verify if the last move was valid
        self.valid_move = True
        # connect the marker and draw the picture
        self.connect_markers([self.top_marker, self.top_line])
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
               half_width=None, half_height=None, center=None):
        """
        Draw the new roughness on the graph.
        :param x1: new maximum value of x coordinates
        :param x2: new minimum value of x coordinates
        :param y1: new maximum value of y coordinates
        :param y2: new minimum value of y coordinates
        :param half_width: is the half width of the new rectangle
        :param half_height: is the half height of the new rectangle
        :param center: provided x, y  coordinates of the center point
        """
        # Save the new height, width of the rectangle if given as a param
        if half_width is not None:
            self.half_width = half_width
        if half_height is not None:
            self.half_height = half_height
        # If new  center coordinates are given draw the rectangle
        # given these value
        if center is not None:
            self.center_x = center.x
            self.center_y = center.y
            self.x1 = self.center_x + self.half_width
            self.x2 = self.center_x - self.half_width

            self.y1 = self.center_y + self.half_height
            self.y2 = self.center_y - self.half_height

            self.top_marker.set(xdata=[self.center_x], ydata=[self.y1])
            self.top_line.set(xdata=[self.x1, self.x2],
                              ydata=[self.y1, self.y1])
            self.bottom_line.set(xdata=[self.x1, self.x2],
                                 ydata=[self.y2, self.y2])
            return
        # if x1, y1, x2, y2 are given draw the rectangle with these values
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
        can restore on Esc. This save is run on mouse click (not a drag event)
        by BaseInteractor
        """
        self.save_x2 = self.x2
        self.save_y2 = self.y2
        self.save_x1 = self.x1
        self.save_y1 = self.y1
        self.save_half_height = self.half_height
        self.save_half_width = self.half_width

    def moveend(self, ev):
        """
        After a dragging motion update the 1D average plot and then reset the
        flag self.has_move to False.
        """
        self.base.moveend(ev)
        self.has_move = False

    def restore(self, ev):
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
        In principle, the move must not create a box without any data points
        in it. For the dragging (continuous move), we make sure that the width
        or height are not negative and that the entire ROI resides withing the
        data. We leave the check of whether there are any data in that ROI to
        the manipulations.py which is called from _post_data, itself being
        called on moveend(ev).
        """
        if y - self.center_y > 0:
            self.valid_move = True
            if self.center_y - (y - self.center_y) < self.base.data.ymin:
                self.y1 = self.center_y - (self.base.data.ymin - self.center_y)
            else:
                self.y1 = y
            self.half_height = self.y1 - self.center_y
            self.y2 = self.center_y - self.half_height
            self.has_move = True
            self.base.update()
            self.base.draw()
        else:
            if self.valid_move:
                self.valid_move = False
                logging.warning("the ROI cannot be negative")

    def setCursor(self, x, y):
        """
        Update the figure given x and y
        """
        self.move(x, y, None)
        self.update()



class BoxInteractorX(BoxInteractor):
    """
    Average in Qx direction. The data for all Qy at a constant Qx are
    averaged together to provide a 1D array in Qx (to be plotted as a function
    of Qx)
    """

    def __init__(self, base, axes, item=None, color='black', zorder=3):
        BoxInteractor.__init__(self, base, axes, item=item, color=color, direction="X")
        self.base = base

    def _post_data(self, new_slab=None, nbins=None, direction=None):
        """
        Post data creating by averaging in Qx direction
        """
        from sasdata.data_util.manipulations import SlabX
        super()._post_data(SlabX, direction="X")


class BoxInteractorY(BoxInteractor):
    """
    Average in Qy direction. The data for all Qx at a constant Qy are
    averaged together to provide a 1D array in Qy (to be plotted as a function
    of Qy)
    """

    def __init__(self, base, axes, item=None, color='black', zorder=3):
        BoxInteractor.__init__(self, base, axes, item=item, color=color, direction="Y")
        self.base = base

    def _post_data(self, new_slab=None, nbins=None, direction=None):
        """
        Post data creating by averaging in Qy direction
        """
        from sasdata.data_util.manipulations import SlabY
        super()._post_data(SlabY, direction="Y")
