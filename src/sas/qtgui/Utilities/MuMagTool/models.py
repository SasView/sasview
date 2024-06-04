
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
