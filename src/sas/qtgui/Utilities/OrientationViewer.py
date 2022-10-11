
from sas.qtgui.Utilities.UI.OrientationViewerUI import Ui_OrientationViewer

from PyQt5 import QtWidgets

class OrientationViewer(QtWidgets.QMainWindow, Ui_OrientationViewer):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent
        self.setupUi(self)


def main():
    """ Show a demo of the slider """
    app = QtWidgets.QApplication([])
    viewer = OrientationViewer()

    viewer.show()
    app.exec_()


if __name__ == "__main__":
    main()