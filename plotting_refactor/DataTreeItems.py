from PySide6.QtWidgets import QTreeWidgetItem


class PlotPageItem(QTreeWidgetItem):
    def __init__(self, parent, name, fitpage_index, data_id):
        super().__init__(parent, name)
        self._fitpage_index = fitpage_index
        self._data_id = data_id
        super().setData(0, 1, self)

    @property
    def fitpage_index(self):
        return self._fitpage_index

    @property
    def data_id(self):
        return self._data_id

class DataItem(PlotPageItem):
    def __init__(self, parent, name, fitpage_index, data_id, type_num):
        super().__init__(parent, name, fitpage_index, data_id)
        # self.type_num saves if the item is a data item or a fit item in the tree widget
        # identifier=1 is for data and identifier=2 is for fit identifier=3 is for residuals
        self._type_num = type_num

    @property
    def type_num(self):
        return self._type_num

