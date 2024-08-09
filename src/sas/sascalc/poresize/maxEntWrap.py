from maxEnt_method import sizeDistribution
import plottableHist
from sasdata.dataloader import data_info
from sasmodels import resolution as rst
import csv
import numpy as np
import matplotlib.pyplot as plt

# Spherical volume
def SphereVol(Bins):
    Vol = (4./3.)*np.pi*Bins**3
    return Vol

# Import some data and put them in the Data1D for the sake of the example.
Q = np.array([])
I = np.array([])
dI = np.array([])

file = "test_data/Alumina_usaxs_irena_input.csv"

with open(file) as fp:
    spamreader = csv.reader(fp, delimiter=',')

    for row in spamreader:
        try:
            Q = np.append(Q, float(row[0]))
            I = np.append(I, float(row[1]))
            dI = np.append(dI, float(row[2]))
        except:
            pass
        
data_from_loader = data_info.Data1D(x=Q, y=I, dx=None, dy=dI,lam=None, dlam=None, isSesans=False)
data_from_loader.filename = file

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
slit1D = rst.Slit1D(Q[Ibeg:Ifin],q_length=qlength,q_width=qwidth,q_calc=Q[Ibeg:Ifin])
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
    I_smeared = slit1D.apply(I)
    plt.figure()
    plt.loglog(Q,I_smeared)
    plt.loglog(Q,I)

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