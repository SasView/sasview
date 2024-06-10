import numpy as np
import matplotlib.pylab as pl
import os
import os.path
from datetime import datetime

import scipy.optimize

from PySide6 import QtWidgets
from PySide6.QtWidgets import QFileDialog

from sas.qtgui.Utilities.MuMagTool.experimental_data import ExperimentalData
from sas.qtgui.Utilities.MuMagTool.failure import LoadFailure
from sas.qtgui.Utilities.MuMagTool.fit_parameters import FitParameters, ExperimentGeometry
from sas.qtgui.Utilities.MuMagTool.fit_result import FitResults
from sas.qtgui.Utilities.MuMagTool.least_squares_output import LeastSquaresOutputPerpendicular, \
    LeastSquaresOutputParallel
from sas.qtgui.Utilities.MuMagTool.sweep_output import SweepOutput

from sasdata.dataloader.loader import Loader


class MuMagLib:
    """ Library for methods supporting MuMag"""

    mu_0 = 4 * np.pi * 1e-7

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


    @staticmethod
    def simple_fit(data: list[ExperimentalData], parameters: FitParameters):
        """ Main fitting ("simple fit") """

        geometry = parameters.experiment_geometry

        # Use an index for data upto qmax based on first data set
        # Not ideal, would be preferable make sure the data was
        # compatible, using something like interpolation TODO
        square_distance_from_qmax = (data[0].scattering_curve.x - parameters.q_max) ** 2
        max_q_index = int(np.argmin(square_distance_from_qmax))

        filtered_inputs = [datum.restrict_by_index(max_q_index)
                           for datum in data
                           if datum.applied_field >= parameters.min_applied_field]

        # Brute force check for something near the minimum
        sweep_data = MuMagLib.sweep_exchange_A(parameters, filtered_inputs)

        # Refine this result
        crude_A = sweep_data.optimal.exchange_A
        refined = MuMagLib.refine_exchange_A(filtered_inputs, crude_A, geometry)

        # Get uncertainty estimate TODO: Check units
        uncertainty = MuMagLib.uncertainty(filtered_inputs, refined.exchange_A, geometry) * 1e12

        return FitResults(
            input_data=data,
            sweep_data=sweep_data,
            refined_fit_data=refined,
            optimal_exchange_A_uncertainty=uncertainty)

    @staticmethod
    def sweep_exchange_A(parameters: FitParameters, data: list[ExperimentalData]) -> SweepOutput:
        """ Sweep over Exchange Stiffness A for perpendicular SANS geometry to
        get an initial estimate which can then be refined"""

        a_values = np.linspace(
            parameters.exchange_A_min,
            parameters.exchange_A_max,
            parameters.exchange_A_n) * 1e-12  # From pJ/m to J/m

        if parameters.experiment_geometry == ExperimentGeometry.PERPENDICULAR:
            least_squared_fits = [MuMagLib.least_squares_perpendicular(data, a) for a in a_values]

        elif parameters.experiment_geometry == ExperimentGeometry.PARALLEL:
            least_squared_fits = [MuMagLib.least_squares_parallel(data, a) for a in a_values]

        else:
            raise ValueError(f"Unknown ExperimentGeometry value: {parameters.experiment_geometry}")

        optimal_fit = min(least_squared_fits, key=lambda x: x.exchange_A_chi_sq)

        chi_sq = np.array([fit.exchange_A_chi_sq for fit in least_squared_fits])

        return SweepOutput(
            exchange_A_checked=a_values,
            exchange_A_chi_sq=chi_sq,
            optimal=optimal_fit)

    @staticmethod
    def least_squares_perpendicular(data: list[ExperimentalData], A) -> LeastSquaresOutputPerpendicular:
        """ Least squares fitting for a given exchange stiffness, A, perpendicular case

            We are fitting the equation:

              I_sim = I_res + response_H * S_H + response_M * S_M
                    = (I_res, S_H, S_M) . (1, response_H, response_M)
                    = (I_res, S_H, S_M) . least_squares_x

            finding I_res, S_H, and S_M for each q value


        """

        # Get matrices from the input data
        n_data = len(data)

        #  Factor of (1e-3 / mu_0) converts from mT to A/m
        applied_field = np.array([datum.applied_field for datum in data]) * (1e-3 / MuMagLib.mu_0)
        demagnetising_field = np.array([datum.demagnetising_field for datum in data]) * (1e-3 / MuMagLib.mu_0)
        saturation_magnetisation = np.array([datum.saturation_magnetisation for datum in data]) * (1e-3 / MuMagLib.mu_0)

        # TODO: The following is how things should be done in the future, rather than hard-coding
        #  a scaling factor...
        # def data_nanometers(data: Data1D):
        #     raw_data = data.x
        #     units = data.x_unit
        #     converter = Converter(units)
        #     return converter.scale("1/m", raw_data)
        #
        # q = np.array([data_nanometers(datum.scattering_curve) for datum in data])

        q = np.array([datum.scattering_curve.x for datum in data]) * 1e9
        I = np.array([datum.scattering_curve.y for datum in data])
        I_stdev = np.array([datum.scattering_curve.dy for datum in data])

        n_q = q.shape[1]

        # Micromagnetic Model
        internal_field = (applied_field - demagnetising_field).reshape(-1, 1)
        magnetic_scattering_length = np.sqrt(
            (2 * A) / (MuMagLib.mu_0 * saturation_magnetisation.reshape(-1, 1) * internal_field))
        effective_field = internal_field * (1 + (magnetic_scattering_length ** 2) * (q ** 2))

        # Calculate the response functions
        p = saturation_magnetisation.reshape(-1, 1) / effective_field
        response_H = (p ** 2) / 4 * (2 + 1 / np.sqrt(1 + p))
        response_M = (np.sqrt(1 + p) - 1) / 2

        # print("Input", q.shape, q[0,10])
        # sys.exit()

        # Lists for output of calculation
        I_residual = []
        S_H = []
        S_M = []

        I_residual_error_weight = []
        S_M_error_weight = []
        S_H_error_weight = []

        for nu in range(n_q):

            # non-negative linear least squares
            least_squares_x = (np.array([np.ones((n_data,)), response_H[:, nu], response_M[:, nu]]) / I_stdev[:, nu]).T
            least_squares_y = I[:, nu] / I_stdev[:, nu]

            least_squares_x_squared = np.dot(least_squares_x.T, least_squares_x)

            # Non-negative least squares
            try:
                fit_result = scipy.optimize.nnls(
                    least_squares_x_squared,
                    np.matmul(least_squares_x.T, least_squares_y))

            except ValueError as ve:
                print("Value Error:")
                print(" A =", A)

                raise ve

            I_residual.append(fit_result[0][0])
            S_H.append(fit_result[0][1])
            S_M.append(fit_result[0][2])

            errors = np.linalg.inv(np.dot(least_squares_x_squared.T, least_squares_x_squared))

            I_residual_error_weight.append(errors[0, 0])
            S_H_error_weight.append(errors[1, 1])
            S_M_error_weight.append(errors[2, 2])

        # Arrayise
        S_H = np.array(S_H)
        S_M = np.array(S_M)
        I_residual = np.array(I_residual)

        I_sim = I_residual + response_H * S_H + response_M * S_M

        s_q = np.mean(((I - I_sim) / I_stdev) ** 2, axis=0)

        sigma_I_res = np.sqrt(np.abs(np.array(I_residual_error_weight) * s_q))
        sigma_S_H = np.sqrt(np.abs(np.array(S_H_error_weight) * s_q))
        sigma_S_M = np.sqrt(np.abs(np.array(S_M_error_weight) * s_q))

        chi_sq = float(np.mean(s_q))

        output_q_values = np.mean(q, axis=0)

        return LeastSquaresOutputPerpendicular(
            exchange_A=A,
            exchange_A_chi_sq=chi_sq,
            q=output_q_values,
            I_residual=I_residual,
            I_simulated=I_sim,
            S_H=S_H,
            S_M=S_M,
            I_residual_stdev=sigma_I_res,
            S_H_stdev=sigma_S_H,
            S_M_stdev=sigma_S_M)


    @staticmethod
    def least_squares_parallel(data: list[ExperimentalData], A):

        """ Least squares fitting for a given exchange stiffness, A, parallel case

                We are fitting the equation:

                  I_sim = I_res + response_H * S_H
                        = (I_res, S_H) . (1, response_H)
                        = (I_res, S_H) . least_squares_x

                finding I_res and S_H for each q value


            """

        # Get matrices from the input data
        n_data = len(data)

        #  Factor of (1e-3 / mu_0) converts from mT to A/m
        applied_field = np.array([datum.applied_field for datum in data]) * (1e-3 / MuMagLib.mu_0)
        demagnetising_field = np.array([datum.demagnetising_field for datum in data]) * (1e-3 / MuMagLib.mu_0)
        saturation_magnetisation = np.array([datum.saturation_magnetisation for datum in data]) * (1e-3 / MuMagLib.mu_0)

        # TODO: The following is how things should be done in the future, rather than hard-coding
        #  a scaling factor...
        # def data_nanometers(data: Data1D):
        #     raw_data = data.x
        #     units = data.x_unit
        #     converter = Converter(units)
        #     return converter.scale("1/m", raw_data)
        #
        # q = np.array([data_nanometers(datum.scattering_curve) for datum in data])

        q = np.array([datum.scattering_curve.x for datum in data]) * 1e9
        I = np.array([datum.scattering_curve.y for datum in data])
        I_stdev = np.array([datum.scattering_curve.dy for datum in data])

        n_q = q.shape[1]

        # Micromagnetic Model
        internal_field = (applied_field - demagnetising_field).reshape(-1, 1)
        magnetic_scattering_length = np.sqrt(
            (2 * A) / (MuMagLib.mu_0 * saturation_magnetisation.reshape(-1, 1) * internal_field))
        effective_field = internal_field * (1 + (magnetic_scattering_length ** 2) * (q ** 2))

        # Calculate the response functions
        p = saturation_magnetisation.reshape(-1, 1) / effective_field
        response_H = (p ** 2) / 2

        # Lists for output of calculation
        I_residual = []
        S_H = []

        I_residual_error_weight = []
        S_H_error_weight = []

        for nu in range(n_q):

            # non-negative linear least squares
            least_squares_x = (np.array([np.ones((n_data,)), response_H[:, nu]]) / I_stdev[:, nu]).T
            least_squares_y = I[:, nu] / I_stdev[:, nu]

            least_squares_x_squared = np.dot(least_squares_x.T, least_squares_x)

            # Non-negative least squares
            try:
                fit_result = scipy.optimize.nnls(
                    least_squares_x_squared,
                    np.matmul(least_squares_x.T, least_squares_y))

            except ValueError as ve:
                print("Value Error:")
                print(" A =", A)

                raise ve

            I_residual.append(fit_result[0][0])
            S_H.append(fit_result[0][1])

            errors = np.linalg.inv(np.dot(least_squares_x_squared.T, least_squares_x_squared))

            I_residual_error_weight.append(errors[0, 0])
            S_H_error_weight.append(errors[1, 1])

        # Arrayise
        S_H = np.array(S_H)
        I_residual = np.array(I_residual)

        I_sim = I_residual + response_H * S_H

        s_q = np.mean(((I - I_sim) / I_stdev) ** 2, axis=0)

        sigma_I_res = np.sqrt(np.abs(np.array(I_residual_error_weight) * s_q))
        sigma_S_H = np.sqrt(np.abs(np.array(S_H_error_weight) * s_q))

        chi_sq = float(np.mean(s_q))

        output_q_values = np.mean(q, axis=0)

        return LeastSquaresOutputParallel(
            exchange_A=A,
            exchange_A_chi_sq=chi_sq,
            q=output_q_values,
            I_residual=I_residual,
            I_simulated=I_sim,
            S_H=S_H,
            I_residual_stdev=sigma_I_res,
            S_H_stdev=sigma_S_H)

    @staticmethod
    def refine_exchange_A(
            data: list[ExperimentalData],
            exchange_A_initial: float,
            geometry: ExperimentGeometry,
            epsilon: float = 0.0001) -> LeastSquaresOutputPerpendicular | LeastSquaresOutputParallel:

        """ Refines the A parameter using Jarratt's method of successive parabolic interpolation"""

        match geometry:
            case ExperimentGeometry.PARALLEL:
                least_squares_function = MuMagLib.least_squares_parallel
            case ExperimentGeometry.PERPENDICULAR:
                least_squares_function = MuMagLib.least_squares_perpendicular
            case _:
                raise ValueError(f"Unknown experimental geometry: {geometry}")

        delta = exchange_A_initial * 0.1

        x_1 = exchange_A_initial - delta
        x_2 = exchange_A_initial
        x_3 = exchange_A_initial + delta

        # We want all the least squares fitting data around the final value, so keep that in a variable
        refined_least_squared_data = least_squares_function(data, x_3)

        y_1 = least_squares_function(data, x_1).exchange_A_chi_sq
        y_2 = least_squares_function(data, x_2).exchange_A_chi_sq
        y_3 = refined_least_squared_data.exchange_A_chi_sq

        x_4 = x_3 + 0.5 * ((x_2 - x_3) ** 2 * (y_3 - y_1) + (x_1 - x_3) ** 2 * (y_2 - y_3)) \
              / ((x_2 - x_3) * (y_3 - y_1) + (x_1 - x_3) * (y_2 - y_3))

        for i in range(200):
            if np.abs(2 * (x_4 - x_3) / (x_4 + x_3)) < epsilon:
                break

            refined_least_squared_data = least_squares_function(data, x_3)

            x_1, x_2, x_3 = x_2, x_3, x_4
            y_1, y_2, y_3 = y_2, y_3, refined_least_squared_data.exchange_A_chi_sq

            x_4 = x_3 + 0.5 * ((x_2 - x_3) ** 2 * (y_3 - y_1) + (x_1 - x_3) ** 2 * (y_2 - y_3)) \
                  / ((x_2 - x_3) * (y_3 - y_1) + (x_1 - x_3) * (y_2 - y_3))

        return refined_least_squared_data

    @staticmethod
    def uncertainty(
            data: list[ExperimentalData],
            A_opt: float,
            geometry: ExperimentGeometry) -> float:
        """Calculate the uncertainty for the optimal exchange stiffness A"""

        # Estimate variance from second order derivative of chi-square function via Finite Differences

        match geometry:
            case ExperimentGeometry.PARALLEL:
                least_squares_function = MuMagLib.least_squares_parallel
            case ExperimentGeometry.PERPENDICULAR:
                least_squares_function = MuMagLib.least_squares_perpendicular
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
