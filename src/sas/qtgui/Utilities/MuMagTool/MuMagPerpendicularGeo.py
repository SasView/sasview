import numpy as np
import scipy.optimize as scopt
import matplotlib.pyplot as plt



####################################################################################################
# Functions for the analysis of perpendicular SANS #################################################
####################################################################################################
# Lorentzian Model for the generation of clean synthetic test data for perpendicular SANS geometry
def LorentzianModelPERP(q, A, M_s, H_0, H_dem, a_H, a_M, l_c):

    # All inputs in SI-units
    # Micromagnetic Model
    mu_0 = 4 * np.pi * 1e-7
    H_i = H_0 - H_dem
    l_H = np.sqrt((2*A)/(mu_0 * M_s * H_i))
    H_eff = H_i * (1 + l_H**2 * q**2)
    p = M_s/H_eff
    R_H = p**2 / 4 * (2 + 1/np.sqrt(1 + p))
    R_M = (np.sqrt(1 + p) - 1)/2

    # Lorentzian functions for S_H, S_M
    S_H = a_H**2/(1 + q**2 * l_c**2)**2
    S_M = a_M**2/(1 + q**2 * l_c**2)**2

    # Magnetic SANS cross sections
    I_M = R_H * S_H + R_M * S_M

    # Model of I_res
    idx = np.argmax(H_0[:, 1])
    print(H_0[idx, 1]*mu_0*1e3)
    I_res = 0.9 * I_M[idx, :]

    # Total SANS cross section
    I_sim = I_res + I_M
    sigma = 0 * I_sim + 1

    return I_sim, sigma, S_H, S_M, I_res

####################################################################################################
# Lorentzian Model for the generation of noisy synthetic test data for perpendicular SANS geometry
def LorentzianNoisyModelPERP(q, A, M_s, H_0, H_dem, a_H, a_M, l_c, beta):

    # All inputs in SI-units

    # Micromagnetic Model
    mu_0 = 4 * np.pi * 1e-7
    H_i = H_0 - H_dem
    l_H = np.sqrt((2*A)/(mu_0 * M_s * H_i))
    H_eff = H_i * (1 + l_H**2 * q**2)
    p = M_s/H_eff
    R_H = p**2 / 4 * (2 + 1/np.sqrt(1 + p))
    R_M = (np.sqrt(1 + p) - 1)/2

    # Lorentzian functions for S_H, S_M
    S_H = a_H**2/(1 + q**2 * l_c**2)**2
    S_M = a_M**2/(1 + q**2 * l_c**2)**2

    # Magnetic SANS cross sections
    I_M = R_H * S_H + R_M * S_M

    # Model of I_res
    idx = np.argmax(H_0[:, 1])
    I_res = 0.9 * I_M[idx, :]

    # Model of standard deviation
    sigma = beta * (I_res + I_M)

    # Total SANS cross section
    I_sim = I_res + I_M + sigma * np.random.randn(len(sigma[:, 1]), len(sigma[1, :]))

    return I_sim, sigma, S_H, S_M, I_res

####################################################################################################
# Least squares method for perpendicular SANS geometry
def LSQ_PERP(q, I_exp, sigma, M_s, H_0, H_dem, A):

    # Micromagnetic Model
    mu_0 = 4 * np.pi * 1e-7
    H_i = H_0 - H_dem
    l_H = np.sqrt((2 * A) / (mu_0 * M_s * H_i))
    H_eff = H_i * (1 + (l_H ** 2) * (q ** 2))
    p = M_s / H_eff
    R_H = (p ** 2) / 4 * (2 + 1 / np.sqrt(1 + p))
    R_M = (np.sqrt(1 + p) - 1) / 2

    # Non-negative least squares loop
    L_nu = len(q[1, :])
    S_H = np.zeros((1, L_nu))
    S_M = np.zeros((1, L_nu))
    I_res = np.zeros((1, L_nu))
    sigma_S_H = np.zeros((1, L_nu))
    sigma_S_M = np.zeros((1, L_nu))
    sigma_I_res = np.zeros((1, L_nu))
    for nu in np.arange(0, L_nu):
        A = np.array([1/sigma[:, nu], R_H[:, nu]/sigma[:, nu], R_M[:, nu]/sigma[:, nu]]).T
        y = I_exp[:, nu]/sigma[:, nu]
        c = np.matmul(A.T, y)
        H = np.dot(A.T, A)

        # non-negative linear least squares
        x = scopt.nnls(H, c)
        I_res[0, nu] = x[0][0]
        S_H[0, nu] = x[0][1]
        S_M[0, nu] = x[0][2]

        Gamma = np.linalg.inv(np.dot(H.T, H))
        sigma_I_res[0, nu] = Gamma[0, 0]
        sigma_S_H[0, nu] = Gamma[1, 1]
        sigma_S_M[0, nu] = Gamma[2, 2]

    I_sim = I_res + R_H * S_H + R_M * S_M
    s_q = np.mean(((I_exp - I_sim)/sigma)**2, axis=0)

    sigma_S_H = np.sqrt(np.abs(sigma_S_H * s_q))
    sigma_S_M = np.sqrt(np.abs(sigma_S_M * s_q))
    sigma_I_res = np.sqrt(np.abs(sigma_I_res * s_q))

    chi_q = np.mean(s_q)

    return chi_q, I_res, S_H, S_M, sigma_I_res, sigma_S_H, sigma_S_M

####################################################################################################
# Least squares method for perpendicular SANS geometry
def chi_q_PERP(q, I_exp, sigma, M_s, H_0, H_dem, A):

    # Micromagnetic Model
    A = abs(A)
    mu_0 = 4 * np.pi * 1e-7
    H_i = H_0 - H_dem
    l_H = np.sqrt((2 * A) / (mu_0 * M_s * H_i))
    H_eff = H_i * (1 + (l_H ** 2) * (q ** 2))
    p = M_s / H_eff
    R_H = (p ** 2) / 4 * (2 + 1 / np.sqrt(1 + p))
    R_M = (np.sqrt(1 + p) - 1) / 2

    # Non-negative least squares loop
    L_nu = len(q[0, :])
    S_H = np.zeros((1, L_nu))
    S_M = np.zeros((1, L_nu))
    I_res = np.zeros((1, L_nu))
    for nu in np.arange(0, L_nu):
        A = np.array([1/sigma[:, nu], R_H[:, nu]/sigma[:, nu], R_M[:, nu]/sigma[:, nu]]).T
        y = I_exp[:, nu]/sigma[:, nu]

        c = np.matmul(A.T, y)
        H = np.dot(A.T, A)

        # non-negative linear least squares
        x = scopt.nnls(H, c)
        I_res[0, nu] = x[0][0]
        S_H[0, nu] = x[0][1]
        S_M[0, nu] = x[0][2]

    I_sim = I_res + R_H * S_H + R_M * S_M
    s_q = np.mean(((I_exp - I_sim)/sigma)**2, axis=0)
    chi_q = np.mean(s_q)

    return chi_q

####################################################################################################
# Sweep over Exchange Stiffness A for perpendicular SANS geometry
def SweepA_PERP(q, I_exp, sigma, M_s, H_0, H_dem, A_1, A_2, A_N):

    A = np.linspace(A_1, A_2, A_N)
    chi_q = np.zeros(len(A))
    for k in np.arange(0, len(A)):
        chi_q[k], I_res, S_H, S_M, sigma_I_res, sigma_S_H, sigma_S_M = LSQ_PERP(q, I_exp, sigma, M_s, H_0, H_dem, A[k])

    min_idx = np.argmin(chi_q)
    A_opt = A[min_idx]

    chi_q_opt, I_res_opt, S_H_opt, S_M_opt, sigma_I_res, sigma_S_H, sigma_S_M = LSQ_PERP(q, I_exp, sigma, M_s, H_0, H_dem, A_opt)

    return A, chi_q, A_opt, chi_q_opt, I_res_opt, S_H_opt, S_M_opt, sigma_I_res, sigma_S_H, sigma_S_M

####################################################################################################
# find optimal Exchange Stiffness A for perpendicular SANS geometry using fsolve function (slow and very accurate)
def OptimA_fsolve_PERP(q, I_exp, sigma, M_s, H_0, H_dem, A_initial):

    def func(A):
        return chi_q_PERP(q, I_exp, sigma, M_s, H_0, H_dem, A)

    return scopt.fsolve(func, A_initial)

####################################################################################################
# find optimal Exchange Stiffness A for perpendicular SANS geometry using
# successive parabolic interpolation (fast and accurate)
# implemented as Jarratt's Method
def OptimA_SPI_PERP(q, I_exp, sigma, M_s, H_0, H_dem, A_1, eps):

    delta = A_1 * 0.1

    x_1 = A_1 - delta
    x_2 = A_1
    x_3 = A_1 + delta

    y_1 = chi_q_PERP(q, I_exp, sigma, M_s, H_0, H_dem, x_1)
    y_2 = chi_q_PERP(q, I_exp, sigma, M_s, H_0, H_dem, x_2)
    y_3 = chi_q_PERP(q, I_exp, sigma, M_s, H_0, H_dem, x_3)

    x_4 = x_3 + 0.5 * ((x_2 - x_3)**2 * (y_3 - y_1) + (x_1 - x_3)**2 * (y_2 - y_3))/((x_2 - x_3) * (y_3 - y_1) + (x_1 - x_3) * (y_2 - y_3))
    while np.abs(2 * (x_4 - x_3)/(x_4 + x_3)) > eps:

        x_1 = x_2
        x_2 = x_3
        x_3 = x_4

        y_1 = y_2
        y_2 = y_3
        y_3 = chi_q_PERP(q, I_exp, sigma, M_s, H_0, H_dem, x_3)

        x_4 = x_3 + 0.5 * ((x_2 - x_3) ** 2 * (y_3 - y_1) + (x_1 - x_3) ** 2 * (y_2 - y_3)) / ((x_2 - x_3) * (y_3 - y_1) + (x_1 - x_3) * (y_2 - y_3))

    return x_4

####################################################################################################
# 1D-Cross-Section of the perendicular model
def SANS_Model_PERP(q, S_H, S_M, I_res, M_s, H_0, H_dem, A):

    # Micromagnetic Model
    mu_0 = 4 * np.pi * 1e-7
    H_i = H_0 - H_dem
    l_H = np.sqrt((2 * A) / (mu_0 * M_s * H_i))
    H_eff = H_i * (1 + (l_H ** 2) * (q ** 2))
    p = M_s / H_eff
    R_H = (p ** 2) / 4 * (2 + 1 / np.sqrt(1 + p))
    R_M = (np.sqrt(1 + p) - 1) / 2

    return I_res + R_H * S_H + R_M * S_M

####################################################################################################
# Plot Fitting results of simple fit
def PlotFittingResultsPERP_SimpleFit(q, A, chi_q, A_opt, chi_q_opt, I_res_opt, S_H_opt, S_M_opt, A_Uncertainty,
                                     figure, axes1, axes2, axes3, axes4):

    if A_Uncertainty < 1e-4:
        A_Uncertainty = 0

    A_uncertainty_str = str(A_Uncertainty)
    A_opt_str = str(A_opt * 1e12)
    axes1.set_title('$A_{\mathrm{opt}} = (' + A_opt_str[0:5] + ' \pm ' + A_uncertainty_str[0:4] + ')$ pJ/m', usetex=True)
    axes1.plot(A * 1e12, chi_q)
    axes1.plot(A_opt * 1e12, chi_q_opt, 'o')
    axes1.set_xlim([min(A * 1e12), max(A * 1e12)])
    axes1.set_xlabel('$A$ [pJ/m]', usetex=True)
    axes1.set_ylabel('$\chi^2$', usetex=True)

    axes2.plot(q[0, :] * 1e-9, I_res_opt[0, :], label='fit')
    axes2.set_yscale('log')
    axes2.set_xscale('log')
    axes2.set_xlim([min(q[0, :] * 1e-9), max(q[0, :] * 1e-9)])
    axes2.set_xlabel('$q$ [1/nm]', usetex=True)
    axes2.set_ylabel('$I_{\mathrm{res}}$', usetex=True)

    axes3.plot(q[0, :] * 1e-9, S_H_opt[0, :], label='fit')
    axes3.set_yscale('log')
    axes3.set_xscale('log')
    axes3.set_xlim([min(q[0, :] * 1e-9), max(q[0, :] * 1e-9)])
    axes3.set_xlabel('$q$ [1/nm]', usetex=True)
    axes3.set_ylabel('$S_H$', usetex=True)

    axes4.plot(q[0, :] * 1e-9, S_M_opt[0, :], label='fit')
    axes4.set_yscale('log')
    axes4.set_xscale('log')
    axes4.set_xlim([min(q[0, :] * 1e-9), max(q[0, :] * 1e-9)])
    axes4.set_xlabel('$q$ [1/nm]', usetex=True)
    axes4.set_ylabel('$S_M$', usetex=True)

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
# Second Order Derivative of chi-square function via Finite Differences
def FDM2Ord_PERP(q, I_exp, sigma, M_s, H_0, H_dem, A_opt):

    p = 0.001
    dA = A_opt * p
    A1 = A_opt - 2*dA
    A2 = A_opt - 1*dA
    A3 = A_opt
    A4 = A_opt + 1*dA
    A5 = A_opt + 2*dA

    chi1 = chi_q_PERP(q, I_exp, sigma, M_s, H_0, H_dem, A1)
    chi2 = chi_q_PERP(q, I_exp, sigma, M_s, H_0, H_dem, A2)
    chi3 = chi_q_PERP(q, I_exp, sigma, M_s, H_0, H_dem, A3)
    chi4 = chi_q_PERP(q, I_exp, sigma, M_s, H_0, H_dem, A4)
    chi5 = chi_q_PERP(q, I_exp, sigma, M_s, H_0, H_dem, A5)

    d2_chi_dA2 = (-chi1 + 16 * chi2 - 30 * chi3 + 16 * chi4 - chi5)/(12 * dA**2)

    return d2_chi_dA2