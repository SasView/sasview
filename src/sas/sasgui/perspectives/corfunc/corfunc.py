"""
    Corfunc perspective
"""
import wx
import sys
import logging
from sas.sasgui.guiframe.plugin_base import PluginBase
from sas.sasgui.guiframe.gui_manager import MDIFrame
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.guiframe.events import NewPlotEvent
from sas.sasgui.guiframe.gui_style import GUIFRAME_ID
from sas.sasgui.perspectives.corfunc.corfunc_panel import CorfuncPanel
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.perspectives.pr.pr_widgets import DataDialog


GROUP_ID_IQ_DATA = r"$I_{obs}(q)$"
IQ_DATA_LABEL = r"$I_{obs}(q)$"


class Plugin(PluginBase):
    """
    This class defines the interface for a plugin class for a correlation
    function perspective
    """

    def __init__(self):
        PluginBase.__init__(self, name="Correlation Function")
        logging.info("Correlation function plug-in started")
        self._always_active = True

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
        self.perspective.append(self.corfunc_panel.window_name)

        return [self.corfunc_panel]

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
                    self.corfunc_panel._set_data(data)
                except:
                    msg = "Corfunc set_data: " + str(sys.exc_value)
                    wx.PostEvent(self.parent, StatusEvent(status=msg,
                        info='error'))

    def show_data(self, path=None, data=None, reset=False):
        """
        Show data read from a file

        :param path: The path to the file
        :param data: The data to plot (Data1D)
        :param reset: If True, all other plottables will be cleared
        """
        if data.dy is not None:
            new_plot = Data1D(data.x, data.y, dy=data.dy)
        else:
            new_plot = Data1D(data.x, data.y)
        new_plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
        new_plot.name = IQ_DATA_LABEL
        new_plot.xaxis("\\rm{Q}", 'A^{-1}')
        new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")
        new_plot.interactive = True
        new_plot.group_id = GROUP_ID_IQ_DATA
        new_plot.id = self.data_id
        new_plot.title = "I(q)"
        new_plot.xtransform = 'x'
        new_plot.ytransform = 'y'
        wx.PostEvent(self.parent,
                     NewPlotEvent(plot=new_plot, title="I(q)", reset=reset))
