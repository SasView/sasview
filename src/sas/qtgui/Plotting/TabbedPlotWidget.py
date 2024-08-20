from PySide6 import QtWidgets

class TabbedPlotWidget(QtWidgets.QTabWidget):
    """
    Central plot widget that holds tabs and subtabs for all existing plots
    """
    name = 'TabbedPlotWidget'
    def __init__(self, parent=None):
        super(TabbedPlotWidget, self).__init__()

        self.manager = parent
        self.setObjectName('TabbedPlotWidget')
        self.setMinimumSize(500, 500)
        self.hide()