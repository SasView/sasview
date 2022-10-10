
from sas.qtgui.Utilities.UI.OrientationViewerUI import Ui_OrientationViewer

from PyQt5 import QtWidgets

class OrientationViewer(QtWidgets.QMainWindow, Ui_OrientationViewer):

    def __init__(self, parent=None):
        super().__init__(parent._parent)

        self.parent = parent
        self.setupUi(self)


def main():
    pass

if __name__ == "__main__":
    main()