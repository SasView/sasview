import numpy as np
import scipy.optimize as scopt
import matplotlib.pyplot as plt

from sas.qtgui.Utilities.MuMagTool.experimental_data import ExperimentalData
from sas.qtgui.Utilities.MuMagTool.fit_parameters import ExperimentGeometry
from sas.qtgui.Utilities.MuMagTool.least_squares_output import LeastSquaresOutputParallel, \
    LeastSquaresOutputPerpendicular
from sas.qtgui.Utilities.MuMagTool.sweep_output import SweepOutput

mu_0 = 4 * np.pi * 1e-7

def LSQ_PAR(data: list[ExperimentalData], A):

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
    response_H = (p ** 2) / 2

    # print("Input", q.shape, q[0,10])
    # sys.exit()

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
            fit_result = scopt.nnls(
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


####################################################################################################


####################################################################################################
# Plot Fitting results of simple fit

####################################################################################################
def PlotSweepFitResultPAR(q_max_mat, H_min_mat, A_opt_mat):
    fig = plt.figure()
    ax = plt.axes(projection='3d')
    ax.plot_surface(q_max_mat * 1e-9, H_min_mat, A_opt_mat * 1e12)
    ax.set(xlabel='q_max [1/nm]', ylabel='H_min [mT]', zlabel='A_opt [pJ/m]')
    ax.grid()

    plt.tight_layout()
    plt.show()

####################################################################################################
# Second Order Derivative of chi-square function via Finite Differences
def FDM2Ord_PAR(q, I_exp, sigma, M_s, H_0, H_dem, A_opt):

    p = 0.01
    dA = A_opt * p
    A1 = A_opt - 2*dA
    A2 = A_opt - 1*dA
    A3 = A_opt
    A4 = A_opt + 1*dA
    A5 = A_opt + 2*dA

    chi1 = chi_q_PAR(q, I_exp, sigma, M_s, H_0, H_dem, A1)
    chi2 = chi_q_PAR(q, I_exp, sigma, M_s, H_0, H_dem, A2)
    chi3 = chi_q_PAR(q, I_exp, sigma, M_s, H_0, H_dem, A3)
    chi4 = chi_q_PAR(q, I_exp, sigma, M_s, H_0, H_dem, A4)
    chi5 = chi_q_PAR(q, I_exp, sigma, M_s, H_0, H_dem, A5)

    d2_chi_dA2 = (-chi1 + 16 * chi2 - 30 * chi3 + 16 * chi4 - chi5)/(12 * dA**2)

    return d2_chi_dA2