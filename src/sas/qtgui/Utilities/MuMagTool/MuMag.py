from sas.qtgui.Utilities.MuMagTool.UI.MuMagUI import Ui_MuMagTool
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6 import QtWidgets
from sas.qtgui.Utilities.MuMagTool import MuMagLib

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import matplotlib.pylab as pl
import numpy as np

from sas.qtgui.Utilities.MuMagTool.fit_parameters import FitParameters, ExperimentGeometry


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
        self.simple_fit_axes = self.fig.add_subplot(1, 1, 1)
        self.simple_fit_axes.set_visible(False)
        self.chi_squared_axes = self.fig.add_subplot(2, 2, 1)
        self.chi_squared_axes.set_visible(False)
        self.residuals_axes = self.fig.add_subplot(2, 2, 2)
        self.residuals_axes.set_visible(False)
        self.s_h_axes = self.fig.add_subplot(2, 2, 3)
        self.s_h_axes.set_visible(False)
        self.longitudinal_scattering_axes = self.fig.add_subplot(2, 2, 4)
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
        """ Get an object containing all the parameters needed for doing the fitting """

        a_min = self.aMinSpinBox.value()
        a_max = self.aMaxSpinBox.value()

        if a_max <= a_min:
            raise ValueError(f"minimum A must be less than maximum A")

        match self.ScatteringGeometrySelect.currentText().lower():
            case "parallel":
                geometry = ExperimentGeometry.PARALLEL
            case "perpendicular":
                geometry = ExperimentGeometry.PERPENDICULAR
            case _:
                raise ValueError(f"Unknown experiment geometry: {self.ScatteringGeometrySelect.currentText()}")

        return FitParameters(
            q_max=self.qMaxSpinBox.value(),
            min_applied_field=self.hMinSpinBox.value(),
            exchange_A_n=self.aSamplesSpinBox.value(),
            exchange_A_min=a_min,
            exchange_A_max=a_max,
            experiment_geometry=geometry)

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

        match parameters.experiment_geometry:
            case ExperimentGeometry.PERPENDICULAR:
                self.longitudinal_scattering_axes.set_visible(True)
            case ExperimentGeometry.PARALLEL:
                self.longitudinal_scattering_axes.set_visible(False)
            case _:
                raise ValueError(f"Unknown Value: {parameters.experiment_geometry}")


        self.MuMagLib_obj.do_fit(
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