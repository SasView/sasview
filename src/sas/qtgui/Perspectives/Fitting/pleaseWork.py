import sys
from PySide6 import QtWidgets, QtCore, QtGui
from .UI.ZE import Ui_Form


class sample(QtWidgets.QDialog, Ui_Form):
    def __init__(self, parent=None, edit_only=False):
        super().__init__()

        self.parent = parent

        self.setupUi(self)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win =  sample()
    win.show()
    app.exec()