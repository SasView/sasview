import numpy as np
import matplotlib.pylab as pl
from tkinter import messagebox
import os
import os.path
from datetime import datetime

from PySide6 import QtWidgets
from PySide6.QtWidgets import QFileDialog

from sas.qtgui.Utilities.MuMagTool import MuMagPerpendicularGeo
from sas.qtgui.Utilities.MuMagTool.MuMagParallelGeo import LSQ_PAR
from sas.qtgui.Utilities.MuMagTool.MuMagPerpendicularGeo import LSQ_PERP
from sas.qtgui.Utilities.MuMagTool.experimental_data import ExperimentalData
from sas.qtgui.Utilities.MuMagTool.failure import LoadFailure
from sas.qtgui.Utilities.MuMagTool.fit_parameters import FitParameters, ExperimentGeometry
from sas.qtgui.Utilities.MuMagTool.least_squares_output import LeastSquaresOutputPerpendicular, \
    LeastSquaresOutputParallel
from sas.qtgui.Utilities.MuMagTool.sweep_output import SweepOutput

from sasdata.dataloader.loader import Loader


class MuMagLib:
    def __init__(self):

        self.input_data: list[ExperimentalData] | None = None

    @staticmethod
    def directory_popup():
        directory = QFileDialog.getExistingDirectory()

        if directory.strip() == "":
            return None
        else:
            return directory


    @staticmethod
    def import_data(directory):
        """Import experimental data and get information from filenames"""

        try:
            # Load the data
            loader = Loader()
            input_names = [name for name in os.listdir(directory) if name.lower().endswith(".csv")]
            input_paths = [os.path.join(directory, filename) for filename in input_names]

            input_data = loader.load(input_paths)

            data = []
            for filename, data1d in zip(input_names, input_data):

                # Extract the metadata from the filename
                filename_parts = filename.split(".")
                filename = ".".join(filename_parts[:-1])

                parts = filename.split("_")

                applied_field = float(parts[1])  # mT
                saturation_magnetisation = float(parts[2])  # mT
                demagnetising_field = float(parts[3])  # mT

                # Create input data object
                data.append(ExperimentalData(
                    scattering_curve=data1d,
                    applied_field=applied_field,
                    saturation_magnetisation=saturation_magnetisation,
                    demagnetising_field=demagnetising_field))

            return sorted(data, key=lambda x: x.applied_field)

        except Exception as e:
            raise LoadFailure(f"Failed to load from {directory}: " + repr(e))

    @staticmethod
    def nice_log_plot_bounds(data: list[np.ndarray]):
        """ Get nice bounds for the loglog plots

        :return: (lower, upper) bounds appropriate to pass to plt.xlim/ylim
        """

        upper = np.amax(np.array(data))
        lower = np.amin(np.array(data))

        return (
            10 ** (np.floor(np.log10(lower))) * np.floor(lower / 10 ** (np.floor(np.log10(lower)))),
            10 ** (np.floor(np.log10(upper))) * np.ceil(upper / 10 ** (np.floor(np.log10(upper))))
        )


    # @staticmethod
    def do_fit(self, parameters: FitParameters, figure, axes1, axes2, axes3, axes4):

        if self.input_data is None:
            messagebox.showerror(title="Error!",
                                 message="No experimental Data available! Please import experimental data!")

            return None

        # Use an index for data upto qmax based on first data set
        # Not ideal, would be preferable make sure the data was
        # compatible, using something like interpolation TODO
        square_distance_from_qmax = (self.input_data[0].scattering_curve.x - parameters.q_max) ** 2
        max_q_index = int(np.argmin(square_distance_from_qmax))

        filtered_inputs = [datum.restrict_by_index(max_q_index)
                           for datum in self.input_data
                           if datum.applied_field >= parameters.min_applied_field]


        # Least Squares Fit in case of perpendicular SANS geometry
        match parameters.experiment_geometry:
            case ExperimentGeometry.PERPENDICULAR:


                sweep_data = MuMagPerpendicularGeo.sweep(parameters, filtered_inputs)

                crude_A = sweep_data.optimal.exchange_A
                refined_A = self.refine_exchange_A(filtered_inputs, crude_A, ExperimentGeometry.PERPENDICULAR)

                refined = MuMagPerpendicularGeo.LSQ_PERP(filtered_inputs, refined_A)

                uncertainty = self.uncertainty(filtered_inputs, refined_A, ExperimentGeometry.PERPENDICULAR)

                self.plot_results(sweep_data, refined, uncertainty * 1e12, figure, axes1, axes2, axes3, axes4)



            case ExperimentGeometry.PARALLEL:


                sweep_data = MuMagPerpendicularGeo.sweep(parameters, filtered_inputs)

                crude_A = sweep_data.optimal.exchange_A
                print(crude_A)
                refined_A = self.refine_exchange_A(filtered_inputs, parameters.exchange_A_min*1e-12, ExperimentGeometry.PARALLEL)

                refined = MuMagPerpendicularGeo.LSQ_PAR(filtered_inputs, refined_A)

                uncertainty = self.uncertainty(filtered_inputs, refined_A, ExperimentGeometry.PARALLEL)

                self.plot_results(sweep_data, refined, uncertainty * 1e12,
                                              figure, axes1, axes2, axes3, axes4)

                # Save to global Variables
                # self.SimpleFit_q_exp = q
                # self.SimpleFit_I_exp = I_exp_red
                # self.SimpleFit_sigma_exp = sigma
                # self.SimpleFit_B_0_exp = self.B_0_exp[K_H:]
                # self.SimpleFit_Ms_exp = self.Ms_exp[K_H:]
                # self.SimpleFit_Hdem_exp = self.Hdem_exp[K_H:]
                # self.SimpleFit_I_fit = I_opt
                # self.SimpleFit_A = A
                # self.SimpleFit_chi_q = chi_q
                # self.SimpleFit_S_H_fit = S_H_opt
                # self.SimpleFit_I_res_fit = I_res_opt
                # self.SimpleFit_A_opt = A_opt
                # self.SimpleFit_chi_q_opt = chi_q_opt
                # self.SimpleFit_A_sigma = A_Uncertainty
                # self.SimpleFit_SANSgeometry = "parallel"

    @staticmethod
    def refine_exchange_A(
            data: list[ExperimentalData],
            exchange_A_initial: float,
            geometry: ExperimentGeometry,
            epsilon: float = 0.0001):

        """ Refines the A parameter using Jarratt's method of successive parabolic interpolation"""

        match geometry:
            case ExperimentGeometry.PARALLEL:
                least_squares_function = LSQ_PAR
            case ExperimentGeometry.PERPENDICULAR:
                least_squares_function = LSQ_PERP
            case _:
                raise ValueError(f"Unknown experimental geometry: {geometry}")

        delta = exchange_A_initial * 0.1

        x_1 = exchange_A_initial - delta
        x_2 = exchange_A_initial
        x_3 = exchange_A_initial + delta

        y_1 = least_squares_function(data, x_1).exchange_A_chi_sq
        y_2 = least_squares_function(data, x_2).exchange_A_chi_sq
        y_3 = least_squares_function(data, x_3).exchange_A_chi_sq

        x_4 = x_3 + 0.5 * ((x_2 - x_3) ** 2 * (y_3 - y_1) + (x_1 - x_3) ** 2 * (y_2 - y_3)) \
              / ((x_2 - x_3) * (y_3 - y_1) + (x_1 - x_3) * (y_2 - y_3))

        for i in range(200):
            if np.abs(2 * (x_4 - x_3) / (x_4 + x_3)) < epsilon:
                break

            x_1, x_2, x_3 = x_2, x_3, x_4
            y_1, y_2, y_3 = y_2, y_3, least_squares_function(data, x_3).exchange_A_chi_sq

            x_4 = x_3 + 0.5 * ((x_2 - x_3) ** 2 * (y_3 - y_1) + (x_1 - x_3) ** 2 * (y_2 - y_3)) \
                  / ((x_2 - x_3) * (y_3 - y_1) + (x_1 - x_3) * (y_2 - y_3))

        return x_4

    @staticmethod
    def uncertainty(
            data: list[ExperimentalData],
            A_opt: float,
            geometry: ExperimentGeometry):
        """Calculate the uncertainty for the optimal exchange stiffness A"""

        # Estimate variance from second order derivative of chi-square function via Finite Differences

        match geometry:
            case ExperimentGeometry.PARALLEL:
                least_squares_function = LSQ_PAR
            case ExperimentGeometry.PERPENDICULAR:
                least_squares_function = LSQ_PERP
            case _:
                raise ValueError(f"Unknown experimental geometry: {geometry}")

        p = 0.001  # fractional gap size for finite differences
        dA = A_opt * p
        A1 = A_opt - 2 * dA
        A2 = A_opt - 1 * dA
        A3 = A_opt
        A4 = A_opt + 1 * dA
        A5 = A_opt + 2 * dA

        chi1 = least_squares_function(data, A1).exchange_A_chi_sq
        chi2 = least_squares_function(data, A2).exchange_A_chi_sq
        chi3 = least_squares_function(data, A3).exchange_A_chi_sq
        chi4 = least_squares_function(data, A4).exchange_A_chi_sq
        chi5 = least_squares_function(data, A5).exchange_A_chi_sq

        d2chi_dA2 = (-chi1 + 16 * chi2 - 30 * chi3 + 16 * chi4 - chi5) / (12 * dA ** 2)

        # Scale variance by number of samples and return reciprocal square root

        n_field_strengths = len(data)  # Number of fields
        n_q = len(data[0].scattering_curve.x)  # Number of q points

        return np.sqrt(2 / (n_field_strengths * n_q * d2chi_dA2))

    def save_button_callback(self):

        SimpleFit_q_exp = self.SimpleFit_q_exp
        SimpleFit_I_exp = self.SimpleFit_I_exp
        SimpleFit_sigma_exp = self.SimpleFit_sigma_exp
        SimpleFit_B_0_exp = self.SimpleFit_B_0_exp
        SimpleFit_Ms_exp = self.SimpleFit_Ms_exp
        SimpleFit_Hdem_exp = self.SimpleFit_Hdem_exp
        SimpleFit_I_fit = self.SimpleFit_I_fit
        SimpleFit_A = self.SimpleFit_A
        SimpleFit_chi_q = self.SimpleFit_chi_q
        SimpleFit_S_H_fit = self.SimpleFit_S_H_fit
        SimpleFit_S_M_fit = self.SimpleFit_S_M_fit
        SimpleFit_I_res_fit = self.SimpleFit_I_res_fit
        SimpleFit_A_opt = self.SimpleFit_A_opt
        SimpleFit_chi_q_opt = self.SimpleFit_chi_q_opt
        SimpleFit_A_sigma = self.SimpleFit_A_sigma
        SimpleFit_SANSgeometry = self.SimpleFit_SANSgeometry

        print('hello')
        print(np.size(SimpleFit_q_exp))

        if np.size(SimpleFit_q_exp) > 1:
            if SimpleFit_SANSgeometry == 'perpendicular':
                DIR = QFileDialog.getExistingDirectory()

                now = datetime.now()
                TimeStamp = now.strftime("%d_%m_%Y__%H_%M_%S")
                FolderName = "SimpleFitResults_" + TimeStamp
                path = os.path.join(DIR, FolderName)
                os.mkdir(path)

                InfoFile = open(path + "/InfoFile.txt", "w")
                InfoFile.write("FitMagneticSANS Toolbox - SimpleFit Results Info File \n\n")
                InfoFile.write("Timestamp: " + TimeStamp + " \n\n")
                InfoFile.write("SANS geometry: " + SimpleFit_SANSgeometry + "\n\n")
                InfoFile.write("Maximal Scattering Vector:  q_max = " +
                               str(np.amax(SimpleFit_q_exp*1e-9)) + " 1/nm \n")
                InfoFile.write("Minimal Applied Field: mu_0*H_min = " +
                               str(np.around(np.amin(SimpleFit_B_0_exp), 0)) + " mT \n\n")
                InfoFile.write("Result for the exchange stiffness constant: A = (" +
                               str(np.around(SimpleFit_A_opt*1e12, 3)) + " +/- " +
                               str(np.around(SimpleFit_A_sigma*1e12, 2)) + ") pJ/m \n")
                InfoFile.close()

                FolderName2 = "SANS_Intensity_Fit"
                path2 = os.path.join(path, FolderName2)
                os.mkdir(path2)

                for k in np.arange(0, np.size(SimpleFit_B_0_exp)):
                    np.savetxt(os.path.join(path2, str(k+1) + "_" + str(SimpleFit_B_0_exp[k]) + "_"
                                            + str(SimpleFit_Ms_exp[k]) + "_" + str(SimpleFit_Hdem_exp[k]) + ".csv"),
                               np.array([SimpleFit_q_exp[k, :].T, SimpleFit_I_fit[k, :].T]).T, delimiter=" ")

                FolderName3 = "SANS_Intensity_Exp"
                path3 = os.path.join(path, FolderName3)
                os.mkdir(path3)

                for k in np.arange(0, np.size(SimpleFit_B_0_exp)):
                    np.savetxt(os.path.join(path3, str(k+1) + "_" + str(SimpleFit_B_0_exp[k]) + "_"
                                            + str(SimpleFit_Ms_exp[k]) + "_" + str(SimpleFit_Hdem_exp[k]) + ".csv"),
                               np.array([SimpleFit_q_exp[k, :].T, SimpleFit_I_exp[k, :].T,
                                         SimpleFit_sigma_exp[k, :]]).T, delimiter=" ")

                FolderName4 = "Fit_Results"
                path4 = os.path.join(path, FolderName4)
                os.mkdir(path4)

                np.savetxt(os.path.join(path4, "chi.csv"), np.array([SimpleFit_A, SimpleFit_chi_q]).T, delimiter=" ")
                np.savetxt(os.path.join(path4, "S_H.csv"), np.array([SimpleFit_q_exp[0, :].T,
                                                                     SimpleFit_S_H_fit[0, :]]).T, delimiter=" ")
                np.savetxt(os.path.join(path4, "S_M.csv"), np.array([SimpleFit_q_exp[0, :].T,
                                                                     SimpleFit_S_M_fit[0, :]]).T, delimiter=" ")
                np.savetxt(os.path.join(path4, "I_res.csv"), np.array([SimpleFit_q_exp[0, :].T,
                                                                       SimpleFit_I_res_fit[0, :]]).T, delimiter=" ")

            elif SimpleFit_SANSgeometry == 'parallel':
                DIR = QFileDialog.getExistingDirectory()

                now = datetime.now()
                TimeStamp = now.strftime("%d_%m_%Y__%H_%M_%S")
                FolderName = "SimpleFitResults_" + TimeStamp
                path = os.path.join(DIR, FolderName)
                os.mkdir(path)

                InfoFile = open(path + "/InfoFile.txt", "w")
                InfoFile.write("FitMagneticSANS Toolbox - SimpleFit Results Info File \n\n")
                InfoFile.write("Timestamp: " + TimeStamp + " \n\n")
                InfoFile.write("SANS geometry: " + SimpleFit_SANSgeometry + "\n\n")
                InfoFile.write("Maximal Scattering Vector:  q_max = " +
                               str(np.amax(SimpleFit_q_exp * 1e-9)) + " 1/nm \n")
                InfoFile.write("Minimal Applied Field: mu_0*H_min = " +
                               str(np.around(np.amin(SimpleFit_B_0_exp), 0)) + " mT \n\n")
                InfoFile.write("Result for the exchange stiffness constant: A = (" +
                               str(np.around(SimpleFit_A_opt * 1e12, 3)) + " +/- " +
                               str(np.around(SimpleFit_A_sigma * 1e12, 2)) + ") pJ/m \n")
                InfoFile.close()

                FolderName2 = "SANS_Intensity_Fit"
                path2 = os.path.join(path, FolderName2)
                os.mkdir(path2)

                for k in np.arange(0, np.size(SimpleFit_B_0_exp)):
                    np.savetxt(os.path.join(path2, str(k + 1) + "_" + str(int(SimpleFit_B_0_exp[k])) + "_" + str(
                        int(SimpleFit_Ms_exp[k])) + "_" + str(int(SimpleFit_Hdem_exp[k])) + ".csv"),
                               np.array([SimpleFit_q_exp[k, :].T, SimpleFit_I_fit[k, :].T]).T, delimiter=" ")

                FolderName3 = "SANS_Intensity_Exp"
                path3 = os.path.join(path, FolderName3)
                os.mkdir(path3)

                for k in np.arange(0, np.size(SimpleFit_B_0_exp)):
                    np.savetxt(os.path.join(path3, str(k + 1) + "_" + str(int(SimpleFit_B_0_exp[k])) + "_" + str(
                        int(SimpleFit_Ms_exp[k])) + "_" + str(int(SimpleFit_Hdem_exp[k])) + ".csv"),
                               np.array([SimpleFit_q_exp[k, :].T, SimpleFit_I_exp[k, :].T, SimpleFit_sigma_exp[k, :]]).T,
                               delimiter=" ")

                FolderName4 = "Fit_Results"
                path4 = os.path.join(path, FolderName4)
                os.mkdir(path4)

                np.savetxt(os.path.join(path4, "chi.csv"), np.array([SimpleFit_A, SimpleFit_chi_q]).T, delimiter=" ")
                np.savetxt(os.path.join(path4, "S_H.csv"), np.array([SimpleFit_q_exp[0, :].T,
                                                                     SimpleFit_S_H_fit[0, :]]).T, delimiter=" ")
                np.savetxt(os.path.join(path4, "I_res.csv"), np.array([SimpleFit_q_exp[0, :].T,
                                                                       SimpleFit_I_res_fit[0, :]]).T, delimiter=" ")

        else:
            messagebox.showerror(title="Error!", message="No SimpleFit results available!")

    @staticmethod
    def plot_results(sweep_data: SweepOutput,
                     refined: LeastSquaresOutputPerpendicular | LeastSquaresOutputParallel,
                     A_Uncertainty,
                     figure, axes1, axes2, axes3, axes4):

        if A_Uncertainty < 1e-4:
            A_Uncertainty = 0

        A_uncertainty_str = str(A_Uncertainty)
        A_opt_str = str(refined.exchange_A * 1e12)

        q = refined.q * 1e-9

        # Plot A search data

        axes1.set_title('$A_{\mathrm{opt}} = (' + A_opt_str[0:5] + ' \pm ' + A_uncertainty_str[0:4] + ')$ pJ/m')
        axes1.plot(sweep_data.exchange_A_checked * 1e12, sweep_data.exchange_A_chi_sq)
        axes1.plot(sweep_data.optimal.exchange_A * 1e12, sweep_data.optimal.exchange_A_chi_sq, 'o')

        axes1.set_xlim([min(sweep_data.exchange_A_checked * 1e12), max(sweep_data.exchange_A_checked * 1e12)])
        axes1.set_xlabel('$A$ [pJ/m]')
        axes1.set_ylabel('$\chi^2$')

        # Residual intensity plot

        axes2.plot(q, refined.I_residual, label='fit')
        axes2.set_yscale('log')
        axes2.set_xscale('log')
        axes2.set_xlim([min(q), max(q)])
        axes2.set_xlabel('$q$ [1/nm]')
        axes2.set_ylabel('$I_{\mathrm{res}}$')

        # S_H parameter

        axes3.plot(q, refined.S_H, label='fit')
        axes3.set_yscale('log')
        axes3.set_xscale('log')
        axes3.set_xlim([min(q), max(q)])
        axes3.set_xlabel('$q$ [1/nm]')
        axes3.set_ylabel('$S_H$')

        # S_M parameter
        if isinstance(refined, LeastSquaresOutputPerpendicular):
            axes4.plot(q, refined.S_M, label='fit')
            axes4.set_yscale('log')
            axes4.set_xscale('log')
            axes4.set_xlim([min(q), max(q)])
            axes4.set_xlabel('$q$ [1/nm]')
            axes4.set_ylabel('$S_M$')

        figure.tight_layout()

    #################################################################################################################

    def SimpleFit_CompareButtonCallback(self, figure, axes):

        SimpleFit_q_exp = self.SimpleFit_q_exp
        SimpleFit_I_exp = self.SimpleFit_I_exp
        SimpleFit_sigma_exp = self.SimpleFit_sigma_exp
        SimpleFit_B_0_exp = self.SimpleFit_B_0_exp
        SimpleFit_Ms_exp = self.SimpleFit_Ms_exp
        SimpleFit_Hdem_exp = self.SimpleFit_Hdem_exp
        SimpleFit_I_fit = self.SimpleFit_I_fit
        SimpleFit_A = self.SimpleFit_A
        SimpleFit_chi_q = self.SimpleFit_chi_q
        SimpleFit_S_H_fit = self.SimpleFit_S_H_fit
        SimpleFit_S_M_fit = self.SimpleFit_S_M_fit
        SimpleFit_I_res_fit = self.SimpleFit_I_res_fit
        SimpleFit_A_opt = self.SimpleFit_A_opt
        SimpleFit_chi_q_opt = self.SimpleFit_chi_q_opt
        SimpleFit_A_sigma = self.SimpleFit_A_sigma
        SimpleFit_SANSgeometry = self.SimpleFit_SANSgeometry

        if np.size(SimpleFit_q_exp) > 1:
            q_exp_min = np.amin(SimpleFit_q_exp) * 1e-9
            q_exp_min = 10 ** (np.floor(np.log10(q_exp_min))) * np.floor(q_exp_min / 10 ** (np.floor(np.log10(q_exp_min))))

            q_exp_max = np.amax(SimpleFit_q_exp) * 1e-9
            q_exp_max = 10 ** (np.floor(np.log10(q_exp_max))) * np.ceil(q_exp_max / 10 ** (np.floor(np.log10(q_exp_max))))

            I_exp_min = np.amin(SimpleFit_I_exp)
            I_exp_min = 10 ** (np.floor(np.log10(I_exp_min))) * np.floor(I_exp_min / 10 ** (np.floor(np.log10(I_exp_min))))

            I_exp_max = np.amax(SimpleFit_I_exp)
            I_exp_max = 10 ** (np.floor(np.log10(I_exp_max))) * np.ceil(I_exp_max / 10 ** (np.floor(np.log10(I_exp_max))))

            self.PlotCompareExpFitData(figure, axes, SimpleFit_q_exp * 1e-9, SimpleFit_I_exp, SimpleFit_I_fit, SimpleFit_B_0_exp * 1e-3, q_exp_min, q_exp_max, I_exp_min, I_exp_max)
        else:
            messagebox.showerror(title="Error!", message="No SimpleFit results available!")

    def PlotCompareExpFitData(self, figure, axes, q, I_exp, I_fit, B_0, x_min, x_max, y_min, y_max):

        fig = figure
        fig.tight_layout()
        ax = axes

        colors = pl.cm.jet(np.linspace(0, 1, len(B_0)))
        for k in np.arange(0, len(B_0)):
            ax.loglog(q[k, :], I_exp[k, :], '.', color=colors[k], linewidth=0.3, markersize=1)

        colors = pl.cm.YlGn(np.linspace(0, 1, len(B_0)))
        for k in np.arange(0, len(B_0)):
            ax.plot(q[k, :], I_fit[k, :], linestyle='solid', color=colors[k],
                     linewidth=0.5, label='(fit) B_0 = ' + str(B_0[k]) + ' T')

        ax.set_xlabel(r'$q$ [1/nm]')
        ax.set_ylabel(r'$I_{\mathrm{exp}}$')
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        figure.tight_layout()
        figure.canvas.draw()

if __name__ == "__main__":

    app = QtWidgets.QApplication([])
    # app.exec_()

    MuMagLib.directory_popup()
