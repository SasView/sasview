import logging
import os
import os.path
from datetime import datetime

import numpy as np
import scipy.optimize
from PySide6.QtWidgets import QFileDialog

from sasdata.dataloader.loader import Loader

from sas.qtgui.Utilities.MuMag.datastructures import (
    ExperimentalData,
    ExperimentGeometry,
    FitFailure,
    FitParameters,
    FitResults,
    LeastSquaresOutputParallel,
    LeastSquaresOutputPerpendicular,
    LoadFailure,
    SweepOutput,
)


class MuMagLib:
    """ Library for methods supporting MuMag"""

    logger = logging.getLogger("MuMag")

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
                # Check for error, and skip if necessary
                if isinstance(data1d, Exception):
                    MuMagLib.logger.error(f"Failed to load in data: {data1d}")
                    continue

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
            parameters=parameters,
            input_data=filtered_inputs,
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
                raise FitFailure(f"A = {A} ({repr(ve)})")

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
                raise FitFailure(f"A = {A} ({repr(ve)})")

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

    @staticmethod
    def _filename_string(datum: ExperimentalData):
        """ Get the filename string associated with a bit of experimental data """

        return f"{datum.applied_field}_{datum.saturation_magnetisation}_{datum.demagnetising_field}"

    @staticmethod
    def save_data(data: FitResults, directory: str):
        """ Save the data """

        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y_%H-%M-%S")
        output_folder = f"mumag_fit_{timestamp}"
        path = os.path.join(directory, output_folder)

        if not os.path.exists(path):
            os.mkdir(path)

        with open(os.path.join(path, "fit_info.txt"), "w") as fid:
            fid.write("FitMagneticSANS Toolbox - SimpleFit Results Info File \n\n")
            fid.write(f"Timestamp: {timestamp}\n")
            fid.write(f"SANS geometry: {data.parameters.experiment_geometry.name}\n\n")
            fid.write(f"Maximal Scattering Vector:  q_max = {np.max(data.refined_fit_data.q)} /nm\n")
            fid.write(f"Minimal Applied Field: mu_0*H_min = {data.input_data[0].applied_field}\n mT \n")
            fid.write(f"Result for the exchange stiffness constant: "
                      f"A = {data.refined_fit_data.exchange_A} +- {data.optimal_exchange_A_uncertainty} pJ/m \n")

        #
        # Save fitted data
        #

        subpath = os.path.join(path, "intensity_fit")

        if not os.path.exists(subpath):
            os.mkdir(subpath)

        for k, datum in enumerate(data.input_data):

            filename = f"{k}_" + MuMagLib._filename_string(datum) + ".csv"

            q = data.refined_fit_data.q
            I = data.refined_fit_data.I_simulated[k, :]

            np.savetxt(os.path.join(subpath, filename), np.array([q, I]).T, delimiter=",")

        #
        # Save original data (but truncated)
        #

        subpath = os.path.join(path, "input_intensity")

        if not os.path.exists(subpath):
            os.mkdir(subpath)

        for k, datum in enumerate(data.input_data):
            filename = f"{k}_" + MuMagLib._filename_string(datum) + ".csv"

            q = datum.scattering_curve.x
            I = datum.scattering_curve.y
            dI = datum.scattering_curve.dy

            np.savetxt(os.path.join(subpath, filename), np.array([q, I, dI]).T, delimiter=",")

        #
        # Optimised results
        #

        np.savetxt(os.path.join(path, "chi.csv"),
                   np.array([
                       data.sweep_data.exchange_A_checked,
                       data.sweep_data.exchange_A_chi_sq]).T,
                   delimiter=",")

        np.savetxt(os.path.join(path, "S_H.csv"),
                   np.array([
                       data.refined_fit_data.q,
                       data.refined_fit_data.S_H,
                       data.refined_fit_data.S_H_stdev]).T,
                   delimiter=",")

        np.savetxt(os.path.join(path, "I_res.csv"),
                   np.array([
                       data.refined_fit_data.q,
                       data.refined_fit_data.I_residual,
                       data.refined_fit_data.I_residual_stdev]).T,
                   delimiter=",")

        if data.parameters.experiment_geometry == ExperimentGeometry.PERPENDICULAR:
            np.savetxt(os.path.join(path, "S_M.csv"),
                       np.array([
                           data.refined_fit_data.q,
                           data.refined_fit_data.S_M,
                           data.refined_fit_data.S_M_stdev]).T,
                       delimiter=",")





