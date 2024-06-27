#items that are supposed to be used in the plottreewidget for checking if an item is for example a tab or a subtab
from PySide6.QtWidgets import QTreeWidgetItem
class TabItem(QTreeWidgetItem):
    def __init__(self, parent, name, fitpage_index):
        super().__init__(parent, name)
        self.fitpage_index = fitpage_index
        super().setData(0, 1, self)

    def get_fitpage_index(self):
        return self.fitpage_index

class SubTabItem(TabItem):
    def __init__(self, parent, name, fitpage_index, subtab_index):
        super().__init__(parent, name, fitpage_index)
        self.subtab_index = subtab_index

    def get_subtab_index(self):
        return self.subtab_index

class PlotItem(SubTabItem):
    def __init__(self, parent, name, fitpage_index, subtab_index, ax_index):
        super().__init__(parent, name, fitpage_index, subtab_index)
        self.ax_index = ax_index

    def get_ax_index(self):
        return self.ax_index

class PlottableItem(QTreeWidgetItem):
    def __init__(self, parent, name, data_id, type_num):
        super().__init__(parent, name)
        self.data_id = data_id
        # type serves the same purpose as in plottreeitems - knowing if the item is a data item or a fit item
        # although this maybe does not even matter for plotting purposes, if one knows the name?
        self.type_num = type_num
        super().setData(0, 1, self)

    def get_data_id(self):
        return self.data_id
    def get_type(self):
        return self.type_num



