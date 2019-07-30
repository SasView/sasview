"""
Python implementation of the P(r) inversion
Pinvertor is the base class for the Invertor class
and provides the underlying computations.
"""
import sas.sascalc.pr.py_invertor as py_invertor
#import py_invertor
import numpy as np
import logging
import math
import timeit
logger = logging.getLogger(__name__)

try:
    from numba import jit, njit, vectorize, float64, guvectorize, prange, generated_jit
    USE_NUMBA = True
except ImportError:
    USE_NUMBA = False

def conditional_decorator(dec, condition):
    """
    If condition is true returns dec(func).
    Returns the function with decorator applied otherwise
    uses default.
    Called by @conditional_decorator(dec, condition)
              def():
    """
    def decorator(func):
        if not condition:
            return func
        return dec(func)
    return decorator

@conditional_decorator(njit('u8(f8, f8, f8)'), USE_NUMBA)
def accept_q(q, q_min, q_max):
    """
    Check whether a q-value is within acceptable limits.

    :return: 1 if accepted, 0 if rejected.
    """
    if(q_min > 0 and q < q_min):
        return 0
    if(q_max > 0 and q > q_max):
        return 0
    return 1

@conditional_decorator(njit('b1(f8[:])'), USE_NUMBA)
def check_for_zero(x):
    for i in range(len(x)):
        if(x[i] == 0):
            return True
    return False


class Pinvertor:
    #q data
    #x = np.empty(0, dtype = np.float64)
    #I(q) data
    #y = np.empty(0, dtype = np.float64)
    #dI(q) data
    #err = np.empty(0, dtype = np.float64)
    #Number of q points
    #npoints = 0
    #Number of I(q) points
    #ny = 0
    #Number of dI(q) points
    #nerr = 0
    #Alpha value
    #alpha = np.float64(0)
    #Slit height in units of q [A-1]
    #slit_height = np.float64(0)
    #Slit width in units of q [A-1]
    #slit_width = np.float64(0)

    def __init__(self):
        #Maximum distance between any two points in the system
        self.d_max = (180)
        #Minimum q to include in inversion
        self.q_min = -1.0
        #Maximum q to include in inversion
        self.q_max = -1.0
        #Flag for whether or not to evaluate a constant background
        #while inverting
        self.est_bck = False
        self.x = np.empty([0])
        self.y = np.empty([0])
        self.err = np.empty([0])

        self.npoints = 0
        self.nx = 0
        self.ny = 0
        self.nerr = 0
        self.alpha = 1.0
        self.slit_height = 0.0
        self.slit_width = 0.0

    def residuals(self, pars):
        """
        Function to call to evaluate the residuals for P(r) inversion.

        :param pars: input parameters.
        :return: residuals - list of residuals.
        """
        pars = np.float64(pars)

        residuals = []
        residual = 0.0
        diff = 0.0
        regterm = 0.0
        nslice = 25
        regterm = py_invertor.reg_term(pars, self.d_max, nslice)

        computed_residuals = Pinvertor._compute_residuals(self.npoints, pars, self.d_max, self.x,
                                               self.y, self.err, self.alpha, regterm)
        residuals = computed_residuals.tolist()

        return residuals

    @staticmethod
    @conditional_decorator(njit('f8[:](u8, f8[:], f8, f8[:], f8[:], f8[:], f8, f8)'), USE_NUMBA)
    def _compute_residuals(npoints, pars, d_max, x, y, err, alpha, regterm):
        ret = np.zeros(npoints)
        for i in range(npoints):
           diff = y[i] - np.float64(py_invertor.iq(pars, d_max, x[i]))
           residual = np.float64((diff*diff) / (err[i]*err[i]))
           residual += np.float64(alpha * regterm)
           ret[i] = residual

        return ret


    def pr_residuals(self, pars):
        """
        Function to call to evaluate the residuals for P(r) minimization (for testing purposes).

        :param pars: input parameters.
        :return: residuals - list of residuals.
        """
        pars = np.float64(pars)

        residuals = []
        regterm = 0.0
        nslice = 25
        regterm = py_invertor.reg_term(pars, self.d_max, nslice)

        for i in range(self.npoints):
            diff = self.y[i] - py_invertor.pr(pars, self.d_max, self.x[i])
            residual = np.float64((diff*diff) / (self.err[i]*self.err[i]))
            residual += self.float64(self.alpha * regterm)
            residuals.append(float(residual))

        return residuals

    @property
    def x(self):
        """
        Function to get the x data.

        :param data: Array to place x into
        :return: npoints - Number of entries found.
        """
        return self._x

    @x.setter
    def x(self, data):
        """
        Function to set the x data.

        :param data: Array of doubles to set x to.
        :return: npoints - Number of entries found, the size of x.
        """
        data = np.float64(data)
        ndata = len(data)

        if 0.0 in data:
            msg = "Invertor: one of your q-values is zero. "
            msg += "Delete that entry before proceeding"
            raise ValueError(msg)

        self._x = np.copy(data)
        self.npoints = int(ndata)

        return self.npoints

    @property
    def y(self):
        """
        Function to get the y data.

        :param data: Array of doubles to place y into.
        :return: npoints - Number of entries found.
        """
        return self._y

    @y.setter
    def y(self, data):
        """
        Function to set the y data.

        :param data: Array of doubles to set y to.
        :return: ny - Number of entries found.
        """
        data = np.float64(data)
        ndata = len(data)


        self._y = np.copy(data)
        self.ny = int(ndata)

        return self.ny

    @property
    def err(self):
        """
        Function to get the err data.

        :param data: Array of doubles to place err into.
        :return: npoints - number of entries found
        """
        return self._err


    @err.setter
    def err(self, data):
        """
        Function to set the err data.

        :param data: Array of doubles to set err to.
        :return: nerr - Number of entries found.
        """
        data = abs(data)
        ndata = len(data)

        self._err = np.copy(data)
        self._nerr = int(ndata)

        return self._nerr

    @property
    def d_max(self):
        """
        Gets the maximum distance.

        :return: d_max.
        """
        return self._d_max


    @d_max.setter
    def d_max(self, d_max):
        """
        Sets the maximum distance.

        :param d_max: float to set d_max to.
        :return: d_max
        """
        if d_max <= 0.0:
            msg = "Invertor: d_max must be greater than zero."
            msg += "Correct that entry before proceeding"
            raise ValueError(msg)
        self._d_max = np.float64(d_max)

        return self._d_max

    @property
    def q_min(self):
        """
        Gets the minimum q.

        :return: q_min.
        """
        #if self._qmin < 0:
        #    return None
        return self._qmin


    @q_min.setter
    def q_min(self, min_q):
        """
        Sets the minimum q.

        :param min_q: float to set q_min to.
        :return: q_min.
        """
        if min_q is None:
            self._qmin = np.float64(-1.0)
        else:
            self._qmin = np.float64(min_q)
        return self._qmin

    @property
    def q_max(self):
        """
        Gets the maximum q.

        :return: q_max.
        """
        #if self._qmax < 0:
        #    return None
        return self._qmax


    @q_max.setter
    def q_max(self, max_q):
        """
        Sets the maximum q.

        :param max_q: float to set q_max to.
        :return: q_max.
        """
        if max_q is None:
            self._qmax = np.float64(-1.0)
        else:
            self._qmax = np.float64(max_q)
        return self._qmax

    @property
    def alpha(self):
        """
        Gets the alpha parameter.

        :return: alpha.
        """
        return self._alpha


    @alpha.setter
    def alpha(self, alpha):
        """
        Sets the alpha parameter.

        :param alpha_: float to set alpha to.
        :return: alpha.
        """
        self._alpha = np.float64(alpha)
        return self._alpha

    @property
    def slit_width(self):
        """
        Gets the slit width.

        :return: slit_width.
        """
        return self._slit_width

    @slit_width.setter
    def slit_width(self, slit_width):
        """
        Sets the slit width in units of q [A-1].

        :param slit_width: float to set slit_width to.
        :return: slit_width.
        """
        self._slit_width = np.float64(slit_width)
        return self._slit_width

    @property
    def slit_height(self):
        """
        Gets the slit height.

        :return: slit_height.
        """
        return self._slit_height


    @slit_height.setter
    def slit_height(self, slit_height):
        """
        Sets the slit height in units of q [A-1].

        :param slit_height: float to set slit-height to.
        :return: slit_height.
        """
        self._slit_height = np.float64(slit_height)
        return self._slit_height

    @property
    def est_bck(self):
        """
        Gets background flag.

        :return: est_bck.
        """
        return (self._est_bck == 1)

    @est_bck.setter
    def est_bck(self, est_bck):
        """
        Sets background flag.

        :param est_bck: int to set est_bck to.
        :return: est_bck.
        """
        if est_bck == True:
            self._est_bck = 1
        elif est_bck == False:
            self._est_bck = 0
        else:
            raise ValueError("Invertor: est_bck can only be True or False")

        return self._est_bck


    @property
    def nx(self):
        """
        Gets the number of x points.

        :return: npoints.
        """
        return self._npoints

    @nx.setter
    def nx(self, nx):
        self._npoints = int(nx)

    @property
    def ny(self):
        """
        Gets the number of y points.

        :return: ny.
        """
        return self._ny

    @ny.setter
    def ny(self, ny):
        self._ny = int(ny)

    @property
    def nerr(self):
        """
        Gets the number of error points.

        :return: nerr.
        """
        return self._nerr

    @nerr.setter
    def nerr(self, nerr):
        self._nerr = int(nerr)

    #Legacy get_ and set_ support to pass tests.
    def set_dmax(self, data):
        self.d_max = data

    def get_dmax(self):
        return self.d_max

    def get_nx(self):
        return self.nx

    def get_qmin(self):
        return self.q_min

    def set_qmin(self, data):
        self.q_min = data

    def get_x(self):
        return self.x

    #support old way of getting x
    def get_x(self, data):
        data = self.x

    def get_qmax(self):
        return self.q_max

    def get_y(self, data):
        data = self.x

    def set_dmax(self, value):
        self.d_max = value
    def set_qmin(self, value):
        self.q_min = value
    def set_qmax(self, value):
        self.q_max = value

    def set_alpha(self, value):
        self.alpha = value

    def set_slit_height(self, value):
        self.slit_height = value

    def set_slit_width(self, value):
        self.slit_width = value
    def set_x(self, value):
        self.x = value
    def set_y(self, value):
        self.y = value
    def set_err(self, value):
        self.err = value


    def iq(self, pars, q):
        """
        Function to call to evaluate the scattering intensity.

        :param pars: c-parameters
        :param q: q.

        :return: I(q)
        """
        q = np.float64(q)
        pars = np.float64(pars)
        pars = np.atleast_1d(pars)

        iq_val = py_invertor.iq(pars, self.d_max, q)
        return iq_val

    def get_iq_smeared(self, pars, q):
        """
        Function to call to evaluate the scattering intensity.
        The scattering intensity is slit-smeared.

        :param pars: c-parameters
        :param q: q, scalar or vector.

        :return: I(q), either scalar or vector depending on q.
        """
        q = np.atleast_1d(q)
        pars = np.float64(pars)
        q = np.float64(q)

        npts = 21
        iq_val = py_invertor.iq_smeared_qvec_njit(pars, q, np.float64(self.d_max), self.slit_height,
                                       self.slit_width, npts)
        #If q was a scalar
        if(iq_val.shape[0] == 1):
            return np.asscalar(iq_val)
        return iq_val

    def pr(self, pars, r):
        """
        Function to call to evaluate P(r).

        :param pars: c-parameters.
        :param r: r-value to evaluate P(r) at.

        :return: P(r)
        """
        r = np.float64(r)
        pars = np.float64(pars)
        pars = np.atleast_1d(pars)
        pr_val = py_invertor.pr(pars, self.d_max, r)

        return pr_val

    def get_pr_err(self, pars, pars_err, r):
        """
        Function to call to evaluate P(r) with errors.

        :param pars: c-parameters
        :param pars_err: pars_err.
        :param r: r-value.

        :return: (P(r), dP(r))
        """
        pars = np.atleast_1d(pars)
        pars_err = np.atleast_2d(pars_err)
        pars = np.float64(pars)
        pars_err = np.float64(pars_err)
        r = np.float64(r)

        pr_val = 0.0
        pr_err_val = 0.0
        result = np.zeros(2, dtype = np.float64)

        if(pars_err is None):
            pr_val = np.float64(pr(pars, self.d_max, r))
            pr_err_value = 0.0
            result[0] = pr_val
            result[1] = pr_err_value
        else:
            result = py_invertor.pr_err(pars, pars_err, self.d_max, r)

        return (result[0], result[1])

    def is_valid(self):
        """
        Check the validity of the stored data.

        :return: Returns the number of points if it's all good, -1 otherwise.
        """
        if(self.npoints == self.ny and self.npoints == self.nerr):
            return self.npoints
        else:
            return -1

    def basefunc_ft(self, d_max, n, q):
        """
        Returns the value of the nth Fourier transformed base function.

        :param d_max: d_max.
        :param n: n.
        :param q: q.

        :return: nth Fourier transformed base function, evaluated at q.
        """
        d_max = np.float64(d_max)
        n = int(n)
        q = np.float64(q)
        ortho_val = py_invertor.ortho_transformed(d_max, n, q)

        return ortho_val

    def oscillations(self, pars):
        """
        Returns the value of the oscillation figure of merit for
        the given set of coefficients. For a sphere, the oscillation
        figure of merit is 1.1.

        :param pars: c-parameters.
        :return: oscillation figure of merit.
        """
        nslice = 100
        pars = np.float64(pars)
        pars = np.atleast_1d(pars)

        oscill = py_invertor.reg_term(pars, self.d_max, nslice)
        norm = py_invertor.int_p2(pars, self.d_max, nslice)
        ret_val = np.float64(np.sqrt(oscill/norm) / np.arccos(-1.0) * self.d_max)

        return ret_val

    def get_peaks(self, pars):
        """
        Returns the number of peaks in the output P(r) distribution
        for the given set of coefficients.

        :param pars: c-parameters.
        :return: number of P(r) peaks.
        """
        nslice = 100
        pars = np.float64(pars)
        pars = np.atleast_1d(pars)
        count = py_invertor.npeaks(pars, self.d_max, nslice)

        return count

    def get_positive(self, pars):
        """
        Returns the fraction of P(r) that is positive over
        the full range of r for the given set of coefficients.

        :param pars: c-parameters.
        :return: fraction of P(r) that is positive.
        """
        nslice = 100
        pars = np.float64(pars)
        pars = np.atleast_1d(pars)
        fraction = py_invertor.positive_integral(pars, self.d_max, nslice)

        return fraction

    def get_pos_err(self, pars, pars_err):
        """
        Returns the fraction of P(r) that is 1 standard deviation
        above zero over the full range of r for the given set of coefficients.

        :param pars: c-parameters.
        :param pars_err: pars_err.

        :return: fraction of P(r) that is positive.
        """
        nslice = 51
        pars = np.float64(pars)
        pars_err = np.float64(pars_err)
        fraction = py_invertor.positive_errors(pars, pars_err, self.d_max, nslice)

        return fraction

    def rg(self, pars):
        """
        Returns the value of the radius of gyration Rg.

        :param pars: c-parameters.
        :return: Rg.
        """
        nslice = 101
        pars = np.float64(pars)
        val = py_invertor.rg(pars, self.d_max, nslice)

        return val


    def iq0(self, pars):
        """
        Returns the value of I(q=0).

        :param pars: c-parameters.
        :return: I(q=0)
        """
        nslice = 101
        pars = np.float64(pars)
        val = 4.0 * np.arccos(-1.0) * py_invertor.int_pr(pars, self.d_max, nslice)

        return val

    @staticmethod
    @conditional_decorator(njit('f8[:,:](f8[:,:], u8, u8, u8, f8, f8, f8, u8, f8[:], f8[:], u8, f8, f8, f8, f8)'), USE_NUMBA)
    def _compute_a(a, nfunc, nr, offset, pi, sqrt_alpha, d_max, npoints, x, err, est_bck, slit_height, slit_width, q_min, q_max):
        smeared = False
        if(slit_width > 0 or slit_height > 0):
            smeared = True

        for j in range(nfunc):
            npts = 21
            if(smeared):
                precompute_ortho_smeared = py_invertor.ortho_transformed_smeared_qvec_njit(x, d_max, j + offset,
                                                                                slit_height, slit_width, npts)/err
            else:
                precompute_ortho = py_invertor.ortho_transformed_qvec_njit(x, d_max, j + offset) / err

            for i in range(npoints):
                if(accept_q(x[i], q_min, q_max) == 1):
                    if(est_bck == 1 and j == 0):
                        a[i, j] = (1.0/err[i])
                    else:
                        if(smeared):
                            a[i, j] = precompute_ortho_smeared[i]
                        else:
                            a[i, j] = precompute_ortho[i]

            for i_r in range(nr):
                index_i = i_r + npoints
                index_j = j
                if(est_bck == 1 and j == 0):
                    a[index_i, index_j] = 0.0
                else:
                    r = d_max / nr * i_r
                    tmp = np.float64(pi * (j+offset) / d_max)
                    t1 = np.float64(sqrt_alpha * 1.0/nr * d_max * 2.0)
                    t2 = np.float64((2.0 * pi * (j+offset)/d_max * np.cos(pi * (j+offset)*r/d_max)
                    + tmp * tmp * r * np.sin(pi * (j+offset)*r/d_max)))
                    a[index_i, index_j] =  np.float64(t1 * t2)
        return a

    @staticmethod
    @conditional_decorator(njit('f8[:](f8[:], f8[:], f8[:], f8[:], u8, f8, f8)'), USE_NUMBA)
    def _compute_b(b, x, y, err, npoints, q_min, q_max):
        for i in range(npoints):
            if(accept_q(x[i], q_min, q_max)):
                b[i] = np.float64(y[i] / err[i])
        return b

    def _get_matrix(self, nfunc, nr, a_obj, b_obj):
        """
        Returns A matrix and b vector for least square problem.

        :param nfunc: number of base functions.
        :param nr: number of r-points used when evaluating reg term.
        :param a: A array to fill.
        :param b: b vector to fill.

        :return: 0
        """
        nfunc = int(nfunc)
        nr = int(nr)
        a_obj = np.float64(a_obj)
        b_obj = np.float64(b_obj)

        if not (b_obj.shape[0] >= nfunc):
            raise RuntimeError("Pinvertor: b vector too small.")

        if not (a_obj.size >= nfunc*(nr + self.npoints)):
            raise RuntimeError("Pinvertor: a array too small.")

        a = np.float64(a_obj)
        b = np.float64(b_obj)

        sqrt_alpha = np.sqrt(self.alpha)
        pi = np.arccos(-1.0)
        offset = (1, 0)[self.est_bck == 1]

        #Compute zero error case.
        #def check_for_zero(x):
        #    for i, ni in enumerate(x):
        #        if(ni == 0):
        #            return True
        #    return False

        if(check_for_zero(self.err)):
            raise RuntimeError("Pinvertor.get_matrix: Some I(Q) points have no error.")
        #d_max, npoints, x, err, est_bck, slit_height, slit_width):
        a = Pinvertor._compute_a(a, nfunc, nr, offset, pi, sqrt_alpha, self.d_max, self.nx, self.x, self.err, self.est_bck, self.slit_height, self.slit_width, self.q_min, self.q_max)
        b = Pinvertor._compute_b(b, self.x, self.y, self.err, self.npoints, self.q_min, self.q_max)
        #_compute_b(b, x, y, err, npoints, q_min, q_max)
        return 0


    def _get_invcov_matrix(self, nfunc, nr, a_obj, cov_obj):
        """
        Compute the inverse covariance matrix, defined as inv_cov = a_transposed x a.

        :param nfunc: number of base functions.
        :param nr: number of r-points used when evaluating reg term.
        :param a: A array to fill.
        :param inv_cov: inverse covariance array to be filled.

        :return: 0
        """
        nfunc = int(nfunc)
        nr = int(nr)
        a_obj = np.float64(a_obj)
        cov_obj = np.float64(cov_obj)
        n_a = a_obj.size
        n_cov = cov_obj.size
        a = a_obj
        inv_cov = cov_obj

        if not (n_cov >= (nfunc * nfunc)):
            raise RuntimeError("Pinvertor._get_invcov_matrix: cov array too small.")

        if not (n_a >= (nfunc * (nr + self.npoints))):
            raise RuntimeError("Pinvertor._get_invcov_matrix: a array too small.")

        size = nr + self.npoints
        #Pinvertor._compute_invcov(a, inv_cov, size, nfunc)
        for i in range(nfunc):
            for j in range(nfunc):
                inv_cov[i, j] = 0.0
                for k in range(nr + self.npoints):
                    inv_cov[i, j] += np.float64(a[k, i]*a[k, j])
        return 0

    @staticmethod
    def _compute_invcov(a, inv_cov, size, nfunc):
        #reset to 0
        for i in range(nfunc):
            for j in range(nfunc):
                inv_cov[i, j] = np.float64(np.sum((a[:, i] * a[:, j])))
        return 0



    def _get_reg_size(self, nfunc, nr, a_obj):
        #in Cinvertor, doc was same as invcov_matrix, left for now -
        """
        Compute the covariance matrix, defined as inv_cov = a_transposed x a.
	    :param nfunc: number of base functions.
	    :param nr: number of r-points used when evaluating reg term.
	    :param a: A array to fill.
	    :param inv_cov: inverse covariance array to be filled.

        :return: 0
        """
        nfunc = int(nfunc)
        nr = int(nfunc)
        a_obj = np.float64(a_obj)
        if not (a_obj.size >= nfunc * (nr + self.npoints)):
            raise RuntimeError("Pinvertor._get_reg_size: input array too short for data.")

        sum_sig = 0.0
        sum_reg = 0.0
        a = a_obj

        for j in range(nfunc):
            for i in range(self.npoints):
                if(accept_q(self.x[i], np.float64(self.q_min), np.float64(self.q_max)) == 1):
                    sum_sig += np.float64(a[i, j] * a[i, j])
            for i in range(nr):
                sum_reg += np.float64((a[(i+self.npoints), j]) * (a[(i+self.npoints), j]))

        return sum_sig, sum_reg




if(__name__ == "__main__"):
    test = Pinvertor()
    test.est_bck = 2
    print(test.est_bck)
    print("asdf")
    test.x = np.arange(300, dtype = int) + 9
    print(test.x)