from sas.qtgui.Utilities.MuMagTool.UI.MuMagUI import Ui_MuMagTool
from PySide6.QtWidgets import QWidget
from PySide6 import QtWidgets
from sas.qtgui.Utilities.MuMagTool import MuMagLib


class MuMag(QtWidgets.QMainWindow, Ui_MuMagTool):
    def __init__(self, parent=None):
        super().__init__()
        self.MuMagLib_obj = MuMagLib.MuMagLib()
        self.setupUi(self)
        self.ImportDataButton.clicked.connect(self.import_data_button_callback)
        self.PlotDataButton.clicked.connect(self.plot_experimental_data_button_callback)
        self.SimpleFitButton.clicked.connect(self.simple_fit_button_callback)

    def import_data_button_callback(self):
        self.MuMagLib_obj.import_data_button_callback_sub()

    def plot_experimental_data_button_callback(self):
        self.MuMagLib_obj.plot_experimental_data()

    def simple_fit_button_callback(self):
        q_max = float(self.qMaxEdit.toPlainText())
        H_min = float(self.HminEdit.toPlainText())
        A1 = float(self.AMinEdit.toPlainText())
        A2 = float(self.AMaxEdit.toPlainText())
        A_N = int(self.ASamplesEdit.toPlainText())
        SANSgeometry = self.ScatteringGeometrySelect.currentText()
        self.MuMagLib_obj.simple_fit_button_callback(q_max, H_min, A1, A2, A_N, SANSgeometry)


def main():
    """ Show a demo of the slider """
    app = QtWidgets.QApplication([])
    form = MuMag()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()