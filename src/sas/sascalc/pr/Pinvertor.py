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
    slit_height = 0.0
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
        #if given an array with shape = []
        if(len(args.shape) == 0):
            return None

        data = np.asanyarray(args, dtype = np.float)

        ndata = data.shape[0]

        #reset x
        self.x = None
        self.x = np.zeros(ndata)

        #if(self.x == None):
        #    logger.error("Pinvertor.set_x: problem allocating memory.")
        #    return None

        for i in range(ndata):
            self.x[i] = data[i]

        self.npoints = int(ndata)
        return self.npoints

    def get_x(self, args):
        """
        Function to get the x data
        Takes an array of doubles as input
        @return: number of entries found
        """
        ndata = args.shape[0]

        #check that the input array is large enough
        if(ndata < self.npoints):
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
        #check for null input case
        if args is None:
            return None
        #if given an array with shape = []
        if(len(args.shape) == 0):
            return None

        data = np.asanyarray(args, dtype = np.float)
        #not 100% about this line
        ndata = data.shape[0]

        #reset y
        self.y = None
        self.y = np.zeros(ndata)

        #if(self.y = None):
         #   logger.error("Pinvertor.set_y: problem allocating memory.")
          #  return None

        for i in range(ndata):
            self.y[i] = data[i]


        self.ny = int(ndata)
        return self.ny


    def get_y(self, args):
        """
        Function to get the y data
        Takes an arrayof doubles as input
        @return: number of entries found
        """
        ndata = args.shape[0]
        #check that the input array is large enough
        if(ndata < self.ny):
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
        if(args is None):
            return None
        #if given an array with shape = []
        if(len(args.shape) == 0):
            return None

        ndata = args.shape[0]

        self.err = None
        self.err = np.zeros(ndata)

        #if(self.err == None):
        #    logger.error("Pinvertor.set_err: problem allocating memory.")
        #    return None

        for i in range(ndata):
            self.err[i] = args[i]

        self.nerr = int(ndata)
        return self.nerr


    def get_err(self, args):
        """
        Function to get the err data
        Takes an array of doubles as input.
        @return: number of entries found
        """
        ndata = args.shape[0]

        if(ndata < self.nerr):
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
        if not isinstance(args, float):
            logger.error("Pinvertor.set_dmax: input not of type float.")
            return None
        self.d_max = args

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
        if not isinstance(args, float):
            logger.error("Pinvertor.set_qmin: input not of type float.")
            return None
        self.q_min = args
        return self.q_min

    def get_qmin(self):
        """
        Gets the minimum q
        """
        return self.q_min

    def set_qmax(self, args):
        """
        Sets the maximum q
        """
        if not isinstance(args, float):
            logger.error("Pinvertor.set_qmax: input not of type float.")
            return None
        self.q_max = args
        return self.q_max

    def get_qmax(self):
        """
        Gets the maximum q
        """
        return self.q_max

    def set_alpha(self, args):
        """
        Sets the alpha parameter.
        Takes a float, returns if succesful the
        new alpha value.
        """
        if not isinstance(args, float):
            logger.error("Pinvertor.set_alpha: input not of type float.")
            return None
        self.alpha = args
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
        if not isinstance(args, float):
            logger.error("Pinvertor.set_slit_width: input not of type float.")
            return None
        self.slit_width = args
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
        if not isinstance(args, float):
            logger.error("Pinvertor.set_slit_height: input not of type float.")
            return None
        self.slit_height = args
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
        if not isinstance(args, int):
            logger.error("Pinvertor.set_est_bck: input not of type int")
            return None
        self.est_bck = args
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

    def get_iq(self, pars, q):
        """
        Function to call to evaluate the scattering intensity
        @param args: c-parameters, and q
        @return: I(q)
        """
        if not isinstance(q, float):
            logger.error("Pinvertor.get_iq: q is not a float.")
            return None

        iq_val = py_invertor.iq(pars, self.d_max, q)
        return iq_val

    def get_iq_smeared(self, pars, q):
        """
        Function to call to evaluate the scattering intensity.
        The scattering intensity is slit-smeared.
        @param args: c-parameters, and q
        @return: I(q)
        """
        if not isinstance(q, float):
            logger.error("Pinvertor.get_iq_smeared: q is not a float.")
            return None

        #npts = 21 hardcoded in Cinvertor.c
        npts = 21
        iq_val = py_invertor.iq_smeared(pars, self.d_max, self.slit_height,
                                       self.slit_width, q, npts)
        return iq_val

    def get_pr(self, pars, r):
        """
        Function to call to evaluate P(r)
        @param args: c-parameters and r
        @return: P(r)
        """
        if not isinstance(r, float):
            logger.error("Pinvertor.get_pr: r is not of type float.")
            return None

        pr_val =py_invertor.pr(pars, self.d_max, r)
        return pr_val

    def get_pr_err(self, pars, pars_err, r):
        """
        Function to call to evaluate P(r) with errors
        @param args: c-parameters and r
        @return: (P(r), dP(r))
        """
        if not isinstance(r, float):
            logger.error("Pinvertor.get_pr_err: r is not of type float")
            return None

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
        if not isinstance(d_max, float):
            logger.error("Pinvertor.basefunc_ft: d_max is not of type float.")
            return None
        if not isinstance(n, int):
            logger.error("Pinvertor.basefunc_ft: n is not of type int.")
            return None
        if not isinstance(q, float):
            logger.error("Pinvertor.basefunc_ft: q is not of type float.")
            return None
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

    def get_pos_err(self, pars):
        """
        Returns the fraction of P(r) that is 1 standard deviation
        above zero over the full range of r for the given set of coefficients.
        @param args: c-parameters
        @return: fraction of P(r) that is positive
        """
        pass
    def get_rg(self, args):
        pass
    def get_iq0(self, args):
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


if(__name__ == "__main__"):
    it = Pinvertor()
    d_max = 2000.0
    n = 21
    q = 0.5
    pars = np.arange(50)

    print(it.set_dmax(d_max))
    print(it.get_positive(pars))
    print(py_invertor.positive_integral(pars, d_max, 100))

