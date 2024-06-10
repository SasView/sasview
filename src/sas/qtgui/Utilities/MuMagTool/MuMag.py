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

from sas.qtgui.Utilities.MuMagTool.fit_result import FitResults
from sas.qtgui.Utilities.MuMagTool.least_squares_output import LeastSquaresOutputPerpendicular

log = getLogger("MuMag")

class MuMag(QtWidgets.QMainWindow, Ui_MuMagTool):
    def __init__(self, parent=None):
        super().__init__()

        self.setupUi(self)

        # Callbacks
        self.ImportDataButton.clicked.connect(self.importData)
        self.SimpleFitButton.clicked.connect(self.onFit)
        self.CompareResultsButton.clicked.connect(self.compare_data_button_callback)
        self.SaveResultsButton.clicked.connect(self.save_data_button_callback)

        #
        # Data
        #

        self.data: list[ExperimentalData] | None = None
        self.fit_data: FitResults | None = None

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
        self.residual_axes = self.fit_results_figure.add_subplot(2, 2, 2)
        self.s_h_axes = self.fit_results_figure.add_subplot(2, 2, 3)
        self.longitudinal_scattering_axes = self.fit_results_figure.add_subplot(2, 2, 4)

        fit_results_layout.addWidget(self.fit_results_canvas)

        # Set visibility
        self.hide_everything()

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

        self.hide_everything()
        self.plot_tabs.setTabEnabled(0, True)
        self.plot_data()

    def hide_everything(self):
        """ Hide all plots, disable tabs"""

        self.data_axes.cla()
        self.chi_squared_axes.cla()
        self.residual_axes.cla()
        self.s_h_axes.cla()
        self.longitudinal_scattering_axes.cla()

        self.plot_tabs.setTabEnabled(1, False)
        self.plot_tabs.setTabEnabled(2, False)
        # weird order because of how the widget behaves when all are not enabled
        self.plot_tabs.setTabEnabled(0, False)


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

        self.data_axes.set_visible(True)
        self.data_figure.canvas.draw()


    def get_fit_parameters(self) -> FitParameters:
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

    def onFit(self):

        if self.data is None:
            log.error("No data loaded")
            return None

        parameters = self.get_fit_parameters()

        match parameters.experiment_geometry:
            case ExperimentGeometry.PERPENDICULAR:
                self.longitudinal_scattering_axes.set_visible(True)
            case ExperimentGeometry.PARALLEL:
                self.longitudinal_scattering_axes.set_visible(False)
            case _:
                raise ValueError(f"Unknown Value: {parameters.experiment_geometry}")

        self.fit_data = MuMagLib.simple_fit(self.data, parameters)

        self.show_fit_results()


    def show_fit_results(self):
        """ Show the results of the fit in the widget """

        # Check for data
        if self.fit_data is None:
            log.error("No fit data to show")
            return

        # Some dereferencing to make things more readable
        A_uncertainty = self.fit_data.optimal_exchange_A_uncertainty
        refined = self.fit_data.refined_fit_data
        sweep_data = self.fit_data.sweep_data

        # Text to show TODO: Replace with field in dialog
        if A_uncertainty < 1e-4:
            A_uncertainty = 0

        A_uncertainty_str = str(A_uncertainty)
        A_opt_str = str(refined.exchange_A * 1e12)

        q = refined.q * 1e-9

        # Clear plots
        self.chi_squared_axes.cla()
        self.residual_axes.cla()
        self.s_h_axes.cla()
        self.longitudinal_scattering_axes.cla()

        # Plot A search data
        self.chi_squared_axes.set_title('$A_{\mathrm{opt}} = (' + A_opt_str[0:5] + ' \pm ' + A_uncertainty_str[0:4] + ')$ pJ/m')
        self.chi_squared_axes.plot(sweep_data.exchange_A_checked * 1e12, sweep_data.exchange_A_chi_sq)
        self.chi_squared_axes.plot(sweep_data.optimal.exchange_A * 1e12, sweep_data.optimal.exchange_A_chi_sq, 'o')

        self.chi_squared_axes.set_xlim([min(sweep_data.exchange_A_checked * 1e12), max(sweep_data.exchange_A_checked * 1e12)])
        self.chi_squared_axes.set_xlabel('$A$ [pJ/m]')
        self.chi_squared_axes.set_ylabel('$\chi^2$')

        # Residual intensity plot
        self.residual_axes.plot(q, refined.I_residual, label='fit')
        self.residual_axes.set_yscale('log')
        self.residual_axes.set_xscale('log')
        self.residual_axes.set_xlim([min(q), max(q)])
        self.residual_axes.set_xlabel('$q$ [1/nm]')
        self.residual_axes.set_ylabel('$I_{\mathrm{res}}$')

        # S_H parameter
        self.s_h_axes.plot(q, refined.S_H, label='fit')
        self.s_h_axes.set_yscale('log')
        self.s_h_axes.set_xscale('log')
        self.s_h_axes.set_xlim([min(q), max(q)])
        self.s_h_axes.set_xlabel('$q$ [1/nm]')
        self.s_h_axes.set_ylabel('$S_H$')

        # S_M parameter
        if isinstance(refined, LeastSquaresOutputPerpendicular):
            self.longitudinal_scattering_axes.plot(q, refined.S_M, label='fit')
            self.longitudinal_scattering_axes.set_yscale('log')
            self.longitudinal_scattering_axes.set_xscale('log')
            self.longitudinal_scattering_axes.set_xlim([min(q), max(q)])
            self.longitudinal_scattering_axes.set_xlabel('$q$ [1/nm]')
            self.longitudinal_scattering_axes.set_ylabel('$S_M$')

        self.fit_results_figure.tight_layout()

        self.chi_squared_axes.set_visible(True)
        self.residual_axes.set_visible(True)
        self.s_h_axes.set_visible(True)
        self.longitudinal_scattering_axes.set_visible(True)

        self.plot_tabs.setTabEnabled(1, True)
        self.plot_tabs.setTabEnabled(2, True)

        self.plot_tabs.setCurrentIndex(1)


    def compare_data_button_callback(self):

        # Clear axes
        self.data_axes.cla()
        self.chi_squared_axes.cla()
        self.residual_axes.cla()
        self.s_h_axes.cla()
        self.longitudinal_scattering_axes.cla()

        # Set visibility
        self.data_axes.set_visible(True)
        self.chi_squared_axes.set_visible(False)
        self.residual_axes.set_visible(False)
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