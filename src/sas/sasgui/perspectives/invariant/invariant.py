


################################################################################
# This software was developed by the University of Tennessee as part of the
# Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
# project funded by the US National Science Foundation.
#
# See the license text in license.txt
#
# copyright 2009, University of Tennessee
################################################################################


import sys
import wx
import copy
import logging
from sas.sasgui.guiframe.gui_manager import MDIFrame
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.guiframe.events import NewPlotEvent
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.guiframe.gui_style import GUIFRAME_ID
from sas.sasgui.perspectives.invariant.invariant_state import Reader as reader
from sas.sascalc.dataloader.loader import Loader
from sas.sasgui.perspectives.invariant.invariant_panel import InvariantPanel
from sas.sasgui.guiframe.plugin_base import PluginBase

logger = logging.getLogger(__name__)

class Plugin(PluginBase):
    """
    This class defines the interface for invariant Plugin class
    that can be used by the gui_manager.
    """

    def __init__(self):
        PluginBase.__init__(self, name="Invariant")

        # dictionary containing data name and error on dy of that data
        self.err_dy = {}

        # default state objects
        self.state_reader = None
        self._extensions = '.inv'
        self.temp_state = None
        self.__data = None

        # Log startup
        logger.info("Invariant plug-in started")

    def get_data(self):
        """
        """
        return self.__data

    def get_panels(self, parent):
        """
        Create and return the list of wx.Panels for your plug-in.
        Define the plug-in perspective.

        Panels should inherit from DefaultPanel defined below,
        or should present the same interface. They must define
        "window_caption" and "window_name".

        :param parent: parent window

        :return: list of panels
        """
        # # Save a reference to the parent
        self.parent = parent
        self.frame = MDIFrame(self.parent, None, 'None', (100, 200))
        self.invariant_panel = InvariantPanel(parent=self.frame)
        self.frame.set_panel(self.invariant_panel)
        self._frame_set_helper()
        self.invariant_panel.set_manager(manager=self)
        self.perspective.append(self.invariant_panel.window_name)
        # Create reader when fitting panel are created
        self.state_reader = reader(self.set_state)
        # append that reader to list of available reader
        loader = Loader()
        loader.associate_file_reader(".inv", self.state_reader)
        # loader.associate_file_reader(".svs", self.state_reader)
        # Return the list of panels
        return [self.invariant_panel]

    def get_context_menu(self, plotpanel=None):
        """
        This method is optional.

        When the context menu of a plot is rendered, the
        get_context_menu method will be called to give you a
        chance to add a menu item to the context menu.

        A ref to a Graph object is passed so that you can
        investigate the plot content and decide whether you
        need to add items to the context menu.

        This method returns a list of menu items.
        Each item is itself a list defining the text to
        appear in the menu, a tool-tip help text, and a
        call-back method.

        :param graph: the Graph object to which we attach the context menu

        :return: a list of menu items with call-back function
        """
        graph = plotpanel.graph
        invariant_option = "Compute invariant"
        invariant_hint = "Will displays the invariant panel for"
        invariant_hint += " further computation"

        if graph.selected_plottable not in plotpanel.plots:
            return []
        data = plotpanel.plots[graph.selected_plottable]

        if issubclass(data.__class__, Data1D):
            if data.name != "$I_{obs}(q)$" and  data.name != " $P_{fit}(r)$":
                return [[invariant_option, invariant_hint, self._compute_invariant]]
        return []

    def _compute_invariant(self, event):
        """
        Open the invariant panel to invariant computation
        """
        self.panel = event.GetEventObject()
        Plugin.on_perspective(self, event=event)
        id = self.panel.graph.selected_plottable
        data = self.panel.plots[self.panel.graph.selected_plottable]
        if data is None:
            return
        if not issubclass(data.__class__, Data1D):
            name = data.__class__.__name__
            msg = "Invariant use only Data1D got: [%s] " % str(name)
            raise ValueError(msg)
        self.compute_helper(data=data)

    def set_data(self, data_list=None):
        """
        receive a list of data and compute invariant
        """
        msg = ""
        data = None
        if data_list is None:
            data_list = []
        if len(data_list) >= 1:
            if len(data_list) == 1:
                data = data_list[0]
            else:
                data_1d_list = []
                data_2d_list = []
                error_msg = ""
                # separate data into data1d and data2d list
                for data in data_list:
                    if data is not None:
                        if issubclass(data.__class__, Data1D):
                            data_1d_list.append(data)
                        else:
                            error_msg += " %s  type %s \n" % (str(data.name),
                                                              str(data.__class__.__name__))
                            data_2d_list.append(data)
                if len(data_2d_list) > 0:
                    msg = "Invariant does not support the following data types:\n"
                    msg += error_msg
                if len(data_1d_list) == 0:
                    wx.PostEvent(self.parent, StatusEvent(status=msg, info='error'))
                    return
                msg += "Invariant panel does not allow multiple data!\n"
                msg += "Please select one.\n"
                if len(data_list) > 1:
                    from .invariant_widgets import DataDialog
                    dlg = DataDialog(data_list=data_1d_list, text=msg)
                    if dlg.ShowModal() == wx.ID_OK:
                        data = dlg.get_data()
                    else:
                        data = None
                    dlg.Destroy()

            if data is None:
                msg += "invariant receives no data. \n"
                wx.PostEvent(self.parent, StatusEvent(status=msg, info='error'))
                return
            if not issubclass(data.__class__, Data1D):
                msg += "invariant cannot be computed for data of "
                msg += "type %s\n" % (data.__class__.__name__)
                wx.PostEvent(self.parent, StatusEvent(status=msg, info='error'))
                return
            else:
                wx.PostEvent(self.parent, NewPlotEvent(plot=data, title=data.title))
                try:
                    self.compute_helper(data)
                except:
                    msg = "Invariant Set_data: " + str(sys.exc_info()[1])
                    wx.PostEvent(self.parent, StatusEvent(status=msg, info="error"))
        else:
            msg = "invariant cannot be computed for data of "
            msg += "type %s" % (data.__class__.__name__)
            wx.PostEvent(self.parent, StatusEvent(status=msg, info='error'))

    def delete_data(self, data_id):
        """
        """
        if self.__data is None:
            return
        for id in data_id:
            if id == self.__data.id:
                self.clear_panel()

    def clear_panel(self):
        """
        """
        self.invariant_panel.clear_panel()

    def compute_helper(self, data):
        """
        """
        if data is None:
            return
        # set current data if not it's a state data
        if not self.invariant_panel.is_state_data:
            # Store reference to data
            self.__data = data
            # Set the data set to be user for invariant calculation
            self.invariant_panel.set_data(data=data)

    def save_file(self, filepath, state=None):
        """
        Save data in provided state object.

        :param filepath: path of file to write to
        :param state: invariant state
        """
        # Write the state to file
        # First, check that the data is of the right type
        current_plottable = self.__data

        if issubclass(current_plottable.__class__, Data1D):
            self.state_reader.write(filepath, current_plottable, state)
        else:
            msg = "invariant.save_file: the data being saved is"
            msg += " not a sas.sascalc.dataloader.data_info.Data1D object"
            raise RuntimeError(msg)

    def set_state(self, state=None, datainfo=None):
        """
        Call-back method for the state reader.
        This method is called when a .inv/.svs file is loaded.

        :param state: State object
        """
        self.temp_state = None
        try:
            if datainfo.__class__.__name__ == 'list':
                data = datainfo[0]
            else:
                data = datainfo
            if data is None:
                msg = "invariant.set_state: datainfo parameter cannot"
                msg += " be None in standalone mode"
                raise RuntimeError(msg)
            # Make sure the user sees the invariant panel after loading
            # self.parent.set_perspective(self.perspective)
            self.on_perspective(event=None)
            name = data.meta_data['invstate'].file
            data.meta_data['invstate'].file = name
            data.name = name
            data.filename = name

            data = self.parent.create_gui_data(data, None)
            self.__data = data
            wx.PostEvent(self.parent, NewPlotEvent(plot=self.__data,
                                                   reset=True, title=self.__data.title))
            data_dict = {self.__data.id:self.__data}
            self.parent.add_data(data_list=data_dict)
            # set state
            self.invariant_panel.is_state_data = True

            # Load the invariant states
            self.temp_state = state
            # Requires to have self.__data and self.temp_state  first.
            self.on_set_state_helper(None)

        except:
            logger.error("invariant.set_state: %s" % sys.exc_info()[1])

    def on_set_state_helper(self, event=None):
        """
        Set the state when called by EVT_STATE_UPDATE event from guiframe
        after a .inv/.svs file is loaded
        """
        self.invariant_panel.set_state(state=self.temp_state,
                                       data=self.__data)
        self.temp_state = None


    def plot_theory(self, data=None, name=None):
        """
        Receive a data set and post a NewPlotEvent to parent.

        :param data: extrapolated data to be plotted
        :param name: Data's name to use for the legend
        """
        # import copy
        if data is None:
            id = str(self.__data.id) + name
            group_id = self.__data.group_id
            wx.PostEvent(self.parent, NewPlotEvent(id=id, group_id=group_id, action='Remove'))
            return

        new_plot = Data1D(x=[], y=[], dy=None)
        new_plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
        scale = self.invariant_panel.get_scale()
        background = self.invariant_panel.get_background()

        if scale != 0:
            # Put back the sacle and bkg for plotting
            data.y = (data.y + background) / scale
            new_plot = Data1D(x=data.x, y=data.y, dy=None)
            new_plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
        else:
            msg = "Scale can not be zero."
            raise ValueError(msg)
        if len(new_plot.x) == 0:
            return

        new_plot.name = name
        new_plot.xaxis(self.__data._xaxis, self.__data._xunit)
        new_plot.yaxis(self.__data._yaxis, self.__data._yunit)
        new_plot.group_id = self.__data.group_id
        new_plot.id = str(self.__data.id) + name
        new_plot.title = self.__data.title
        # Save theory_data in a state
        if data is not None:
            name_head = name.split('-')
            if name_head[0] == 'Low':
                self.invariant_panel.state.theory_lowQ = copy.deepcopy(new_plot)
            elif name_head[0] == 'High':
                self.invariant_panel.state.theory_highQ = copy.deepcopy(new_plot)

        self.parent.update_theory(data_id=self.__data.id, theory=new_plot)
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,
                                               title=self.__data.title))

    def plot_data(self, scale, background):
        """
        replot the current data if the user enters a new scale or background
        """
        new_plot = scale * self.__data - background
        new_plot.name = self.__data.name
        new_plot.group_id = self.__data.group_id
        new_plot.id = self.__data.id
        new_plot.title = self.__data.title

        # Save data in a state: but seems to never happen
        if new_plot is not None:
            self.invariant_panel.state.data = copy.deepcopy(new_plot)
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,
                                               title=new_plot.title))

