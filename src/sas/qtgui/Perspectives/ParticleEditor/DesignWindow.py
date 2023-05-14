from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from sas.qtgui.Perspectives.ParticleEditor.FunctionViewer import FunctionViewer
from sas.qtgui.Perspectives.ParticleEditor.PythonViewer import PythonViewer
from sas.qtgui.Perspectives.ParticleEditor.OutputViewer import OutputViewer
from sas.qtgui.Perspectives.ParticleEditor.UI.DesignWindowUI import Ui_DesignWindow
class DesignWindow(QtWidgets.QDialog, Ui_DesignWindow):
    def __init__(self, parent=None):
        super().__init__()

        self.setupUi(self)
        self.setWindowTitle("Placeholder title")
        self.parent = parent

        #
        # First Tab
        #

        hbox = QtWidgets.QHBoxLayout(self)

        splitter = QtWidgets.QSplitter(Qt.Vertical)


        self.pythonViewer = PythonViewer()
        self.outputViewer = OutputViewer()

        splitter.addWidget(self.pythonViewer)
        splitter.addWidget(self.outputViewer)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        hbox.addWidget(splitter)

        self.functionViewer = FunctionViewer()
        hbox.addWidget(self.functionViewer)

        self.definitionTab.setLayout(hbox)

        #
        # Second Tab
        #

        # Populate combo boxes

        self.orientationCombo.addItem("Unoriented")
        self.orientationCombo.addItem("Fixed Orientation")

        self.structureFactorCombo.addItem("None") # TODO: Structure Factor Options

        self.methodCombo.addItem("Monte Carlo")
        self.methodCombo.addItem("Grid")

        # Populate tables

        # Columns should be name, value, min, max, fit, [remove]
        self.parametersTable.setHorizontalHeaderLabels(["Name", "Value", "Min", "Max", "Fit", ""])
        self.structureFactorParametersTable.setHorizontalHeaderLabels(["Name", "Value", "Min", "Max", "Fit", ""])

        self.tabWidget.setAutoFillBackground(True)

        self.tabWidget.setStyleSheet("#tabWidget {background-color:red;}")





def main():
    """ Demo/testing window"""

    from sas.qtgui.convertUI import main

    main()

    app = QtWidgets.QApplication([])
    window = DesignWindow()

    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
