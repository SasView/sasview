from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6 import QtGui

from sas.qtgui.Plotting.SubTabs import SubTabs

from sas.qtgui.Utilities import GuiUtils

class TabbedPlotWidget(QtWidgets.QTabWidget):
    """
    Central plot widget that holds tabs and subtabs for all existing plots
    """
    def __init__(self, parent=None):
        super(TabbedPlotWidget, self).__init__()

        # the manager/parent of this class is the GuiManager
        self.manager = parent

        # use this dictionary to keep track of the tab that the plots of a certain fitpage are saved in
        # works like: {"1": "2"}, where 1 is the tab_id (the number associated to the Fitpage from the FittingWidget)
        # and 2 is the index of the corresponding tab to that fitpage in this widget.
        self.tab_fitpage_dict = {}

        # since this correlation should be unambiguous in both directions, this dict can be inverted, so that the
        # subtabs of a certain tab can find out, which fitpage they belong to by finding out about the index of their
        # parent tab in this widget
        self.inv_tab_fitpage_dict = {}

        self._set_icon()
        self.setWindowTitle('TabbedPlotWidget')

        self.setMinimumSize(500, 500)
        self.hide()

    def _set_icon(self):
        """
        Set the icon of the window
        """
        icon = QtGui.QIcon()
        icon.addFile(u":/res/ball.ico", QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

    def show_or_activate(self):
        """
        Shows the widget itself, if it is hidden. Activates it, if already shown.
        """
        if self.isVisible():
            self.activateWindow()
        else:
            self.show()
            self.activateWindow()

    def add_tab_to_dict(self, tab_id: int) -> int:
        """
        This method handles the bookkeeping for the existing tabs and there respective fitpages.
        Only adds the tab_id to the dict, if it does not already exist in there.
        Returns the tab index of the existing or newly added tab.
        """
        if tab_id not in self.tab_fitpage_dict.keys():
            self.tab_fitpage_dict[tab_id] = self.count()

        self.update_inv_dict(tab_id, self.count())

        return self.tab_fitpage_dict[tab_id]

    def update_inv_dict(self, tab_id: int, tab_index: int):
        self.inv_tab_fitpage_dict[tab_index] = tab_id

    def tab_exists(self, tab_id: int) -> bool:
        """
        Check if a tab for the given tab_id already exists.
        """
        if tab_id in self.tab_fitpage_dict.keys():
            return True
        else:
            return False

    def add_tab(self, item_name, item_model, tab_id: int):
        """
        The idea is to add only one tab for all the plots that are associated with the plot_item QStandardItem
        """

        plots = GuiUtils.plotsFromDisplayName(item_name, item_model)

        current_tab_index = self.add_tab_to_dict(tab_id)

        new_tab = SubTabs(self, plots)

        if not self.tab_exists(tab_id):
            self.addTab(new_tab, f"Fitpage {tab_id}")

        else:
            self.removeTab(current_tab_index)
            self.insertTab(current_tab_index, new_tab, f"Fitpage {tab_id}")
            self.setCurrentIndex(current_tab_index)

        # Set the tab_id and the parent tab index of this SubTabs index so that it knows these values.
        new_tab.set_parent_tab_index()


    def get_subtab_by_tab_id(self, tab_id: int):
        if tab_id in self.tab_fitpage_dict.keys():
            return self.widget(self.tab_fitpage_dict[tab_id])
        else:
            return None


