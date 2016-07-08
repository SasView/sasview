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
from sas.sasgui.guiframe.gui_style import GUIFRAME_ID
from sas.sasgui.perspectives.corfunc.corfunc_panel import CorfuncPanel
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.perspectives.pr.pr_widgets import DataDialog
from sas.sasgui.perspectives.corfunc.corfunc_state import Reader
from sas.sascalc.dataloader.loader import Loader
import sas.sascalc.dataloader


GROUP_ID_IQ_DATA = r"$I(q)$"
IQ_DATA_LABEL = r"$I_{obs}(q)$"
IQ_EXTRAPOLATED_DATA_LABEL = r"$I_{extrap}(q)$"

GROUP_ID_TRANSFORM = r"$\Gamma(x)$"
TRANSFORM_LABEL = r"$\Gamma(x)$"


class Plugin(PluginBase):
    """
    This class defines the interface for a plugin class for a correlation
    function perspective
    """

    def __init__(self):
        PluginBase.__init__(self, name="Correlation Function")
        logging.info("Correlation function plug-in started")
        self._always_active = True
        self.state_reader = Reader(self.set_state)
        self._extensions = '.cor'
        l = Loader()
        l.associate_file_reader('.cor', self.state_reader)

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

    def set_state(self, state=None, datainfo=None):
        """
        Callback for CorfuncState reader. Called when a .cor file is loaded
        """
        self.corfunc_panel.set_state(state=state, data=datainfo)

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
                    msg = "Corfunc set_data: " + str(sys.exc_value)
                    wx.PostEvent(self.parent, StatusEvent(status=msg,
                        info='error'))

    def show_data(self, data, label, reset=False):
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
            group_id = GROUP_ID_IQ_DATA
        elif label == TRANSFORM_LABEL:
            new_plot.xaxis("{x}", 'A')
            new_plot.yaxis("{\\Gamma}", '')
            group_id = GROUP_ID_TRANSFORM
        new_plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
        new_plot.id = label
        new_plot.name = label
        new_plot.group_id = group_id
        new_plot.interactive = True
        new_plot.title = group_id.replace('$', '').replace('\\', '')
        # Show data on a linear scale
        new_plot.xtransform = 'x'
        new_plot.ytransform = 'y'
        wx.PostEvent(self.parent,
                     NewPlotEvent(plot=new_plot, title=new_plot.title,
                        reset=reset))

    def clear_data(self):
        wx.PostEvent(self.parent,
            NewPlotEvent(action='delete', group_id=GROUP_ID_TRANSFORM))
        wx.PostEvent(self.parent,
            NewPlotEvent(action='clear', group_id=GROUP_ID_IQ_DATA))
