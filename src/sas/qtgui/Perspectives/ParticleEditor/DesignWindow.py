from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Qt

from sas.qtgui.Perspectives.ParticleEditor.FunctionViewer import FunctionViewer
from sas.qtgui.Perspectives.ParticleEditor.PythonViewer import PythonViewer
from sas.qtgui.Perspectives.ParticleEditor.OutputViewer import OutputViewer
from sas.qtgui.Perspectives.ParticleEditor.CodeToolBar import CodeToolBar

from sas.qtgui.Perspectives.ParticleEditor.UI.DesignWindowUI import Ui_DesignWindow

import sas.qtgui.Perspectives.ParticleEditor.UI.icons_rc
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
        self.codeToolBar = CodeToolBar()

        self.codeToolBar.saveButton.clicked.connect(self.onSave)
        self.codeToolBar.loadButton.clicked.connect(self.onLoad)
        self.codeToolBar.buildButton.clicked.connect(self.onBuild)
        self.codeToolBar.scatterButton.clicked.connect(self.onScatter)

        self.solvent_sld = 0.0


        topSection = QtWidgets.QVBoxLayout()
        topSection.addWidget(self.pythonViewer)
        topSection.addWidget(self.codeToolBar)
        topSection.setContentsMargins(0,0,0,5)

        topWidget = QtWidgets.QWidget()
        topWidget.setLayout(topSection)


        splitter.addWidget(topWidget)
        splitter.addWidget(self.outputViewer)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        hbox.addWidget(splitter)

        # Function viewer
        self.functionViewer = FunctionViewer()
        self.functionViewer.radius_control.radiusField.valueChanged.connect(self.onRadiusChanged)

        # A components
        hbox.addWidget(self.functionViewer)
        self.definitionTab.setLayout(hbox)


        #
        # Ensemble tab
        #

        # Populate combo boxes

        self.orientationCombo.addItem("Unoriented")
        self.orientationCombo.addItem("Fixed Orientation")

        self.structureFactorCombo.addItem("None") # TODO: Structure Factor Options

        self.solventSLDBox.valueChanged.connect(self.onSolventSLDBoxChanged)


        #
        # Calculation Tab
        #

        self.methodCombo.addItem("Monte Carlo")
        self.methodCombo.addItem("Grid")



        # Populate tables

        # Columns should be name, value, min, max, fit, [remove]
        self.parametersTable.setHorizontalHeaderLabels(["Name", "Value", "Min", "Max", "Fit", ""])
        self.parametersTable.horizontalHeader().setStretchLastSection(True)

        self.structureFactorParametersTable.setHorizontalHeaderLabels(["Name", "Value", "Min", "Max", "Fit", ""])
        self.structureFactorParametersTable.horizontalHeader().setStretchLastSection(True)

        self.tabWidget.setAutoFillBackground(True)

        self.tabWidget.setStyleSheet("#tabWidget {background-color:red;}")

    def onRadiusChanged(self):
        if self.radiusFromParticleTab.isChecked():
            self.sampleRadius.setText("%.4g"%self.functionViewer.radius_control.radius())

    def onSolventSLDBoxChanged(self):
        sld = float(self.solventSLDBox.value())
        self.solvent_sld = sld
        # self.functionViewer.solvent_sld = sld # TODO: Think more about where to put this variable
        self.functionViewer.updateImage()

    def onLoad(self):
        print("Load clicked")

    def onSave(self):
        print("Save clicked")

    def onBuild(self):
        pass

    def onScatter(self):
        pass

    def onFit(self):
        pass

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
