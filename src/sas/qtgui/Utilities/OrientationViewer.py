
from sas.qtgui.Utilities.UI.OrientationViewerUIBackup import Ui_OrientationViewer

from PyQt5 import QtWidgets

class OrientationViewer(QtWidgets.QWidget, Ui_OrientationViewer):

    def __init__(self, parent=None):
        super().__init__()

        self.parent = parent
        self.setupUi(parent)


def main():
    """ Show a demo of the slider """
    app = QtWidgets.QApplication([])
    app.setStyleSheet("* {font-size: 11pt;}")

    mainWindow = QtWidgets.QMainWindow()
    viewer = OrientationViewer(mainWindow)

    mainWindow.setCentralWidget(viewer)

    mainWindow.show()
    app.exec_()


if __name__ == "__main__":
    main()