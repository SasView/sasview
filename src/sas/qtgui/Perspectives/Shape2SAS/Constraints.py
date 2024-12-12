# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QWidget

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from UI.ConstraintsUI import Ui_Constraints
from Tables.variableTable import VariableTable
from ButtonOptions import ButtonOptions
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


class Constraints(QWidget, Ui_Constraints):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        #Setup variableTable and ButtonOptions here

        #Setup GUI for Constraints
        self.variableTable = VariableTable()
        self.buttonOptions = ButtonOptions()

        self.gridLayout_2.addWidget(self.variableTable, 0, 1, 1, 1)
        self.gridLayout_2.addWidget(self.buttonOptions, 1, 0, 1, 0, Qt.AlignmentFlag.AlignRight)

        self.createPlugin = QPushButton("Create Plugin")
        self.createPlugin.setMinimumSize(110, 24)
        self.createPlugin.setMaximumSize(110, 24)

        self.buttonOptions.horizontalLayout_5.insertWidget(1, self.createPlugin)
        self.buttonOptions.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)

        
        #self.createPlugin.clicked.connect(self.getPluginModel)


    #Methods to TextBrowser here



if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Constraints()
    widget.show()
    sys.exit(app.exec())