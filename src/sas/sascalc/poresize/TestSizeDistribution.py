"""
This module is a temporary module used for Development of this perspective only
It alows testing the module code without loading a notebook though not clear
this is needed.
"""

from SizeDistribution import sizeDistribution
import plottableHist
#from sasdata.dataloader import data_info
#from sasmodels import resolution as rst
import csv
import numpy as np
from scipy import integrate
import matplotlib.pyplot as plt

import sys
import os
from os.path import abspath, dirname, realpath, join as joinpath

def addpath(path):
    """
    Add a directory to the python path environment, and to the PYTHONPATH
    environment variable for subprocesses.
    """
    path = abspath(path)
    if 'PYTHONPATH' in os.environ:
        PYTHONPATH = path + os.pathsep + os.environ['PYTHONPATH']
    else:
        PYTHONPATH = path
    os.environ['PYTHONPATH'] = PYTHONPATH
    sys.path.insert(0, path)


from sasdata.dataloader import data_info
from sasmodels import resolution as rst
from maxEnt_method import matrix_operation

# Spherical volume
def SphereVol(Bins):
    Vol = (4./3.)*np.pi*Bins**3
    return Vol

# Import some data and put them in the Data1D for the sake of the example
Q = np.array([])
I = np.array([])
dI = np.array([])

file = "test_data/Alumina_usaxs_irena_input.csv"

with open(file) as fp:
    spamreader = csv.reader(fp, delimiter=',')
    
    for row in spamreader:
        #print(float(row[0]))
        try:
            Q = np.append(Q, float(row[0]))
            I = np.append(I, float(row[1]))
            dI = np.append(dI, float(row[2]))
        except:
            pass
        
data_from_loader = data_info.Data1D(x=Q, y=I, dx=None, dy=dI,lam=None, dlam=None, isSesans=False)
data_from_loader.filename = file

size_distribution = sizeDistribution(data_from_loader)
print(size_distribution.aspectRatio)
print(f'qrange is {size_distribution.qMin}-{size_distribution.qMax}',)
print(f'indxing is {size_distribution.ndx_qmin}-{size_distribution.ndx_qmax}')
size_distribution.qMin = 0.04
print(f'qrange is {size_distribution.qMin} to {size_distribution.qMax}',)
print(f'indxing is {size_distribution.ndx_qmin} to {size_distribution.ndx_qmax}')

size_distribution.ndx_qmin = 25
size_distribution.ndx_qmax = 94

print(f'qrange is {size_distribution.qMin} to {size_distribution.qMax}',)
print(f'indxing is {size_distribution.ndx_qmin} to {size_distribution.ndx_qmax}')

## Testing binning 
print("Testing Binning changes between setting bins and switching between log and linear binning")
size_distribution.nbins = 200
logbinning = size_distribution.nbins

size_distribution.logbin = False
linbinning = size_distribution.bins
if np.all(logbinning!=linbinning):
    print("logbinned and linear binned data is different")
else:
    raise AssertionError('setting the bins to linear binning failed to reset bins')

print("Testing switching weights")
print(size_distribution.weights)
size_distribution.useWeights = False
print(np.all(size_distribution.weights==1))
size_distribution.weightType='dI'
print(np.all(size_distribution.weights==1))
size_distribution.useWeights=True
print(np.all(size_distribution.weights==1))


#print('Testing model matrix generation')
#prev_ar = size_distribution.aspectRatio
#size_distribution.aspectRatio = 1.1
#print(f"The aspect ratio is changed from {prev_ar} to {size_distribution.aspectRatio}")
#cutdata = data_info.Data1D(x=Q[size_distribution.ndx_qmin: size_distribution.ndx_qmax],
#                            y=size_distribution.scale*I[size_distribution.ndx_qmin: size_distribution.ndx_qmax] - size_distribution.background,
#                              dx=None, dy=dI[size_distribution.ndx_qmin: size_distribution.ndx_qmax]*size_distribution.scale,lam=None, dlam=None, isSesans=False)
#cutdata.__dict__['qmin'] = size_distribution.qMin
#cutdata.__dict__['qmax'] = size_distribution.qMax
#size_distribution.generate_model_matrix(cutdata)

size_distribution.aspectRatio = 1.0
size_distribution.diamMin = 75
size_distribution.diamMax = 5000
size_distribution.skyBackground = 1e-3
size_distribution.weightType='dI'
# when using Guaussian noise we need to increase the effective error bars (decrease WeightFactor)
#size_distribution.weightFactor = 1.0
size_distribution.weightFactor = 0.5


background = np.ones(len(data_from_loader.y))*0.120605

subdata = data_info.Data1D(x=Q, y=background, dx=None, dy=background*0.0001, lam=None, dlam=None, isSesans=False)
trim_data, intensities, init_binsBack, sigma = size_distribution.prep_maxEnt(subdata, full_fit=True)

print(sigma)
operation = matrix_operation()
gqr = operation.G_matrix(trim_data.x, size_distribution.bins, size_distribution.contrast, 'Sphere', rst.Perfect1D).T

plt.figure()
plt.loglog(data_from_loader.x, data_from_loader.y)
plt.loglog(trim_data.x, trim_data.y)
#plt.loglog(trim_data.x, intensities[0])
plt.loglog(subdata.x, subdata.y, color='red', linestyle='--')
plt.loglog(trim_data.x, size_distribution.model_matrix[:,0:200:10])
#plt.loglog(trim_data.x, gqr[:,10])
plt.show()

convergence = size_distribution.run_maxEnt(trim_data, intensities, init_binsBack, sigma)
print(size_distribution.BinMagnitude_Errs)

#print(size_distribution.MaxEnt_statistics)
#print(size_distribution.volumefrac_cdf)

plt.figure()
plt.semilogx(size_distribution.bins[1:]*2, size_distribution.volumefrac_cdf)
plt.semilogx(size_distribution.bins[1:]*2, size_distribution.number_cdf)
axtwn = plt.gca().twinx()
axtwn.semilogx(size_distribution.bins*2,size_distribution.BinMagnitude_maxEnt)
axtwn.errorbar(size_distribution.bins*2, size_distribution.BinMagnitude_maxEnt, size_distribution.BinMagnitude_Errs)

plt.show()





"""
# Contrust the input dictionary
input = {}
input["IterMax"] = 5000
input["Filename"] = data_from_loader.filename
input["Data"] = [data_from_loader.x,data_from_loader.y]
Qmin = min(data_from_loader.x[25:])
Qmax = max(data_from_loader.x[:94])
input["Limits"] = [Qmin, Qmax]
input["Scale"] = 1
input["Logbin"] = True
input["DiamRange"] = [75,5000,200] 
input["WeightFactors"] = np.ones(len(data_from_loader.y))
input["Contrast"] = 1 
input["Sky"] = 1e-3
input["Weights"] = 1/(dI*dI)
#input["Weights"] = 1/(I*I)
input["Background"] = np.ones(len(data_from_loader.y))*0.120605
input["Model"] = 'Sphere'
perfect1D = rst.Perfect1D(data_from_loader.x) 
qlength, qwidth = 0.117, None 
Ibeg = np.searchsorted(Q,Qmin)
Ifin = np.searchsorted(Q,Qmax)+1
#slit1D = rst.Slit1D(Q[Ibeg:Ifin],q_length=qlength,q_width=qwidth,q_calc=Q[Ibeg:Ifin])
input["Resolution"] = perfect1D

# Call the sizeDistribution function and feed in the input
chisq,Bins,Dbins,BinMag,Qc,Ic = sizeDistribution(input)

# TODO: Change the distribution back to P(r) 
# V = SphereVol(Bins)
# diffV = np.diff(V,prepend=[0])
# BinMagOverV = BinMag/diffV

# Store results in a Data1D object (and temporarily also a separate plottable_hist object)
I_result = data_info.Data1D(x=Qc, y=Ic, dx=None, dy=None,lam=None, dlam=None, isSesans=False)
dist_result = plottableHist.plottable_hist(x=Bins, y=BinMag, dy=input["Weights"], binWidth=Dbins)
dist_result._logx = True

if __name__ == "__main__":
    # Plot to visualize
    #I_smeared = slit1D.apply(I[Ibeg:Ifin])
    #plt.figure()
    #plt.loglog(Q[Ibeg:Ifin],I_smeared)
    #plt.loglog(Q,I)

    plt.figure()
    plt.bar(x=dist_result.x,height=dist_result.y/SphereVol(dist_result.x),width=dist_result.binWidth,label='fit_distribution')
    if dist_result._logx is True:
        plt.xscale('log')
    plt.xlabel('r')
    plt.ylabel('P(r)')
    plt.legend()

    plt.figure()
    plt.loglog(I_result.x,I_result.y,linewidth=2,label='fit',zorder=1)
    plt.errorbar(data_from_loader.x,data_from_loader.y,yerr=data_from_loader.dy,marker='.',label='original',zorder=0)
    plt.xlabel('Q ['+I_result.x_unit+']')
    plt.ylabel('I(Q) ['+I_result.y_unit+']')
    plt.legend()

    plt.figure()
    plt.semilogx(I_result.x,I_result.y-data_from_loader.y[25:94],'.')
    plt.xlabel('Q ['+I_result.x_unit+']')
    plt.ylabel('I residual ['+I_result.y_unit+']')
    plt.show()
"""
