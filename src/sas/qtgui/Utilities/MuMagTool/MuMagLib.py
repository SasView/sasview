import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.pylab as pl
import scipy.optimize as scopt
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import os
import os.path
from datetime import datetime
from PySide6.QtWidgets import QFileDialog
import string

from sas.qtgui.Utilities.MuMagTool import MuMagParallelGeo
from sas.qtgui.Utilities.MuMagTool import MuMagPerpendicularGeo

class MuMagLib():
    def __init__(self):

        # attributes for the input data
        self.q_exp = 0
        self.I_exp = 0
        self.sigma_exp = 0
        self.B_0_exp = 0
        self.Ms_exp = 0
        self.Hdem_exp = 0
        self.DataCounter = 0

        # attributes for the simple fit result
        self.SimpleFit_q_exp = 0
        self.SimpleFit_I_exp = 0
        self.SimpleFit_sigma_exp = 0
        self.SimpleFit_B_0_exp = 0
        self.SimpleFit_Ms_exp = 0
        self.SimpleFit_Hdem_exp = 0
        self.SimpleFit_I_fit = 0
        self.SimpleFit_A = 0
        self.SimpleFit_chi_q = 0
        self.SimpleFit_S_H_fit = 0
        self.SimpleFit_S_M_fit = 0
        self.SimpleFit_I_res_fit = 0
        self.SimpleFit_A_opt = 0
        self.SimpleFit_chi_q_opt = 0
        self.SimpleFit_A_sigma = 0
        self.SimpleFit_SANSgeometry = 0

    #####################################################################################################################
    def get_directory(self):
        fname = QFileDialog.getOpenFileName()
        if fname:
            fname = fname[0]
            index = [i for i, val in enumerate(fname) if val == "/"]
            fname = fname[0:index[-1]+1]
        return fname

    #####################################################################################################################
    # Import experimental data and get information from filenames
    def import_data_button_callback_sub(self):

        self.DataCounter = 0
        # Predefine array's
        DIR = self.get_directory()
        for name in os.listdir(DIR):
            if name.find(".csv") != -1:
                data = np.genfromtxt(DIR + '/' + name)
                Lq = len(data[:, 0])
                if self.DataCounter == 0:
                    self.q_exp = np.array([np.zeros(Lq)])
                    self.I_exp = np.array([np.zeros(Lq)])
                    self.sigma_exp = np.array([np.zeros(Lq)])
                    self.B_0_exp = np.array([np.zeros(1)])
                    self.Ms_exp = np.array([np.zeros(1)])
                    self.Hdem_exp = np.array([np.zeros(1)])
                    self.DataCounter = self.DataCounter + 1
                else:
                    self.q_exp = np.append(self.q_exp, [np.zeros(Lq)], axis=0)
                    self.I_exp = np.append(self.I_exp, [np.zeros(Lq)], axis=0)
                    self.sigma_exp = np.append(self.sigma_exp, [np.zeros(Lq)], axis=0)
                    self.B_0_exp = np.append(self.B_0_exp, [np.zeros(1)])
                    self.Ms_exp = np.append(self.Ms_exp, [np.zeros(1)])
                    self.Hdem_exp = np.append(self.Hdem_exp, [np.zeros(1)])
                    self.DataCounter = self.DataCounter + 1

        # Load the data and sort the data
        for name in os.listdir(DIR):
            if name.find(".csv") != -1:
                str_name = name[0:len(name)-4]
                str_name = str_name.split('_')
                idx = int(str_name[0])
                data = np.genfromtxt(DIR + '/' + name)
                self.B_0_exp[idx-1] = float(str_name[1])
                self.Ms_exp[idx-1] = float(str_name[2])
                self.Hdem_exp[idx-1] = float(str_name[3])
                self.q_exp[idx-1, :] = data[:, 0].T * 1e9
                self.I_exp[idx-1, :] = data[:, 1].T
                self.sigma_exp[idx-1, :] = data[:, 2].T

    #####################################################################################################################
    # Plot Experimental Data: Set Bounds and Call Plotting Function
    def plot_experimental_data(self, figure, axes):

        if np.size(self.q_exp) > 1:
            q_exp_min = np.amin(self.q_exp)*1e-9
            q_exp_min = 10**(np.floor(np.log10(q_exp_min))) * np.floor(q_exp_min/10**(np.floor(np.log10(q_exp_min))))

            q_exp_max = np.amax(self.q_exp)*1e-9
            q_exp_max = 10**(np.floor(np.log10(q_exp_max))) * np.ceil(q_exp_max/10**(np.floor(np.log10(q_exp_max))))

            I_exp_min = np.amin(self.I_exp)
            I_exp_min = 10**(np.floor(np.log10(I_exp_min))) * np.floor(I_exp_min/10**(np.floor(np.log10(I_exp_min))))

            I_exp_max = np.amax(self.I_exp)
            I_exp_max = 10 ** (np.floor(np.log10(I_exp_max))) * np.ceil(I_exp_max / 10 ** (np.floor(np.log10(I_exp_max))))

            self.plot_exp_data(figure, axes, self.q_exp*1e-9, self.I_exp, self.B_0_exp*1e-3, q_exp_min, q_exp_max, I_exp_min, I_exp_max)
        else:
            messagebox.showerror(title="Error!", message="No experimental data available! Please import experimental data!")




    ################################################################################################################
    # Plot Experimental Data: Generate Figure
    def plot_exp_data(self, figure, axes, q, I_exp, B_0, x_min, x_max, y_min, y_max):

        ax = axes
        colors = pl.cm.jet(np.linspace(0, 1, len(B_0)))
        for k in np.arange(0, len(B_0)):
            #print(k)
            ax.loglog(q[k, :], I_exp[k, :], linestyle='-', color=colors[k], linewidth=0.5, label=r'$B_0 = ' + str(B_0[k]) + '$ T')
            ax.loglog(q[k, :], I_exp[k, :], '.', color=colors[k], linewidth=0.3, markersize=1)

        ax.set_xlabel(r'$q$ [1/nm]', usetex=True)
        ax.set_ylabel(r'$I_{\mathrm{exp}}$', usetex=True)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        figure.tight_layout()
        figure.canvas.draw()

    #######################################################################################################################

    def simple_fit_button_callback(self, q_max, H_min, A1, A2, A_N, SANSgeometry, figure, axes1, axes2, axes3, axes4):

        if np.size(self.q_exp) > 1:

            # search index for q_max
            q_diff = (self.q_exp[0, :]*1e-9 - q_max)**2
            K_q = np.where(q_diff == np.min(q_diff))
            K_q = K_q[0][0]

            # search index for H_min
            H_diff = (self.B_0_exp - H_min)**2
            K_H = np.where(H_diff == np.min(H_diff))
            K_H = K_H[0][0]

            # apply the restrictions
            mu_0 = 4*math.pi*1e-7
            q = self.q_exp[K_H:, 0:K_q]
            I_exp_red = self.I_exp[K_H:, 0:K_q]
            sigma = self.sigma_exp[K_H:, 0:K_q]
            H_0 = np.outer(self.B_0_exp[K_H:]/mu_0 * 1e-3, np.ones(K_q))
            H_dem = np.outer(self.Hdem_exp[K_H:], np.ones(K_q))/mu_0 * 1e-3
            Ms = np.outer(self.Ms_exp[K_H:], np.ones(K_q))/mu_0 * 1e-3

            # Least Squares Fit in case of perpendicular SANS geometry
            if SANSgeometry == "perpendicular":
                A_1 = A1 * 1e-12
                A_2 = A2 * 1e-12
                A, chi_q, A_opt, chi_q_opt, I_res_opt, S_H_opt, S_M_opt, sigma_I_res, sigma_S_H, sigma_S_M \
                    = MuMagPerpendicularGeo.SweepA_PERP(q, I_exp_red, sigma, Ms, H_0, H_dem, A_1, A_2, A_N)

                A_opt = MuMagPerpendicularGeo.OptimA_SPI_PERP(q, I_exp_red, sigma, Ms, H_0, H_dem, A_1, 0.0001)
                chi_q_opt, I_res_opt, S_H_opt, S_M_opt, sigma_I_res, sigma_S_H, sigma_S_M = MuMagPerpendicularGeo.LSQ_PERP(q, I_exp_red, sigma, Ms, H_0, H_dem, A_opt)

                I_opt = MuMagPerpendicularGeo.SANS_Model_PERP(q, S_H_opt, S_M_opt, I_res_opt, Ms, H_0, H_dem, A_opt)

                d2chi_dA2 = MuMagPerpendicularGeo.FDM2Ord_PERP(q, I_exp_red, sigma, Ms, H_0, H_dem, A_opt)

                N_mu = len(I_exp_red[0, :])
                N_nu = len(I_exp_red[:, 0])
                A_Uncertainty = np.sqrt(2 / (N_mu * N_nu * d2chi_dA2))

                MuMagPerpendicularGeo.PlotFittingResultsPERP_SimpleFit(q, A, chi_q, A_opt, chi_q_opt, I_res_opt,
                                                                       S_H_opt, S_M_opt, A_Uncertainty * 1e12,
                                                                       figure, axes1, axes2, axes3, axes4)

                # Save to global Variables
                self.SimpleFit_q_exp = q
                self.SimpleFit_I_exp = I_exp_red
                self.SimpleFit_sigma_exp = sigma
                self.SimpleFit_B_0_exp = self.B_0_exp[K_H:]
                self.SimpleFit_Ms_exp = self.Ms_exp[K_H:]
                self.SimpleFit_Hdem_exp = self.Hdem_exp[K_H:]
                self.SimpleFit_I_fit = I_opt
                self.SimpleFit_A = A
                self.SimpleFit_chi_q = chi_q
                self.SimpleFit_S_H_fit = S_H_opt
                self.SimpleFit_S_M_fit = S_M_opt
                self.SimpleFit_I_res_fit = I_res_opt
                self.SimpleFit_A_opt = A_opt
                self.SimpleFit_chi_q_opt = chi_q_opt
                self.SimpleFit_A_sigma = A_Uncertainty
                self.SimpleFit_SANSgeometry = "perpendicular"

            elif SANSgeometry == "parallel":

                A_1 = A1 * 1e-12
                A_2 = A2 * 1e-12
                A, chi_q, A_opt, chi_q_opt, I_res_opt, S_H_opt, sigma_I_res, sigma_S_H \
                    = MuMagParallelGeo.SweepA_PAR(q, I_exp_red, sigma, Ms, H_0, H_dem, A_1, A_2, A_N)

                A_opt = MuMagParallelGeo.OptimA_SPI_PAR(q, I_exp_red, sigma, Ms, H_0, H_dem, A_1, 0.0001)
                chi_q_opt, I_res_opt, S_H_opt, sigma_I_res, sigma_S_H = MuMagParallelGeo.LSQ_PAR(q, I_exp_red, sigma,
                                                                                           Ms, H_0,
                                                                                           H_dem,
                                                                                           A_opt)

                I_opt = MuMagParallelGeo.SANS_Model_PAR(q, S_H_opt, I_res_opt, Ms, H_0, H_dem, A_opt)

                d2chi_dA2 = MuMagParallelGeo.FDM2Ord_PAR(q, I_exp_red, sigma, Ms, H_0, H_dem, A_opt)
                N_mu = len(I_exp_red[0, :])
                N_nu = len(I_exp_red[:, 0])
                A_Uncertainty = np.sqrt(2 / (N_mu * N_nu * d2chi_dA2))

                MuMagParallelGeo.PlotFittingResultsPAR_SimpleFit(q, A, chi_q, A_opt, chi_q_opt,
                                                                 I_res_opt, S_H_opt, A_Uncertainty * 1e12,
                                                                 figure, axes1, axes2, axes3, axes4)

                # Save to global Variables
                self.SimpleFit_q_exp = q
                self.SimpleFit_I_exp = I_exp_red
                self.SimpleFit_sigma_exp = sigma
                self.SimpleFit_B_0_exp = self.B_0_exp[K_H:]
                self.SimpleFit_Ms_exp = self.Ms_exp[K_H:]
                self.SimpleFit_Hdem_exp = self.Hdem_exp[K_H:]
                self.SimpleFit_I_fit = I_opt
                self.SimpleFit_A = A
                self.SimpleFit_chi_q = chi_q
                self.SimpleFit_S_H_fit = S_H_opt
                self.SimpleFit_I_res_fit = I_res_opt
                self.SimpleFit_A_opt = A_opt
                self.SimpleFit_chi_q_opt = chi_q_opt
                self.SimpleFit_A_sigma = A_Uncertainty
                self.SimpleFit_SANSgeometry = "parallel"

        else:
            messagebox.showerror(title="Error!",
                                 message="No experimental Data available! Please import experimental data!")

######################################################################################################################
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

        ax.set_xlabel(r'$q$ [1/nm]', usetex=True)
        ax.set_ylabel(r'$I_{\mathrm{exp}}$', usetex=True)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        figure.tight_layout()
        figure.canvas.draw()
