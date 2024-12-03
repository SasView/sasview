
##########################################################################################
"""My code to implement paths such that the modules can be found by Python and the program can run"""
import sys
import os

additional_path = ['C:/Users/Qerne/OneDrive/Documents/VSCode/Projects/Thesis/SasView_dev_version/sasview/src', 
                   'C:/Users/Qerne/OneDrive/Documents/VSCode/Projects/Thesis/SasView_dev_version/sasmodels', 
                   'C:/Users/Qerne/OneDrive/Documents/VSCode/Projects/Thesis/SasView_dev_version/sasdata']

# Add the directory to sys.path
for path in additional_path:
    absolute_path = os.path.abspath(path)
    if absolute_path not in sys.path:
        sys.path.append(absolute_path)

#print("Python is searching for modules in the following directories:")
#for path in sys.path:
#    print(path)
##########################################################################################
import time
from sas.qtgui.Perspectives.Shape2SAS.DataHandler.Parameters import ModelProfile, ScatteringCalculation, SimulationParameters, ModelSystem
from Shape2SAS import getSimulatedScattering, getPointDistribution, getTheoreticalScattering
import matplotlib.pyplot as plt

start_total = time.time()


prof = ModelProfile(subunits=["sphere"], p_s=[1.0],
                                                    dimensions=[[50.0, 0.0, 0.0]],
                                                    com=[[0.0, 0.0, 0.0]],
                                                    rotation_points=[[0.0, 0.0, 0.0]],
                                                    rotation=[[0.0, 0.0, 0.0]],
                                                    exclude_overlap=True)

syss = ModelSystem(prof, Stype="None", par=[], polydispersity=0.0, conc=0.02, sigma_r=0., exposure=500.)

simpar = SimulationParameters(qmin=0.001, qmax=0.5, Nq=400, prpoints=100, Npoints=10000, 
                              seed=None, method=None, model_name=None)

testScattering = ScatteringCalculation(syss, simpar)

ITheory = getTheoreticalScattering(testScattering)

time_total = time.time() - start_total
print("    Total run time:", round(time_total, 3), "seconds.")

I = ITheory.I_theory
q = ITheory.q

plt.plot(q, I)
plt.xscale('log')
plt.yscale('log')
plt.show()

"""
prof = ModelProfile(subunits=["sphere"], p_s=[1.0],
                                                    dimensions=[[50.0, 0.0, 0.0]],
                                                    com=[[0.0, 0.0, 0.0]],
                                                    rotation_points=[[0.0, 0.0, 0.0]],
                                                    rotation=[[0.0, 0.0, 0.0]],
                                                    exclude_overlap=True)

syss = ModelSystem(prof, Stype="None", par=[], polydispersity=0.0, conc=0.02, sigma_r=0., exposure=500.)

simpar = SimulationParameters(qmin=0.001, qmax=0.5, Nq=400, prpoints=100, Npoints=10000, 
                              seed=None, method=None, model_name=None)

testScattering = ScatteringCalculation(syss, simpar)

Isim = getSimulatedScattering(testScattering)

I = Isim.I_sim
Q = Isim.q
Ierr = Isim.I_err

plt.errorbar(Q, I, yerr=Ierr, fmt='o')
plt.xscale('log')
plt.yscale('log')
plt.show()

"""
####Test of the getPointDistribution function
"""
Npoints = 3000
testmodel = ModelProfile(subunits=["sphere", "sphere"], p_s=[1.0, 1.0], 
                         dimensions=[[50.0, 0.0, 0.0], [50.0, 0.0, 0.0]], 
                         com=[[0.0, 0.0, 0.0], [50.0, 0.0, 0.0]], 
                         rotation_points=[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], 
                         rotation=[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], 
                         exclude_overlap=True)


test = getPointDistribution(testmodel, Npoints)

x = test.x
y = test.y
z = test.z

fig, ax = plt.subplots(subplot_kw={'projection': '3d'})

ax.scatter(x, y, z, c='r', marker='o')

ax.set_xlabel('X Label')
ax.set_ylabel('Y Label')
ax.set_zlabel('Z Label')
ax.set_xlim(-60, 60)
ax.set_ylim(-60, 60)
ax.set_zlim(-60, 60)
plt.show()

print(test)
"""


