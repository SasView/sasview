from sas.qtgui.Utilities.MuMagTool.UI.MuMagUI import Ui_MuMagTool
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6 import QtWidgets
from sas.qtgui.Utilities.MuMagTool import MuMagLib

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import matplotlib.pylab as pl
import numpy as np

from sas.qtgui.Utilities.MuMagTool.experimental_data import ExperimentalData
from sas.qtgui.Utilities.MuMagTool.failure import LoadFailure
from sas.qtgui.Utilities.MuMagTool.fit_parameters import FitParameters, ExperimentGeometry
from sas.qtgui.Utilities.MuMagTool.MuMagLib import MuMagLib

from logging import getLogger

log = getLogger("MuMag")

class MuMag(QtWidgets.QMainWindow, Ui_MuMagTool):
    def __init__(self, parent=None):
        super().__init__()

        self.setupUi(self)

        # Callbacks
        self.ImportDataButton.clicked.connect(self.importData)
        self.SimpleFitButton.clicked.connect(self.simple_fit_button_callback)
        self.CompareResultsButton.clicked.connect(self.compare_data_button_callback)
        self.SaveResultsButton.clicked.connect(self.save_data_button_callback)

        #
        # Data
        #

        self.data: list[ExperimentalData] | None = None

        #
        # Plotting
        #

        # Data
        data_plot_layout = QVBoxLayout()
        self.data_tab.setLayout(data_plot_layout)
        self.data_figure = plt.figure() #Figure(figsize=(width, height), dpi=dpi)
        self.figure_canvas = FigureCanvas(self.data_figure)
        self.data_axes = self.data_figure.add_subplot(1, 1, 1)
        self.data_axes.set_visible(False)
        data_plot_layout.addWidget(self.figure_canvas)

        # Fit results
        fit_results_layout = QVBoxLayout()
        self.fit_results_tab.setLayout(fit_results_layout)
        self.fit_results_figure = plt.figure()
        self.fit_results_canvas = FigureCanvas(self.fit_results_figure)

        self.chi_squared_axes = self.fit_results_figure.add_subplot(2, 2, 1)
        self.chi_squared_axes.set_visible(False)
        self.residuals_axes = self.fit_results_figure.add_subplot(2, 2, 2)
        self.residuals_axes.set_visible(False)
        self.s_h_axes = self.fit_results_figure.add_subplot(2, 2, 3)
        self.s_h_axes.set_visible(False)
        self.longitudinal_scattering_axes = self.fit_results_figure.add_subplot(2, 2, 4)
        self.longitudinal_scattering_axes.set_visible(False)

        fit_results_layout.addWidget(self.fit_results_canvas)

    def importData(self):
        """ Callback for the import data button """

        # Get the directory from the user
        directory = MuMagLib.directory_popup()

        if directory is None:
            log.info("No directory selected")
            return

        try:
            self.data = MuMagLib.import_data(directory)
        except LoadFailure as lf:
            log.error(repr(lf))
            return

        log.info(f"Loaded {len(self.data)} datasets")
        self.plot_data()
        self.data_figure.canvas.draw()

    def hide_everything(self):

        self.data_axes.set_visible(True)
        self.chi_squared_axes.set_visible(False)
        self.residuals_axes.set_visible(False)
        self.s_h_axes.set_visible(False)
        self.longitudinal_scattering_axes.set_visible(False)

        self.data_axes.cla()
        self.chi_squared_axes.cla()
        self.residuals_axes.cla()
        self.s_h_axes.cla()
        self.longitudinal_scattering_axes.cla()



    def plot_data(self):
        """ Plot Experimental Data: Generate Figure """

        colors = pl.cm.jet(np.linspace(0, 1, len(self.data)))

        for i, datum in enumerate(self.data):

            self.data_axes.loglog(datum.scattering_curve.x,
                      datum.scattering_curve.y,
                      linestyle='-', color=colors[i], linewidth=0.5,
                      label=r'$B_0 = ' + str(datum.applied_field) + '$ T')

            self.data_axes.loglog(datum.scattering_curve.x,
                      datum.scattering_curve.y, '.',
                      color=colors[i], linewidth=0.3, markersize=1)

        # Plot limits
        qlim = MuMagLib.nice_log_plot_bounds([datum.scattering_curve.x for datum in self.data])
        ilim = MuMagLib.nice_log_plot_bounds([datum.scattering_curve.y for datum in self.data])

        self.data_axes.set_xlabel(r'$q$ [1/nm]')
        self.data_axes.set_ylabel(r'$I_{\mathrm{exp}}$')
        self.data_axes.set_xlim(qlim)
        self.data_axes.set_ylim(ilim)
        self.data_figure.tight_layout()
        self.data_figure.canvas.draw()
        self.data_axes.set_visible(True)


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
        self.data_axes.cla()
        self.chi_squared_axes.cla()
        self.residuals_axes.cla()
        self.s_h_axes.cla()
        self.longitudinal_scattering_axes.cla()

        # Set axes visibility
        self.data_axes.set_visible(False)
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
            self.data_figure,
            self.chi_squared_axes,
            self.residuals_axes,
            self.s_h_axes,
            self.longitudinal_scattering_axes)

        self.figure_canvas.draw()

    def compare_data_button_callback(self):

        # Clear axes
        self.data_axes.cla()
        self.chi_squared_axes.cla()
        self.residuals_axes.cla()
        self.s_h_axes.cla()
        self.longitudinal_scattering_axes.cla()

        # Set visibility
        self.data_axes.set_visible(True)
        self.chi_squared_axes.set_visible(False)
        self.residuals_axes.set_visible(False)
        self.s_h_axes.set_visible(False)
        self.longitudinal_scattering_axes.set_visible(False)

        self.MuMagLib_obj.SimpleFit_CompareButtonCallback(self.data_figure, self.data_axes)



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