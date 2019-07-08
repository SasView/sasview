"""
Under Development-
Class duplicating Cinvertor.c's functionality in Python
depends on py_invertor.py as a pose to invertor.c
"""
import py_invertor
import numpy as np
import logging

logger = logging.getLogger(__name__)

class Pinvertor:
    #class variables, from internal data structure P(r) inversion
    #invertor.h
    #Maximum distance between any two points in the system
    d_max = 0.0
    #q data
    x = np.empty([], dtype = np.float)
    #I(q) data
    y = np.empty([], dtype = np.float)
    #dI(q) data
    err = np.empty([], dtype = np.float)
    #Number of q points
    npoints = 0
    #Number of I(q) points
    ny = 0
    #Number of dI(q) points
    nerr = 0
    #Alpha value
    alpha = 0.0
    #Minimum q to include in inversion
    q_min = 0.0
    #Maximum q to include in inversion
    q_max = 0.0
    #Flag for whether or not to evaluate a constant background
    #while inverting
    est_bck = 0
    #Slit height in units of q [A-1]
    slight_height = 0.0
    #Slit width in units of q [A-1]
    slit_width = 0.0

    def __init__(self):
        pass
    def residuals(self, args):
        """
        Function to call to evaluate the residuals\n
	    for P(r) inversion\n
	    @param args: input parameters\n
	    @return: list of residuals
        """
        #May not be correct, initial version
        #check for null case
        if args is None:
            return None

        residuals = []

        pars = np.asanyarray(args, dtype = np.float)

        residual = 0.0
        diff = 0.0
        regterm = 0.0
        nslice = 25
        regterm = reg_term(pars, d_max, nslice)

        for i in range(self.npoints):
            diff = y[i] - iq(pars, d_max, x[i])
            residual = diff*diff / (err[i] * err[i])

            residual += alpha * regterm
            try:
                residuals.append(residual)
            except:
                logger.error("Pinvertor.residuals: error setting residual.")

        return residuals
    def set_x(self, args):
        """
        Function to set the x data
        Takes an array of the doubles as input
        Returns the number of entries found
        """
        #check for null input case
        if args is None:
            return None

        data = np.asanyarray(args, dtype = np.float)
        #not 100% about this line
        ndata = data.shape[0]

        #try to set every element in x to data input
        #try:
        self.x = np.ones(20)
        for i in range(ndata):
            self.x[i] = data[i]
        #except:
         #   logger.error("Pinvertor.set_x: problem allocating memory.")
          #  return None

        self.npoints = int(ndata)
        return self.npoints

    def get_x(self, args):
        """
        Function to get the x data
        Takes an array of doubles as input
        @return: number of entries found
        """
        if args is None:
            return None


        data = np.asanyarray(args, dtype = np.float)
        ndata = data.shape[0]

        #Check that the input array is large enough

        if(ndata < self.npoints):
            logger.error("Pinvertor.get_x: input array too short for data. ")
            return None

        for i in range(self.npoints):
            data[i] = self.x[i]

        return self.npoints


    def set_y(self, args):
        """
        Function to set the y data
        Takes an array of doubles as input
        @return: number of entries found
        """
        pass
    def get_y(self, args):
        """
        Function to get the y data
        Takes an arrayof doubles as input
        @return: number of entries found
        """
        pass
    def set_err(self, args):
        """
        Function to set the err data
        Takes an array of doubles as input
        Returns the number of entries found
        """
        pass
    def get_err(self, args):
        pass
    def set_dmax(self, args):
        pass
    def get_dmax(self, args):
        pass
    def set_qmin(self, args):
        pass
    def get_qmin(self, args):
        pass
    def set_qmax(self, args):
        pass
    def get_qmax(self, args):
        pass
    def set_alpha(self, args):
        pass
    def get_alpha(self, args):
        pass
    def set_slit_width(self, args):
        pass
    def get_slit_width(self, args):
        pass
    def set_slit_height(self, args):
        pass
    def get_slit_height(self, args):
        pass
    def set_est_bck(self, args):
        pass
    def get_est_bck(self, args):
        pass
    def get_nx(self, args):
        pass
    def get_ny(self, args):
        pass
    def get_nerr(self, args):
        pass
    def iq(self, args):
        pass
    def iq_smeared(self, args):
        pass
    def pr(self, args):
        pass
    def get_pr_err(self, args):
        pass
    def is_valid(self, args):
        pass
    def basefunc_ft(self, args):
        pass
    def oscillations(self, args):
        pass
    def get_peaks(self, args):
        pass
    def get_positive(self, args):
        pass
    def get_pos_err(self, args):
        pass
    def rg(self, args):
        pass
    def iq0(self, args):
        pass
    def _get_matrix(self, args):
        pass
    def _get_invcov_matrix(self, args):
        pass
    def _get_reg_size(self, args):
        pass

class Invertor_Test(Pinvertor):
    def __init__(self):
        Pinvertor.__init__(self)
    def set_x(self):
        return Pinvertor.set_x(self, np.arange(20))
    def get_x(self):
        return Pinvertor.get_x(self, np.empty([20]))


if(__name__ == "__main__"):
    it = Invertor_Test()
    print(it.set_x())
    print(it.get_x())