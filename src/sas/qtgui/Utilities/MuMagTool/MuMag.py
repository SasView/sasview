from sas.qtgui.Utilities.MuMagTool.UI.MuMagUI import Ui_MainWindow
from PySide6.QtWidgets import QWidget
from PySide6 import QtWidgets
import MuMagLib


def on_press_2():
    print("HELLO")

class MuMag(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__()

        self.setupUi(self)
        self.pushButton.clicked.connect(self.import_data_button_callback)
        self.pushButton_2.clicked.connect(self.plot_experimental_data_button_callback)
        self.pushButton.clicked.connect(on_press_2)

    def import_data_button_callback(self):
        MuMagLib.import_data_button_callback_sub()

    def plot_experimental_data_button_callback(self):
        MuMagLib.plot_experimental_data()


def main():
    """ Show a demo of the slider """
    app = QtWidgets.QApplication([])
    form = MuMag()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()