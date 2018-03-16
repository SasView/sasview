"""
Prototype plottable object support.

The main point of this prototype is to provide a clean separation between
the style (plotter details: color, grids, widgets, etc.) and substance
(application details: which information to plot).  Programmers should not be
dictating line colours and plotting symbols.

Unlike the problem of style in CSS or Word, where most paragraphs look
the same, each line on a graph has to be distinguishable from its neighbours.
Our solution is to provide parametric styles, in which a number of
different classes of object (e.g., reflectometry data, reflectometry
theory) representing multiple graph primitives cycle through a colour
palette provided by the underlying plotter.

A full treatment would provide perceptual dimensions of prominence and
distinctiveness rather than a simple colour number.

"""

# Design question: who owns the color?
# Is it a property of the plottable?
# Or of the plottable as it exists on the graph?
# Or if the graph?
# If a plottable can appear on multiple graphs, in some case the
# color should be the same on each graph in which it appears, and
# in other cases (where multiple plottables from different graphs
# coexist), the color should be assigned by the graph.  In any case
# once a plottable is placed on the graph its color should not
# depend on the other plottables on the graph.  Furthermore, if
# a plottable is added and removed from a graph and added again,
# it may be nice, but not necessary, to have the color persist.
#
# The safest approach seems to be to give ownership of color
# to the graph, which will allocate the colors along with the
# plottable.  The plottable will need to return the number of
# colors that are needed.
#
# The situation is less clear for symbols.  It is less clear
# how much the application requires that symbols be unique across
# all plots on the graph.

# Support for ancient python versions
import copy
import numpy as np
import sys
import logging

logger = logging.getLogger(__name__)

if 'any' not in dir(__builtins__):
    def any(L):
        for cond in L:
            if cond:
                return True
        return False

    def all(L):
        for cond in L:
            if not cond:
                return False
        return True


class Graph(object):
    """
    Generic plottables graph structure.

    Plot styles are based on color/symbol lists.  The user gets to select
    the list of colors/symbols/sizes to choose from, not the application
    developer.  The programmer only gets to add/remove lines from the
    plot and move to the next symbol/color.

    Another dimension is prominence, which refers to line sizes/point sizes.

    Axis transformations allow the user to select the coordinate view
    which provides clarity to the data.  There is no way we can provide
    every possible transformation for every application generically, so
    the plottable objects themselves will need to provide the transformations.
    Here are some examples from reflectometry: ::

       independent: x -> f(x)
          monitor scaling: y -> M*y
          log:  y -> log(y if y > min else min)
          cos:  y -> cos(y*pi/180)
       dependent:   x -> f(x,y)
          Q4:      y -> y*x^4
          fresnel: y -> y*fresnel(x)
       coordinated: x,y = f(x,y)
          Q:    x -> 2*pi/L (cos(x*pi/180) - cos(y*pi/180))
                y -> 2*pi/L (sin(x*pi/180) + sin(y*pi/180))
       reducing: x,y = f(x1,x2,y1,y2)
          spin asymmetry: x -> x1, y -> (y1 - y2)/(y1 + y2)
          vector net: x -> x1, y -> y1*cos(y2*pi/180)

    Multiple transformations are possible, such as Q4 spin asymmetry

    Axes have further complications in that the units of what are being
    plotted should correspond to the units on the axes.  Plotting multiple
    types on the same graph should be handled gracefully, e.g., by creating
    a separate tab for each available axis type, breaking into subplots,
    showing multiple axes on the same plot, or generating inset plots.
    Ultimately the decision should be left to the user.

    Graph properties such as grids/crosshairs should be under user control,
    as should the sizes of items such as axis fonts, etc.  No direct
    access will be provided to the application.

    Axis limits are mostly under user control.  If the user has zoomed or
    panned then those limits are preserved even if new data is plotted.
    The exception is when, e.g., scanning through a set of related lines
    in which the user may want to fix the limits so that user can compare
    the values directly.  Another exception is when creating multiple
    graphs sharing the same limits, though this case may be important
    enough that it is handled by the graph widget itself.  Axis limits
    will of course have to understand the effects of axis transformations.

    High level plottable objects may be composed of low level primitives.
    Operations such as legend/hide/show copy/paste, etc. need to operate
    on these primitives as a group.  E.g., allowing the user to have a
    working canvas where they can drag lines they want to save and annotate
    them.

    Graphs need to be printable.  A page layout program for entire plots
    would be nice.

    """
    def _xaxis_transformed(self, name, units):
        """
        Change the property of the x axis
        according to an axis transformation
        (as opposed to changing the basic properties)
        """
        if units != "":
            name = "%s (%s)" % (name, units)
        self.prop["xlabel"] = name
        self.prop["xunit"] = units

    def _yaxis_transformed(self, name, units):
        """
        Change the property of the y axis
        according to an axis transformation
        (as opposed to changing the basic properties)
        """
        if units != "":
            name = "%s (%s)" % (name, units)
        self.prop["ylabel"] = name
        self.prop["yunit"] = units

    def xaxis(self, name, units):
        """
        Properties of the x axis.
        """
        if units != "":
            name = "%s (%s)" % (name, units)
        self.prop["xlabel"] = name
        self.prop["xunit"] = units
        self.prop["xlabel_base"] = name
        self.prop["xunit_base"] = units

    def yaxis(self, name, units):
        """
        Properties of the y axis.
        """
        if units != "":
            name = "%s (%s)" % (name, units)
        self.prop["ylabel"] = name
        self.prop["yunit"] = units
        self.prop["ylabel_base"] = name
        self.prop["yunit_base"] = units

    def title(self, name):
        """
        Graph title
        """
        self.prop["title"] = name

    def get(self, key):
        """
        Get the graph properties
        """
        if key == "color":
            return self.color
        elif key == "symbol":
            return self.symbol
        else:
            return self.prop[key]

    def set(self, **kw):
        """
        Set the graph properties
        """
        for key in kw:
            if key == "color":
                self.color = kw[key] % len(self.colorlist)
            elif key == "symbol":
                self.symbol = kw[key] % len(self.symbollist)
            else:
                self.prop[key] = kw[key]

    def isPlotted(self, plottable):
        """Return True is the plottable is already on the graph"""
        if plottable in self.plottables:
            return True
        return False

    def add(self, plottable, color=None):
        """Add a new plottable to the graph"""
        # record the colour associated with the plottable
        if not plottable in self.plottables:
            if color is not None:
                self.plottables[plottable] = color
            else:
                self.color += plottable.colors()
                self.plottables[plottable] = self.color
                plottable.custom_color = self.color

    def changed(self):
        """Detect if any graphed plottables have changed"""
        return any([p.changed() for p in self.plottables])

    def get_range(self):
        """
        Return the range of all displayed plottables
        """
        min_value = None
        max_value = None
        for p in self.plottables:
            if p.hidden == True:
                continue
            if p.x is not None:
                for x_i in p.x:
                    if min_value is None or x_i < min_value:
                        min_value = x_i
                    if max_value is None or x_i > max_value:
                        max_value = x_i
        return min_value, max_value

    def replace(self, plottable):
        """Replace an existing plottable from the graph"""
        # If the user has set a custom color, ensure the new plot is the same color
        selected_color = plottable.custom_color
        selected_plottable = None
        for p in list(self.plottables.keys()):
            if plottable.id == p.id:
                selected_plottable = p
                if selected_color is None:
                    selected_color = self.plottables[p]
                break
        if selected_plottable is not None and selected_color is not None:
            del self.plottables[selected_plottable]
            plottable.custom_color = selected_color
            self.plottables[plottable] = selected_color

    def delete(self, plottable):
        """Remove an existing plottable from the graph"""
        if plottable in self.plottables:
            del self.plottables[plottable]
            self.color = len(self.plottables)

    def reset_scale(self):
        """
        Resets the scale transformation data to the underlying data
        """
        for p in self.plottables:
            p.reset_view()

    def reset(self):
        """Reset the graph."""
        self.color = -1
        self.symbol = 0
        self.prop = {"xlabel": "", "xunit": None,
                     "ylabel": "", "yunit": None,
                     "title": ""}
        self.plottables = {}

    def _make_labels(self):
        """
        """
        # Find groups of related plottables
        sets = {}
        for p in self.plottables:
            if p.__class__ in sets:
                sets[p.__class__].append(p)
            else:
                sets[p.__class__] = [p]
        # Ask each plottable class for a set of unique labels
        labels = {}
        for c in sets:
            labels.update(c.labels(sets[c]))
        return labels

    def get_plottable(self, name):
        """
        Return the plottable with the given
        name if it exists. Otherwise return None
        """
        for item in self.plottables:
            if item.name == name:
                return item
        return None

    def returnPlottable(self):
        """
        This method returns a dictionary of plottables contained in graph
        It is just by Plotpanel to interact with the complete list of plottables
        inside the graph.
        """
        return self.plottables

    def render(self, plot):
        """Redraw the graph"""
        plot.connect.clearall()
        plot.clear()
        plot.properties(self.prop)
        labels = self._make_labels()
        for p in self.plottables:
            if p.custom_color is not None:
                p.render(plot, color=p.custom_color, symbol=0,
                         markersize=p.markersize, label=labels[p])
            else:
                p.render(plot, color=self.plottables[p], symbol=0,
                         markersize=p.markersize, label=labels[p])
        plot.render()

    def __init__(self, **kw):
        self.reset()
        self.set(**kw)
        # Name of selected plottable, if any
        self.selected_plottable = None


# Transform interface definition
# No need to inherit from this class, just need to provide
# the same methods.
class Transform(object):
    """
    Define a transform plugin to the plottable architecture.

    Transforms operate on axes.  The plottable defines the
    set of transforms available for it, and the axes on which
    they operate.  These transforms can operate on the x axis
    only, the y axis only or on the x and y axes together.

    This infrastructure is not able to support transformations
    such as log and polar plots as these require full control
    over the drawing of axes and grids.

    A transform has a number of attributes.

    name
      user visible name for the transform.  This will
      appear in the context menu for the axis and the transform
      menu for the graph.

    type
      operational axis.  This determines whether the
      transform should appear on x,y or z axis context
      menus, or if it should appear in the context menu for
      the graph.

    inventory
      (not implemented)
      a dictionary of user settable parameter names and
      their associated types.  These should appear as keyword
      arguments to the transform call.  For example, Fresnel
      reflectivity requires the substrate density:
      ``{ 'rho': type.Value(10e-6/units.angstrom**2) }``
      Supply reasonable defaults in the callback so that
      limited plotting clients work even though they cannot
      set the inventory.

    """
    def __call__(self, plottable, **kwargs):
        """
        Transform the data.  Whenever a plottable is added
        to the axes, the infrastructure will apply all required
        transforms.  When the user selects a different representation
        for the axes (via menu, script, or context menu), all
        plottables on the axes will be transformed.  The
        plottable should store the underlying data but set
        the standard x,dx,y,dy,z,dz attributes appropriately.

        If the call raises a NotImplemented error the dataline
        will not be plotted.  The associated string will usually
        be 'Not a valid transform', though other strings are possible.
        The application may or may not display the message to the
        user, along with an indication of which plottable was at fault.

        """
        raise NotImplemented("Not a valid transform")

    # Related issues
    # ==============
    #
    # log scale:
    #    All axes have implicit log/linear scaling options.
    #
    # normalization:
    #    Want to display raw counts vs detector efficiency correction
    #    Want to normalize by time/monitor/proton current/intensity.
    #    Want to display by eg. counts per 3 sec or counts per 10000 monitor.
    #    Want to divide by footprint (ab initio, fitted or measured).
    #    Want to scale by attenuator values.
    #
    # compare/contrast:
    #    Want to average all visible lines with the same tag, and
    #    display difference from one particular line.  Not a transform
    #    issue?
    #
    # multiline graph:
    #    How do we show/hide data parts.  E.g., data or theory, or
    #    different polarization cross sections?  One way is with
    #    tags: each plottable has a set of tags and the tags are
    #    listed as check boxes above the plotting area.  Click a
    #    tag and all plottables with that tag are hidden on the
    #    plot and on the legend.
    #
    # nonconformant y-axes:
    #    What do we do with temperature vs. Q and reflectivity vs. Q
    #    on the same graph?
    #
    # 2D -> 1D:
    #    Want various slices through the data.  Do transforms apply
    #    to the sliced data as well?


class Plottable(object):
    """
    """
    # Short ascii name to refer to the plottable in a menu
    short_name = None
    # Fancy name
    name = None
    # Data
    x = None
    y = None
    dx = None
    dy = None
    # Parameter to allow a plot to be part of the list without being displayed
    hidden = False
    # Flag to set whether a plottable has an interactor or not
    interactive = True
    custom_color = None
    markersize = 5  # default marker size is 'size 5'

    def __init__(self):
        self.view = View()
        self._xaxis = ""
        self._xunit = ""
        self._yaxis = ""
        self._yunit = ""

    def __setattr__(self, name, value):
        """
        Take care of changes in View when data is changed.
        This method is provided for backward compatibility.
        """
        object.__setattr__(self, name, value)
        if name in ['x', 'y', 'dx', 'dy']:
            self.reset_view()
            # print "self.%s has been called" % name

    def set_data(self, x, y, dx=None, dy=None):
        """
        """
        self.x = x
        self.y = y
        self.dy = dy
        self.dx = dx
        self.transformView()

    def xaxis(self, name, units):
        """
        Set the name and unit of x_axis

        :param name: the name of x-axis
        :param units: the units of x_axis

        """
        self._xaxis = name
        self._xunit = units

    def yaxis(self, name, units):
        """
        Set the name and unit of y_axis

        :param name: the name of y-axis
        :param units: the units of y_axis

        """
        self._yaxis = name
        self._yunit = units

    def get_xaxis(self):
        """Return the units and name of x-axis"""
        return self._xaxis, self._xunit

    def get_yaxis(self):
        """ Return the units and name of y- axis"""
        return self._yaxis, self._yunit

    @classmethod
    def labels(cls, collection):
        """
        Construct a set of unique labels for a collection of plottables of
        the same type.

        Returns a map from plottable to name.

        """
        n = len(collection)
        label_dict = {}
        if n > 0:
            basename = str(cls).split('.')[-1]
            if n == 1:
                label_dict[collection[0]] = basename
            else:
                for i in range(len(collection)):
                    label_dict[collection[i]] = "%s %d" % (basename, i)
        return label_dict

    # #Use the following if @classmethod doesn't work
    # labels = classmethod(labels)
    def setLabel(self, labelx, labely):
        """
        It takes a label of the x and y transformation and set View parameters

        :param transx: The label of x transformation is sent by Properties Dialog
        :param transy: The label of y transformation is sent Properties Dialog

        """
        self.view.xLabel = labelx
        self.view.yLabel = labely

    def set_View(self, x, y):
        """Load View"""
        self.x = x
        self.y = y
        self.reset_view()

    def reset_view(self):
        """Reload view with new value to plot"""
        self.view = View(self.x, self.y, self.dx, self.dy)
        self.view.Xreel = self.view.x
        self.view.Yreel = self.view.y
        self.view.DXreel = self.view.dx
        self.view.DYreel = self.view.dy

    def render(self, plot):
        """
        The base class makes sure the correct units are being used for
        subsequent plottable.

        For now it is assumed that the graphs are commensurate, and if you
        put a Qx object on a Temperature graph then you had better hope
        that it makes sense.

        """
        plot.xaxis(self._xaxis, self._xunit)
        plot.yaxis(self._yaxis, self._yunit)

    def is_empty(self):
        """
        Returns True if there is no data stored in the plottable
        """
        if (self.x is not None and len(self.x) == 0
            and self.y is not None and len(self.y) == 0):
            return True
        return False

    def colors(self):
        """Return the number of colors need to render the object"""
        return 1

    def transformView(self):
        """
        It transforms x, y before displaying
        """
        self.view.transform(self.x, self.y, self.dx, self.dy)

    def returnValuesOfView(self):
        """
        Return View parameters and it is used by Fit Dialog
        """
        return self.view.returnXview()

    def check_data_PlottableX(self):
        """
        Since no transformation is made for log10(x), check that
        no negative values is plot in log scale
        """
        self.view.check_data_logX()

    def check_data_PlottableY(self):
        """
        Since no transformation is made for log10(y), check that
        no negative values is plot in log scale
        """
        self.view.check_data_logY()

    def transformX(self, transx, transdx):
        """
        Receive pointers to function that transform x and dx
        and set corresponding View pointers

        :param transx: pointer to function that transforms x
        :param transdx: pointer to function that transforms dx

        """
        self.view.setTransformX(transx, transdx)

    def transformY(self, transy, transdy):
        """
        Receive pointers to function that transform y and dy
        and set corresponding View pointers

        :param transy: pointer to function that transforms y
        :param transdy: pointer to function that transforms dy

        """
        self.view.setTransformY(transy, transdy)

    def onReset(self):
        """
        Reset x, y, dx, dy view with its parameters
        """
        self.view.onResetView()

    def onFitRange(self, xmin=None, xmax=None):
        """
        It limits View data range to plot from min to max

        :param xmin: the minimum value of x to plot.
        :param xmax: the maximum value of x to plot

        """
        self.view.onFitRangeView(xmin, xmax)


class View(object):
    """
    Representation of the data that might include a transformation
    """
    x = None
    y = None
    dx = None
    dy = None

    def __init__(self, x=None, y=None, dx=None, dy=None):
        """
        """
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        # To change x range to the reel range
        self.Xreel = self.x
        self.Yreel = self.y
        self.DXreel = self.dx
        self.DYreel = self.dy
        # Labels of x and y received from Properties Dialog
        self.xLabel = ""
        self.yLabel = ""
        # Function to transform x, y, dx and dy
        self.funcx = None
        self.funcy = None
        self.funcdx = None
        self.funcdy = None

    def transform(self, x=None, y=None, dx=None, dy=None):
        """
        Transforms the x,y,dx and dy vectors and stores
         the output in View parameters

        :param x: array of x values
        :param y: array of y values
        :param dx: array of  errors values on x
        :param dy: array of error values on y

        """
        # Sanity check
        # Do the transofrmation only when x and y are empty
        has_err_x = not (dx is None or len(dx) == 0)
        has_err_y = not (dy is None or len(dy) == 0)

        if(x is not None) and (y is not None):
            if dx is not None and not len(dx) == 0 and not len(x) == len(dx):
                msg = "Plottable.View: Given x and dx are not"
                msg += " of the same length"
                raise ValueError(msg)
            # Check length of y array
            if not len(y) == len(x):
                msg = "Plottable.View: Given y "
                msg += "and x are not of the same length"
                raise ValueError(msg)

            if dy is not None and not len(dy) == 0 and not len(y) == len(dy):
                msg = "Plottable.View: Given y and dy are not of the same "
                msg += "length: len(y)=%s, len(dy)=%s" % (len(y), len(dy))
                raise ValueError(msg)
            self.x = []
            self.y = []
            if has_err_x:
                self.dx = []
            else:
                self.dx = None
            if has_err_y:
                self.dy = []
            else:
                self.dy = None
            if not has_err_x:
                dx = np.zeros(len(x))
            if not has_err_y:
                dy = np.zeros(len(y))
            for i in range(len(x)):
                try:
                    tempx = self.funcx(x[i], y[i])
                    tempy = self.funcy(y[i], x[i])
                    if has_err_x:
                        tempdx = self.funcdx(x[i], y[i], dx[i], dy[i])
                    if has_err_y:
                        tempdy = self.funcdy(y[i], x[i], dy[i], dx[i])
                    self.x.append(tempx)
                    self.y.append(tempy)
                    if has_err_x:
                        self.dx.append(tempdx)
                    if has_err_y:
                        self.dy.append(tempdy)
                except Exception:
                    pass
            # Sanity check
            if not len(self.x) == len(self.y):
                msg = "Plottable.View: transformed x "
                msg += "and y are not of the same length"
                raise ValueError(msg)
            if has_err_x and not (len(self.x) == len(self.dx)):
                msg = "Plottable.View: transformed x and dx"
                msg += " are not of the same length"
                raise ValueError(msg)
            if has_err_y and not (len(self.y) == len(self.dy)):
                msg = "Plottable.View: transformed y"
                msg += " and dy are not of the same length"
                raise ValueError(msg)
            # Check that negative values are not plot on x and y axis for
            # log10 transformation
            self.check_data_logX()
            self.check_data_logY()
            # Store x ,y dx,and dy in their full range for reset
            self.Xreel = self.x
            self.Yreel = self.y
            self.DXreel = self.dx
            self.DYreel = self.dy

    def onResetView(self):
        """
        Reset x,y,dx and y in their full range  and in the initial scale
        in case their previous range has changed
        """
        self.x = self.Xreel
        self.y = self.Yreel
        self.dx = self.DXreel
        self.dy = self.DYreel

    def setTransformX(self, funcx, funcdx):
        """
        Receive pointers to function that transform x and dx
        and set corresponding View pointers

        :param transx: pointer to function that transforms x
        :param transdx: pointer to function that transforms dx
        """
        self.funcx = funcx
        self.funcdx = funcdx

    def setTransformY(self, funcy, funcdy):
        """
        Receive pointers to function that transform y and dy
        and set corresponding View pointers

        :param transx: pointer to function that transforms y
        :param transdx: pointer to function that transforms dy
        """
        self.funcy = funcy
        self.funcdy = funcdy

    def returnXview(self):
        """
        Return View  x,y,dx,dy
        """
        return self.x, self.y, self.dx, self.dy

    def check_data_logX(self):
        """
        Remove negative value in x vector to avoid plotting negative
        value of Log10
        """
        tempx = []
        tempdx = []
        tempy = []
        tempdy = []
        if self.dx is None:
            self.dx = np.zeros(len(self.x))
        if self.dy is None:
            self.dy = np.zeros(len(self.y))
        if self.xLabel == "log10(x)":
            for i in range(len(self.x)):
                try:
                    if self.x[i] > 0:
                        tempx.append(self.x[i])
                        tempdx.append(self.dx[i])
                        tempy.append(self.y[i])
                        tempdy.append(self.dy[i])
                except:
                    logger.error("check_data_logX: skipping point x %g", self.x[i])
                    logger.error(sys.exc_info()[1])
            self.x = tempx
            self.y = tempy
            self.dx = tempdx
            self.dy = tempdy

    def check_data_logY(self):
        """
        Remove negative value in y vector
        to avoid plotting negative value of Log10

        """
        tempx = []
        tempdx = []
        tempy = []
        tempdy = []
        if self.dx is None:
            self.dx = np.zeros(len(self.x))
        if self.dy is None:
            self.dy = np.zeros(len(self.y))
        if self.yLabel == "log10(y)":
            for i in range(len(self.x)):
                try:
                    if self.y[i] > 0:
                        tempx.append(self.x[i])
                        tempdx.append(self.dx[i])
                        tempy.append(self.y[i])
                        tempdy.append(self.dy[i])
                except:
                    logger.error("check_data_logY: skipping point %g", self.y[i])
                    logger.error(sys.exc_info()[1])

            self.x = tempx
            self.y = tempy
            self.dx = tempdx
            self.dy = tempdy

    def onFitRangeView(self, xmin=None, xmax=None):
        """
        It limits View data range to plot from min to max

        :param xmin: the minimum value of x to plot.
        :param xmax: the maximum value of x to plot

        """
        tempx = []
        tempdx = []
        tempy = []
        tempdy = []
        if self.dx is None:
            self.dx = np.zeros(len(self.x))
        if self.dy is None:
            self.dy = np.zeros(len(self.y))
        if xmin is not None and xmax is not None:
            for i in range(len(self.x)):
                if self.x[i] >= xmin and self.x[i] <= xmax:
                    tempx.append(self.x[i])
                    tempdx.append(self.dx[i])
                    tempy.append(self.y[i])
                    tempdy.append(self.dy[i])
            self.x = tempx
            self.y = tempy
            self.dx = tempdx
            self.dy = tempdy


class Data2D(Plottable):
    """
    2D data class for image plotting
    """
    def __init__(self, image=None, qx_data=None, qy_data=None,
                 err_image=None, xmin=None, xmax=None, ymin=None,
                 ymax=None, zmin=None, zmax=None):
        """
        Draw image
        """
        Plottable.__init__(self)
        self.name = "Data2D"
        self.label = None
        self.data = image
        self.qx_data = qx_data
        self.qy_data = qx_data
        self.err_data = err_image
        self.source = None
        self.detector = []

        # # Units for Q-values
        self.xy_unit = 'A^{-1}'
        # # Units for I(Q) values
        self.z_unit = 'cm^{-1}'
        self._zaxis = ''
        # x-axis unit and label
        self._xaxis = '\\rm{Q_{x}}'
        self._xunit = 'A^{-1}'
        # y-axis unit and label
        self._yaxis = '\\rm{Q_{y}}'
        self._yunit = 'A^{-1}'

        # ## might remove that later
        # # Vector of Q-values at the center of each bin in x
        self.x_bins = []
        # # Vector of Q-values at the center of each bin in y
        self.y_bins = []

        # x and y boundaries
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax

        self.zmin = zmin
        self.zmax = zmax
        self.id = None

    def xaxis(self, label, unit):
        """
        set x-axis

        :param label: x-axis label
        :param unit: x-axis unit

        """
        self._xaxis = label
        self._xunit = unit

    def yaxis(self, label, unit):
        """
        set y-axis

        :param label: y-axis label
        :param unit: y-axis unit

        """
        self._yaxis = label
        self._yunit = unit

    def zaxis(self, label, unit):
        """
        set z-axis

        :param label: z-axis label
        :param unit: z-axis unit

        """
        self._zaxis = label
        self._zunit = unit

    def setValues(self, datainfo=None):
        """
        Use datainfo object to initialize data2D

        :param datainfo: object

        """
        self.image = copy.deepcopy(datainfo.data)
        self.qx_data = copy.deepcopy(datainfo.qx_data)
        self.qy_data = copy.deepcopy(datainfo.qy_data)
        self.err_image = copy.deepcopy(datainfo.err_data)

        self.xy_unit = datainfo.Q_unit
        self.z_unit = datainfo.I_unit
        self._zaxis = datainfo._zaxis

        self.xaxis(datainfo._xunit, datainfo._xaxis)
        self.yaxis(datainfo._yunit, datainfo._yaxis)
        # x and y boundaries
        self.xmin = datainfo.xmin
        self.xmax = datainfo.xmax
        self.ymin = datainfo.ymin
        self.ymax = datainfo.ymax
        # # Vector of Q-values at the center of each bin in x
        self.x_bins = datainfo.x_bins
        # # Vector of Q-values at the center of each bin in y
        self.y_bins = datainfo.y_bins

    def set_zrange(self, zmin=None, zmax=None):
        """
        """
        if zmin < zmax:
            self.zmin = zmin
            self.zmax = zmax
        else:
            raise "zmin is greater or equal to zmax "

    def render(self, plot, **kw):
        """
        Renders the plottable on the graph

        """
        plot.image(self.data, self.qx_data, self.qy_data,
                   self.xmin, self.xmax, self.ymin,
                   self.ymax, self.zmin, self.zmax, **kw)

    def changed(self):
        """
        """
        return False

    @classmethod
    def labels(cls, collection):
        """Build a label mostly unique within a collection"""
        label_dict = {}
        for item in collection:
            if item.label == "Data2D":
                item.label = item.name
            label_dict[item] = item.label
        return label_dict


class Data1D(Plottable):
    """
    Data plottable: scatter plot of x,y with errors in x and y.
    """

    def __init__(self, x, y, dx=None, dy=None, lam=None, dlam=None):
        """
        Draw points specified by x[i],y[i] in the current color/symbol.
        Uncertainty in x is given by dx[i], or by (xlo[i],xhi[i]) if the
        uncertainty is asymmetric.  Similarly for y uncertainty.

        The title appears on the legend.
        The label, if it is different, appears on the status bar.
        """
        Plottable.__init__(self)
        self.name = "data"
        self.label = "data"
        self.x = x
        self.y = y
        self.lam = lam
        self.dx = dx
        self.dy = dy
        self.dlam = dlam
        self.source = None
        self.detector = None
        self.xaxis('', '')
        self.yaxis('', '')
        self.view = View(self.x, self.y, self.dx, self.dy)
        self.symbol = 0
        self.custom_color = None
        self.markersize = 5
        self.id = None
        self.zorder = 1
        self.hide_error = False

    def render(self, plot, **kw):
        """
        Renders the plottable on the graph
        """
        if self.interactive == True:
            kw['symbol'] = self.symbol
            kw['id'] = self.id
            kw['hide_error'] = self.hide_error
            kw['markersize'] = self.markersize
            plot.interactive_points(self.view.x, self.view.y,
                                    dx=self.view.dx, dy=self.view.dy,
                                    name=self.name, zorder=self.zorder, **kw)
        else:
            kw['id'] = self.id
            kw['hide_error'] = self.hide_error
            kw['symbol'] = self.symbol
            kw['color'] = self.custom_color
            kw['markersize'] = self.markersize
            plot.points(self.view.x, self.view.y, dx=self.view.dx,
                        dy=self.view.dy, zorder=self.zorder,
                        marker=self.symbollist[self.symbol], **kw)

    def changed(self):
        return False

    @classmethod
    def labels(cls, collection):
        """Build a label mostly unique within a collection"""
        label_dict = {}
        for item in collection:
            if item.label == "data":
                item.label = item.name
            label_dict[item] = item.label
        return label_dict


class Theory1D(Plottable):
    """
    Theory plottable: line plot of x,y with confidence interval y.
    """
    def __init__(self, x, y, dy=None):
        """
        Draw lines specified in x[i],y[i] in the current color/symbol.
        Confidence intervals in x are given by dx[i] or by (xlo[i],xhi[i])
        if the limits are asymmetric.

        The title is the name that will show up on the legend.
        """
        Plottable.__init__(self)
        msg = "Theory1D is no longer supported, please use Data1D and change symbol.\n"
        raise DeprecationWarning(msg)

class Fit1D(Plottable):
    """
    Fit plottable: composed of a data line plus a theory line.  This
    is treated like a single object from the perspective of the graph,
    except that it will have two legend entries, one for the data and
    one for the theory.

    The color of the data and theory will be shared.

    """
    def __init__(self, data=None, theory=None):
        """
        """
        Plottable.__init__(self)
        self.data = data
        self.theory = theory

    def render(self, plot, **kw):
        """
        """
        self.data.render(plot, **kw)
        self.theory.render(plot, **kw)

    def changed(self):
        """
        """
        return self.data.changed() or self.theory.changed()


# ---------------------------------------------------------------
class Text(Plottable):
    """
    """
    def __init__(self, text=None, xpos=0.5, ypos=0.9, name='text'):
        """
        Draw the user-defined text in plotter
        We can specify the position of text
        """
        Plottable.__init__(self)
        self.name = name
        self.text = text
        self.xpos = xpos
        self.ypos = ypos

    def render(self, plot, **kw):
        """
        """
        from matplotlib import transforms

        xcoords = transforms.blended_transform_factory(plot.subplot.transAxes,
                                                       plot.subplot.transAxes)
        plot.subplot.text(self.xpos,
                          self.ypos,
                          self.text,
                          label=self.name,
                          transform=xcoords)

    def setText(self, text):
        """Set the text string."""
        self.text = text

    def getText(self, text):
        """Get the text string."""
        return self.text

    def set_x(self, x):
        """
        Set the x position of the text
        ACCEPTS: float
        """
        self.xpos = x

    def set_y(self, y):
        """
        Set the y position of the text
        ACCEPTS: float
        """
        self.ypos = y


# ---------------------------------------------------------------
class Chisq(Plottable):
    """
    Chisq plottable plots the chisq
    """
    def __init__(self, chisq=None):
        """
        Draw the chisq in plotter
        We can specify the position of chisq
        """
        Plottable.__init__(self)
        self.name = "chisq"
        self._chisq = chisq
        self.xpos = 0.5
        self.ypos = 0.9

    def render(self, plot, **kw):
        """
        """
        if  self._chisq is None:
            chisqTxt = r'$\chi^2=$'
        else:
            chisqTxt = r'$\chi^2=%g$' % (float(self._chisq))

        from matplotlib import transforms

        xcoords = transforms.blended_transform_factory(plot.subplot.transAxes,
                                                      plot.subplot.transAxes)
        plot.subplot.text(self.xpos,
                          self.ypos,
                          chisqTxt, label='chisq',
                          transform=xcoords)

    def setChisq(self, chisq):
        """
        Set the chisq value.
        """
        self._chisq = chisq


######################################################

def sample_graph():
    import numpy as np

    # Construct a simple graph
    if False:
        x = np.array([1, 2, 3, 4, 5, 6], 'd')
        y = np.array([4, 5, 6, 5, 4, 5], 'd')
        dy = np.array([0.2, 0.3, 0.1, 0.2, 0.9, 0.3])
    else:
        x = np.linspace(0, 1., 10000)
        y = np.sin(2 * np.pi * x * 2.8)
        dy = np.sqrt(100 * np.abs(y)) / 100
    data = Data1D(x, y, dy=dy)
    data.xaxis('distance', 'm')
    data.yaxis('time', 's')
    graph = Graph()
    graph.title('Walking Results')
    graph.add(data)
    graph.add(Theory1D(x, y, dy=dy))
    return graph


def demo_plotter(graph):
    import wx
    from pylab_plottables import Plotter
    # from mplplotter import Plotter

    # Make a frame to show it
    app = wx.PySimpleApp()
    frame = wx.Frame(None, -1, 'Plottables')
    plotter = Plotter(frame)
    frame.Show()

    # render the graph to the pylab plotter
    graph.render(plotter)

    class GraphUpdate(object):
        callnum = 0

        def __init__(self, graph, plotter):
            self.graph, self.plotter = graph, plotter

        def __call__(self):
            if self.graph.changed():
                self.graph.render(self.plotter)
                return True
            return False

        def onIdle(self, event):
            self.callnum = self.callnum + 1
            if self.__call__():
                pass  # event.RequestMore()
    update = GraphUpdate(graph, plotter)
    frame.Bind(wx.EVT_IDLE, update.onIdle)
    app.MainLoop()
