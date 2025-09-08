"""
Widget/logic for dataset ordering.
"""
from PySide6 import QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils

# Local UI
from sas.qtgui.Perspectives.Fitting.UI.OrderWidgetUI import Ui_OrderWidgetUI


class OrderWidget(QtWidgets.QWidget, Ui_OrderWidgetUI):
    def __init__(self, parent=None, all_data=None):
        super(OrderWidget, self).__init__()

        self.setupUi(self)
        self.all_data = all_data
        self.order = {}

        self.setupTable()

    def updateData(self, all_data):
        """
        Read in new datasets and update the view
        """
        self.all_data = all_data
        self.lstOrder.clear()
        self.setupTable()

    def setupTable(self):
        """
        Populate the widget with dataset names in original order
        """
        if self.all_data is None:
            return
        for item in self.all_data:
            if not hasattr(item, 'data'):
                continue
            dataset = GuiUtils.dataFromItem(item)
            if dataset is None:
                continue
            dataset_name = dataset.name
            self.order[dataset_name] = item
            self.lstOrder.addItem(dataset_name)

    def ordering(self):
        """
        Returns the current ordering of the datasets
        """
        order = []
        for row in range(self.lstOrder.count()):
            item_name = self.lstOrder.item(row).text()
            order.append(self.order[item_name])
        return order

