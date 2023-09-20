from sas.qtgui.Utilities.MuMagTool.UI.MuMagUI import Ui_MuMagTool
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6 import QtWidgets
from sas.qtgui.Utilities.MuMagTool import MuMagLib

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import matplotlib.pylab as pl
import numpy as np

class MuMag(QtWidgets.QMainWindow, Ui_MuMagTool):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)

        self.MuMagLib_obj = MuMagLib.MuMagLib()

        # Callbacks
        self.ImportDataButton.clicked.connect(self.import_data_button_callback)
        self.PlotDataButton.clicked.connect(self.plot_experimental_data_button_callback)
        self.SimpleFitButton.clicked.connect(self.simple_fit_button_callback)

        # Plotting
        layout = QVBoxLayout()
        self.PlotDisplayPanel.setLayout(layout)

        self.fig = Figure() #Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        figure_canvas = FigureCanvas(self.fig)

        layout.addWidget(figure_canvas)

    def import_data_button_callback(self):
        self.MuMagLib_obj.import_data_button_callback_sub()

    def plot_experimental_data_button_callback(self):
        self.MuMagLib_obj.plot_experimental_data(self.fig)

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