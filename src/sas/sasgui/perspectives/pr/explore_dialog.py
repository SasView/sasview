
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################

"""
Dialog panel to explore the P(r) inversion results for a range
of D_max value. User picks a number of points and a range of
distances, then can toggle between inversion outputs and see
their distribution as a function of D_max.
"""


import wx
import numpy as np
import logging
import sys

logger = logging.getLogger(__name__)

# Avoid Matplotlib complaining about the lack of legend on the plot
import warnings
warnings.simplefilter("ignore")

# Import plotting classes
from sas.sasgui.plottools.PlotPanel import PlotPanel
from sas.sasgui.plottools import Data1D as Model1D
from sas.sasgui.guiframe.gui_style import GUIFRAME_ID
from sas.sasgui.plottools.plottables import Graph

from .pr_widgets import PrTextCtrl

# Default number of points on the output plot
DEFAULT_NPTS = 10
# Default output parameter to plot
DEFAULT_OUTPUT = 'Chi2/dof'

class OutputPlot(PlotPanel):
    """
    Plot panel used to show the selected results as a function
    of D_max
    """
    ## Title for plottools
    window_caption = "D Explorer"

    def __init__(self, d_min, d_max, parent, id= -1, color=None, \
                 dpi=None, style=wx.NO_FULL_REPAINT_ON_RESIZE, **kwargs):
        """
        Initialization. The parameters added to PlotPanel are:

        :param d_min: Minimum value of D_max to explore
        :param d_max: Maximum value of D_max to explore

        """
        PlotPanel.__init__(self, parent, id=id, style=style, **kwargs)

        self.parent = parent
        self.min = d_min
        self.max = d_max
        self.npts = DEFAULT_NPTS

        step = (self.max - self.min) / (self.npts - 1)
        self.x = np.arange(self.min, self.max + step * 0.01, step)
        dx = np.zeros(len(self.x))
        y = np.ones(len(self.x))
        dy = np.zeros(len(self.x))

        # Plot area
        self.plot = Model1D(self.x, y=y, dy=dy)
        self.plot.name = DEFAULT_OUTPUT
        self.plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM

        # Graph        
        self.graph = Graph()
        self.graph.xaxis("\\rm{D_{max}}", 'A')
        self.graph.yaxis("\\rm{%s}" % DEFAULT_OUTPUT, "")
        self.graph.add(self.plot)
        self.graph.render(self)

        self.toolbar.DeleteToolByPos(0)
        self.toolbar.DeleteToolByPos(8)
        self.toolbar.Realize()

    def onContextMenu(self, event):
        """
        Default context menu for the plot panel

        :TODO: Would be nice to add printing and log/linear scales.
            The current verison of plottools no longer plays well with
            plots outside of guiframe. Guiframe team needs to fix this.
        """
        # Slicer plot popup menu
        wx_id = wx.NewId()
        slicerpop = wx.Menu()
        slicerpop.Append(wx_id, '&Save image', 'Save image as PNG')
        wx.EVT_MENU(self, wx_id, self.onSaveImage)

        wx_id = wx.NewId()
        slicerpop.AppendSeparator()
        slicerpop.Append(wx_id, '&Reset Graph')
        wx.EVT_MENU(self, wx_id, self.onResetGraph)

        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(slicerpop, pos)

class Results(object):
    """
    Class to hold the inversion output parameters
    as a function of D_max
    """
    def __init__(self):
        """
        Initialization. Create empty arrays
        and dictionary of labels.
        """
        # Array of output for each inversion
        self.chi2 = []
        self.osc = []
        self.pos = []
        self.pos_err = []
        self.rg = []
        self.iq0 = []
        self.bck = []
        self.d_max = []

        # Dictionary of outputs
        self.outputs = {}
        self.outputs['Chi2/dof'] = ["\chi^2/dof", "a.u.", self.chi2]
        self.outputs['Oscillation parameter'] = ["Osc", "a.u.", self.osc]
        self.outputs['Positive fraction'] = ["P^+", "a.u.", self.pos]
        self.outputs['1-sigma positive fraction'] = ["P^+_{1\ \sigma}",
                                                     "a.u.", self.pos_err]
        self.outputs['Rg'] = ["R_g", "A", self.rg]
        self.outputs['I(q=0)'] = ["I(q=0)", "1/A", self.iq0]
        self.outputs['Background'] = ["Bck", "1/A", self.bck]

class ExploreDialog(wx.Dialog):
    """
    The explorer dialog box. This dialog is meant to be
    invoked by the InversionControl class.
    """

    def __init__(self, pr_state, nfunc, *args, **kwds):
        """
        Initialization. The parameters added to Dialog are:

        :param pr_state: sas.sascalc.pr.invertor.Invertor object
        :param nfunc: Number of terms in the expansion

        """
        kwds["style"] = wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)

        # Initialize Results object
        self.results = Results()

        self.pr_state = pr_state
        self._default_min = 0.9 * self.pr_state.d_max
        self._default_max = 1.1 * self.pr_state.d_max
        self.nfunc = nfunc

        # Control for number of points
        self.npts_ctl = PrTextCtrl(self, -1, style=wx.TE_PROCESS_ENTER,
                                   size=(60, 20))
        # Control for the minimum value of D_max
        self.dmin_ctl = PrTextCtrl(self, -1, style=wx.TE_PROCESS_ENTER,
                                   size=(60, 20))
        # Control for the maximum value of D_max
        self.dmax_ctl = PrTextCtrl(self, -1, style=wx.TE_PROCESS_ENTER,
                                   size=(60, 20))

        # Output selection box for the y axis
        self.output_box = None

        # Create the plot object
        self.plotpanel = OutputPlot(self._default_min, self._default_max,
                                    self, -1, style=wx.RAISED_BORDER)

        # Create the layout of the dialog
        self.__do_layout()
        self.Fit()

        # Calculate exploration results
        self._recalc()
        # Graph the default output curve
        self._plot_output()

    class Event(object):
        """
        Class that holds the content of the form
        """
        ## Number of points to be plotted
        npts = 0
        ## Minimum value of D_max
        dmin = 0
        ## Maximum value of D_max
        dmax = 0

    def _get_values(self, event=None):
        """
        Invoked when the user changes a value of the form.
        Check that the values are of the right type.

        :return: ExploreDialog.Event object if the content is good,
            None otherwise
        """
        # Flag to make sure that all values are good
        flag = True

        # Empty ExploreDialog.Event content
        content_event = self.Event()

        # Read each text control and make sure the type is valid
        # Let the user know if a type is invalid by changing the
        # background color of the control.
        try:
            content_event.npts = int(self.npts_ctl.GetValue())
            self.npts_ctl.SetBackgroundColour(wx.WHITE)
            self.npts_ctl.Refresh()
        except:
            flag = False
            self.npts_ctl.SetBackgroundColour("pink")
            self.npts_ctl.Refresh()

        try:
            content_event.dmin = float(self.dmin_ctl.GetValue())
            self.dmin_ctl.SetBackgroundColour(wx.WHITE)
            self.dmin_ctl.Refresh()
        except:
            flag = False
            self.dmin_ctl.SetBackgroundColour("pink")
            self.dmin_ctl.Refresh()

        try:
            content_event.dmax = float(self.dmax_ctl.GetValue())
            self.dmax_ctl.SetBackgroundColour(wx.WHITE)
            self.dmax_ctl.Refresh()
        except:
            flag = False
            self.dmax_ctl.SetBackgroundColour("pink")
            self.dmax_ctl.Refresh()

        # If the content of the form is valid, return the content,
        # otherwise return None
        if flag:
            if event is not None:
                event.Skip(True)
            return content_event
        else:
            return None

    def _plot_output(self, event=None):
        """
        Invoked when a new output type is selected for plotting,
        or when a new computation is finished.
        """
        # Get the output type selection
        output_type = self.output_box.GetString(self.output_box.GetSelection())

        # If the selected output type is part of the results ojbect,
        # display the results.
        # Note: by design, the output type should always be part of the
        #       results object.
        if output_type in self.results.outputs:
            self.plotpanel.plot.x = self.results.d_max
            self.plotpanel.plot.y = self.results.outputs[output_type][2]
            self.plotpanel.plot.name = '_nolegend_'
            y_label = "\\rm{%s}" % self.results.outputs[output_type][0]
            self.plotpanel.graph.yaxis(y_label,
                                       self.results.outputs[output_type][1])

            # Redraw
            self.plotpanel.graph.render(self.plotpanel)
            self.plotpanel.subplot.figure.canvas.draw_idle()
        else:
            msg = "ExploreDialog: the Results object's dictionary "
            msg += "does not contain "
            msg += "the [%s] output type. This must be indicative of "
            msg += "a change in the " % str(output_type)
            msg += "ExploreDialog code."
            logger.error(msg)

    def __do_layout(self):
        """
        Do the layout of the dialog
        """
        # Dialog box properties
        self.SetTitle("D_max Explorer")
        self.SetSize((600, 595))

        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_params = wx.GridBagSizer(5, 5)

        iy = 0
        ix = 0
        label_npts = wx.StaticText(self, -1, "Npts")
        sizer_params.Add(label_npts, (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_params.Add(self.npts_ctl, (iy, ix), (1, 1),
                         wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        self.npts_ctl.SetValue("%g" % DEFAULT_NPTS)

        ix += 1
        label_dmin = wx.StaticText(self, -1, "Min Distance [A]")
        sizer_params.Add(label_dmin, (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_params.Add(self.dmin_ctl, (iy, ix), (1, 1),
                         wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        self.dmin_ctl.SetValue(str(self._default_min))

        ix += 1
        label_dmax = wx.StaticText(self, -1, "Max Distance [A]")
        sizer_params.Add(label_dmax, (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_params.Add(self.dmax_ctl, (iy, ix), (1, 1),
                         wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        self.dmax_ctl.SetValue(str(self._default_max))

        # Ouput selection box
        selection_msg = wx.StaticText(self, -1, "Select a dependent variable:")
        self.output_box = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        for item in list(self.results.outputs.keys()):
            self.output_box.Append(item, "")
        self.output_box.SetStringSelection(DEFAULT_OUTPUT)

        output_sizer = wx.GridBagSizer(5, 5)
        output_sizer.Add(selection_msg, (0, 0), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 10)
        output_sizer.Add(self.output_box, (0, 1), (1, 2),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 10)

        wx.EVT_COMBOBOX(self.output_box, -1, self._plot_output)
        sizer_main.Add(output_sizer, 0, wx.EXPAND | wx.ALL, 10)

        sizer_main.Add(self.plotpanel, 0, wx.EXPAND | wx.ALL, 10)
        sizer_main.SetItemMinSize(self.plotpanel, 400, 400)

        sizer_main.Add(sizer_params, 0, wx.EXPAND | wx.ALL, 10)
        static_line_3 = wx.StaticLine(self, -1)
        sizer_main.Add(static_line_3, 0, wx.EXPAND, 0)

        # Bottom area with the close button
        sizer_button.Add((20, 20), 1, wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        button_OK = wx.Button(self, wx.ID_OK, "Close")
        sizer_button.Add(button_OK, 0, wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 10)

        sizer_main.Add(sizer_button, 0, wx.EXPAND | wx.BOTTOM | wx.TOP, 10)
        self.SetAutoLayout(True)
        self.SetSizer(sizer_main)
        self.Layout()
        self.Centre()

        # Bind the Enter key to recalculation
        self.Bind(wx.EVT_TEXT_ENTER, self._recalc)

    def set_plot_unfocus(self):
        """
        Not implemented
        """
        pass

    def send_focus_to_datapanel(self, name):
        """
            The GUI manager sometimes calls this method
            TODO: refactor this
        """
        pass

    def _recalc(self, event=None):
        """
        Invoked when the user changed a value on the form.
        Process the form and compute the output to be plottted.
        """
        # Get the content of the form
        content = self._get_values()
        # If the content of the form is invalid, return and do nothing
        if content is None:
            return

        # Results object to store the computation outputs.
        results = Results()

        # Loop over d_max values
        for i in range(content.npts):
            temp = (content.dmax - content.dmin) / (content.npts - 1.0)
            d = content.dmin + i * temp

            self.pr_state.d_max = d
            try:
                out, cov = self.pr_state.invert(self.nfunc)

                # Store results
                iq0 = self.pr_state.iq0(out)
                rg = self.pr_state.rg(out)
                pos = self.pr_state.get_positive(out)
                pos_err = self.pr_state.get_pos_err(out, cov)
                osc = self.pr_state.oscillations(out)

                results.d_max.append(self.pr_state.d_max)
                results.bck.append(self.pr_state.background)
                results.chi2.append(self.pr_state.chi2)
                results.iq0.append(iq0)
                results.rg.append(rg)
                results.pos.append(pos)
                results.pos_err.append(pos_err)
                results.osc.append(osc)
            except:
                # This inversion failed, skip this D_max value
                msg = "ExploreDialog: inversion failed "
                msg += "for D_max=%s\n%s" % (str(d), sys.exc_info()[1])
                logger.error(msg)

        self.results = results

        # Plot the selected output
        self._plot_output()
