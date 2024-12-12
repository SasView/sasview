# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QWidget

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from Tables.UI.variableTableUI import Ui_VariableTable


class VariableTable(QWidget, Ui_VariableTable):

    def __init__(self):
        super(VariableTable, self).__init__()
        self.setupUi(self)

    #Methods on generating table with checkboxes and variable names here


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = VariableTable()
    widget.show()
    sys.exit(app.exec())
