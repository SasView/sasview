import numpy as np
import scipy.optimize as scopt
import matplotlib.pyplot as plt


####################################################################################################
# Functions for the analysis of parallel SANS ######################################################
####################################################################################################
# Lorentzian Model for the generation of clean synthetic test data for perpendicular SANS geometry
def LorentzianModelPAR(q, A, M_s, H_0, H_dem, a_H, l_c):

    # All inputs in SI-units
    # Micromagnetic Model
    mu_0 = 4 * np.pi * 1e-7
    H_i = H_0 - H_dem
    l_H = np.sqrt((2 * A) / (mu_0 * M_s * H_i))
    H_eff = H_i * (1 + (l_H ** 2) * (q ** 2))
    p = M_s / H_eff
    R_H = (p ** 2) / 2

    # Lorentzian functions for S_H, S_M
    S_H = a_H**2/(1 + q**2 * l_c**2)**2

    # Magnetic SANS cross sections
    I_M = R_H * S_H

    # Model of I_res
    idx = np.argmax(H_0[:, 1])
    I_res = 0.9 * I_M[idx, :]

    # Total SANS cross section
    I_sim = I_res + I_M
    sigma = 0 * I_sim + 1

    return I_sim, sigma, S_H, I_res

####################################################################################################
# Least squares method for parallel SANS geometry
def LSQ_PAR(q, I_exp, sigma, M_s, H_0, H_dem, A):

    # Micromagnetic Model
    mu_0 = 4 * np.pi * 1e-7
    H_i = H_0 - H_dem
    l_H = np.sqrt((2 * A) / (mu_0 * M_s * H_i))
    H_eff = H_i * (1 + (l_H ** 2) * (q ** 2))
    p = M_s / H_eff
    R_H = (p ** 2) / 2

    # Non-negative least squares loop
    L_nu = len(q[1, :])
    S_H = np.zeros((1, L_nu))
    I_res = np.zeros((1, L_nu))
    sigma_S_H = np.zeros((1, L_nu))
    sigma_I_res = np.zeros((1, L_nu))
    for nu in np.arange(0, L_nu):
        A = np.array([1/sigma[:, nu], R_H[:, nu]/sigma[:, nu]]).T
        y = I_exp[:, nu]/sigma[:, nu]
        c = np.matmul(A.T, y)
        H = np.dot(A.T, A)

        # non-negative linear least squares
        x = scopt.nnls(H, c)
        I_res[0, nu] = x[0][0]
        S_H[0, nu] = x[0][1]

        Gamma = np.linalg.inv(np.dot(H.T, H))
        sigma_I_res[0, nu] = Gamma[0, 0]
        sigma_S_H[0, nu] = Gamma[1, 1]

    I_sim = I_res + R_H * S_H
    s_q = np.mean(((I_exp - I_sim)/sigma)**2, axis=0)

    sigma_S_H = np.sqrt(np.abs(sigma_S_H * s_q))
    sigma_I_res = np.sqrt(np.abs(sigma_I_res * s_q))

    chi_q = np.mean(s_q)

    return chi_q, I_res, S_H, sigma_I_res, sigma_S_H

####################################################################################################
# Least squares method for parallel SANS geometry
def chi_q_PAR(q, I_exp, sigma, M_s, H_0, H_dem, A):

    # Micromagnetic Model
    mu_0 = 4 * np.pi * 1e-7
    H_i = H_0 - H_dem
    l_H = np.sqrt((2 * A) / (mu_0 * M_s * H_i))
    H_eff = H_i * (1 + (l_H ** 2) * (q ** 2))
    p = M_s / H_eff
    R_H = (p ** 2) / 2

    # Non-negative least squares loop
    L_nu = len(q[0, :])
    S_H = np.zeros((1, L_nu))
    I_res = np.zeros((1, L_nu))
    for nu in np.arange(0, L_nu):
        A = np.array([1/sigma[:, nu], R_H[:, nu]/sigma[:, nu]]).T
        y = I_exp[:, nu]/sigma[:, nu]

        c = np.matmul(A.T, y)
        H = np.dot(A.T, A)

        # non-negative linear least squares
        x = scopt.nnls(H, c)
        I_res[0, nu] = x[0][0]
        S_H[0, nu] = x[0][1]

    I_sim = I_res + R_H * S_H
    s_q = np.mean(((I_exp - I_sim)/sigma)**2, axis=0)
    chi_q = np.mean(s_q)

    return chi_q

####################################################################################################
# Sweep over Exchange Stiffness A for parallel SANS geometry
def SweepA_PAR(q, I_exp, sigma, M_s, H_0, H_dem, A_1, A_2, A_N):

    A = np.linspace(A_1, A_2, A_N)
    chi_q = np.zeros(len(A))
    for k in np.arange(0, len(A)):
        chi_q[k], I_res, S_H, sigma_I_res, sigma_S_H = LSQ_PAR(q, I_exp, sigma, M_s, H_0, H_dem, A[k])

    min_idx = np.argmin(chi_q)
    A_opt = A[min_idx]

    chi_q_opt, I_res_opt, S_H_opt, sigma_I_res, sigma_S_H = LSQ_PAR(q, I_exp, sigma, M_s, H_0, H_dem, A_opt)

    return A, chi_q, A_opt, chi_q_opt, I_res_opt, S_H_opt,  sigma_I_res, sigma_S_H

####################################################################################################
# find optimal Exchange Stiffness A for parallel SANS geometry using fsolve function (slow and very accurate)
def OptimA_fsolve_PAR(q, I_exp, sigma, M_s, H_0, H_dem, A_initial):

    def func(A):
        return chi_q_PAR(q, I_exp, sigma, M_s, H_0, H_dem, A)

    return scopt.fsolve(func, A_initial)

####################################################################################################
# find optimal Exchange Stiffness A for parallel SANS geometry using successive parabolic interpolation (fast and accurate)
# implemented as Jarratt's Method
def OptimA_SPI_PAR(q, I_exp, sigma, M_s, H_0, H_dem, A_1, eps):

    delta = A_1 * 0.1

    x_1 = A_1 - delta
    x_2 = A_1
    x_3 = A_1 + delta

    y_1 = chi_q_PAR(q, I_exp, sigma, M_s, H_0, H_dem, x_1)
    y_2 = chi_q_PAR(q, I_exp, sigma, M_s, H_0, H_dem, x_2)
    y_3 = chi_q_PAR(q, I_exp, sigma, M_s, H_0, H_dem, x_3)

    x_4 = x_3 + 0.5 * ((x_2 - x_3)**2 * (y_3 - y_1) + (x_1 - x_3)**2 * (y_2 - y_3))/((x_2 - x_3) * (y_3 - y_1) + (x_1 - x_3) * (y_2 - y_3))
    while np.abs(2 * (x_4 - x_3)/(x_4 + x_3)) > eps:

        x_1 = x_2
        x_2 = x_3
        x_3 = x_4

        y_1 = y_2
        y_2 = y_3
        y_3 = chi_q_PAR(q, I_exp, sigma, M_s, H_0, H_dem, x_3)

        x_4 = x_3 + 0.5 * ((x_2 - x_3) ** 2 * (y_3 - y_1) + (x_1 - x_3) ** 2 * (y_2 - y_3)) / ((x_2 - x_3) * (y_3 - y_1) + (x_1 - x_3) * (y_2 - y_3))

    return x_4

####################################################################################################
# 1D-Cross-Section of the parallel model
def SANS_Model_PAR(q, S_H, I_res, M_s, H_0, H_dem, A):

    # Micromagnetic Model
    mu_0 = 4 * np.pi * 1e-7
    H_i = H_0 - H_dem
    l_H = np.sqrt((2 * A) / (mu_0 * M_s * H_i))
    H_eff = H_i * (1 + (l_H ** 2) * (q ** 2))
    p = M_s / H_eff
    R_H = (p ** 2) / 2

    return I_res + R_H * S_H

####################################################################################################
# Plot Fitting results of simple fit
def PlotFittingResultsPAR_SimpleFit(q, A, chi_q, A_opt, chi_q_opt, I_res_opt, S_H_opt, A_Uncertainty):

    fig, axs = plt.subplots(2, 2)
    A_uncertainty_str = str(A_Uncertainty)
    A_opt_str = str(A_opt * 1e12)
    axs[0, 0].set_title('A_opt = (' + A_opt_str[0:5] + ' +/- ' + A_uncertainty_str[0:4] + ') pJ/m')
    axs[0, 0].plot(A * 1e12, chi_q)
    axs[0, 0].plot(A_opt * 1e12, chi_q_opt, 'o')
    axs[0, 0].grid()
    axs[0, 0].set_xlim([min(A * 1e12), max(A * 1e12)])
    axs[0, 0].set(xlabel='A [pJ/m]', ylabel='chi^2')

    axs[0, 1].plot(q[0, :] * 1e-9, I_res_opt[0, :], label='fit')
    axs[0, 1].set_yscale('log')
    axs[0, 1].set_xscale('log')
    axs[0, 1].grid()
    axs[0, 1].set_xlim([min(q[0, :] * 1e-9), max(q[0, :] * 1e-9)])
    axs[0, 1].set(xlabel='q [1/nm]', ylabel='I_res')
    axs[0, 1].legend()

    axs[1, 0].plot(q[0, :] * 1e-9, S_H_opt[0, :], label='fit')
    axs[1, 0].set_yscale('log')
    axs[1, 0].set_xscale('log')
    axs[1, 0].grid()
    axs[1, 0].set_xlim([min(q[0, :] * 1e-9), max(q[0, :] * 1e-9)])
    axs[1, 0].set(xlabel='q [1/nm]', ylabel='S_H')
    axs[1, 0].legend()

    plt.tight_layout()
    plt.show()

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