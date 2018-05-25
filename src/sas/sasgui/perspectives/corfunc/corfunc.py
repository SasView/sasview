"""
    Corfunc perspective
"""
import wx
import sys
import logging
import copy
from sas.sasgui.guiframe.plugin_base import PluginBase
from sas.sasgui.guiframe.gui_manager import MDIFrame
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.guiframe.events import NewPlotEvent
from sas.sasgui.guiframe.events import PlotLimitEvent
from sas.sasgui.guiframe.gui_style import GUIFRAME_ID
from sas.sasgui.perspectives.corfunc.corfunc_panel import CorfuncPanel
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.perspectives.pr.pr_widgets import DataDialog
from sas.sasgui.perspectives.corfunc.corfunc_state import Reader
from sas.sascalc.dataloader.loader import Loader
import sas.sascalc.dataloader
from .plot_labels import *

logger = logging.getLogger(__name__)

class Plugin(PluginBase):
    """
    This class defines the interface for a plugin class for a correlation
    function perspective
    """

    def __init__(self):
        PluginBase.__init__(self, name="Correlation Function")
        logger.info("Correlation function plug-in started")
        self._always_active = True
        self.state_reader = Reader(self.set_state)
        self._extensions = '.crf'

    def get_panels(self, parent):
        """
        Define the GUI panels
        """
        self.parent = parent
        self.frame = MDIFrame(self.parent, None, 'None', (100,200))
        self.data_id = IQ_DATA_LABEL
        self.corfunc_panel = CorfuncPanel(parent=self.frame)
        self.frame.set_panel(self.corfunc_panel)
        self.corfunc_panel.set_manager(self)
        self._frame_set_helper()
        self.perspective.append(self.corfunc_panel.window_name)

        l = Loader()
        l.associate_file_reader('.crf', self.state_reader)

        return [self.corfunc_panel]

    def get_context_menu(self, plotpanel=None):
        """
        Get the context menu items available for Corfunc.

        :param plotpanel: A Plotter1D panel

        :return: a list of menu items with call-back function

        :note: if Data1D was generated from Theory1D
                the fitting option is not allowed
        """
        graph = plotpanel.graph
        if graph.selected_plottable not in plotpanel.plots:
            return []
        data = plotpanel.plots[graph.selected_plottable]
        if data.id == IQ_DATA_LABEL or data.id == IQ_EXTRAPOLATED_DATA_LABEL or data.id == TRANSFORM_LABEL1 or data.id == TRANSFORM_LABEL3:
            return []
        item = plotpanel.plots[graph.selected_plottable]
        if item.__class__.__name__ is "Data2D":
            return []
        elif item.__class__.__name__ is "Data1D":
            return [["Select data in corfunc",
                "Send this data to the correlation function perspective",
                self._on_select_data]]



    def set_state(self, state=None, datainfo=None):
        """
        Callback for CorfuncState reader. Called when a .crf file is loaded
        """
        if isinstance(datainfo, list):
            data = datainfo[0]
        else:
            data = datainfo
        self.corfunc_panel.set_state(state=state, data=data)
        self.on_perspective(event=None)
        data = self.parent.create_gui_data(data, None)
        self.parent.add_data({ data.id: data })

    def set_data(self, data_list=None):
        """
        Load the data that's been selected

        :param data_list: The data to load in
        """
        if data_list is None:
            data_list = []
        if len(data_list) >= 1:
            msg = ""
            if len(data_list) == 1:
                data = data_list[0]
            else:
                data_1d_list = []
                data_2d_list = []
                err_msg = ""

                for data in data_list:
                    if data is not None:
                        if issubclass(data.__class__, Data1D):
                            data_1d_list.append(data)
                        else:
                            err_msg += "{} type {} \n".format(str(data.name),
                                str(data.__class__))
                            data_2d_list.append(data)
                if len(data_2d_list) > 0:
                    msg = "Corfunc doesn't support the following data types:\n"
                    msg += err_msg
                if len(data_1d_list) == 0:
                    msg += "No data recieved"
                    wx.PostEvent(self.parent, StatusEvent(status=msg,
                                                info='error'))
                    return
                elif len(data_list) > 1:
                    msg = "Corfunc does not allow multiple data\n"
                    msg += "Please select one.\n"
                    dlg = DataDialog(data_list=data_1d_list, text=msg)
                    if dlg.ShowModal() == wx.ID_OK:
                        data = dlg.get_data()
                    else:
                        data = None
                    dlg.Destroy()

            if data is None:
                msg += "Corfunc recieved no data\n"
                wx.PostEvent(self.parent, StatusEvent(status=msg,
                                            info='error'))
                return
            if issubclass(data.__class__, Data1D):
                try:
                    wx.PostEvent(self.parent, NewPlotEvent(action='remove',
                                                group_id=GROUP_ID_IQ_DATA,
                                                id=self.data_id))
                    self.data_id = data.id
                    self.corfunc_panel.set_data(data)
                except:
                    msg = "Corfunc set_data: " + str(sys.exc_info()[1])
                    wx.PostEvent(self.parent, StatusEvent(status=msg,
                        info='error'))

    def delete_data(self, data):
        """
        Delete the data from the perspective
        """
        self.clear_data()
        self.corfunc_panel.set_data(None)

    def show_data(self, data, label, reset=False, active_ctrl=None):
        """
        Show data read from a file

        :param data: The data to plot (Data1D)
        :param label: What to label the plot. Also used as the plot ID
        :param reset: If True, all other plottables will be cleared
        """
        new_plot = Data1D(data.x, copy.deepcopy(data.y), dy=data.dy)
        group_id = ""
        if label == IQ_DATA_LABEL or label == IQ_EXTRAPOLATED_DATA_LABEL:
            new_plot.xaxis("\\rm{Q}", 'A^{-1}')
            new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")
            new_plot.y -= self.corfunc_panel.background
            # Show data on a log(Q)/I scale
            new_plot.ytransform = 'y'
            group_id = GROUP_ID_IQ_DATA
            if label == IQ_EXTRAPOLATED_DATA_LABEL:
                # Show the extrapolation as a curve instead of points
                new_plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
        elif label == TRANSFORM_LABEL1 or label == TRANSFORM_LABEL3:
            new_plot.xaxis("{x}", 'A')
            new_plot.yaxis("{\\Gamma}", '')
            # Show transform on a linear scale
            new_plot.xtransform = 'x'
            new_plot.ytransform = 'y'
            group_id = GROUP_ID_TRANSFORM
            # Show the transformation as a curve instead of points
            new_plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
        elif label == IDF_LABEL:
            new_plot.xaxis("{x}", 'A')
            new_plot.yaxis("{g_1}", '')
            # Linear scale
            new_plot.xtransform = 'x'
            new_plot.ytransform = 'y'
            group_id = GROUP_ID_IDF
            # Show IDF as a curve instead of points
            new_plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
        new_plot.id = label
        new_plot.name = label
        new_plot.group_id = group_id
        new_plot.interactive = True
        new_plot.title = group_id.replace('$', '').replace('\\', '')
        wx.PostEvent(self.parent,
                     NewPlotEvent(plot=new_plot, title=new_plot.title,
                        reset=reset))
        if label == IQ_DATA_LABEL or label == IQ_EXTRAPOLATED_DATA_LABEL:
            wx.CallAfter(self.corfunc_panel.plot_qrange, active=active_ctrl,
                leftdown=True)
        if label == IQ_EXTRAPOLATED_DATA_LABEL:
            # Zoom in to the region we're interested in
            xlim = (min(self.corfunc_panel._extrapolated_data.x), self.corfunc_panel.qmax[1]*1.2)
            wx.CallAfter(wx.PostEvent, self.parent, PlotLimitEvent(id=IQ_DATA_LABEL, group_id=GROUP_ID_IQ_DATA, xlim=xlim))

    def clear_data(self):
        wx.PostEvent(self.parent,
            NewPlotEvent(action='delete', group_id=GROUP_ID_TRANSFORM))
        wx.PostEvent(self.parent,
            NewPlotEvent(action='clear', group_id=GROUP_ID_IQ_DATA))

    def _on_select_data(self, event):
        panel = event.GetEventObject()
        if not panel.graph.selected_plottable in panel.plots:
            return
        data = panel.plots[panel.graph.selected_plottable]
        self.set_data([data])
