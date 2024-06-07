import sys

import numpy as np
import scipy.optimize as scopt
import matplotlib.pyplot as plt

from sasdata.dataloader import Data1D
from data_util.nxsunit import Converter
from sas.qtgui.Utilities.MuMagTool.experimental_data import ExperimentalData
from sas.qtgui.Utilities.MuMagTool.fit_parameters import FitParameters
from sas.qtgui.Utilities.MuMagTool.fit_result import FitResults
from sas.qtgui.Utilities.MuMagTool.least_squares_output import LeastSquaresOutput, LeastSquaresOutputPerpendicular
from sas.qtgui.Utilities.MuMagTool.sweep_output import SweepOutput

mu_0 = 4 * np.pi * 1e-7

def LSQ_PERP(data: list[ExperimentalData], A) -> LeastSquaresOutput:
    """ Least squares fitting for a given exchange stiffness, A

        We are fitting the equation:

          I_sim = I_res + response_H * S_H + response_M * S_M
                = (I_res, S_H, S_M) . (1, response_H, response_M)
                = (I_res, S_H, S_M) . least_squares_x

        finding I_res, S_H, and S_M for each q value


    """



    # Get matrices from the input data
    n_data = len(data)

    #  Factor of (1e-3 / mu_0) converts from mT to A/m
    applied_field = np.array([datum.applied_field for datum in data]) * (1e-3 / mu_0)
    demagnetising_field = np.array([datum.demagnetising_field for datum in data]) * (1e-3 / mu_0)
    saturation_magnetisation = np.array([datum.saturation_magnetisation for datum in data]) * (1e-3 / mu_0)

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
    magnetic_scattering_length = np.sqrt((2 * A) / (mu_0 * saturation_magnetisation.reshape(-1, 1) * internal_field))
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
        least_squares_y = I[:, nu]/I_stdev[:, nu]

        least_squares_x_squared = np.dot(least_squares_x.T, least_squares_x)

        # Non-negative least squares
        try:
            fit_result = scopt.nnls(
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

    s_q = np.mean(((I - I_sim)/I_stdev)**2, axis=0)

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


####################################################################################################
# Sweep over Exchange Stiffness A for perpendicular SANS geometry
def SweepA_PERP(parameters: FitParameters, data: list[ExperimentalData]) -> SweepOutput:

    a_values = np.linspace(
                        parameters.exchange_A_min,
                        parameters.exchange_A_max,
                        parameters.exchange_A_n) * 1e-12 # From pJ/m to J/m

    least_squared_fits = [LSQ_PERP(data, a) for a in a_values]

    optimal_fit = min(least_squared_fits, key=lambda x: x.exchange_A_chi_sq)

    chi_sq = np.array([fit.exchange_A_chi_sq for fit in least_squared_fits])

    return SweepOutput(
        exchange_A_checked=a_values,
        exchange_A_chi_sq=chi_sq,
        optimal=optimal_fit)


####################################################################################################
# find optimal Exchange Stiffness A for perpendicular SANS geometry using
# successive parabolic interpolation (fast and accurate)
# implemented as Jarratt's Method
def OptimA_SPI_PERP(data: list[ExperimentalData], A_1, epsilon):

    delta = A_1 * 0.1

    x_1 = A_1 - delta
    x_2 = A_1
    x_3 = A_1 + delta

    y_1 = LSQ_PERP(data, x_1).exchange_A_chi_sq
    y_2 = LSQ_PERP(data, x_2).exchange_A_chi_sq
    y_3 = LSQ_PERP(data, x_3).exchange_A_chi_sq

    x_4 = x_3 + 0.5 * ((x_2 - x_3)**2 * (y_3 - y_1) + (x_1 - x_3)**2 * (y_2 - y_3))/((x_2 - x_3) * (y_3 - y_1) + (x_1 - x_3) * (y_2 - y_3))
    while np.abs(2 * (x_4 - x_3)/(x_4 + x_3)) > epsilon:

        # print("x1,x2,x3,x4:", x_1, x_2, x_3, x_4)

        x_1 = x_2
        x_2 = x_3
        x_3 = x_4

        y_1 = y_2
        y_2 = y_3
        y_3 = LSQ_PERP(data, x_3).exchange_A_chi_sq

        x_4 = x_3 + 0.5 * ((x_2 - x_3) ** 2 * (y_3 - y_1) + (x_1 - x_3) ** 2 * (y_2 - y_3)) / ((x_2 - x_3) * (y_3 - y_1) + (x_1 - x_3) * (y_2 - y_3))

    return x_4


####################################################################################################
# Plot Fitting results of simple fit
def PlotFittingResultsPERP_SimpleFit(z: SweepOutput, A_Uncertainty,
                                     figure, axes1, axes2, axes3, axes4):

    if A_Uncertainty < 1e-4:
        A_Uncertainty = 0

    A_uncertainty_str = str(A_Uncertainty)
    A_opt_str = str(z.optimal.exchange_A * 1e12)

    q = z.optimal.q * 1e-9

    # Plot A search data

    axes1.set_title('$A_{\mathrm{opt}} = (' + A_opt_str[0:5] + ' \pm ' + A_uncertainty_str[0:4] + ')$ pJ/m')
    axes1.plot(z.exchange_A_checked * 1e12, z.exchange_A_chi_sq)
    axes1.plot(z.optimal.exchange_A * 1e12, z.optimal.exchange_A_chi_sq, 'o')

    axes1.set_xlim([min(z.exchange_A_checked * 1e12), max(z.exchange_A_checked * 1e12)])
    axes1.set_xlabel('$A$ [pJ/m]')
    axes1.set_ylabel('$\chi^2$')

    # Residual intensity plot

    axes2.plot(q, z.optimal.I_residual, label='fit')
    axes2.set_yscale('log')
    axes2.set_xscale('log')
    axes2.set_xlim([min(q), max(q)])
    axes2.set_xlabel('$q$ [1/nm]')
    axes2.set_ylabel('$I_{\mathrm{res}}$')

    axes3.plot(q, z.optimal.S_H, label='fit')
    axes3.set_yscale('log')
    axes3.set_xscale('log')
    axes3.set_xlim([min(q), max(q)])
    axes3.set_xlabel('$q$ [1/nm]')
    axes3.set_ylabel('$S_H$')

    axes4.plot(q, z.optimal.S_M, label='fit')
    axes4.set_yscale('log')
    axes4.set_xscale('log')
    axes4.set_xlim([min(q), max(q)])
    axes4.set_xlabel('$q$ [1/nm]')
    axes4.set_ylabel('$S_M$')

    figure.tight_layout()


####################################################################################################
def PlotSweepFitResultPERP(q_max_mat, H_min_mat, A_opt_mat):
    fig = plt.figure()
    ax = plt.axes(projection='3d')
    ax.plot_surface(q_max_mat * 1e-9, H_min_mat, A_opt_mat * 1e12)
    ax.set(xlabel='q_max [1/nm]', ylabel='H_min [mT]', zlabel='A_opt [pJ/m]')
    ax.grid()

    plt.tight_layout()
    plt.show()

####################################################################################################
#
def uncertainty_perp(data: list[ExperimentalData], A_opt: float):
    """Calculate the uncertainty for the optimal exchange stiffness A"""

    # Estimate variance from second order derivative of chi-square function via Finite Differences

    p = 0.001 # fractional gap size for finite differences
    dA = A_opt * p
    A1 = A_opt - 2*dA
    A2 = A_opt - 1*dA
    A3 = A_opt
    A4 = A_opt + 1*dA
    A5 = A_opt + 2*dA

    chi1 = LSQ_PERP(data, A1).exchange_A_chi_sq
    chi2 = LSQ_PERP(data, A2).exchange_A_chi_sq
    chi3 = LSQ_PERP(data, A3).exchange_A_chi_sq
    chi4 = LSQ_PERP(data, A4).exchange_A_chi_sq
    chi5 = LSQ_PERP(data, A5).exchange_A_chi_sq

    d2chi_dA2 = (-chi1 + 16 * chi2 - 30 * chi3 + 16 * chi4 - chi5)/(12 * dA**2)

    # Scale variance by number of samples and return reciprocal square root

    n_field_strengths = len(data)  # Number of fields
    n_q = len(data[0].scattering_curve.x)  # Number of q points

    return np.sqrt(2 / (n_field_strengths * n_q * d2chi_dA2))
