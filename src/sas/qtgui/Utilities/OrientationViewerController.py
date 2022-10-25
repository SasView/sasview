from PyQt5 import QtWidgets

from sas.qtgui.Utilities.UI.OrientationViewerControllerUI import Ui_OrientationViewierControllerUI


class OrientationViewierController(QtWidgets.QDialog, Ui_OrientationViewierControllerUI):
    def __init__(self, parent=None):
        super().__init__()

        self.setupUi(self)




def main():
    """ Show a demo of the slider """
    app = QtWidgets.QApplication([])

    mainWindow = QtWidgets.QMainWindow()
    viewer = OrientationViewierController(mainWindow)

    mainWindow.setCentralWidget(viewer)

    mainWindow.show()

    mainWindow.resize(700, 100)
    app.exec_()


if __name__ == "__main__":
    main()