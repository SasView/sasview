from logging import getLogger
from typing import cast, override

import matplotlib.pylab as pl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6 import QtWidgets
from PySide6.QtWidgets import QVBoxLayout, QWidget

from sasdata.quantities.quantity import Quantity
from sasdata.quantities.unit_parser import parse_unit
from sasdata.trend import Trend

from sas.data_manager import NewDataManager as DataManager
from sas.data_manager import TrackedData
from sas.qtgui.Utilities.MuMag.datastructures import (
    ExperimentGeometry,
    FitFailure,
    FitParameters,
    FitResults,
    LeastSquaresOutputPerpendicular,
)
from sas.qtgui.Utilities.MuMag.MuMagLib import MuMagLib
from sas.qtgui.Utilities.MuMag.UI.MuMagUI import Ui_MuMagTool
from sas.refactored import Perspective

log = getLogger("MuMag")

class MuMag(Perspective, Ui_MuMagTool):
    """ Main widget for the MuMag tool """

    def __init__(self, data_manager: DataManager, parent: QWidget | None=None):
        super().__init__(data_manager, parent)

        self.parent = parent
        self.setupUi(self)

        # Callbacks
        self.SimpleFitButton.clicked.connect(self.onFit)
        self.SaveResultsButton.clicked.connect(self.onSave)
        self.helpButton.clicked.connect(self.onHelp)

        #
        # Data
        #

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

        # Comparison
        comparison_layout = QVBoxLayout()
        self.comparison_tab.setLayout(comparison_layout)
        self.comparison_figure = plt.figure()
        self.comparison_canvas = FigureCanvas(self.comparison_figure)

        self.comparison_axes = self.comparison_figure.add_subplot(1, 1, 1)

        comparison_layout.addWidget(self.comparison_canvas)

        # Set visibility
        self.hide_everything()

    @property
    def trend(self) -> Trend | None:
        if len(self.associatedData) == 0:
            return None
        return cast(Trend, self.associatedData[0])

    @property
    @override
    def title(self) -> str:
        return "MuMag Perspective"

    @property
    @override
    def supported_data(self) -> set[type[TrackedData]]:
        return {Trend}

    @property
    @override
    def supports_multiple_data(self) -> bool:
        return False

    @override
    def newAssocation(self):
        self.show_input_data()
        self.plot_tabs.setTabEnabled(0, True)

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


    def show_input_data(self):
        """ Plot Experimental Data: Generate Figure """

        if self.trend is None:
            return

        applied_fields = [
            Quantity(float(value), parse_unit("mT"))
            for value in self.trend.get_trend_values("applied_magnetic_field")
        ]
        colors = pl.cm.jet(np.linspace(0, 1, len(self.trend.data)))

        for i, datum in enumerate(self.trend.data):

            self.data_axes.loglog(datum.abscissae.axes[0].value,
                       datum.ordinate.value,
                       linestyle='-', color=colors[i], linewidth=0.5,
                       label=r'$B_0 = ' + applied_fields[i].explicitly_formatted("T") + '$')

            self.data_axes.loglog(datum.abscissae.axes[0].value,
                       datum.ordinate.value, '.',
                       color=colors[i], linewidth=0.3, markersize=1)

        # Plot limits
        qlim = MuMagLib.nice_log_plot_bounds([datum.abscissae.axes[0].value for datum in self.trend.data])
        ilim = MuMagLib.nice_log_plot_bounds([datum.ordinate.value for datum in self.trend.data])

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
            raise ValueError("minimum A must be less than maximum A")

        match self.ScatteringGeometrySelect.currentText().lower():
            case "parallel":
                geometry = ExperimentGeometry.PARALLEL
            case "perpendicular":
                geometry = ExperimentGeometry.PERPENDICULAR
            case _:
                raise ValueError(f"Unknown experiment geometry: {self.ScatteringGeometrySelect.currentText()}")

        return FitParameters(
            q_max=Quantity(self.qMaxSpinBox.value(), parse_unit("1/nm")),
            min_applied_field=Quantity(self.hMinSpinBox.value(), parse_unit("mT")),
            exchange_A_n=self.aSamplesSpinBox.value(),
            exchange_A_min=Quantity(a_min, parse_unit("pJ/m")),
            exchange_A_max=Quantity(a_max, parse_unit("pJ/m")),
            experiment_geometry=geometry)

    def onFit(self):

        if self.trend is None:
            log.error("No data loaded")
            return None

        parameters = self.get_fit_parameters()

        match parameters.experiment_geometry:
            case ExperimentGeometry.PERPENDICULAR:
                self.longitudinal_scattering_axes.set_visible(True)
            case ExperimentGeometry.PARALLEL:
                self.longitudinal_scattering_axes.set_visible(False)
            case _:
                raise log.error(f"Unknown geometry: {parameters.experiment_geometry}")

        try:
            self.fit_data = MuMagLib.simple_fit(self.trend, parameters)

        except FitFailure as ff:
            log.error("Fitting failed - are the parameters correct? "+repr(ff))
            return


        self.show_fit_results()


    def show_fit_results(self):
        """ Show the results of the fit in the widget """

        # Check for data
        if self.fit_data is None:
            log.error("No fit data to show")
            return

        # Some dereferencing to make things more readable
        refined = self.fit_data.refined_fit_data
        sweep_data = self.fit_data.sweep_data

        q = (refined.q * 1e-9).value

        # Update text boxes

        self.exchange_a_display.setText(f"{(self.fit_data.refined_fit_data.exchange_A).value * 1e12 : .5g} pJ/m")
        self.exchange_a_std_display.setText(f"{(self.fit_data.optimal_exchange_A_uncertainty).value : .5g} pJ/m")



        # Clear plots
        self.chi_squared_axes.cla()
        self.residual_axes.cla()
        self.s_h_axes.cla()
        self.longitudinal_scattering_axes.cla()

        # Plot A search data
        self.chi_squared_axes.plot((sweep_data.exchange_A_checked * 1e12).value, sweep_data.exchange_A_chi_sq)
        self.chi_squared_axes.plot((sweep_data.optimal.exchange_A * 1e12).value, sweep_data.optimal.exchange_A_chi_sq, 'o')

        self.chi_squared_axes.set_xlim([min((sweep_data.exchange_A_checked * 1e12).value), max((sweep_data.exchange_A_checked * 1e12).value)])
        self.chi_squared_axes.set_xlabel('$A$ [pJ/m]')
        self.chi_squared_axes.set_ylabel(r'$\chi^2$')

        # Residual intensity plot
        self.residual_axes.plot(q, refined.I_residual.value, label='fit')
        self.residual_axes.set_yscale('log')
        self.residual_axes.set_xscale('log')
        self.residual_axes.set_xlim([min(q), max(q)])
        self.residual_axes.set_xlabel('$q$ [1/nm]')
        self.residual_axes.set_ylabel(r'$I_{\mathrm{res}}$')

        # S_H parameter
        self.s_h_axes.plot(q, refined.S_H.value, label='fit')
        self.s_h_axes.set_yscale('log')
        self.s_h_axes.set_xscale('log')
        self.s_h_axes.set_xlim([min(q), max(q)])
        self.s_h_axes.set_xlabel('$q$ [1/nm]')
        self.s_h_axes.set_ylabel('$S_H$')

        # S_M parameter
        if isinstance(refined, LeastSquaresOutputPerpendicular):
            self.longitudinal_scattering_axes.plot(q, refined.S_M.value, label='fit')
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

        #
        # Comparison Tab
        #

        # Plot limits
        qlim = MuMagLib.nice_log_plot_bounds([datum.abscissae.axes[0].value for datum in self.fit_data.input_trend.data])
        ilim = MuMagLib.nice_log_plot_bounds([datum.ordinate.value for datum in self.fit_data.input_trend.data])

        # Show the experimental data
        colors = pl.cm.jet(np.linspace(0, 1, len(self.fit_data.input_trend.data)))
        for k, datum in enumerate(self.fit_data.input_trend.data):
            self.comparison_axes.loglog(
                datum.abscissae.axes[0].value,
                datum.ordinate.value,
                linestyle='None', color=colors[k], marker='x')

        # Show the fitted curves
        n_sim = self.fit_data.refined_fit_data.I_simulated.value.shape[0]
        applied_fields = [
            Quantity(float(value), parse_unit("mT"))
            for value in self.fit_data.input_trend.get_trend_values("applied_magnetic_field")
        ]
        colors = pl.cm.jet(np.linspace(0, 1, n_sim))
        for k in range(n_sim):
            self.comparison_axes.loglog(
                (self.fit_data.refined_fit_data.q * 1e-9).value,
                self.fit_data.refined_fit_data.I_simulated.value[k, :],
                linestyle='solid', color=colors[k],
                label='B_0 = ' + applied_fields[k].explicitly_formatted("T"))

        self.comparison_axes.set_xlabel(r'$q$ [1/nm]')
        self.comparison_axes.set_ylabel(r'$I_{\mathrm{exp}}$')
        self.comparison_axes.set_xlim(qlim)
        self.comparison_axes.set_ylim(ilim)
        self.comparison_figure.tight_layout()
        self.comparison_figure.canvas.draw()


        #
        # Set up tabs
        #

        self.plot_tabs.setTabEnabled(1, True)
        self.plot_tabs.setTabEnabled(2, True)

        self.plot_tabs.setCurrentIndex(1)

    def onSave(self):
        """ Save button pressed """

        raise NotImplementedError("The Mumag save result functionality has not been reimplemented for data exporters yet.")

        if self.fit_data is None:
            log.error("Nothing to save!")
            return

        directory = MuMagLib.directory_popup()

        if directory is not None:

            MuMagLib.save_data(self.fit_data, directory)

    def onHelp(self):
        url = "/user/qtgui/Utilities/MuMag/mumag_help.html"
        self.parent.showHelp(url)

def main():
    """ Show a demo of the slider """
    app = QtWidgets.QApplication([])
    form = MuMag()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()
