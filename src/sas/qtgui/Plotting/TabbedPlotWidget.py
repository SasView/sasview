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
        self.tab_fitpage_dict = {}

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

        return self.tab_fitpage_dict[tab_id]

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

        if not self.tab_exists(tab_id):
            self.addTab(SubTabs(self, plots), f"Fitpage {tab_id}")
        else:
            self.removeTab(current_tab_index)

            self.insertTab(current_tab_index, SubTabs(self, plots), f"Fitpage {tab_id}")

            self.setCurrentIndex(current_tab_index)


    def get_subtab_by_tab_id(self, tab_id: int):
        if tab_id in self.tab_fitpage_dict.keys():
            return self.widget(self.tab_fitpage_dict[tab_id])
        else:
            return None


