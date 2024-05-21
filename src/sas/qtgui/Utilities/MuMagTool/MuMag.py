from sas.qtgui.Utilities.MuMagTool.UI.MuMagUI import Ui_MuMagTool
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6 import QtWidgets
from sas.qtgui.Utilities.MuMagTool import MuMagLib

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import matplotlib.pylab as pl
import numpy as np

from sas.qtgui.Utilities.MuMagTool.fit_parameters import FitParameters


class MuMag(QtWidgets.QMainWindow, Ui_MuMagTool):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)

        self.MuMagLib_obj = MuMagLib.MuMagLib()

        # Callbacks
        self.ImportDataButton.clicked.connect(self.import_data_button_callback)
        self.PlotDataButton.clicked.connect(self.plot_experimental_data_button_callback)
        self.SimpleFitButton.clicked.connect(self.simple_fit_button_callback)
        self.CompareResultsButton.clicked.connect(self.compare_data_button_callback)
        self.SaveResultsButton.clicked.connect(self.save_data_button_callback)

        # Plotting
        layout = QVBoxLayout()
        self.PlotDisplayPanel.setLayout(layout)

        self.fig = plt.figure() #Figure(figsize=(width, height), dpi=dpi)
        self.simple_fit_axes = self.fig.add_subplot(111)
        self.simple_fit_axes.set_visible(False)
        self.chi_squared_axes = self.fig.add_subplot(221)
        self.chi_squared_axes.set_visible(False)
        self.residuals_axes = self.fig.add_subplot(222)
        self.residuals_axes.set_visible(False)
        self.s_h_axes = self.fig.add_subplot(223)
        self.s_h_axes.set_visible(False)
        self.longitudinal_scattering_axes = self.fig.add_subplot(224)
        self.longitudinal_scattering_axes.set_visible(False)

        self.figure_canvas = FigureCanvas(self.fig)
        layout.addWidget(self.figure_canvas)

    def import_data_button_callback(self):
        self.MuMagLib_obj.import_data()

    def plot_experimental_data_button_callback(self):
        self.simple_fit_axes.set_visible(True)
        self.chi_squared_axes.set_visible(False)
        self.residuals_axes.set_visible(False)
        self.s_h_axes.set_visible(False)
        self.longitudinal_scattering_axes.set_visible(False)

        self.simple_fit_axes.cla()
        self.chi_squared_axes.cla()
        self.residuals_axes.cla()
        self.s_h_axes.cla()
        self.longitudinal_scattering_axes.cla()

        self.MuMagLib_obj.plot_exp_data(self.fig, self.simple_fit_axes)
        self.figure_canvas.draw()

    def fit_parameters(self) -> FitParameters:
        return FitParameters(
            q_max = float(self.qMaxEdit.toPlainText()),
            min_applied_field= float(self.HminEdit.toPlainText()),
            exchange_A_min = float(self.AMinEdit.toPlainText()),
            exchange_A_max = float(self.AMaxEdit.toPlainText()),
            exchange_A_n = int(self.ASamplesEdit.toPlainText()),
            experiment_geometry = self.ScatteringGeometrySelect.currentText())

    def simple_fit_button_callback(self):


        # Clear axes
        self.simple_fit_axes.cla()
        self.chi_squared_axes.cla()
        self.residuals_axes.cla()
        self.s_h_axes.cla()
        self.longitudinal_scattering_axes.cla()

        # Set axes visibility
        self.simple_fit_axes.set_visible(False)
        self.chi_squared_axes.set_visible(True)
        self.residuals_axes.set_visible(True)
        self.s_h_axes.set_visible(True)

        parameters = self.fit_parameters()

        if parameters.experiment_geometry == 'perpendicular':
            self.longitudinal_scattering_axes.set_visible(True)
        else:
            self.longitudinal_scattering_axes.set_visible(False)


        self.MuMagLib_obj.simple_fit_button_callback(
            parameters,
            self.fig,
            self.chi_squared_axes,
            self.residuals_axes,
            self.s_h_axes,
            self.longitudinal_scattering_axes)

        self.figure_canvas.draw()

    def compare_data_button_callback(self):

        # Clear axes
        self.simple_fit_axes.cla()
        self.chi_squared_axes.cla()
        self.residuals_axes.cla()
        self.s_h_axes.cla()
        self.longitudinal_scattering_axes.cla()

        # Set visibility
        self.simple_fit_axes.set_visible(True)
        self.chi_squared_axes.set_visible(False)
        self.residuals_axes.set_visible(False)
        self.s_h_axes.set_visible(False)
        self.longitudinal_scattering_axes.set_visible(False)

        self.MuMagLib_obj.SimpleFit_CompareButtonCallback(self.fig, self.simple_fit_axes)



    def save_data_button_callback(self):
        self.MuMagLib_obj.save_button_callback()



def main():
    """ Show a demo of the slider """
    app = QtWidgets.QApplication([])
    form = MuMag()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()