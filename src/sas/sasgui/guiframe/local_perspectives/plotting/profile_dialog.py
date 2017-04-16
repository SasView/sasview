"""
SLD Profile Dialog for multifunctional models
"""
import wx
import sys
from copy import deepcopy
from sas.sasgui.plottools.plottables import Graph
from Plotter1D import ModelPanel1D as PlotPanel
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.guiframe.gui_style import GUIFRAME_ID

DEFAULT_CMAP = None  #pylab.cm.jet
_BOX_WIDTH = 76
_STATICBOX_WIDTH = 400
# X Y offset on plot
_X_OFF = 15
_Y_OFF = 0.5

#SLD panel size
if sys.platform.count("win32") > 0:
    _STATICBOX_WIDTH = 563
    PANEL_SIZE = 425
    FONT_VARIANT = 0
else:
    _STATICBOX_WIDTH = 605
    PANEL_SIZE = 500
    FONT_VARIANT = 1


class SLDPanel(wx.Dialog):
    """
    Provides the SLD profile plot panel.
    """
    ## Internal nickname for the window, used by the AUI manager
    window_name = "Scattering Length Density Profile"
    ## Name to appear on the window title bar
    window_caption = "Scattering Length Density Profile"
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = True
    def __init__(self, parent=None, base=None, data=None, axes=['Radius'],
                 id=-1, *args, **kwds):
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        kwds["size"] = wx.Size(_STATICBOX_WIDTH, PANEL_SIZE)
        wx.Dialog.__init__(self, parent, id=id, *args, **kwds)

        if data is not None:
            #Font size
            kwds = []
            self.SetWindowVariant(variant=FONT_VARIANT)

            self.SetTitle("Scattering Length Density Profile")
            self.parent = parent
            self._mgr = None
            self.data = data
            self.str = self.data.__str__()
            ## when 2 data have the same id override the 1 st plotted
            self.name = self.data.name
            # Panel for plot
            self.plotpanel = SLDplotpanel(self, axes, -1,
                                          style=wx.TRANSPARENT_WINDOW)
            self.cmap = DEFAULT_CMAP
            ## Create Artist and bind it
            self.subplot = self.plotpanel.subplot
            # layout
            self._setup_layout()

            # plot
            data_plot = deepcopy(self.data)
            data_plot.dy = self._set_dy_data()
            # unit increase to M times for users
            data_plot.y = self._set_y_data()

            self.newplot = Data1D(data_plot.x, data_plot.y, data_plot.dy)
            self.newplot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
            self.newplot.dy = None
            self.newplot.name = 'SLD'
            self.newplot.is_data = False

            self.newplot.id = self.newplot.name
            self.plotpanel.add_image(self.newplot)

            self.plotpanel.resizing = False
            self.plotpanel.canvas.set_resizing(self.plotpanel.resizing)

            self.plotpanel.subplot.set_ylim(min(data_plot.y) - _Y_OFF,
                                            max(data_plot.y) + _Y_OFF)
            self.plotpanel.subplot.set_xlim(min(data_plot.x) - _X_OFF,
                                            max(data_plot.x) + _X_OFF)
            self.plotpanel.graph.render(self.plotpanel)
            self.plotpanel.canvas.draw()

    def _set_dy_data(self):
        """
        make fake dy data

        :return dy:
        """
        # set dy as zero
        dy = [0 for y in self.data.y]
        return dy

    def _set_y_data(self):
        """
        make y data unit Mega times

        :return y_value:
        """
        # changes the unit
        y_value = [yvalue * 1e+006 for yvalue in self.data.y]

        return y_value

    def _setup_layout(self):
        """
        Set up the layout
        """
        # panel sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.plotpanel, 0, wx.LEFT | wx.RIGHT, 5)
        sizer.Add(wx.StaticLine(self), 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add((0, 5))
        #-----Button------------1
        button_reset = wx.Button(self, wx.NewId(), "Close")
        button_reset.SetToolTipString("Close...")
        button_reset.Bind(wx.EVT_BUTTON, self._close,
                          id=button_reset.GetId())
        sizer.Add(button_reset, 0, wx.LEFT, _STATICBOX_WIDTH - 80)
        sizer.Add((0, 10))
        self.SetSizerAndFit(sizer)
        self.Centre()
        self.Show(True)
        button_reset.SetFocus()

    def _close(self, event):
        """
        Close the dialog
        """
        self.Close(True)

    def _draw_model(self, event):
        """
         on_close, update the model2d plot
        """
        pass

    def get_current_context_menu(self, graph=None):
        """
        When the context menu of a plot is rendered, the
        get_context_menu method will be called to give you a
        chance to add a menu item to the context menu.
        :param graph: the Graph object to which we attach the context menu

        :return: a list of menu items with call-back function
        """
        return []

    def set_schedule_full_draw(self, panel=None, func=None):
        """
        Set_schedule for full draw
        """
        # Not implemented
        pass

    def set_schedule(self, schedule=False):
        """
        Set schedule for redraw
        """
        # Not implemented
        pass

    def set_plot_unfocus(self):
        """
        Set_plot unfocus
        """
        # NOt implemented
        pass

    def on_change_caption(self, name, old_caption, new_caption):
        """
        """
        self.parent.parent.parent.on_change_caption(name, old_caption, new_caption)

    def disable_app_menu(self, panel):
        """
        Disable menu bar
        """
        # Not implemented!
        return

    def show_data1d(self, data, name):
        """
        Show data dialog
        """
        self.parent._manager.parent.show_data1d(data, name)

class SLDplotpanel(PlotPanel):
    """
    Panel
    """
    def __init__(self, parent, axes=[], id=-1, color=None, dpi=None, **kwargs):
        """
        """
        PlotPanel.__init__(self, parent, id=id, xtransform='x', ytransform='y',
                           color=color, dpi=dpi,
                           size=(_STATICBOX_WIDTH, PANEL_SIZE - 100), **kwargs)

        # Keep track of the parent Frame
        self.parent = parent
        self.window_name = "Scattering Length Density Profile"
        self.window_caption = self.window_name
        self.prevXtrans = "x"
        self.prevYtrans = "y"
        self.viewModel = "--"
        # Internal list of plottable names (because graph
        # doesn't have a dictionary of handles for the plottables)
        self.plots = {}
        self.graph = Graph()
        self.axes_label = []
        for idx in range(0, len(axes)):
            self.axes_label.append(axes[idx])
        self.xaxis_label = ''
        self.xaxis_unit = ''
        self.yaxis_label = ''
        self.yaxis_unit = ''
        self.resizing = True
        self.xcolor = 'black'
        self.ycolor = 'black'

    def add_image(self, plot):
        """
        Add image(Theory1D)
        """
        self.plots[plot.id] = plot
        self.plots[plot.id].is_data = True
        #add plot
        self.graph.add(plot)
        #add axes
        x1_label = self.axes_label[0]
        self.xaxis_label = '\\rm{%s} ' % x1_label
        self.xaxis_unit = 'A'
        self.graph.xaxis(self.xaxis_label, self.xaxis_unit)
        self.yaxis_label = '\\rm{SLD} '
        self.yaxis_unit = '10^{-6}A^{-2}'
        self.graph.yaxis(self.yaxis_label, self.yaxis_unit)
        # For latter scale changes
        self.plots[plot.id].xaxis('\\rm{%s} ' % x1_label, 'A')
        self.plots[plot.id].yaxis('\\rm{SLD} ', '10^{-6}A^{-2}')

    def on_set_focus(self, event):
        """
        send to the parenet the current panel on focus

        """
        #Not implemented
        pass

    def on_kill_focus(self, event):
        """
        reset the panel color

        """
        #Not implemented
        pass

    def onChangeCaption(self, event):
        """
        Not implemented
        """
        pass

    def _onSave(self, evt):
        """
        Save a data set to a text file

        :param evt: Menu event

        """
        menu = evt.GetEventObject()
        event_id = evt.GetId()
        self.set_selected_from_menu(menu, event_id)
        data = self.plots[self.graph.selected_plottable]
        default_name = data.label
        if default_name.count('.') > 0:
            default_name = default_name.split('.')[0]
        default_name += "_out"
        if self.parent is not None:
            # What an ancestor!
            fit_panel = self.parent.parent.parent
            fit_panel._manager.parent.save_data1d(data, default_name)

class ViewerFrame(wx.Frame):
    """
    Add comment
    """
    def __init__(self, parent, id, title):
        """
        comment
        :param parent: parent panel/container
        """
        # Initialize the Frame object
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition,
                          wx.Size(_STATICBOX_WIDTH, PANEL_SIZE))
        # Panel for 1D plot
        self.plotpanel = SLDplotpanel(self, -1, style=wx.RAISED_BORDER)

class ViewApp(wx.App):
    def OnInit(self):
        frame = ViewerFrame(None, -1, 'testView')
        frame.Show(True)
        self.SetTopWindow(frame)

        return True

if __name__ == "__main__":
    app = ViewApp(0)
    app.MainLoop()
