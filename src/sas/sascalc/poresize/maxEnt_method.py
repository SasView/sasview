import numpy as np
import math
import csv
import matplotlib.pyplot as plt
from sasmodels import resolution as rst
from sasdata.dataloader import data_info

'''
sbmaxent

Entropy maximization routine as described in the article
J Skilling and RK Bryan; MNRAS 211 (1984) 111 - 124.
("MNRAS": "Monthly Notices of the Royal Astronomical Society")

:license: Copyright (c) 2013, UChicago Argonne, LLC
:license: This file is distributed subject to a Software License Agreement found
     in the file LICENSE that is included with this distribution. 

References:

1. J Skilling and RK Bryan; MON NOT R ASTR SOC 211 (1984) 111 - 124.
2. JA Potton, GJ Daniell, and BD Rainford; Proc. Workshop
   Neutron Scattering Data Analysis, Rutherford
   Appleton Laboratory, UK, 1986; ed. MW Johnson,
   IOP Conference Series 81 (1986) 81 - 86, Institute
   of Physics, Bristol, UK.
3. ID Culverwell and GP Clarke; Ibid. 87 - 96.
4. JA Potton, GK Daniell, & BD Rainford,
   J APPL CRYST 21 (1988) 663 - 668.
5. JA Potton, GJ Daniell, & BD Rainford,
   J APPL CRYST 21 (1988) 891 - 897.

'''
# All SB eq. refers to equations in the J Skilling and RK Bryan; MNRAS 211 (1984) 111 - 124. paper
# Overall idea is to maximize entropy S subject to constraint C<=C_aim, which is some Chi^2 target
# Most comments are copied from GSASIIsasd.py
# Currently, this code only works with spherical models

# a new plottable_hist that can be integrated into Data1D object in the future
class plottable_hist(object):
    """
    A class storing all the info needed to plot a bar graph
    Designed to be used in plt.bar instead of plt.hist
    """
    x = None # center of bins
    y = None # height of bins
    dy = None # errorbar of bins
    binWidth = None # width of bins
    
    # Units
    _xaxis = ''
    _xunit = ''
    _logx = False
    _yaxis = ''
    _yunit = ''
    
    def __init__(self, x, y, dy=None, binWidth=None):
        self.x = np.asarray(x)
        self.y = np.asarray(y)
        if dy is not None:
            self.dy = np.asarray(dy)
        if binWidth is not None:
            if len(binWidth) > 1:
                self.binWidth = np.asarray(binWidth)
            else:
                self.binWidth = binWidth

    def xaxis(self, label, unit, islog):
        """
        set the x axis label and unit
        """
        self._xaxis = label
        self._xunit = unit
        self._logx = islog

    def yaxis(self, label, unit):
        """
        set the y axis label and unit
        """
        self._yaxis = label
        self._yunit = unit

# Constants (comments mostly copied from the original GSASIIsasd.py)
TEST_LIMIT        = 0.05                    # for convergence
CHI_SQR_LIMIT     = 0.01                    # maximum difference in ChiSqr for a solution
SEARCH_DIRECTIONS = 3                       # <10.  This code requires value = 3
RESET_STRAYS      = 1                       # was 0.001, correction of stray negative values
DISTANCE_LIMIT_FACTOR = 0.1                 # limitation on df to constrain runaways
MAX_MOVE_LOOPS = 5000                       # for no solution in routine: move (MaxEntMove)
MOVE_PASSES       = 0.001                   # convergence test in routine: move (MaxEntMove)

# Spherical form factor
def SphereFF(Q,Bins):
    QR = Q[:,np.newaxis]*Bins
    FF = (3./(QR**3))*(np.sin(QR)-(QR*np.cos(QR)))
    return FF

# Spherical volume
def SphereVol(Bins):
    Vol = (4./3.)*np.pi*Bins**3
    return Vol

# Transformation matrix
def G_matrix(Q,Bins,contrast,choice,resolution):
    '''
    Defined as (form factor)^2 times volume times some scaling
    The integrand for Iq technically requires volume^2
    The size distribution obtained from this code takes care of the missing volume
    Therefore, it is IMPORTANT to not that the size distribution from this code is technically P(r) multiplied by something
    Converting to the size distribution back to P(r) isn't super straightforward and needs work (a TODO)
    '''
    Gmat = np.array([])
    # TODO: Make this G_matrix function flexible for other form factors (currerntly only works for spheres)
    # TODO: See if we can make use of existing Sasmodels
    if choice == 'Sphere':
        Gmat = 1.e-4*(contrast*SphereVol(Bins)*SphereFF(Q,Bins)**2).transpose()
    Gmat = resolution.apply(Gmat)
    Gmat = Gmat.reshape((len(Bins),len(Q)))
    return Gmat

class MaxEntException(Exception): 
    '''Any exception from this module'''
    pass

# calculate_solution, calculate_data, Dist, ChiNow, ChoSol, MaxEntMove, and MaxEnt_SB are all from GSASIIsasd.py

def calculate_solution(data, G):
    # orginally named tropus in GSASIIsasd.py (comments also mostly from original code)
    '''
    Transform data-space -> solution-space:  [G] * data
    
    n = len(first_bins)
    npt = len(Iq) = len(Q)
    
    Definition according to SB: solution = image = a set of positive numbers which are to be determined and on which entropy is defined
    
    :param float[npt] data: related to distribution, ndarray of shape (npt)
    :param float[n][npt] G: transformation matrix, ndarray of shape (n,npt)
    :param obj resolution: resolution object providing information about smearing
    :returns float[n]: calculated solution, ndarray of shape (n)
    '''
    solution = np.dot(G,data)
    return solution

def calculate_data(solution, G):
    # orginally named opus in GSASIIsasd.py (comments also mostly from original code)
    '''
    Transform solution-space -> data-space:  [G]^tr * solution
    
    n = len(first_bins)
    npt = len(Iq) = len(Q)
    
    :param float[n] solution: related to Iq, ndarray of shape (n)
    :param float[n][npt] G: transformation matrix, ndarray of shape (n,npt)
    :returns float[npt]: calculated data, ndarray of shape (npt)
    '''
    data = np.dot(G.transpose(),solution)
    return data   

def Dist(s2, beta):
    '''Measure the distance of this possible solution'''
    w = 0
    n = beta.shape[0]
    for k in range(n):
        z = -sum(s2[k] * beta)
        w += beta[k] * z
    return w

def ChiNow(ax, c1, c2, s1, s2):
    '''
    ChiNow
    
    :returns tuple: (ChiNow computation of ``w``, beta)
    '''
    
    bx = 1 - ax
    a =   bx * c2  -  ax * s2
    b = -(bx * c1  -  ax * s1)

    beta = ChoSol(a, b)
    w = 1.0
    for k in range(SEARCH_DIRECTIONS):
        w += beta[k] * (c1[k] + 0.5*sum(c2[k] * beta))
    return w, beta

def ChoSol(a, b):
    '''
    ChoSol: ? Chop the solution vectors ?
    
    :returns: new vector beta
    '''
    n = b.shape[0]
    fl = np.zeros((n,n))
    bl = np.zeros_like(b)
    
    if (a[0][0] <= 0):
        msg = "ChoSol: a[0][0] = " 
        msg += str(a[0][0])
        msg += '  Value must be positive'
        raise MaxEntException(msg)

    # first, compute fl from a
    # note fl is a lower triangular matrix
    fl[0][0] = math.sqrt (a[0][0])
    for i in (1, 2):
        fl[i][0] = a[i][0] / fl[0][0]
        for j in range(1, i+1):
            z = 0.0
            for k in range(j):
                z += fl[i][k] * fl[j][k]
            z = a[i][j] - z
            if j == i:
                y = math.sqrt(max(0.,z))
            else:
                y = z / fl[j][j]
            fl[i][j] = y

    # next, compute bl from fl and b
    bl[0] = b[0] / fl[0][0]
    for i in (1, 2):
        z = 0.0
        for k in range(i):
            z += fl[i][k] * bl[k]
        bl[i] = (b[i] - z) / fl[i][i]

    # last, compute beta from bl and fl
    beta = np.empty((n))
    beta[-1] = bl[-1] / fl[-1][-1]
    for i in (1, 0):
        z = 0.0
        for k in range(i+1, n):
            z += fl[k][i] * beta[k]
        beta[i] = (bl[i] - z) / fl[i][i]

    return beta

def MaxEntMove(fSum, blank, chisq, chizer, c1, c2, s1, s2):
    '''
    Goal is to choose the next target Chi^2
    And to move beta one step closer towards the solution (see SB eq. 12 and the text below for the definition of beta)
    '''
    a_lower, a_upper = 0., 1.          # bracket  "a"
    cmin, beta = ChiNow (a_lower, c1, c2, s1, s2)
    #print "MaxEntMove: cmin = %g" % cmin
    if cmin*chisq > chizer:
        ctarg = (1.0 + cmin)/2
    else:
        ctarg = chizer/chisq
    f_lower = cmin - ctarg
    c_upper, beta = ChiNow (a_upper, c1, c2, s1, s2)
    f_upper = c_upper - ctarg

    fx = 2*MOVE_PASSES      # just to start off
    loop = 1
    while abs(fx) >= MOVE_PASSES and loop <= MAX_MOVE_LOOPS:
        a_new = (a_lower + a_upper) * 0.5           # search by bisection
        c_new, beta = ChiNow (a_new, c1, c2, s1, s2)
        fx = c_new - ctarg
        # tighten the search range for the next pass
        if f_lower*fx > 0:
            a_lower, f_lower = a_new, fx
        if f_upper*fx > 0:
            a_upper, f_upper = a_new, fx
        loop += 1

    if abs(fx) >= MOVE_PASSES or loop > MAX_MOVE_LOOPS:
        msg = "MaxEntMove: Loop counter = " 
        msg += str(MAX_MOVE_LOOPS)
        msg += '  No convergence in alpha chop'
        raise MaxEntException(msg)

    w = Dist (s2, beta)
    m = SEARCH_DIRECTIONS
    if (w > DISTANCE_LIMIT_FACTOR*fSum/blank):        # invoke the distance penalty, SB eq. 17
        for k in range(m):
            beta[k] *= math.sqrt (fSum/(blank*w))
    chtarg = ctarg * chisq
    return w, chtarg, loop, a_new, fx, beta

def MaxEnt_SB(Iq,sigma,Gqr,first_bins,IterMax,report):
    '''
    Do the complete Maximum Entropy algorithm of Skilling and Bryan
    
    :param float Iq: background-subtracted scattering intensity data
    :param float sigma: normalization factor obtained using scale, weights, and weight factors
    :param float[][] G: transformation matrix
    :param float first_bins[]: initial guess for distribution
    :param int IterMax: maximum iterations allowed
    :param obj resolution: resolution object providing information about smearing
    :param boolean report: print report if True; do not print if False
    
    :returns float[]: :math:`f(r) dr`
    '''
    SEARCH_DIRECTIONS = 3
    CHI_SQR_LIMIT = 0.01
    n = len(first_bins)
    npt = len(Iq)
    
    xi = np.zeros((SEARCH_DIRECTIONS, n))
    eta = np.zeros((SEARCH_DIRECTIONS, npt))
    beta = np.zeros((SEARCH_DIRECTIONS))
    s2 = np.zeros((SEARCH_DIRECTIONS, SEARCH_DIRECTIONS))
    c2 = np.zeros((SEARCH_DIRECTIONS, SEARCH_DIRECTIONS))
    
    blank = sum(first_bins) / len(first_bins)            # average of initial bins before optimization
    chizer, chtarg = npt*1.0, npt*1.0
    f = first_bins * 1.0                                 # starting distribution is the same as the inital distribution
    fSum  = sum(f)                                       # find the sum of the f-vector
    z = (Iq - calculate_data(f, Gqr)) /sigma             # standardized residuals
    chisq = sum(z*z)                                     # Chi^2
    
    for iter in range(IterMax):
        ox = -2 * z / sigma                                    
        
        cgrad = calculate_solution(ox, Gqr)  # cgrad[i] = del(C)/del(f[i]), SB eq. 8
        sgrad = -np.log(f/first_bins) / (blank*math.exp (1.0)) # sgrad[i] = del(S)/del(f[i])
        snorm = math.sqrt(sum(f * sgrad*sgrad))                # entropy, SB eq. 22
        cnorm = math.sqrt(sum(f * cgrad*cgrad))                # Chi^2, SB eq. 22
        tnorm = sum(f * sgrad * cgrad)                         # norm of gradient
        
        a = 1.0
        b = 1.0 / cnorm
        if iter == 0:
            test = 0.0     # mismatch between entropy and ChiSquared gradients
        else:
            test = math.sqrt( ( 1.0 - tnorm/(snorm*cnorm) )/2 ) # SB eq. 37?
            a = 0.5 / (snorm * test)
            b *= 0.5 / test
        xi[0] = f * cgrad / cnorm
        xi[1] = f * (a * sgrad - b * cgrad)
     	
        eta[0] = calculate_data(xi[0], Gqr);          # solution --> data
        eta[1] = calculate_data(xi[1], Gqr);          # solution --> data
        ox = eta[1] / (sigma * sigma)
        xi[2] = calculate_solution(ox, Gqr);          # data --> solution
        a = 1.0 / math.sqrt(sum(f * xi[2]*xi[2]))
        xi[2] = f * xi[2] * a
        eta[2] = calculate_data(xi[2], Gqr)           # solution --> data

        # prepare the search directions for the conjugate gradient technique
        c1 = xi.dot(cgrad) / chisq                          # C_mu, SB eq. 24
        s1 = xi.dot(sgrad)                                  # S_mu, SB eq. 24

        
        for k in range(SEARCH_DIRECTIONS):
            for l in range(k+1):
                c2[k][l] = 2 * sum(eta[k] * eta[l] / sigma/sigma) / chisq
                s2[k][l] = -sum(xi[k] * xi[l] / f) / blank

        # reflect across the body diagonal
        for k, l in ((0,1), (0,2), (1,2)):
            c2[k][l] = c2[l][k]                     #  M_(mu,nu)
            s2[k][l] = s2[l][k]                     #  g_(mu,nu)
 
        beta[0] = -0.5 * c1[0] / c2[0][0]
        beta[1] = 0.0
        beta[2] = 0.0
        if (iter > 0):
            w, chtarg, loop, a_new, fx, beta = MaxEntMove(fSum, blank, chisq, chizer, c1, c2, s1, s2)
            
        f_old = f.copy()                # preserve the last solution
        f += xi.transpose().dot(beta)   # move the solution towards the solution, SB eq. 25
       
        # As mentioned at the top of p.119,
        # need to protect against stray negative values.
        # In this case, set them to RESET_STRAYS * base[i]
        #f = f.clip(RESET_STRAYS * blank, f.max())
        for i in range(n):
            if f[i] <= 0.0:
                f[i] = RESET_STRAYS * first_bins[i]
        df = f - f_old
        fSum = sum(f)
        fChange = sum(df)

        # calculate the normalized entropy
        S = sum((f/fSum) * np.log(f/fSum))                     # normalized entropy, S&B eq. 1
        z = (Iq - calculate_data(f, Gqr)) / sigma              # standardized residuals
        chisq = sum(z*z)                                       # report this ChiSq

        if report:
            print (" MaxEnt trial/max: %3d/%3d" % ((iter+1), IterMax))
            print (" Residual: %5.2lf%% Entropy: %8lg" % (100*test, S))
            print (" Function sum: %.6lg Change from last: %.2lf%%\n" % (fSum,100*fChange/fSum))
            
        # See if we have finished our task.
        # do the hardest test first
        if (abs(chisq/chizer-1.0) < CHI_SQR_LIMIT) and  (test < TEST_LIMIT):
            print (' Convergence achieved.')
            return chisq,f,calculate_data(f, Gqr)     # solution FOUND returns here
    print (' No convergence! Try increasing Error multiplier.')
    return chisq,f,calculate_data(f, Gqr)             # no solution after IterMax iterations

def sizeDistribution(input):
    '''
    :param dict input:
        input must have the following keys, each corresponding to their specified type of values:
        Key                          | Value
        __________________________________________________________________________________________
        Data                         | list[float[npt],float[npt]]: I and Q. The two arrays should both be length npt
        Limits                       | float[2]: a length-2 array contains Qmin and Qmax
        Scale                        | float:
        DiamRange                    | float[3]: A length-3 array contains minimum and maximum diameters between which the 
                                                 distribution will be constructed, and the thid number is the number of bins 
                                                 (must be an integer) (TODO: maybe restructure that)
        LogBin                       | boolean: Bins will be on a log scale if True; bins will be on a linear scale is False 
        WeightFactors                | float[npt]: Factors on the weights
        Contrast                     | float: The difference in SLD between the two phases
        Sky                          | float: Should be small but non-zero (TODO: Check this statement)
        Weights                      | float[npt]: Provide some sort of uncertainty. Examples include dI and 1/I
        Background                   | float[npt]: Scattering background to be subtracted
        Resolution                   | obj: resolution object
        Model                        | string: model name, currently only supports 'Sphere'
    '''         
    Qmin = input["Limits"][0]
    Qmax = input["Limits"][1]
    scale = input["Scale"]
    minDiam = input["DiamRange"][0]
    maxDiam = input["DiamRange"][1]
    Nbins = input["DiamRange"][2]
    Q,I = input["Data"]
    if input["Logbin"]:
        Bins = np.logspace(np.log10(minDiam),np.log10(maxDiam),Nbins+1,True)/2        #make radii
    else:
        Bins = np.linspace(minDiam,maxDiam,Nbins+1,True)/2        #make radii
    Dbins = np.diff(Bins)
    Bins = Bins[:-1]+Dbins/2.
    Ibeg = np.searchsorted(Q,Qmin)
    Ifin = np.searchsorted(Q,Qmax)+1        #include last point
    wtFactor = input["WeightFactors"][Ibeg:Ifin]
    BinMag = np.zeros_like(Bins)
    contrast = input["Contrast"]
    Ic = np.zeros(len(I))
    sky = input["Sky"]
    wt = input["Weights"][Ibeg:Ifin]
    Back = input["Background"][Ibeg:Ifin]
    res = input["Resolution"]
    Gmat = G_matrix(Q[Ibeg:Ifin],Bins,contrast,input["Model"],res)
    BinsBack = np.ones_like(Bins)*sky*scale/contrast
    chisq,BinMag,Ic[Ibeg:Ifin] = MaxEnt_SB(scale*I[Ibeg:Ifin]-Back,scale/np.sqrt(wtFactor*wt),Gmat,BinsBack,IterMax=1000,report=True)
    BinMag = BinMag/(2.*Dbins)
    return chisq,Bins,Dbins,BinMag,Q[Ibeg:Ifin],Ic[Ibeg:Ifin]

# Example of using sizeDistribution:

# Import some data and put them in the Data1D for the sake of the example.
Q = np.array([])
I = np.array([])
dI = np.array([])

with open("test_data/Alumina_usaxs_irena_input.csv") as fp:
    spamreader = csv.reader(fp, delimiter=',')

    for row in spamreader:
        try:
            Q = np.append(Q, float(row[0]))
            I = np.append(I, float(row[1]))
            dI = np.append(dI, float(row[2]))
        except:
            pass
        
data_from_loader = data_info.Data1D(x=Q, y=I, dx=None, dy=dI,lam=None, dlam=None, isSesans=False)
data_from_loader.filename = "mock data"

# Contrust the input dictionary
input = {}
input["Filename"] = data_from_loader.filename
input["Data"] = [data_from_loader.x,data_from_loader.y]
input["Limits"] = [min(data_from_loader.x[20:]), max(data_from_loader.x[:94])]
input["Scale"] = 1
input["Logbin"] = True
input["DiamRange"] = [25,10000,100] 
input["WeightFactors"] = np.ones(len(data_from_loader.y))
input["Contrast"] = 1 
input["Sky"] = 1e-4
#input["Weights"] = dI
input["Weights"] = 0.1/I
input["Background"] = np.ones(len(data_from_loader.y))*0.12
input["Model"] = 'Sphere'
perfect1D = rst.Perfect1D(data_from_loader.x) 
qlength, qwidth = 0.117, None 
slit1D = rst.Slit1D(Q,q_length=qlength,q_width=qwidth,q_calc=Q)
input["Resolution"] = perfect1D

# Call the sizeDistribution function and feed in the input
chisq,Bins,Dbins,BinMag,Qc,Ic = sizeDistribution(input)

# TODO: Change the distribution back to P(r) 
# V = SphereVol(Bins)
# diffV = np.diff(V,prepend=[0])
# BinMagOverV = BinMag/diffV

# Store results in a Data1D object (and temporarily also a separate plottable_hist object)
I_result = data_info.Data1D(x=Qc, y=Ic, dx=None, dy=None,lam=None, dlam=None, isSesans=False)
dist_result = plottable_hist(x=Bins, y=BinMag, dy=None, binWidth=Dbins)
dist_result._logx = True

# Plot to visualize
#I_smeared = slit1D.apply(I)
#plt.figure()
#plt.loglog(Q,I_smeared)
#plt.loglog(Q,I)

plt.figure()
plt.bar(x=dist_result.x,height=dist_result.y,width=dist_result.binWidth,label='fit_distribution')
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

plt.show()