import logging
import os
import os.path
from datetime import datetime

import numpy as np
import scipy.optimize
from PySide6.QtWidgets import QFileDialog

from sasdata.dataloader.loader import Loader
from sasdata.quantities import units
from sasdata.quantities.quantity import Quantity
from sasdata.quantities.unit_parser import parse_unit
from sasdata.trend import Trend

from sas.qtgui.Utilities.MuMag.datastructures import (
    ExperimentGeometry,
    FitFailure,
    FitParameters,
    FitResults,
    LeastSquaresOutputParallel,
    LeastSquaresOutputPerpendicular,
    SweepOutput,
)


class MuMagLib:
    """Library for methods supporting MuMag"""

    logger = logging.getLogger("MuMag")

    mu_0 = Quantity(4 * np.pi * 1e-7, parse_unit("H/m"))

    @staticmethod
    def directory_popup():
        directory = QFileDialog.getExistingDirectory()

        if directory.strip() == "":
            return None
        else:
            return directory


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
    def simple_fit(trend: Trend, parameters: FitParameters):
        """ Main fitting ("simple fit") """

        geometry = parameters.experiment_geometry

        # Use an index for data upto qmax based on first data set
        # Not ideal, would be preferable make sure the data was
        # compatible, using something like interpolation TODO
        q_quantity = trend.data[0].abscissae.axes[0]
        square_distance_from_qmax = (q_quantity - parameters.q_max) ** 2
        max_q_index = int(np.argmin(square_distance_from_qmax.value))

        applied_fields = [
            Quantity(float(value), parse_unit("mT"))
            for value in trend.get_trend_values("applied_magnetic_field")
        ]
        min_applied_field = parameters.min_applied_field
        filtered_indices = [
            i for i, field in enumerate(applied_fields)
            if (field - min_applied_field).value >= 0
        ]
        filtered_data = [trend.data[i] for i in filtered_indices]
        filtered_trend_axes = {
            name: [trend.get_trend_values(name)[i] for i in filtered_indices]
            if trend.is_manual_axis(name) else trend.trend_axes[name]
            for name in trend.axis_names
        }
        filtered_trend = Trend(filtered_data, filtered_trend_axes)

        # Brute force check for something near the minimum
        sweep_data = MuMagLib.sweep_exchange_A(parameters, filtered_trend, max_q_index)

        # Refine this result
        crude_A = sweep_data.optimal.exchange_A
        refined = MuMagLib.refine_exchange_A(filtered_trend, crude_A, geometry, max_q_index)

        # Get uncertainty estimate
        uncertainty = MuMagLib.uncertainty(filtered_trend, refined.exchange_A, geometry, max_q_index).to_units_of(parse_unit("pJ/m"))

        return FitResults(
            parameters=parameters,
            input_trend=filtered_trend,
            sweep_data=sweep_data,
            refined_fit_data=refined,
            optimal_exchange_A_uncertainty=uncertainty)

    @staticmethod
    def sweep_exchange_A(parameters: FitParameters, trend: Trend, max_q_index: int) -> SweepOutput:
        """ Sweep over Exchange Stiffness A for perpendicular SANS geometry to
        get an initial estimate which can then be refined"""

        # The model works in J/m, so convert the pJ/m bounds to J/m
        a_min_q = parameters.exchange_A_min.to_units_of(parse_unit("J/m"))
        a_max_q = parameters.exchange_A_max.to_units_of(parse_unit("J/m"))

        a_values = Quantity(np.linspace(a_min_q.value, a_max_q.value, parameters.exchange_A_n),
                            parse_unit("J/m"))

        if parameters.experiment_geometry == ExperimentGeometry.PERPENDICULAR:
            least_squared_fits = [MuMagLib.least_squares_perpendicular(trend, Quantity(a, parse_unit("J/m")), max_q_index) for a in a_values.value]

        elif parameters.experiment_geometry == ExperimentGeometry.PARALLEL:
            least_squared_fits = [MuMagLib.least_squares_parallel(trend, Quantity(a, parse_unit("J/m")), max_q_index) for a in a_values.value]

        else:
            raise ValueError(f"Unknown ExperimentGeometry value: {parameters.experiment_geometry}")

        optimal_fit = min(least_squared_fits, key=lambda x: x.exchange_A_chi_sq)

        chi_sq = np.array([fit.exchange_A_chi_sq for fit in least_squared_fits])

        return SweepOutput(
            exchange_A_checked=a_values,
            exchange_A_chi_sq=chi_sq,
            optimal=optimal_fit)

    @staticmethod
    def least_squares_perpendicular(trend: Trend, A, max_q_index: int) -> LeastSquaresOutputPerpendicular:
        """ Least squares fitting for a given exchange stiffness, A, perpendicular case

            We are fitting the equation:

              I_sim = I_res + response_H * S_H + response_M * S_M
                    = (I_res, S_H, S_M) . (1, response_H, response_M)
                    = (I_res, S_H, S_M) . least_squares_x

            finding I_res, S_H, and S_M for each q value


        """

        # Get matrices from the input data
        n_data = len(trend.data)

        def convert_trend_values(trend: Trend, axis_name: str) -> Quantity:
            values = np.array([float(v) for v in trend.get_trend_values(axis_name)])
            return Quantity(values, parse_unit("mT"))

        applied_field = convert_trend_values(trend, "applied_magnetic_field") / MuMagLib.mu_0
        demagnetising_field = convert_trend_values(trend, "demagnetizing_field") / MuMagLib.mu_0
        saturation_magnetisation = convert_trend_values(trend, "saturation_magnetization") / MuMagLib.mu_0

        q = Quantity(
            np.array([datum.abscissae.axes[0].in_units_of(parse_unit("1/m"))[:max_q_index]
                      for datum in trend.data]),
            parse_unit("1/m"))

        I_units = trend.data[0].ordinate.units
        I = Quantity(
            np.array([datum.ordinate.value[:max_q_index] for datum in trend.data]),
            I_units)

        try:
            I_stdev = Quantity(
                np.array([datum.ordinate.standard_error.value[:max_q_index] for datum in trend.data]),
                trend.data[0].ordinate.standard_error.units)
        except KeyError:
            I_stdev = Quantity(np.ones_like(I.value), I.units)

        n_q = q.value.shape[1]

        # Micromagnetic Model
        internal_field = Quantity(
            (applied_field - demagnetising_field).value.reshape(-1, 1),
            applied_field.units)
        magnetic_scattering_length = (
            (2 * A) / (MuMagLib.mu_0 * Quantity(saturation_magnetisation.value.reshape(-1, 1), saturation_magnetisation.units) * internal_field)) ** 0.5
        effective_field = internal_field * (Quantity(1, units.none) + (magnetic_scattering_length ** 2) * (q ** 2))

        # Calculate the response functions
        p = Quantity(saturation_magnetisation.value.reshape(-1, 1), saturation_magnetisation.units) / effective_field
        response_H = (p ** 2) / 4 * (Quantity(2, units.none) + Quantity(1, units.none) / (Quantity(1, units.none) + p) ** 0.5)
        response_M = ((Quantity(1, units.none) + p) ** 0.5 - Quantity(1, units.none)) / 2

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
            least_squares_x_val = (np.array([np.ones((n_data,)), response_H.value[:, nu], response_M.value[:, nu]]) / I_stdev.value[:, nu]).T
            least_squares_y_val = I.value[:, nu] / I_stdev.value[:, nu]

            least_squares_x_squared = np.dot(least_squares_x_val.T, least_squares_x_val)

            # Non-negative least squares
            try:
                fit_result = scipy.optimize.nnls(
                    least_squares_x_squared,
                    np.matmul(least_squares_x_val.T, least_squares_y_val))

            except ValueError as ve:
                raise FitFailure(f"A = {A} ({repr(ve)})")

            I_residual.append(Quantity(fit_result[0][0], I.units))
            S_H.append(Quantity(fit_result[0][1], I.units))
            S_M.append(Quantity(fit_result[0][2], I.units))

            errors = np.linalg.inv(np.dot(least_squares_x_squared.T, least_squares_x_squared))

            I_residual_error_weight.append(errors[0, 0])
            S_H_error_weight.append(errors[1, 1])
            S_M_error_weight.append(errors[2, 2])

        # Arrayise
        S_H = Quantity(np.array([s.value for s in S_H]), I.units)
        S_M = Quantity(np.array([s.value for s in S_M]), I.units)
        I_residual = Quantity(np.array([s.value for s in I_residual]), I.units)

        I_sim = I_residual + response_H * S_H + response_M * S_M

        # TODO: This is probably broken. Removing the axis to fix it for now but
        # its going to have to change.
        s_q = np.mean(((I - I_sim) / I_stdev) ** 2)

        sigma_I_res = (Quantity(np.abs(np.array(I_residual_error_weight)), units.none) * s_q) ** 0.5
        sigma_S_H = (Quantity(np.abs(np.array(S_H_error_weight)), units.none) * s_q) ** 0.5
        sigma_S_M = (Quantity(np.abs(np.array(S_M_error_weight)), units.none) * s_q) ** 0.5

        chi_sq = float(np.mean(s_q.value))

        output_q_values = Quantity(np.mean(q.value, axis=0), q.units)

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
    def least_squares_parallel(trend: Trend, A, max_q_index: int):

        """ Least squares fitting for a given exchange stiffness, A, parallel case

                We are fitting the equation:

                  I_sim = I_res + response_H * S_H
                        = (I_res, S_H) . (1, response_H)
                        = (I_res, S_H) . least_squares_x

                finding I_res and S_H for each q value


            """

        # Get matrices from the input data
        n_data = len(trend.data)

        def convert_trend_values(trend: Trend, axis_name: str) -> Quantity:
            values = np.array([float(v) for v in trend.get_trend_values(axis_name)])
            return Quantity(values, parse_unit("mT"))

        applied_field = convert_trend_values(trend, "applied_magnetic_field") / MuMagLib.mu_0
        demagnetising_field = convert_trend_values(trend, "demagnetizing_field") / MuMagLib.mu_0
        saturation_magnetisation = convert_trend_values(trend, "saturation_magnetization") / MuMagLib.mu_0

        q = Quantity(
            np.array([datum.abscissae.axes[0].in_units_of(parse_unit("1/m"))[:max_q_index]
                      for datum in trend.data]),
            parse_unit("1/m"))

        I_units = trend.data[0].ordinate.units
        I = Quantity(
            np.array([datum.ordinate.value[:max_q_index] for datum in trend.data]),
            I_units)

        try:
            I_stdev = Quantity(
                np.array([datum["dI"].axes[0].value[:max_q_index] for datum in trend.data]),
                trend.data[0]["dI"].axes[0].units)
        except KeyError:
            I_stdev = Quantity(np.ones_like(I.value), I.units)

        n_q = q.value.shape[1]

        # Micromagnetic Model
        internal_field = Quantity(
            (applied_field - demagnetising_field).value.reshape(-1, 1),
            applied_field.units)
        magnetic_scattering_length = (
            (2 * A) / (MuMagLib.mu_0 * Quantity(saturation_magnetisation.value.reshape(-1, 1), saturation_magnetisation.units) * internal_field)) ** 0.5
        effective_field = internal_field * (Quantity(1, units.none) + (magnetic_scattering_length ** 2) * (q ** 2))

        # Calculate the response functions
        p = Quantity(saturation_magnetisation.value.reshape(-1, 1), saturation_magnetisation.units) / effective_field
        response_H = (p ** 2) / 2

        # Lists for output of calculation
        I_residual = []
        S_H = []

        I_residual_error_weight = []
        S_H_error_weight = []

        for nu in range(n_q):

            # non-negative linear least squares
            least_squares_x_val = (np.array([np.ones((n_data,)), response_H.value[:, nu]]) / I_stdev.value[:, nu]).T
            least_squares_y_val = I.value[:, nu] / I_stdev.value[:, nu]

            least_squares_x_squared = np.dot(least_squares_x_val.T, least_squares_x_val)

            # Non-negative least squares
            try:
                fit_result = scipy.optimize.nnls(
                    least_squares_x_squared,
                    np.matmul(least_squares_x_val.T, least_squares_y_val))

            except ValueError as ve:
                raise FitFailure(f"A = {A} ({repr(ve)})")

            I_residual.append(Quantity(fit_result[0][0], I.units))
            S_H.append(Quantity(fit_result[0][1], I.units))

            errors = np.linalg.inv(np.dot(least_squares_x_squared.T, least_squares_x_squared))

            I_residual_error_weight.append(errors[0, 0])
            S_H_error_weight.append(errors[1, 1])

        # Arrayise
        S_H = Quantity(np.array([s.value for s in S_H]), I.units)
        I_residual = Quantity(np.array([s.value for s in I_residual]), I.units)

        I_sim = I_residual + response_H * S_H

        s_q = np.mean(((I - I_sim) / I_stdev) ** 2, axis=0)

        sigma_I_res = (Quantity(np.abs(np.array(I_residual_error_weight)), units.none) * s_q) ** 0.5
        sigma_S_H = (Quantity(np.abs(np.array(S_H_error_weight)), units.none) * s_q) ** 0.5

        chi_sq = float(np.mean(s_q.value))

        output_q_values = Quantity(np.mean(q.value, axis=0), q.units)

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
            trend: Trend,
            exchange_A_initial: Quantity,
            geometry: ExperimentGeometry,
            max_q_index: int,
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
        refined_least_squared_data = least_squares_function(trend, x_3, max_q_index)

        y_1 = least_squares_function(trend, x_1, max_q_index).exchange_A_chi_sq
        y_2 = least_squares_function(trend, x_2, max_q_index).exchange_A_chi_sq
        y_3 = refined_least_squared_data.exchange_A_chi_sq

        x_4 = x_3 + 0.5 * ((x_2 - x_3) ** 2 * (y_3 - y_1) + (x_1 - x_3) ** 2 * (y_2 - y_3)) \
              / ((x_2 - x_3) * (y_3 - y_1) + (x_1 - x_3) * (y_2 - y_3))

        for i in range(200):
            convergence = np.abs((2 * (x_4 - x_3) / (x_4 + x_3)).value)
            if convergence < epsilon:
                break

            refined_least_squared_data = least_squares_function(trend, x_3, max_q_index)

            x_1, x_2, x_3 = x_2, x_3, x_4
            y_1, y_2, y_3 = y_2, y_3, refined_least_squared_data.exchange_A_chi_sq

            x_4 = x_3 + 0.5 * ((x_2 - x_3) ** 2 * (y_3 - y_1) + (x_1 - x_3) ** 2 * (y_2 - y_3)) \
                  / ((x_2 - x_3) * (y_3 - y_1) + (x_1 - x_3) * (y_2 - y_3))

        return refined_least_squared_data

    @staticmethod
    def uncertainty(
            trend: Trend,
            A_opt: Quantity,
            geometry: ExperimentGeometry,
            max_q_index: int) -> Quantity:
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

        chi1 = least_squares_function(trend, A1, max_q_index).exchange_A_chi_sq
        chi2 = least_squares_function(trend, A2, max_q_index).exchange_A_chi_sq
        chi3 = least_squares_function(trend, A3, max_q_index).exchange_A_chi_sq
        chi4 = least_squares_function(trend, A4, max_q_index).exchange_A_chi_sq
        chi5 = least_squares_function(trend, A5, max_q_index).exchange_A_chi_sq

        d2chi_dA2 = (-chi1 + 16 * chi2 - 30 * chi3 + 16 * chi4 - chi5) / (12 * dA ** 2)

        # Scale variance by number of samples and return reciprocal square root

        n_field_strengths = len(trend.data)  # Number of fields
        n_q = max_q_index  # Number of q points

        return (2 / (n_field_strengths * n_q * d2chi_dA2)) ** 0.5

    @staticmethod
    def _filename_string(trend: Trend, index: int):
        """ Get the filename string associated with a bit of experimental data """

        millitesla = parse_unit("mT")
        applied_field = Quantity(float(trend.get_trend_values("applied_magnetic_field")[index]), millitesla)
        saturation_magnetisation = Quantity(float(trend.get_trend_values("saturation_magnetization")[index]), millitesla)
        demagnetising_field = Quantity(float(trend.get_trend_values("demagnetizing_field")[index]), millitesla)

        return (
            f"{applied_field.in_units_of(millitesla)}"
            f"_{saturation_magnetisation.in_units_of(millitesla)}"
            f"_{demagnetising_field.in_units_of(millitesla)}"
        )

    @staticmethod
    def save_data(data: FitResults, directory: str):
        """ Save the data """

        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y_%H-%M-%S")
        output_folder = f"mumag_fit_{timestamp}"
        path = os.path.join(directory, output_folder)

        if not os.path.exists(path):
            os.mkdir(path)

        applied_fields = [
            Quantity(float(value), parse_unit("mT"))
            for value in data.input_trend.get_trend_values("applied_magnetic_field")
        ]

        with open(os.path.join(path, "fit_info.txt"), "w") as fid:
            fid.write("FitMagneticSANS Toolbox - SimpleFit Results Info File \n\n")
            fid.write(f"Timestamp: {timestamp}\n")
            fid.write(f"SANS geometry: {data.parameters.experiment_geometry.name}\n\n")
            fid.write(f"Maximal Scattering Vector:  q_max = {np.max(data.refined_fit_data.q)} /nm\n")
            fid.write(f"Minimal Applied Field: mu_0*H_min = {applied_fields[0].explicitly_formatted('mT')}\n")
            fid.write(f"Result for the exchange stiffness constant: "
                      f"A = {data.refined_fit_data.exchange_A} +- {data.optimal_exchange_A_uncertainty} pJ/m \n")

        #
        # Save fitted data
        #

        subpath = os.path.join(path, "intensity_fit")

        if not os.path.exists(subpath):
            os.mkdir(subpath)

        for k in range(len(data.input_trend.data)):

            filename = f"{k}_" + MuMagLib._filename_string(data.input_trend, k) + ".csv"

            q = data.refined_fit_data.q
            I = data.refined_fit_data.I_simulated[k, :]

            np.savetxt(os.path.join(subpath, filename), np.array([q, I]).T, delimiter=",")

        #
        # Save original data (but truncated)
        #

        subpath = os.path.join(path, "input_intensity")

        if not os.path.exists(subpath):
            os.mkdir(subpath)

        for k in range(len(data.input_trend.data)):
            filename = f"{k}_" + MuMagLib._filename_string(data.input_trend, k) + ".csv"

            q = data.input_trend.data[k].abscissae.axes[0]
            I = data.input_trend.data[k].ordinate
            # Try to get errors, use unit errors if not available
            if data.input_trend.data[k].abscissae.axes[0].has_error:
                dI = data.input_trend.data[k].abscissae.axes[0].standard_error
            else:
                dI = np.ones_like(I)

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





