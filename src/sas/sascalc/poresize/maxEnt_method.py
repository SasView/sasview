import numpy as np
import math
import csv
import matplotlib.pyplot as plt
from sasmodels import resolution as rst
from sasdata.dataloader import data_info

TEST_LIMIT        = 0.05                    # for convergence
CHI_SQR_LIMIT     = 0.01                    # maximum difference in ChiSqr for a solution
SEARCH_DIRECTIONS = 3                       # <10.  This code requires value = 3
RESET_STRAYS      = 1                       # was 0.001, correction of stray negative values
DISTANCE_LIMIT_FACTOR = 0.1                 # limitation on df to constrain runaways
MAX_MOVE_LOOPS = 5000                       # for no solution in routine: move, 
MOVE_PASSES       = 0.001                   # convergence test in routine: move

def SphereFF(Q,Bins):
    QR = Q[:,np.newaxis]*Bins
    FF = (3./(QR**3))*(np.sin(QR)-(QR*np.cos(QR)))
    return FF

def SphereVol(Bins):
    Vol = (4./3.)*np.pi*Bins**3
    return Vol

def G_matrix(Q,Bins,contrast,choice):
    Gmat = np.array([])
    if choice == 'Sphere':
        Gmat = 1.e-4*(contrast*SphereVol(Bins)*SphereFF(Q,Bins)**2).transpose()
    return Gmat

class MaxEntException(Exception): 
    '''Any exception from this module'''
    pass

def update_Gqr(data, G):
    '''
    tropus: transform data-space -> solution-space:  [G] * data
    
    default definition, caller can use this definition or provide an alternative
    
    :param float[M] data: observations, ndarray of shape (M)
    :param float[M][N] G: transformation matrix, ndarray of shape (M,N)
    :returns float[N]: calculated image, ndarray of shape (N)
    '''
    return np.dot(G,data)

def update_IqFit(image, G, resolution):
    '''
    opus: transform solution-space -> data-space:  [G]^tr * image
    
    default definition, caller can use this definition or provide an alternative
    
    :param float[N] image: solution, ndarray of shape (N)
    :param float[M][N] G: transformation matrix, ndarray of shape (M,N)
    :returns float[M]: calculated data, ndarray of shape (M)
    '''
    updated_fit = np.dot(G.transpose(),image)
    updated_fit = resolution.apply(updated_fit.transpose())
    return updated_fit    

def Dist(s2, beta):
    '''measure the distance of this possible solution'''
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
    ChoSol: ? chop the solution vectors ?
    
    :returns: new vector beta
    '''
    n = b.shape[0]
    fl = np.zeros((n,n))
    bl = np.zeros_like(b)
    
    #print_arr("ChoSol: a", a)
    #print_vec("ChoSol: b", b)

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
                #print "ChoSol: %d %d %d  z = %lg" % ( i, j, k, z)
            z = a[i][j] - z
            if j == i:
                y = math.sqrt(max(0.,z))
            else:
                y = z / fl[j][j]
            fl[i][j] = y
    #print_arr("ChoSol: fl", fl)

    # next, compute bl from fl and b
    bl[0] = b[0] / fl[0][0]
    for i in (1, 2):
        z = 0.0
        for k in range(i):
            z += fl[i][k] * bl[k]
            #print "\t", i, k, z
        bl[i] = (b[i] - z) / fl[i][i]
    #print_vec("ChoSol: bl", bl)

    # last, compute beta from bl and fl
    beta = np.empty((n))
    beta[-1] = bl[-1] / fl[-1][-1]
    for i in (1, 0):
        z = 0.0
        for k in range(i+1, n):
            z += fl[k][i] * beta[k]
            #print "\t\t", i, k, 'z=', z
        beta[i] = (bl[i] - z) / fl[i][i]
    #print_vec("ChoSol: beta", beta)

    return beta

def MaxEntMove(fSum, blank, chisq, chizer, c1, c2, s1, s2):
    '''
    move beta one step closer towards the solution
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

    w = Dist (s2, beta);
    m = SEARCH_DIRECTIONS
    if (w > DISTANCE_LIMIT_FACTOR*fSum/blank):        # invoke the distance penalty, SB eq. 17
        for k in range(m):
            beta[k] *= math.sqrt (fSum/(blank*w))
    chtarg = ctarg * chisq
    return w, chtarg, loop, a_new, fx, beta

def MaxEnt_SB(Iq,sigma,Gqr,first_bins,IterMax,resolution,report):
    SEARCH_DIRECTIONS = 3
    CHI_SQR_LIMIT = 0.01
    n = len(first_bins)
    npt = len(Iq)
    
    xi = np.zeros((SEARCH_DIRECTIONS, n))
    eta = np.zeros((SEARCH_DIRECTIONS, npt))
    beta = np.zeros((SEARCH_DIRECTIONS))
    s2 = np.zeros((SEARCH_DIRECTIONS, SEARCH_DIRECTIONS))
    c2 = np.zeros((SEARCH_DIRECTIONS, SEARCH_DIRECTIONS))
    
    blank = sum(first_bins) / len(first_bins) # average of initial bins before optimization
    chizer, chtarg = npt*1.0, npt*1.0
    f = first_bins * 1.0
    fSum  = sum(f) 
    z = (Iq - update_IqFit(f, Gqr, resolution)) /sigma
    chisq = sum(z*z)
    
    for iter in range(IterMax):
        ox = -2 * z / sigma  # gradient of chisq
        
        cgrad = update_Gqr(ox, Gqr)  # need to write a method to update G(Q,r)
        sgrad = -np.log(f/first_bins) / (blank*math.exp (1.0))
        snorm = math.sqrt(sum(f * sgrad*sgrad)) # entropy term
        cnorm = math.sqrt(sum(f * cgrad*cgrad))
        tnorm = sum(f * sgrad * cgrad)
        
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
     	
        eta[0] = update_IqFit(xi[0], Gqr, resolution);          # image --> data
        eta[1] = update_IqFit(xi[1], Gqr, resolution);          # image --> data
        ox = eta[1] / (sigma * sigma)
        xi[2] = update_Gqr(ox, Gqr);              # data --> image
        a = 1.0 / math.sqrt(sum(f * xi[2]*xi[2]))
        xi[2] = f * xi[2] * a
        eta[2] = update_IqFit(xi[2], Gqr, resolution)           # image --> data

        # prepare the search directions for the conjugate gradient technique
        c1 = xi.dot(cgrad) / chisq                          # C_mu, SB eq. 24
        s1 = xi.dot(sgrad)                          # S_mu, SB eq. 24
        # print_vec("MaxEnt: c1", c1)
        # print_vec("MaxEnt: s1", s1)
        
        for k in range(SEARCH_DIRECTIONS):
            for l in range(k+1):
                c2[k][l] = 2 * sum(eta[k] * eta[l] / sigma/sigma) / chisq
                s2[k][l] = -sum(xi[k] * xi[l] / f) / blank
#         print_arr("MaxEnt: c2", c2)
#         print_arr("MaxEnt: s2", s2)

        # reflect across the body diagonal
        for k, l in ((0,1), (0,2), (1,2)):
            c2[k][l] = c2[l][k]                     #  M_(mu,nu)
            s2[k][l] = s2[l][k]                     #  g_(mu,nu)
 
        beta[0] = -0.5 * c1[0] / c2[0][0]
        beta[1] = 0.0
        beta[2] = 0.0
        if (iter > 0):
            w, chtarg, loop, a_new, fx, beta = MaxEntMove(fSum, blank, chisq, chizer, c1, c2, s1, s2)
            
        f_old = f.copy()    # preserve the last image
        f += xi.transpose().dot(beta)   # move the image towards the solution, SB eq. 25
       
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
        S = sum((f/fSum) * np.log(f/fSum))      # normalized entropy, S&B eq. 1
        z = (Iq - update_IqFit(f, Gqr, resolution)) / sigma  # standardized residuals
        chisq = sum(z*z)                            # report this ChiSq

        if report:
            print (" MaxEnt trial/max: %3d/%3d" % ((iter+1), IterMax))
            print (" Residual: %5.2lf%% Entropy: %8lg" % (100*test, S))
            print (" Function sum: %.6lg Change from last: %.2lf%%\n" % (fSum,100*fChange/fSum))
            
        # See if we have finished our task.
        # do the hardest test first
        if (abs(chisq/chizer-1.0) < CHI_SQR_LIMIT) and  (test < TEST_LIMIT):
            print (' Convergence achieved.')
            return chisq,f,update_IqFit(f, Gqr, resolution)     # solution FOUND returns here
    print (' No convergence! Try increasing Error multiplier.')
    return chisq,f,update_IqFit(f, Gqr, resolution)       # no solution after IterMax iterations

def sizeDistribution(input):         
    Qmin = input["Limits"][0]
    Qmax = input["Limits"][1]
    scale = input["Scale"]
    minDiam = input["DiamRange"][0]
    maxDiam = input["DiamRange"][1]
    Nbins = input["DiamRange"][2]
    if input["Logbin"]:
        Bins = np.logspace(np.log10(minDiam),np.log10(maxDiam),Nbins+1,True)/2        #make radii
    else:
        Bins = np.linspace(minDiam,maxDiam,Nbins+1,True)/2        #make radii
    Dbins = np.diff(Bins)
    Bins = Bins[:-1]+Dbins/2.
    wtFactor = input["WeightFactors"]
    Ibeg = np.searchsorted(Q,Qmin)
    Ifin = np.searchsorted(Q,Qmax)+1        #include last point
    BinMag = np.zeros_like(Bins)
    contrast = input["Contrast"]
    Ic = np.zeros(len(I))
    sky = input["Sky"]
    wt = input["Weights"]
    Back = input["Background"]
    Gmat = G_matrix(Q,Bins,contrast,input["Model"])
    BinsBack = np.ones_like(Bins)*sky*scale/contrast
    chisq,BinMag,Ic[Ibeg:Ifin] = MaxEnt_SB(scale*I[Ibeg:Ifin]-Back,scale/np.sqrt(wtFactor*wt[Ibeg:Ifin]),Gmat,BinsBack,IterMax=5000,resolution=perfect1D,report=True)
    BinMag = BinMag/(2.*Dbins)
    return chisq,Bins,BinMag,Q[Ibeg:Ifin],Ic[Ibeg:Ifin]

# main
Q = np.array([])
I = np.array([])
dI = np.array([])

with open("I_for_dist1.txt") as fp:
    spamreader = csv.reader(fp, delimiter=' ')
    for row in spamreader:
        try:
            Q = np.append(Q, float(row[0]))
            I = np.append(I, float(row[1]))
            dI = np.append(dI, float(row[2]))
        except:
            pass
        
data_from_loader = data_info.Data1D(x=Q, y=I, dx=None, dy=dI,lam=None, dlam=None, isSesans=False)
data_from_loader.filename = "mock data"
  
input = {}
input["Filename"] = data_from_loader.filename
input["Data"] = [data_from_loader.x,data_from_loader.y,data_from_loader.dy]
input["Limits"] = [min(Q), max(Q)]
input["Scale"] = 1
input["Logbin"] = False
input["DiamRange"] = [2,240,120]
input["WeightFactors"] = np.ones(len(I))*2
input["Contrast"] = 5 
input["Sky"] = 0.0001
input["Weights"] = dI
input["Background"] = np.zeros(len(I))
input["Model"] = 'Sphere'
#qlength, qwidth = 0.1, 0.117
#slit1D = rst.Slit1D(Q,q_length=qlength,q_width=qwidth,q_calc=Q)
perfect1D = rst.Perfect1D(Q)
input["Resolution"] = perfect1D
input["Sky"] = 0.0001

chisq,Bins,BinMag,Qc,Ic = sizeDistribution(input)

results = data_info.Data1D(x=Qc, y=Ic, dx=None, dy=None,lam=None, dlam=None, isSesans=False)

print(input)
plt.figure()
plt.plot(Bins,BinMag)

plt.figure()
plt.errorbar(data_from_loader.x,data_from_loader.y,yerr=data_from_loader.dy,label='original')
plt.loglog(results.x,results.y,label='fit')
plt.xlabel('Q ['+results.x_unit+']')
plt.ylabel('I(Q) ['+results.y_unit+']')
plt.legend()

plt.show()