from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from sas.qtgui.Plotting.PlotterData import Data2D

# Local UI
from sas.qtgui.UI import main_resources_rc
from sas.qtgui.Plotting.UI.MaskEditorUI import Ui_MaskEditorUI
from sas.qtgui.Plotting.Plotter2D import Plotter2DWidget

class MaskEditor(QtWidgets.QDialog, Ui_MaskEditorUI):
    def __init__(self, parent=None, data=None):
        super(MaskEditor, self).__init__()

        assert(isinstance(data, Data2D))

        self.setupUi(self)

        self.data = data
        filename = data.name
        self.setWindowTitle("Mask Editor for %s" % filename)

        self.plotter = Plotter2DWidget(self, manager=parent, quickplot=True)
        self.plotter.data = self.data

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.frame.setLayout(layout)
        layout.addWidget(self.plotter)

        self.plotter.plot()

