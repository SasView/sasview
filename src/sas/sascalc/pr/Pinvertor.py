import py_invertor
import numpy as np

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
        #regterm = reg_term(pars, )
        pass
    def set_x(self, args):
        """
        Function to set the x data
        Takes an array of the doubles as input
        Returns the number of entries found
        """
        pass
    def get_x(self, args):
        """
        Function to get the x data
        Takes an array of doubles as input
        @return: number of entries found
        """
        pass
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
    def test(self):
        print("asdf")
    def test2(self):
        Pinvertor._get_matrix(self, 34)


if(__name__ == "__main__"):
    #it = Invertor_Test()
    #it.test()
    #it.test2()
    print(reg_term(np.arange(40), 2000, 100))