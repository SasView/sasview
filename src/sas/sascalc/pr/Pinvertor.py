"""
Under Development-
Class duplicating Cinvertor.c's functionality in Python
depends on py_invertor.py as a pose to invertor.c
"""
import sas.sascalc.pr.py_invertor as py_invertor
import numpy as np
import logging
import math
import timeit
from numba import njit

logger = logging.getLogger(__name__)

class Pinvertor:
        #invertor.h
    #Maximum distance between any two points in the system
    #d_max = 0.0
    #q data
    x = np.empty(0, dtype = np.float)
    #I(q) data
    y = np.empty(0, dtype = np.float)
    #dI(q) data
    err = np.empty(0, dtype = np.float)
    #Number of q points
    npoints = 0
    #Number of I(q) points
    ny = 0
    #Number of dI(q) points
    nerr = 0
    #Alpha value
    alpha = 0.0
    #Slit height in units of q [A-1]
    slit_height = 0.0
    #Slit width in units of q [A-1]
    slit_width = 0.0

    def __init__(self):
        #replace invertor.c invertor_init
        self.set_dmax(180)
        #Minimum q to include in inversion
        self.set_qmin(-1.0)
        #Maximum q to include in inversion
        self.set_qmax(-1.0)
        #Flag for whether or not to evaluate a constant background
        #while inverting
        self.set_est_bck(0)

    def residuals(self, args):
        """
        Function to call to evaluate the residuals\n
	    for P(r) inversion\n
	    @param args: input parameters\n
	    @return: list of residuals
        """

        residuals = []

        #pars = np.asanyarray(args, dtype = np.float)
        pars = args

        residual = 0.0
        diff = 0.0
        regterm = 0.0
        nslice = 25
        regterm = py_invertor.reg_term(pars, self.d_max, nslice)

        for i in range(self.npoints):
            diff = self.y[i] - py_invertor.iq(pars, self.d_max, self.x[i])
            residual = diff*diff / (self.err[i] * self.err[i])

            residual += self.alpha * regterm
            try:
                residuals.append(float(residual))
            except:
                logger.error("Pinvertor.residuals: error setting residual.")

        return residuals

    def pr_residuals(self, pars):
        """
        Function to call to evaluate the residuals
        for P(r) minimization (for testing purposes)
        @param args: input parameters
        @return: list of residuals
        """
        regterm = 0.0
        nslice = 25
        residuals = []
        regterm = py_invertor.reg_term(pars, self.d_max, nslice)
        for i in range(self.npoints):
            diff = self.y[i] - py_invertor.pr(pars, self.d_max, self.x[i])
            residual = diff*diff / (self.err[i] * self.err[i])

            residual += self.alpha * regterm

            residuals.append(residual)
        return residuals

    def set_x(self, args):
        """
        Function to set the x data
        Takes an array of the doubles as input
        Returns the number of entries found
        """

        data = np.asanyarray(args, dtype = np.float)

        ndata = data.shape[0]

        #reset x
        #self.x = None
        #self.x = np.zeros(ndata)
        self.__dict__['x'] = np.zeros(ndata)


        #if(self.x == None):
        #    logger.error("Pinvertor.set_x: problem allocating memory.")
        #    return None

        for i in range(ndata):
            self.__dict__['x'][i] = data[i]

        self.__dict__['npoints'] = int(ndata)
        #self.__dict__['npoints'] = int(ndata)
        return self.npoints

    def get_x(self, args):
        """
        Function to get the x data
        Takes an array of doubles as input
        @return: number of entries found
        """
        ndata = args.shape[0]

        #check that the input array is large enough
        if (ndata < self.npoints):
            logger.error("Pinvertor.get_x: input array too short for data.")
            return None

        for i in range(self.npoints):
            args[i] = self.x[i]
        return self.npoints


    def set_y(self, args):
        """
        Function to set the y data
        Takes an array of doubles as input
        @return: number of entries found
        """

        data = np.asanyarray(args, dtype = np.float)
        #not 100% about this line
        ndata = data.shape[0]

        #reset y
        self.__dict__['y'] = np.zeros(ndata)

        #if(self.y = None):
         #   logger.error("Pinvertor.set_y: problem allocating memory.")
          #  return None

        for i in range(ndata):
            self.__dict__['y'][i] = data[i]


        self.__dict__['ny'] = int(ndata)
        return self.ny


    def get_y(self, args):
        """
        Function to get the y data
        Takes an arrayof doubles as input
        @return: number of entries found
        """
        ndata = args.shape[0]
        #check that the input array is large enough
        if (ndata < self.ny):
            logger.error("Pinvertor.get_y: input array too short for data.")
            return None

        for i in range(self.ny):
            args[i] = self.y[i]

        return self.npoints

    def set_err(self, args):
        """
        Function to set the err data
        Takes an array of doubles as input
        Returns the number of entries found
        """
        #if given an array with shape = []

        ndata = args.shape[0]

        self.__dict__['err'] = np.zeros(ndata)

        #if(self.err == None):
        #    logger.error("Pinvertor.set_err: problem allocating memory.")
        #    return None

        for i in range(ndata):
            self.__dict__['err'][i] = args[i]

        self.__dict__['nerr'] = int(ndata)
        return self.nerr


    def get_err(self, args):
        """
        Function to get the err data
        Takes an array of doubles as input.
        @return: number of entries found
        """
        ndata = args.shape[0]

        if (ndata < self.nerr):
            logger.error("Pinvertor.get_err: input array too short for data.")
            return None

        for i in range(self.nerr):
            args[i] = self.err[i]

        return self.npoints

    def set_dmax(self, args):
        """
        Sets the maximum distance
        Takes a float as input. Returns none if not a float
        if succcesful the value of d_max
        """
        #attempt to replace pyarg_parsetuple(args, "d")
        #to read as type of d, floating point number
        #if not return null
        args = float(args)

        #self.d_max = args
        self.__dict__['d_max'] = args
        return self.d_max

    def get_dmax(self):
        """
        Gets the maximum distance
        """
        return self.d_max

    def set_qmin(self, args):
        """
        Sets the minimum q.
        Input is single float, output is if succesful
        the new value of q_min
        """
        args = float(args)
        self._q_min = args
        return self._q_min

    def get_qmin(self):
        """
        Gets the minimum q
        """
        return self._q_min

    def set_qmax(self, args):
        """
        Sets the maximum q
        """
        args = float(args)

        self._q_max = args
        return self._q_max

    def get_qmax(self):
        """
        Gets the maximum q
        """
        return self._q_max

    def set_alpha(self, args):
        """
        Sets the alpha parameter.
        Takes a float, returns if succesful the
        new alpha value.
        """
        args = float(args)

        self.__dict__['alpha'] = args
        return self.alpha

    def get_alpha(self):
        """
        Gets the alpha parameter.
        """
        return self.alpha
    def set_slit_width(self, args):
        """
        Sets the slit width in units of q [A-1]
        """
        args = float(args)

        self.__dict__['slit_width'] = args
        return self.slit_width

    def get_slit_width(self):
        """
        Gets the slit width.
        """
        return self.slit_width

    def set_slit_height(self, args):
        """
        Sets the slit height in units of q [A-1]
        """
        args = float(args)

        self.__dict__['slit_height'] = args
        return self.slit_height

    def get_slit_height(self):
        """
        Gets the slit height.
        """
        return self.slit_height

    def set_est_bck(self, args):
        """
        Sets background flag.
        Takes a single int, returns est_bck value if successful
        """
        args = int(args)

        self.__dict__['est_bck'] = args
        return self.est_bck

    def get_est_bck(self):
        """
        Gets background flag.
        """
        return self.est_bck

    def get_nx(self):
        """
        Gets the number of x points
        """
        return self.npoints

    def get_ny(self):
        """
        Gets the number of y points
        """
        return self.ny

    def get_nerr(self):
        """
        Gets the number of error points
        """
        return self.nerr

    def iq(self, pars, q):
        """
        Function to call to evaluate the scattering intensity
        @param args: c-parameters, and q
        @return: I(q)
        """
        q = float(q)

        iq_val = py_invertor.iq(pars, self.d_max, q)
        return iq_val

    def get_iq_smeared(self, pars, q):
        """
        Function to call to evaluate the scattering intensity.
        The scattering intensity is slit-smeared.
        @param args: c-parameters, and q
        @return: I(q)
        """
        q = float(q)

        #npts = 21 hardcoded in Cinvertor.c
        npts = 21
        iq_val = py_invertor.iq_smeared(pars, self.d_max, self.slit_height,
                                       self.slit_width, q, npts)
        return iq_val

    def pr(self, pars, r):
        """
        Function to call to evaluate P(r)
        @param args: c-parameters and r
        @return: P(r)
        """
        r = float(r)

        pr_val = py_invertor.pr(pars, self.d_max, r)
        return pr_val

    def get_pr_err(self, pars, pars_err, r):
        """
        Function to call to evaluate P(r) with errors
        @param args: c-parameters and r
        @return: (P(r), dP(r))
        """
        r = float(r)

        pr_val = 0.0
        pr_err_val = 0.0
        (pr_val, pr_err_val) = py_invertor.pr_err(pars, pars_err, self.d_max, r)

        return (pr_val, pr_err_val)

    def is_valid(self):
        """
        Check the validity of the stored data
        @return: Returns the number of points if it's all good, -1 otherwise
        """
        if(self.npoints == self.ny and self.npoints == self.nerr):
            #Success, return number of piontspoints
            return self.npoints
        else:
            #Failure, return -1
            return -1

    def basefunc_ft(self, d_max, n, q):
        """
        Returns the value of the nth Fourier transformed base function
        @param args: c-parameters, n and q
        @return: nth Fourier transformed base function, evaluated at q
        """
        d_max = float(d_max)
        n = int(n)
        q = float(q)

        ortho_val = py_invertor.ortho_transformed(d_max, n, q)

        return ortho_val

    def oscillations(self, pars):
        """
        Returns the value of the oscillation figure of merit for
        the given set of coefficients. For a sphere, the oscillation
        figure of merit is 1.1.
        @param args:c-parameters
        @return: oscillation figure of merit
        """
        #nslice hardcoded to 100
        nslice = 100
        oscill = py_invertor.reg_term(pars, self.d_max, nslice)
        norm = py_invertor.int_p2(pars, self.d_max, nslice)
        ret_val = np.sqrt(oscill/norm) / np.arccos(-1.0) * self.d_max

        return ret_val

    def get_peaks(self, pars):
        """
        Returns the number of peaks in the output P(r) distribution
        for the given set of coefficients.
        @param args: c-parameters
        @return: number of P(r) peaks
        """
        nslice = 100
        count = py_invertor.npeaks(pars, self.d_max, nslice)

        return count

    def get_positive(self, pars):
        """
        Returns the fraction of P(r) that is positive over
        the full range of r for the given set of coefficients.
        @param args: c-parameters
        @return: fraction of P(r) that is positive
        """
        nslice = 100
        fraction = py_invertor.positive_integral(pars, self.d_max, nslice)

        return fraction

    def get_pos_err(self, pars, pars_err):
        """
        Returns the fraction of P(r) that is 1 standard deviation
        above zero over the full range of r for the given set of coefficients.
        @param args: c-parameters
        @return: fraction of P(r) that is positive
        """
        nslice = 51
        fraction = py_invertor.positive_errors(pars, pars_err, self.d_max, nslice)

        return fraction

    def rg(self, pars):
        """
        Returns the value of the radius of gyration Rg.
        @param args: c-parameters
        @return: Rg
        """
        nslice = 101
        val = py_invertor.rg(pars, self.d_max, nslice)

        return val


    def iq0(self, pars):
        """
        Returns the value of I(q=0).
        @param args: c-parameters
        @return: I(q=0)
        """
        nslice = 101
        val = 4.0 * np.arccos(-1.0) * py_invertor.int_pr(pars, self.d_max, nslice)

        return val
    def accept_q(self, q):
        """
        Check whether a q-value is within acceptable limits
        Returns 1 if accepted, 0 if rejected.
        """
        if(self.get_qmin() > 0 and q < self.get_qmin()):
            return 0
        if(self.get_qmax() > 0 and q > self.get_qmax()):
            return 0
        return 1

    def _get_matrix(self, nfunc, nr, a_obj, b_obj):
        """
        Returns A matrix and b vector for least square problem.
        @param nfunc: number of base functions
        @param nr: number of r-points used when evaluating reg term.
        @param a: A array to fill
        @param b: b vector to fill
        @return: 0
        """
        #read in input as integer, cast to integer.
        nfunc = int(nfunc)
        nr = int(nr)

        if not (b_obj.shape[0] >= nfunc):
            raise RuntimeError("Pinvertor: b vector too small.")

        if not (a_obj.size >= nfunc*(nr + self.npoints)):
            raise RuntimeError("Pinvertor: a array too small.")

        a = a_obj
        b = b_obj

        sqrt_alpha = np.sqrt(self.alpha)
        pi = np.arccos(-1.0)
        offset = (1, 0)[self.est_bck == 1]

        #instead of checking for 0 in err in for loop, check all
        #for 0 before
        def check_for_zero(x):
            for i, ni in enumerate(x):
                if(ni == 0):
                    return True
            return False

        if(check_for_zero(self.err)):
            raise RuntimeError("Pinvertor.get_matrix: Some I(Q) points have no error.")

        for j in range(nfunc):
            for i in range(self.npoints):
                npts = 21
                if(self.accept_q(self.x[i])):

                    if(self.est_bck == 1 and j == 0):
                        a[i, j] = 1.0/self.err[i]

                    else:
                        if(self.slit_width > 0 or self.slit_height > 0):
                            a[i, j] = py_invertor.ortho_transformed_smeared(self.d_max, j + offset,
                                                                             self.slit_height, self.slit_width, self.x[i], npts)/self.err[i]
                        else:
                            a[i, j] = py_invertor.ortho_transformed(self.d_max, j + offset, self.x[i])/self.err[i]

            for i_r in range(nr):
                index_i = i_r + self.npoints
                index_j = j
                if(self.est_bck == 1 and j == 0):
                    a[index_i, index_j] = 0.0
                else:
                    r = self.d_max / nr * i_r
                    tmp = pi * (j + offset) / self.d_max
                    t1 = sqrt_alpha * 1.0/nr * self.d_max * 2.0

                    t2 = (2.0 * pi * (j + offset)/self.d_max * np.cos(pi * (j + offset)*r/self.d_max)
                    + tmp * tmp * r * np.sin(pi * (j + offset)*r/self.d_max))

                    a[index_i, index_j] =  sqrt_alpha * 1.0/nr * self.d_max * 2.0 * (2.0 * pi * (j + offset)/self.d_max * np.cos(pi * (j + offset)*r/self.d_max)
                    + tmp * tmp * r * np.sin(pi * (j + offset)*r/self.d_max))

        for i in range(self.npoints):
            if(self.accept_q(self.x[i])):
                b[i] = self.y[i] / self.err[i]

        return 0
    def _get_matrix_precomputed(self, nfunc, nr, a_obj, b_obj):
        """
        Returns A matrix and b vector for least square problem.
        @param nfunc: number of base functions
        @param nr: number of r-points used when evaluating reg term.
        @param a: A array to fill
        @param b: b vector to fill
        @return: 0
        """

        nfunc = int(nfunc)
        nr = int(nr)

        assert (b_obj.shape[0] >= nfunc)
        assert (a_obj.size >= nfunc*(nr + self.npoints))

        a = a_obj
        b = b_obj

        sqrt_alpha = np.sqrt(self.alpha)
        pi = np.arccos(-1.0)
        offset = (1, 0)[self.est_bck == 1]

        #instead of checking for 0 in err in for loop, check all
        #for 0 before
        def check_for_zero(x):
            if(x.any() == 0.0):
                return True
            return False

        if(check_for_zero(self.err)):
            logger.error("Pinvertor.get_matrix: Some I(Q) points have no error.")
            return None
        #pre computed ortho_transformed_smeared -
        npts = 21
        #whether to use smeared function or ortho_transform
        smeared = (self.slit_width > 0) or (self.slit_height > 0)
        for j in range(nfunc):
            matrix = 0
            if(smeared):
                ortho_sm = np.zeros(self.npoints)
                ortho_sm = py_invertor.ortho_transformed_smeared(self.x, self.d_max, j + offset,
                                                                   self.slit_height, self.slit_width, npts)
                ortho_sm /= self.err
                matrix = ortho_sm
            else:
                ortho = np.zeros(self.npoints)
                ortho = py_invertor.ortho_transformed( self.x, self.d_max, j + offset)
                ortho /= self.err
                matrix = ortho

            for i in range(self.npoints):
                index = i * nfunc + j
                npts = 21
                if(self.accept_q(self.x[i])):

                    if(self.est_bck == 1 and j == 0):
                        a[index] = 1.0/self.err[i]

                    else:
                        a[index] = matrix[i]

            for i_r in range(nr):
                index = (i_r + self.npoints) * nfunc + j
                if(self.est_bck == 1 and j == 0):
                    a[index] = 0.0
                else:
                    r = self.d_max / nr * i_r
                    tmp = pi * (j + offset) / self.d_max
                    t1 = sqrt_alpha * 1.0/nr * self.d_max * 2.0

                    t2 = (2.0 * pi * (j + offset)/self.d_max * np.cos(pi * (j + offset)*r/self.d_max)
                    + tmp * tmp * r * np.sin(pi * (j + offset)*r/self.d_max))

                    a[index] =  t1 * t2

        for i in range(self.npoints):
            if(self.accept_q(self.x[i])):
                b[i] = self.y[i] / self.err[i]

        return 0

    def _get_invcov_matrix(self, nfunc, nr, a_obj, cov_obj):
        """
        Compute the inverse covariance matrix, defined as inv_cov = a_transposed x a.
        @param nfunc: number of base functions
        @param nr: number of r-points used when evaluating reg term.
        @param a: A array to fill
        @param inv_cov: inverse covariance array to be filled
        @return: 0
        """
        nfunc = int(nfunc)
        nr = int(nr)

        n_a = a_obj.size
        n_cov = cov_obj.size
        a = a_obj
        inv_cov = cov_obj

        if not (n_cov >= (nfunc * nfunc)):
            raise RuntimeError("Pinvertor._get_invcov_matrix: cov array too small.")

        if not (n_a >= (nfunc * (nr + self.npoints))):
            raise RuntimeError("Pinvertor._get_invcov_matrix: a array too small.")

        for i in range(nfunc):
            for j in range(nfunc):
                inv_cov[i, j] = 0.0
                for k in range(nr + self.npoints):
                    inv_cov[i, j] += a[k, i]*a[k, j]
        return 0

    def _get_reg_size(self, nfunc, nr, a_obj):
        #in Cinvertor, doc was same as invcov_matrix so for now left -
        """
        Compute the inverse covariance matrix, defined as inv_cov = a_transposed x a.
        @param nfunc: number of base functions
        @param nr: number of r-points used when evaluating reg term.
        @param a: A array to fill
        @param inv_cov: inverse covariance array to be filled
        @return: 0
        """
        #if not isinstance(nfunc, int):
        #    logger.error("Pinvertor.get_reg_size: nfunc not of type int")
        #    return None,None
        #if not isinstance(nr, int):
        #    logger.error("Pinvertor.get_reg_size: nr not of type int")
        #    return None,None
        #assert (a_obj.shape[0] >= (nfunc * (nr + self.npoints)))

        nfunc = int(nfunc)
        nr = int(nfunc)

        if not (a_obj.size >= nfunc * (nr + self.npoints)):
            raise RuntimeError("Pinvertor._get_reg_size: input array too short for data.")

        sum_sig = 0.0
        sum_reg = 0.0
        a = a_obj
        for j in range(nfunc):
            for i in range(self.npoints):
                if(self.accept_q(self.x[i]) == 1):
                    sum_sig += a[i, j] * a[i, j]
            for i in range(nr):
                sum_reg += (a[(i+self.npoints), j])*(a[(i+self.npoints), j]);
        return sum_sig, sum_reg