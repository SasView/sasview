#items that are supposed to be used in the plottreewidget for checking if an item is for example a tab or a subtab
from PySide6.QtWidgets import QTreeWidgetItem
class TabItem(QTreeWidgetItem):
    def __init__(self, parent, name, fitpage_index):
        super().__init__(parent, name)
        self._fitpage_index = fitpage_index
        super().setData(0, 1, self)

    @property
    def fitpage_index(self):
        return self._fitpage_index

class SubTabItem(TabItem):
    def __init__(self, parent, name, fitpage_index, subtab_index):
        super().__init__(parent, name, fitpage_index)
        self._subtab_index = subtab_index

    @property
    def subtab_index(self):
        return self._subtab_index

class PlotItem(SubTabItem):
    def __init__(self, parent, name, fitpage_index, subtab_index, ax_index, is_plot_2d):
        super().__init__(parent, name, fitpage_index, subtab_index)
        self._ax_index = ax_index
        self._is_plot_2d = is_plot_2d

    @property
    def ax_index(self):
        return self._ax_index

    @property
    def is_plot_2d(self):
        return self._is_plot_2d

class PlottableItem(QTreeWidgetItem):
    def __init__(self, parent, name, data_id, type_num):
        super().__init__(parent, name)
        self._data_id = data_id
        # type serves the same purpose as in DataTreeItems - knowing if the item is a data item or a fit item, so that
        # for example the axes can be scaled accordingly
        self._type_num = type_num
        super().setData(0, 1, self)

    @property
    def data_id(self):
        return self._data_id

    @property
    def type_num(self):
        return self._type_num



