# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QWidget

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from UI.ButtonOptionsUI import Ui_ButtonOptions

class ButtonOptions(QWidget, Ui_ButtonOptions):
    """close, reset and help options"""
    def __init__(self, parent=None):
        super().__init__()

        self.setupUi(self)

