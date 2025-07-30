import logging
import math
import time
from copy import copy
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt
from numpy.linalg import lstsq

if TYPE_CHECKING:
    from sas.qtgui.Perspectives.Inversion.InversionLogic import InversionLogic

# TODO: Add docstrings later

# Default Values for inputs
NUMBER_OF_TERMS = 10
REGULARIZATION = 0.0
BACKGROUND_INPUT = 0.0
Q_MIN_INPUT = 0.0
Q_MAX_INPUT = 0.0
MAX_DIST = 140.0

logger = logging.getLogger(__name__)

def help():
    """
    Provide general online help text
    Future work: extend this function to allow topic selection
    """
    info_txt = "The inversion approach is based on Moore, J. Appl. Cryst. "
    info_txt += "(1980) 13, 168-175.\n\n"
    info_txt += "P(r) is set to be equal to an expansion of base functions "
    info_txt += "of the type "
    info_txt += "phi_n(r) = 2*r*sin(pi*n*r/D_max). The coefficient of each "
    info_txt += "base functions "
    info_txt += "in the expansion is found by performing a least square fit "
    info_txt += "with the "
    info_txt += "following fit function:\n\n"
    info_txt += "chi**2 = sum_i[ I_meas(q_i) - I_th(q_i) ]**2/error**2 +"
    info_txt += "Reg_term\n\n"
    info_txt += "where I_meas(q) is the measured scattering intensity and "
    info_txt += "I_th(q) is "
    info_txt += "the prediction from the Fourier transform of the P(r) "
    info_txt += "expansion. "
    info_txt += "The Reg_term term is a regularization term set to the second"
    info_txt += " derivative "
    info_txt += "d**2P(r)/dr**2 integrated over r. It is used to produce "
    info_txt += "a smooth P(r) output.\n\n"
    info_txt += "The following are user inputs:\n\n"
    info_txt += "   - Number of terms: the number of base functions in the P(r)"
    info_txt += " expansion.\n\n"
    info_txt += "   - Regularization constant: a multiplicative constant "
    info_txt += "to set the size of "
    info_txt += "the regularization term.\n\n"
    info_txt += "   - Maximum distance: the maximum distance between any "
    info_txt += "two points in the system.\n"

    return info_txt

class Invertor:

    def __init__(self, logic: "InversionLogic"):
        self.init_default_values()
        self.logic = logic

    # TODO: Add types.
    def init_default_values(self):
        ## Chisqr of the last computation
        self.chi2 = 0
        ## Time elapsed for last computation
        self.elapsed = 0
        ## Alpha to get the reg term the same size as the signal
        self.suggested_alpha = 0.0
        ## Last number of base functions used
        self.nfunc = 10
        ## Last output values
        self.out = None
        ## Last errors on output values
        self.cov = None
        ## Background value
        self.background = 0
        ## TODO: My suspicion is that this'll go.
        ## Information dictionary for application use
        self.info = {}

        # Stuff that was on p_invertor

        #Maximum distance between any two points in the system
        self.dmax = 180
        #Minimum q to include in inversion
        self.q_min = 0
        #Maximum q to include in inversion
        self.q_max = np.inf
        #Flag for whether or not to evaluate a constant background
        #while inverting
        self.est_bck = True
        # TODO: Is there a reason this is called alpha, and not just regularization.
        self.alpha = REGULARIZATION
        #Slit height in units of q [A-1]
        self.slit_height = 0.0
        #Slit width in units of q [A-1]
        self.slit_width = 0.0

        # Stuff I've added that wasn't previously in the calculator.
        self.noOfTerms = NUMBER_OF_TERMS

    @property
    def x(self) -> npt.NDArray[np.float64]:
        return self.logic.data.x

    @property
    def y(self) -> npt.NDArray[np.float64]:
        return self.logic.data.y

    @property
    def err(self) -> npt.NDArray[np.float64]:
        return self.logic.data.dy

    @property
    def npoints(self) -> int:
        return len(self.x)

    @property
    def ny(self) -> int:
        return len(self.y)

    @property
    def nerr(self) -> int:
        return len(self.err)

    def is_valid(self) -> bool:
        return self.npoints == self.ny and self.npoints == self.nerr

    def clone(self) -> "Invertor":
        return copy(self)

    def lstsq(self, nfunc=5, nr=20):
        """
        The problem is solved by posing the problem as  Ax = b,
        where x is the set of coefficients we are looking for.

        Npts is the number of points.

        In the following i refers to the ith base function coefficient.
        The matrix has its entries j in its first Npts rows set to ::

            A[i][j] = (Fourier transformed base function for point j)

        We then choose a number of r-points, n_r, to evaluate the second
        derivative of P(r) at. This is used as our regularization term.
        For a vector r of length n_r, the following n_r rows are set to ::

            A[i+Npts][j] = (2nd derivative of P(r), d**2(P(r))/d(r)**2,
            evaluated at r[j])

        The vector b has its first Npts entries set to ::

            b[j] = (I(q) observed for point j)

        The following n_r entries are set to zero.

        The result is found by using scipy.linalg.basic.lstsq to invert
        the matrix and find the coefficients x.

        :param nfunc: number of base functions to use.
        :param nr: number of r points to evaluate the 2nd derivative at for the reg. term.

        If the result does not allow us to compute the covariance matrix,
        a matrix filled with zeros will be returned.

        """
        # Note: To make sure an array is contiguous:
        # blah = np.ascontiguousarray(blah_original)
        # ... before passing it to C
        if self.is_valid() < 0:
            msg = "Invertor: invalid data; incompatible data lengths."
            raise RuntimeError(msg)

        self.nfunc = nfunc
        # a -- An M x N matrix.
        # b -- An M x nrhs matrix or M vector.
        npts = len(self.x)
        nq = nr
        sqrt_alpha = math.sqrt(math.fabs(self.alpha))
        if sqrt_alpha < 0.0:
            nq = 0

        # If we need to fit the background, add a term
        if self.est_bck:
            nfunc_0 = nfunc
            nfunc += 1

        a = np.zeros([npts + nq, nfunc])
        b = np.zeros(npts + nq)
        err = np.zeros([nfunc, nfunc])

        # Construct the a matrix and b vector that represent the problem
        t_0 = time.time()
        try:
            a, b = self._get_matrix(nfunc, nq)
        except Exception as exc:
            raise RuntimeError("Invertor: could not invert I(Q)\n  %s" % str(exc))

        # Perform the inversion (least square fit)
        # CRUFT: numpy>=1.14.0 allows rcond=None for the following default

        rcond = np.finfo(float).eps * max(a.shape)
        if rcond is None:
            rcond = -1
        c, chi2, _, _ = lstsq(a, b, rcond=rcond)
        # Sanity check
        try:
            float(chi2)
        except:
            chi2 = -1.0
        self.chi2 = chi2

        # Get the covariance matrix, defined as inv_cov = a_transposed * a
        inv_cov = self._get_invcov_matrix(nfunc, nr, a)
        # Compute the reg term size for the output
        sum_sig, sum_reg = self._get_reg_size(nfunc, nr, a)

        if self.alpha > 0:
            new_alpha = self.alpha * sum_sig / sum_reg
        else:
            new_alpha = 0.0
        self.suggested_alpha = new_alpha

        try:
            cov = np.linalg.pinv(inv_cov)
            err = math.fabs(chi2 / (npts - nfunc)) * cov
        except Exception as exc:
            # We were not able to estimate the errors
            # Return an empty error matrix
            logger.error(exc)

        # Keep a copy of the last output
        if not self.est_bck:
            self.out = c
            self.cov = err
        else:
            self.background = c[0]

            err_0 = np.zeros([nfunc, nfunc])
            c_0 = np.zeros(nfunc)

            c_0[:-1] = c[1:]
            err_0[:-1, :-1] = err[1:, 1:]

            self.out = c_0
            self.cov = err_0

        # Store computation time
        self.elapsed = time.time() - t_0

        return self.out, self.cov

    def invert(self, nfunc=10, nr=20):
        """
        Perform inversion to P(r)

        The problem is solved by posing the problem as  Ax = b,
        where x is the set of coefficients we are looking for.

        Npts is the number of points.

        In the following i refers to the ith base function coefficient.
        The matrix has its entries j in its first Npts rows set to ::

            A[i][j] = (Fourier transformed base function for point j)

        We then choose a number of r-points, n_r, to evaluate the second
        derivative of P(r) at. This is used as our regularization term.
        For a vector r of length n_r, the following n_r rows are set to ::

            A[i+Npts][j] = (2nd derivative of P(r), d**2(P(r))/d(r)**2, evaluated at r[j])

        The vector b has its first Npts entries set to ::

            b[j] = (I(q) observed for point j)

        The following n_r entries are set to zero.

        The result is found by using scipy.linalg.basic.lstsq to invert
        the matrix and find the coefficients x.

        :param nfunc: number of base functions to use.
        :param nr: number of r points to evaluate the 2nd derivative at for the reg. term.
        :return: c_out, c_cov - the coefficients with covariance matrix
        """
        # Reset the background value before proceeding
        # self.background = 0.0
        if not self.est_bck:
            self.logic.data.y -= self.background
        out, cov = self.lstsq(nfunc, nr=nr)
        if not self.est_bck:
            self.logic.data.y += self.background
        return out, cov

    def iq(self, pars, q):
        """
        Function to call to evaluate the scattering intensity.

        :param pars: c-parameters
        :param q: q, scalar or vector.

        :return: I(q)
        """
        from . import calc
        q = np.float64(q)
        pars = np.float64(pars)
        pars = np.atleast_1d(pars)
        q = np.atleast_1d(q)

        iq_val = calc.iq(pars, self.dmax, q) + self.background
        if iq_val.shape[0] == 1:
            return iq_val[0]
        return iq_val

    def get_iq_smeared(self, pars, q):
        """
        Function to call to evaluate the scattering intensity.
        The scattering intensity is slit-smeared.

        :param pars: c-parameters
        :param q: q, scalar or vector.

        :return: I(q), either scalar or vector depending on q.
        """
        from . import calc
        q = np.float64(q)
        q = np.atleast_1d(q)
        pars = np.float64(pars)


        npts = 21
        iq_val = calc.iq_smeared(pars, q, self.dmax, self.slit_height, self.slit_width, npts)
        #If q was a scalar
        if iq_val.shape[0] == 1:
            return iq_val[0]
        return iq_val

    def pr(self, pars, r):
        """
        Function to call to evaluate P(r).

        :param pars: c-parameters.
        :param r: r-value to evaluate P(r) at.

        :return: P(r)
        """
        from . import calc
        r = np.float64(r)
        pars = np.float64(pars)
        pars = np.atleast_1d(pars)
        r = np.atleast_1d(r)
        pr_val = calc.pr(pars, self.dmax, r)
        if len(pr_val) == 1:
            #scalar
            return pr_val[0]
        return pr_val

    def get_pr_err(self, pars, pars_err, r):
        """
        Function to call to evaluate P(r) with errors.

        :param pars: c-parameters.
        :param pars_err: pars_err.
        :param r: r-value.

        :return: (P(r), dP(r))
        """
        from . import calc
        pars = np.atleast_1d(np.float64(pars))
        r = np.atleast_1d(np.float64(r))

        if pars_err is None:
            return calc.pr(pars, self.dmax, r), 0.0
        else:
            pars_err = np.float64(pars_err)
            return calc.pr_err(pars, pars_err, self.dmax, r)

    def pr_err(self, c, c_cov, r):
        """
        Returns the value of P(r) for a given r, and base function
        coefficients, with error.

        :param c: base function coefficients
        :param c_cov: covariance matrice of the base function coefficients
        :param r: r-value to evaluate P(r) at

        :return: P(r)

        """
        c_cov = np.ascontiguousarray(c_cov)
        return self.get_pr_err(c, c_cov, r)

    def basefunc_ft(self, d_max, n, q):
        """
        Returns the value of the nth Fourier transformed base function.

        :param d_max: d_max.
        :param n: n.
        :param q: q, scalar or vector.

        :return: nth Fourier transformed base function, evaluated at q.
        """
        from . import calc
        d_max = np.float64(d_max)
        n = int(n)
        q = np.float64(q)
        q = np.atleast_1d(q)
        ortho_val = calc.ortho_transformed(q, d_max, n)

        if ortho_val.shape[0] == 1:
            #If the q input was scalar.
            return ortho_val[0]
        return ortho_val

    def oscillations(self, pars):
        """
        Returns the value of the oscillation figure of merit for
        the given set of coefficients. For a sphere, the oscillation
        figure of merit is 1.1.

        :param pars: c-parameters.
        :return: oscillation figure of merit.
        """
        from . import calc
        nslice = 100
        pars = np.float64(pars)
        pars = np.atleast_1d(pars)

        oscill = calc.reg_term(pars, self.dmax, nslice)
        norm = calc.int_pr_square(pars, self.dmax, nslice)
        return 0 if norm == 0 else np.sqrt(oscill/norm) / np.pi * self.dmax

    def get_peaks(self, pars):
        """
        Returns the number of peaks in the output P(r) distribution
        for the given set of coefficients.

        :param pars: c-parameters.
        :return: number of P(r) peaks.
        """
        from . import calc
        nslice = 100
        pars = np.float64(pars)
        count = calc.npeaks(pars, self.dmax, nslice)

        return count

    def get_positive(self, pars):
        """
        Returns the fraction of P(r) that is positive over
        the full range of r for the given set of coefficients.

        :param pars: c-parameters.
        :return: fraction of P(r) that is positive.
        """
        from . import calc
        nslice = 100
        pars = np.float64(pars)
        pars = np.atleast_1d(pars)
        fraction = calc.positive_integral(pars, self.dmax, nslice)

        return fraction

    def get_pos_err(self, pars, pars_err):
        """
        Returns the fraction of P(r) that is 1 standard deviation
        above zero over the full range of r for the given set of coefficients.

        :param pars: c-parameters.
        :param pars_err: pars_err.

        :return: fraction of P(r) that is positive.
        """
        from . import calc
        nslice = 51
        pars = np.float64(pars)
        pars = np.atleast_1d(pars)
        pars_err = np.float64(pars_err)
        fraction = calc.positive_errors(pars, pars_err, self.dmax, nslice)

        return fraction

    def rg(self, pars):
        """
        Returns the value of the radius of gyration Rg.

        :param pars: c-parameters.
        :return: Rg.
        """
        from . import calc
        nslice = 101
        pars = np.float64(pars)
        pars = np.atleast_1d(pars)
        val = calc.rg(pars, self.dmax, nslice)

        return val

    def iq0(self, pars):
        """
        Returns the value of I(q=0).

        :param pars: c-parameters.
        :return: I(q=0)
        """
        from . import calc
        nslice = 101
        pars = np.float64(pars)
        pars = np.atleast_1d(pars)
        val = np.float64(4.0 * np.pi * calc.int_pr(pars, self.dmax, nslice))

        return val

    def accept_q(self, q):
        """
        Check whether a q-value is within acceptable limits.

        :return: 1 if accepted, 0 if rejected.
        """
        if self.q_min <= 0 and self.q_max <= 0:
            return True
        return (q >= self.q_min) & (q <= self.q_max)

    def check_for_zero(self, x):
        return (x == 0).any()

    def estimate_numterms(self, isquit_func=None):
        """
        Returns a reasonable guess for the
        number of terms

        :param isquit_func:
          reference to thread function to call to check whether the computation needs to
          be stopped.

        :return: number of terms, alpha, message

        """
        from .num_term import NTermEstimator
        estimator = NTermEstimator(self.clone())
        try:
            return estimator.num_terms(isquit_func)
        except Exception as exc:
            # If we fail, estimate alpha and return the default
            # number of terms
            best_alpha, _, _ = self.estimate_alpha(self.nfunc)
            logger.warning("Invertor.estimate_numterms: %s" % exc)
            return self.nfunc, best_alpha, "Could not estimate number of terms"

    def estimate_alpha(self, nfunc):
        """
        Returns a reasonable guess for the
        regularization constant alpha

        :param nfunc: number of terms to use in the expansion.

        :return: alpha, message, elapsed

        where alpha is the estimate for alpha,
        message is a message for the user,
        elapsed is the computation time
        """
        #import time
        try:
            pr = self.clone()

            # T_0 for computation time
            starttime = time.time()
            elapsed = 0

            # If the current alpha is zero, try
            # another value
            if pr.alpha <= 0:
                pr.alpha = 0.0001

            # Perform inversion to find the largest alpha
            out, _ = pr.invert(nfunc)

            elapsed = time.time() - starttime
            initial_alpha = pr.alpha
            initial_peaks = pr.get_peaks(out)

            # Try the inversion with the estimated alpha
            pr.alpha = pr.suggested_alpha
            out, _ = pr.invert(nfunc)

            npeaks = pr.get_peaks(out)
            # if more than one peak to start with
            # just return the estimate
            if npeaks > 1:
                #message = "Your P(r) is not smooth,
                #please check your inversion parameters"
                message = None
                return pr.suggested_alpha, message, elapsed
            else:

                # Look at smaller values
                # We assume that for the suggested alpha, we have 1 peak
                # if not, send a message to change parameters
                alpha = pr.suggested_alpha
                best_alpha = pr.suggested_alpha
                found = False
                for i in range(10):
                    pr.alpha = (0.33) ** (i + 1) * alpha
                    out, _ = pr.invert(nfunc)

                    peaks = pr.get_peaks(out)
                    if peaks > 1:
                        found = True
                        break
                    best_alpha = pr.alpha

                # If we didn't find a turning point for alpha and
                # the initial alpha already had only one peak,
                # just return that
                if not found and initial_peaks == 1 and \
                    initial_alpha < best_alpha:
                    best_alpha = initial_alpha

                # Check whether the size makes sense
                message = ''

                if not found:
                    message = None
                elif best_alpha >= 0.5 * pr.suggested_alpha:
                    # best alpha is too big, return a
                    # reasonable value
                    message = "The estimated alpha for your system is too "
                    message += "large. "
                    message += "Try increasing your maximum distance."

                return best_alpha, message, elapsed

        except Exception as exc:
            message = "Invertor.estimate_alpha: %s" % exc
            return 0, message, elapsed

    def _get_matrix(self, nfunc, nr):
        """
        Returns A matrix and b vector for least square problem.

        :param nfunc: number of base functions.
        :param nr: number of r-points used when evaluating reg term.
        :param a: A array to fill.
        :param b: b vector to fill.

        :return: 0
        """
        from . import calc
        nfunc = int(nfunc)
        nr = int(nr)
        a_obj = np.zeros([self.npoints + nr, nfunc])
        b_obj = np.zeros(self.npoints + nr)

        sqrt_alpha = np.sqrt(math.fabs(self.alpha))
        pi = np.pi
        offset = (1, 0)[self.est_bck == 1]

        if self.check_for_zero(self.err):
            raise RuntimeError("Pinvertor.get_matrix: Some I(Q) points have no error.")

        #Compute A
        #Whether or not to use ortho_transformed_smeared.
        smeared = False
        if self.slit_width > 0 or self.slit_height > 0:
            smeared = True

        npts = 21
        #Get accept_q vector across all q.
        q_accept_x = self.accept_q(self.x)

        if isinstance(q_accept_x, bool):
            #In the case of q_min and q_max <= 0, so returns scalar, and returns True
            q_accept_x = np.ones(self.npoints, dtype=bool)
        #The x and a that will be used for the first part of 'a' calculation, given to ortho_transformed
        x_use = self.x[q_accept_x]
        a_use = a_obj[0:self.npoints, :]

        for j in range(nfunc):
            if self.est_bck == 1 and j == 0:
                a_use[q_accept_x, j] = 1.0/self.err[q_accept_x]
            elif smeared:
                a_use[q_accept_x, j] = calc.ortho_transformed_smeared(x_use, self.dmax, j+offset,
                                                                      self.slit_height, self.slit_width, npts)/self.err[q_accept_x]
            else:
                a_use[q_accept_x, j] = calc.ortho_transformed(x_use, self.dmax, j+offset)/self.err[q_accept_x]

        a_obj[0:self.npoints, :] = a_use

        for j in range(nfunc):
            i_r = np.arange(nr, dtype=np.float64)

            #Implementing second stage A as a python vector operation with shape = [nr]
            r = (self.dmax / nr) * i_r
            tmp = pi * (j+offset) / self.dmax
            res = (2.0 * sqrt_alpha * self.dmax/nr * tmp) * (2.0 * np.cos(tmp*r) + tmp * r * np.sin(tmp*r))
            #Res should now be np vector size i_r.
            a_obj[self.npoints:self.npoints+nr, j] = res

        #Compute B
        x_accept_index = self.accept_q(self.x)
        #The part of b used for the vector operations, of the accepted q values.
        b_used = b_obj[0:self.npoints]
        b_used[x_accept_index] = self.y[x_accept_index] / self.err[x_accept_index]
        b_obj[0:self.npoints] = b_used

        return a_obj, b_obj

    def _get_invcov_matrix(self, nfunc, nr, a_obj):
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
        cov_obj = np.zeros([nfunc, nfunc])
        n_a = a_obj.size
        n_cov = cov_obj.size

        if not n_a >= (nfunc * (nr + self.npoints)):
            raise RuntimeError("Pinvertor._get_invcov_matrix: a array too small.")

        size = nr + self.npoints
        cov_obj[:, :] = np.dot(a_obj.T, a_obj)
        return cov_obj

    def _get_reg_size(self, nfunc, nr, a_obj):
        """
        Computes sum_sig and sum_reg of input array given.

        :param nfunc: number of base functions.
        :param nr: number of r-points used when evaluating reg term.
        :param a_obj: Array to compute sum_sig and sum_reg of.

        :return: Tuple of (sum_sig, sum_reg)
        """
        nfunc = int(nfunc)
        nr = int(nr)

        if not a_obj.size >= nfunc * (nr + self.npoints):
            raise RuntimeError("Pinvertor._get_reg_size: input array too short for data.")

        a_pass = self.accept_q(self.x)
        a_use = a_obj[0:self.npoints, :]
        a_use = a_use[a_pass, :]
        sum_sig = np.sum(a_use ** 2)
        sum_reg = np.sum(a_obj[self.npoints:self.npoints+nr, :] ** 2)

        return sum_sig, sum_reg
