import math

import numpy as np

# Constants (comments mostly copied from the original GSASIIsasd.py)
TEST_LIMIT        = 0.05                    # for convergence
CHI_SQR_LIMIT     = 0.01                    # maximum difference in ChiSqr for a solution
SEARCH_DIRECTIONS = 3                       # <10.  This code requires value = 3
RESET_STRAYS      = 1                       # was 0.001, correction of stray negative values
DISTANCE_LIMIT_FACTOR = 0.1                 # limitation on df to constrain runaways
MAX_MOVE_LOOPS = 5000                       # for no solution in routine: move (MaxEntMove)
MOVE_PASSES       = 0.001                   # convergence test in routine: move (MaxEntMove)

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
# All SB eq. refers to equations in the J Skilling and RK Bryan; MNRAS 211
# (1984) 111 - 124. paper. Overall idea is to maximize entropy S subject to
# constraint C<=C_aim, which is some Chi^2 target. Most comments are copied
# from GSASIIsasd.py. Currently, this code only works with spheroidal models


class decision_helper:

    class MaxEntException(Exception):
        '''Any exception from this module'''
        pass

        #Dist, ChiNow, ChoSol, MaxEntMove, and MaxEnt_SB are all from GSASIIsasd.py
    def Dist(self, s2, beta):
        '''Measure the distance of this possible solution'''
        w = 0
        n = beta.shape[0]
        for k in range(n):
            z = -sum(s2[k] * beta)
            w += beta[k] * z
        return w

    def ChiNow(self, ax, c1, c2, s1, s2):
        '''
        ChiNow

        :returns tuple: (ChiNow computation of ``w``, beta)
        '''

        bx = 1 - ax
        a =   bx * c2  -  ax * s2
        b = -(bx * c1  -  ax * s1)

        beta = self.ChoSol(a, b)
        w = 1.0
        for k in range(SEARCH_DIRECTIONS):
            w += beta[k] * (c1[k] + 0.5*sum(c2[k] * beta))
        return w, beta

    def ChoSol(self, a, b):
        '''
        ChoSol: Chop the solution vectors

        :returns: new vector beta
        '''
        n = b.shape[0]
        fl = np.zeros((n,n))
        bl = np.zeros_like(b)

        if (a[0][0] <= 0):
            msg = "ChoSol: a[0][0] = "
            msg += str(a[0][0])
            msg += '  Value must be positive'
            raise self.MaxEntException(msg)

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
        beta = np.empty(n)
        beta[-1] = bl[-1] / fl[-1][-1]
        for i in (1, 0):
            z = 0.0
            for k in range(i+1, n):
                z += fl[k][i] * beta[k]
            beta[i] = (bl[i] - z) / fl[i][i]

        return beta

class maxEntMethod:
    def MaxEntMove(self,fSum, blank, chisq, chizer, c1, c2, s1, s2):
        r'''
        Implementing the maximum entropy move for feature size distribution
        The goal of this function is to calculate distance and choose the next
        target $\chi^2$ and to move beta one step closer towards the solution
        (see SB eq. 12 and the text below for the definition of beta).
        '''
        helper = decision_helper()
        a_lower, a_upper = 0., 1.          # bracket  "a"
        cmin, beta = helper.ChiNow (a_lower, c1, c2, s1, s2)
        #print "MaxEntMove: cmin = %g" % cmin
        if cmin*chisq > chizer:
            ctarg = (1.0 + cmin)/2
        else:
            ctarg = chizer/chisq
        f_lower = cmin - ctarg
        c_upper, beta = helper.ChiNow (a_upper, c1, c2, s1, s2)
        f_upper = c_upper - ctarg

        fx = 2*MOVE_PASSES      # just to start off
        loop = 1
        while abs(fx) >= MOVE_PASSES and loop <= MAX_MOVE_LOOPS:
            a_new = (a_lower + a_upper) * 0.5           # search by bisection
            c_new, beta = helper.ChiNow (a_new, c1, c2, s1, s2)
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
            raise helper.MaxEntException(msg)

        w = helper.Dist (s2, beta)
        m = SEARCH_DIRECTIONS
        if (w > DISTANCE_LIMIT_FACTOR*fSum/blank):        # invoke the distance penalty, SB eq. 17
            for k in range(m):
                beta[k] *= math.sqrt (fSum/(blank*w))
        chtarg = ctarg * chisq
        return w, chtarg, loop, a_new, fx, beta

    def MaxEnt_SB(self,Iq,sigma,Gqr,first_bins,IterMax=5000,report=True):
        r'''
        This function does the complete Maximum Entropy algorithm of Skilling
        and Bryan

        The scattering intensity, I(Q), is related to the histogram size
        distribution, Np(r) by the following equation:

        .. math::
            I_{Q}=|\Delta\rho^2|\int|F(Q,r)^2|(V(r))^2N_{P}(r)dr

        Np(r) is a histogram size distribution where a fixed number of bins are
        defined over a given range of diameter with either constant diameter
        bins or constant proportional diameter bins. Solution of the histogram
        size distribution to the scattering equation above is obtained by
        fitting the scattering calculated from trial distributions to the
        measured data and then revising the amplitudes of the trial histogram
        distribution based upon the applied constraints. The trial histogram
        size distribution is not forced to adhere to a particular functional
        form, such as Gaussian or log-normal. However, in the current
        formulation, all sizes of the scatterer are expected to have the same
        scattering contrast and morphology (shape, degree of interaction,
        aspect ratio, orientation, etc.)

        The maximum entropy method seeks solution of the functional, Ξ:

        .. math::
            \equiv =\chi-\alpha S

        Where $\chi^2$ indicates the goodness of fit, S is the applied
        constraint, and alpha is a Lagrange multiplier used to ensure that the
        solution fits the measured data to some extent. But compared to a
        regular regularization method, maximum entropy method also forces all
        histograms in the size distribution to have a positive amplitude

        :param float Iq: background-subtracted scattering intensity data
        :param float sigma: normalization factor obtained using scale, weights,
               and weight factors
        :param float[][] G: transformation matrix
        :param float first_bins[]: initial guess for distribution
        :param int IterMax: maximum iterations allowed
        :param obj resolution: resolution object providing information about
            smearing
        :param boolean report: print report if True; do not print if False

        :returns float[]: :math:`f(r) dr`
        '''
        SEARCH_DIRECTIONS = 3
        CHI_SQR_LIMIT = 0.01
        n = len(first_bins)
        npt = len(Iq)

        #operation = matrix_operation()

        xi = np.zeros((SEARCH_DIRECTIONS, n))
        eta = np.zeros((SEARCH_DIRECTIONS, npt))
        beta = np.zeros(SEARCH_DIRECTIONS)
        s2 = np.zeros((SEARCH_DIRECTIONS, SEARCH_DIRECTIONS))
        c2 = np.zeros((SEARCH_DIRECTIONS, SEARCH_DIRECTIONS))

        blank = sum(first_bins) / len(first_bins)            # average of initial bins before optimization
        chizer, chtarg = npt*1.0, npt*1.0
        f = first_bins * 1.0                                 # starting distribution is the same as the inital distribution
        fSum  = sum(f)                                       # find the sum of the f-vector
        z = (Iq - np.dot(f, Gqr.transpose())) /sigma             # standardized residuals
        chisq = sum(z*z)                                     # Chi^2
        converged = False

        for iter in range(IterMax):
            ox = -2 * z / sigma

            cgrad = np.dot(ox, Gqr)  # cgrad[i] = del(C)/del(f[i]), SB eq. 8
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

            eta[0] = np.dot(xi[0], Gqr.transpose())          # solution --> data
            eta[1] = np.dot(xi[1], Gqr.transpose())          # solution --> data
            ox = eta[1] / (sigma * sigma)
            xi[2] = np.dot(ox, Gqr)          # data --> solution
            a = 1.0 / math.sqrt(sum(f * xi[2]*xi[2]))
            xi[2] = f * xi[2] * a
            eta[2] = np.dot(xi[2], Gqr.transpose())           # solution --> data

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
                w, chtarg, loop, a_new, fx, beta = self.MaxEntMove(fSum, blank, chisq, chizer, c1, c2, s1, s2)

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
            z = (Iq - np.dot(f, Gqr.transpose())) / sigma              # standardized residuals
            chisq = sum(z*z)                                       # report this ChiSq

            if report:
                print (" MaxEnt trial/max: %3d/%3d" % ((iter+1), IterMax))
                print (" Residual: %5.2lf%% Entropy: %8lg" % (100*test, S))
                print (" Function sum: %.6lg Change from last: %.2lf%%\n" % (fSum,100*fChange/fSum))

            # See if we have finished our task.
            # do the hardest test first
            if (abs(chisq/chizer-1.0) < CHI_SQR_LIMIT) and  (test < TEST_LIMIT):
                print (' Convergence achieved.')
                converged = True
                return chisq/chizer, f, np.dot(f, Gqr.transpose()), converged, iter     # solution FOUND returns here
        print (' No convergence! Try increasing Error multiplier.')
        return chisq/chizer, f, np.dot(f, Gqr.transpose()), converged, iter             # no solution after IterMax iterations

