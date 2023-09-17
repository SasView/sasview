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

#####################################################################################################################
def get_directory():
    fname = QFileDialog.getOpenFileName()
    if fname:
        fname = fname[0]
        index = [i for i, val in enumerate(fname) if val == "/"]
        fname = fname[0:index[-1]+1]
    return fname

#####################################################################################################################
# Import experimental data and get information from filenames
def import_data_button_callback_sub():

    global q_exp
    global I_exp
    global sigma_exp
    global B_0_exp
    global Ms_exp
    global Hdem_exp
    global DataCounter

    #print('here')
    DataCounter = 0
    # Predefine array's
    #DIR = filedialog.askdirectory()
    DIR = get_directory()
    #print('here')
    for name in os.listdir(DIR):
        if name.find(".csv") != -1:
            data = np.genfromtxt(DIR + '/' + name)
            Lq = len(data[:, 0])
            if DataCounter == 0:
                q_exp = np.array([np.zeros(Lq)])
                I_exp = np.array([np.zeros(Lq)])
                sigma_exp = np.array([np.zeros(Lq)])
                B_0_exp = np.array([np.zeros(1)])
                Ms_exp = np.array([np.zeros(1)])
                Hdem_exp = np.array([np.zeros(1)])
                DataCounter = DataCounter + 1
            else:
                q_exp = np.append(q_exp, [np.zeros(Lq)], axis=0)
                I_exp = np.append(I_exp, [np.zeros(Lq)], axis=0)
                sigma_exp = np.append(sigma_exp, [np.zeros(Lq)], axis=0)
                B_0_exp = np.append(B_0_exp, [np.zeros(1)])
                Ms_exp = np.append(Ms_exp, [np.zeros(1)])
                Hdem_exp = np.append(Hdem_exp, [np.zeros(1)])
                DataCounter = DataCounter + 1

    #print('here')
    # Load the data and sort the data
    for name in os.listdir(DIR):
        if name.find(".csv") != -1:

            str_name = name[0:len(name)-4]
            str_name = str_name.split('_')
            idx = int(str_name[0])
            B0 = float(str_name[1])
            Ms = float(str_name[2])
            Hdem = float(str_name[3])

            data = np.genfromtxt(DIR + '/' + name)

            B_0_exp[idx-1] = B0
            Ms_exp[idx-1] = Ms
            Hdem_exp[idx-1] = Hdem
            q_exp[idx-1, :] = data[:, 0].T * 1e9
            I_exp[idx-1, :] = data[:, 1].T
            sigma_exp[idx-1, :] = data[:, 2].T


################################################################################################################
# Plot Experimental Data: Generate Figure
def plot_exp_data(q, I_exp, B_0, x_min, x_max, y_min, y_max):

    fig = plt.figure()
    fig.tight_layout()
    ax = fig.add_subplot(1, 1, 1)

    colors = pl.cm.jet(np.linspace(0, 1, len(B_0)))
    for k in np.arange(0, len(B_0)):
        plt.plot(q[k, :], I_exp[k, :], linestyle='-', color=colors[k], linewidth=0.5, label='B_0 = ' + str(B_0[k]) + ' T')
        plt.plot(q[k, :], I_exp[k, :], '.', color=colors[k], linewidth=0.3, markersize=1)

    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

    plt.xlabel('q [1/nm]')
    plt.ylabel('I_exp')
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)
    plt.yscale('log')
    plt.xscale('log')
    plt.grid(True, which="both", linestyle='--')
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.show()



#####################################################################################################################
# Plot Experimental Data: Set Bounds and Call Plotting Function
def plot_experimental_data():
    global q_exp
    global I_exp
    global sigma_exp
    global B_0_exp

    if np.size(q_exp) > 1:
        q_exp_min = np.amin(q_exp)*1e-9
        q_exp_min = 10**(np.floor(np.log10(q_exp_min))) * np.floor(q_exp_min/10**(np.floor(np.log10(q_exp_min))))

        q_exp_max = np.amax(q_exp)*1e-9
        q_exp_max = 10**(np.floor(np.log10(q_exp_max))) * np.ceil(q_exp_max/10**(np.floor(np.log10(q_exp_max))))

        I_exp_min = np.amin(I_exp)
        I_exp_min = 10**(np.floor(np.log10(I_exp_min))) * np.floor(I_exp_min/10**(np.floor(np.log10(I_exp_min))))

        I_exp_max = np.amax(I_exp)
        I_exp_max = 10 ** (np.floor(np.log10(I_exp_max))) * np.ceil(I_exp_max / 10 ** (np.floor(np.log10(I_exp_max))))

        plot_exp_data(q_exp*1e-9, I_exp, B_0_exp*1e-3, q_exp_min, q_exp_max, I_exp_min, I_exp_max)
    else:
        messagebox.showerror(title="Error!", message="No experimental data available! Please import experimental data!")