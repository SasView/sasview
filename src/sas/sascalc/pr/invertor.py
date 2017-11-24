# pylint: disable=invalid-name
"""
Module to perform P(r) inversion.
The module contains the Invertor class.

FIXME: The way the Invertor interacts with its C component should be cleaned up
"""

import numpy as np
import sys
import math
import time
import copy
import os
import re
import logging
from numpy.linalg import lstsq
from scipy import optimize
from sas.sascalc.pr.core.pr_inversion import Cinvertor

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


class Invertor(Cinvertor):
    """
    Invertor class to perform P(r) inversion

    The problem is solved by posing the problem as  Ax = b,
    where x is the set of coefficients we are looking for.

    Npts is the number of points.

    In the following i refers to the ith base function coefficient.
    The matrix has its entries j in its first Npts rows set to ::

        A[j][i] = (Fourier transformed base function for point j)

    We them choose a number of r-points, n_r, to evaluate the second
    derivative of P(r) at. This is used as our regularization term.
    For a vector r of length n_r, the following n_r rows are set to ::

        A[j+Npts][i] = (2nd derivative of P(r), d**2(P(r))/d(r)**2,
        evaluated at r[j])

    The vector b has its first Npts entries set to ::

        b[j] = (I(q) observed for point j)

    The following n_r entries are set to zero.

    The result is found by using scipy.linalg.basic.lstsq to invert
    the matrix and find the coefficients x.

    Methods inherited from Cinvertor:

    * ``get_peaks(pars)``: returns the number of P(r) peaks
    * ``oscillations(pars)``: returns the oscillation parameters for the output P(r)
    * ``get_positive(pars)``: returns the fraction of P(r) that is above zero
    * ``get_pos_err(pars)``: returns the fraction of P(r) that is 1-sigma above zero
    """
    ## Chisqr of the last computation
    chi2 = 0
    ## Time elapsed for last computation
    elapsed = 0
    ## Alpha to get the reg term the same size as the signal
    suggested_alpha = 0
    ## Last number of base functions used
    nfunc = 10
    ## Last output values
    out = None
    ## Last errors on output values
    cov = None
    ## Background value
    background = 0
    ## Information dictionary for application use
    info = {}

    def __init__(self):
        Cinvertor.__init__(self)

    def __setstate__(self, state):
        """
        restore the state of invertor for pickle
        """
        (self.__dict__, self.alpha, self.d_max,
         self.q_min, self.q_max,
         self.x, self.y,
         self.err, self.est_bck,
         self.slit_height, self.slit_width) = state

    def __reduce_ex__(self, proto):
        """
        Overwrite the __reduce_ex__
        """

        state = (self.__dict__,
                 self.alpha, self.d_max,
                 self.q_min, self.q_max,
                 self.x, self.y,
                 self.err, self.est_bck,
                 self.slit_height, self.slit_width,
                )
        return (Invertor, tuple(), state, None, None)

    def __setattr__(self, name, value):
        """
        Set the value of an attribute.
        Access the parent class methods for
        x, y, err, d_max, q_min, q_max and alpha
        """
        if   name == 'x':
            if 0.0 in value:
                msg = "Invertor: one of your q-values is zero. "
                msg += "Delete that entry before proceeding"
                raise ValueError(msg)
            return self.set_x(value)
        elif name == 'y':
            return self.set_y(value)
        elif name == 'err':
            value2 = abs(value)
            return self.set_err(value2)
        elif name == 'd_max':
            if value <= 0.0:
                msg = "Invertor: d_max must be greater than zero."
                msg += "Correct that entry before proceeding"
                raise ValueError(msg)
            return self.set_dmax(value)
        elif name == 'q_min':
            if value is None:
                return self.set_qmin(-1.0)
            return self.set_qmin(value)
        elif name == 'q_max':
            if value is None:
                return self.set_qmax(-1.0)
            return self.set_qmax(value)
        elif name == 'alpha':
            return self.set_alpha(value)
        elif name == 'slit_height':
            return self.set_slit_height(value)
        elif name == 'slit_width':
            return self.set_slit_width(value)
        elif name == 'est_bck':
            if value == True:
                return self.set_est_bck(1)
            elif value == False:
                return self.set_est_bck(0)
            else:
                raise ValueError("Invertor: est_bck can only be True or False")

        return Cinvertor.__setattr__(self, name, value)

    def __getattr__(self, name):
        """
        Return the value of an attribute
        """
        #import numpy
        if name == 'x':
            out = np.ones(self.get_nx())
            self.get_x(out)
            return out
        elif name == 'y':
            out = np.ones(self.get_ny())
            self.get_y(out)
            return out
        elif name == 'err':
            out = np.ones(self.get_nerr())
            self.get_err(out)
            return out
        elif name == 'd_max':
            return self.get_dmax()
        elif name == 'q_min':
            qmin = self.get_qmin()
            if qmin < 0:
                return None
            return qmin
        elif name == 'q_max':
            qmax = self.get_qmax()
            if qmax < 0:
                return None
            return qmax
        elif name == 'alpha':
            return self.get_alpha()
        elif name == 'slit_height':
            return self.get_slit_height()
        elif name == 'slit_width':
            return self.get_slit_width()
        elif name == 'est_bck':
            value = self.get_est_bck()
            if value == 1:
                return True
            else:
                return False
        elif name in self.__dict__:
            return self.__dict__[name]
        return None

    def clone(self):
        """
        Return a clone of this instance
        """
        #import copy

        invertor = Invertor()
        invertor.chi2 = self.chi2
        invertor.elapsed = self.elapsed
        invertor.nfunc = self.nfunc
        invertor.alpha = self.alpha
        invertor.d_max = self.d_max
        invertor.q_min = self.q_min
        invertor.q_max = self.q_max

        invertor.x = self.x
        invertor.y = self.y
        invertor.err = self.err
        invertor.est_bck = self.est_bck
        invertor.background = self.background
        invertor.slit_height = self.slit_height
        invertor.slit_width = self.slit_width

        invertor.info = copy.deepcopy(self.info)

        return invertor

    def invert(self, nfunc=10, nr=20):
        """
        Perform inversion to P(r)

        The problem is solved by posing the problem as  Ax = b,
        where x is the set of coefficients we are looking for.

        Npts is the number of points.

        In the following i refers to the ith base function coefficient.
        The matrix has its entries j in its first Npts rows set to ::

            A[i][j] = (Fourier transformed base function for point j)

        We them choose a number of r-points, n_r, to evaluate the second
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
            self.y -= self.background
        out, cov = self.lstsq(nfunc, nr=nr)
        if not self.est_bck:
            self.y += self.background
        return out, cov

    def iq(self, out, q):
        """
        Function to call to evaluate the scattering intensity

        :param args: c-parameters, and q
        :return: I(q)

        """
        return Cinvertor.iq(self, out, q) + self.background

    def invert_optimize(self, nfunc=10, nr=20):
        """
        Slower version of the P(r) inversion that uses scipy.optimize.leastsq.

        This probably produce more reliable results, but is much slower.
        The minimization function is set to
        sum_i[ (I_obs(q_i) - I_theo(q_i))/err**2 ] + alpha * reg_term,
        where the reg_term is given by Svergun: it is the integral of
        the square of the first derivative
        of P(r), d(P(r))/dr, integrated over the full range of r.

        :param nfunc: number of base functions to use.
        :param nr: number of r points to evaluate the 2nd derivative at
            for the reg. term.

        :return: c_out, c_cov - the coefficients with covariance matrix

        """
        self.nfunc = nfunc
        # First, check that the current data is valid
        if self.is_valid() <= 0:
            msg = "Invertor.invert: Data array are of different length"
            raise RuntimeError(msg)

        p = np.ones(nfunc)
        t_0 = time.time()
        out, cov_x, _, _, _ = optimize.leastsq(self.residuals, p, full_output=1)

        # Compute chi^2
        res = self.residuals(out)
        chisqr = 0
        for i in range(len(res)):
            chisqr += res[i]

        self.chi2 = chisqr

        # Store computation time
        self.elapsed = time.time() - t_0

        if cov_x is None:
            cov_x = np.ones([nfunc, nfunc])
            cov_x *= math.fabs(chisqr)
        return out, cov_x

    def pr_fit(self, nfunc=5):
        """
        This is a direct fit to a given P(r). It assumes that the y data
        is set to some P(r) distribution that we are trying to reproduce
        with a set of base functions.

        This method is provided as a test.
        """
        # First, check that the current data is valid
        if self.is_valid() <= 0:
            msg = "Invertor.invert: Data arrays are of different length"
            raise RuntimeError(msg)

        p = np.ones(nfunc)
        t_0 = time.time()
        out, cov_x, _, _, _ = optimize.leastsq(self.pr_residuals, p, full_output=1)

        # Compute chi^2
        res = self.pr_residuals(out)
        chisqr = 0
        for i in range(len(res)):
            chisqr += res[i]

        self.chisqr = chisqr

        # Store computation time
        self.elapsed = time.time() - t_0

        return out, cov_x

    def pr_err(self, c, c_cov, r):
        """
        Returns the value of P(r) for a given r, and base function
        coefficients, with error.

        :param c: base function coefficients
        :param c_cov: covariance matrice of the base function coefficients
        :param r: r-value to evaluate P(r) at

        :return: P(r)

        """
        return self.get_pr_err(c, c_cov, r)

    def _accept_q(self, q):
        """
        Check q-value against user-defined range
        """
        if self.q_min is not None and q < self.q_min:
            return False
        if self.q_max is not None and q > self.q_max:
            return False
        return True

    def lstsq(self, nfunc=5, nr=20):
        """
        The problem is solved by posing the problem as  Ax = b,
        where x is the set of coefficients we are looking for.

        Npts is the number of points.

        In the following i refers to the ith base function coefficient.
        The matrix has its entries j in its first Npts rows set to ::

            A[i][j] = (Fourier transformed base function for point j)

        We them choose a number of r-points, n_r, to evaluate the second
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
        if self.est_bck == True:
            nfunc_0 = nfunc
            nfunc += 1

        a = np.zeros([npts + nq, nfunc])
        b = np.zeros(npts + nq)
        err = np.zeros([nfunc, nfunc])

        # Construct the a matrix and b vector that represent the problem
        t_0 = time.time()
        try:
            self._get_matrix(nfunc, nq, a, b)
        except Exception as exc:
            raise RuntimeError("Invertor: could not invert I(Q)\n  %s" % str(exc))

        # Perform the inversion (least square fit)
        c, chi2, _, _ = lstsq(a, b)
        # Sanity check
        try:
            float(chi2)
        except:
            chi2 = [-1.0]
        self.chi2 = chi2

        inv_cov = np.zeros([nfunc, nfunc])
        # Get the covariance matrix, defined as inv_cov = a_transposed * a
        self._get_invcov_matrix(nfunc, nr, a, inv_cov)

        # Compute the reg term size for the output
        sum_sig, sum_reg = self._get_reg_size(nfunc, nr, a)

        if math.fabs(self.alpha) > 0:
            new_alpha = sum_sig / (sum_reg / self.alpha)
        else:
            new_alpha = 0.0
        self.suggested_alpha = new_alpha

        try:
            cov = np.linalg.pinv(inv_cov)
            err = math.fabs(chi2 / float(npts - nfunc)) * cov
        except Exception as ex:
            # We were not able to estimate the errors
            # Return an empty error matrix
            logger.error(ex)

        # Keep a copy of the last output
        if self.est_bck == False:
            self.out = c
            self.cov = err
        else:
            self.background = c[0]

            err_0 = np.zeros([nfunc, nfunc])
            c_0 = np.zeros(nfunc)

            for i in range(nfunc_0):
                c_0[i] = c[i + 1]
                for j in range(nfunc_0):
                    err_0[i][j] = err[i + 1][j + 1]

            self.out = c_0
            self.cov = err_0

        # Store computation time
        self.elapsed = time.time() - t_0

        return self.out, self.cov

    def estimate_numterms(self, isquit_func=None):
        """
        Returns a reasonable guess for the
        number of terms

        :param isquit_func:
          reference to thread function to call to check whether the computation needs to
          be stopped.

        :return: number of terms, alpha, message

        """
        from sas.sascalc.pr.num_term import NTermEstimator
        estimator = NTermEstimator(self.clone())
        try:
            return estimator.num_terms(isquit_func)
        except Exception as ex:
            # If we fail, estimate alpha and return the default
            # number of terms
            best_alpha, _, _ = self.estimate_alpha(self.nfunc)
            logger.warning("Invertor.estimate_numterms: %s" % ex)
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

        except Exception as ex:
            message = "Invertor.estimate_alpha: %s" % ex
            return 0, message, elapsed

    def to_file(self, path, npts=100):
        """
        Save the state to a file that will be readable
        by SliceView.

        :param path: path of the file to write
        :param npts: number of P(r) points to be written

        """
        file = open(path, 'w')
        file.write("#d_max=%g\n" % self.d_max)
        file.write("#nfunc=%g\n" % self.nfunc)
        file.write("#alpha=%g\n" % self.alpha)
        file.write("#chi2=%g\n" % self.chi2)
        file.write("#elapsed=%g\n" % self.elapsed)
        file.write("#qmin=%s\n" % str(self.q_min))
        file.write("#qmax=%s\n" % str(self.q_max))
        file.write("#slit_height=%g\n" % self.slit_height)
        file.write("#slit_width=%g\n" % self.slit_width)
        file.write("#background=%g\n" % self.background)
        if self.est_bck == True:
            file.write("#has_bck=1\n")
        else:
            file.write("#has_bck=0\n")
        file.write("#alpha_estimate=%g\n" % self.suggested_alpha)
        if self.out is not None:
            if len(self.out) == len(self.cov):
                for i in range(len(self.out)):
                    file.write("#C_%i=%s+-%s\n" % (i, str(self.out[i]),
                                                   str(self.cov[i][i])))
        file.write("<r>  <Pr>  <dPr>\n")
        r = np.arange(0.0, self.d_max, self.d_max / npts)

        for r_i in r:
            (value, err) = self.pr_err(self.out, self.cov, r_i)
            file.write("%g  %g  %g\n" % (r_i, value, err))

        file.close()

    def from_file(self, path):
        """
        Load the state of the Invertor from a file,
        to be able to generate P(r) from a set of
        parameters.

        :param path: path of the file to load

        """
        #import os
        #import re
        if os.path.isfile(path):
            try:
                fd = open(path, 'r')

                buff = fd.read()
                lines = buff.split('\n')
                for line in lines:
                    if line.startswith('#d_max='):
                        toks = line.split('=')
                        self.d_max = float(toks[1])
                    elif line.startswith('#nfunc='):
                        toks = line.split('=')
                        self.nfunc = int(toks[1])
                        self.out = np.zeros(self.nfunc)
                        self.cov = np.zeros([self.nfunc, self.nfunc])
                    elif line.startswith('#alpha='):
                        toks = line.split('=')
                        self.alpha = float(toks[1])
                    elif line.startswith('#chi2='):
                        toks = line.split('=')
                        self.chi2 = float(toks[1])
                    elif line.startswith('#elapsed='):
                        toks = line.split('=')
                        self.elapsed = float(toks[1])
                    elif line.startswith('#alpha_estimate='):
                        toks = line.split('=')
                        self.suggested_alpha = float(toks[1])
                    elif line.startswith('#qmin='):
                        toks = line.split('=')
                        try:
                            self.q_min = float(toks[1])
                        except:
                            self.q_min = None
                    elif line.startswith('#qmax='):
                        toks = line.split('=')
                        try:
                            self.q_max = float(toks[1])
                        except:
                            self.q_max = None
                    elif line.startswith('#slit_height='):
                        toks = line.split('=')
                        self.slit_height = float(toks[1])
                    elif line.startswith('#slit_width='):
                        toks = line.split('=')
                        self.slit_width = float(toks[1])
                    elif line.startswith('#background='):
                        toks = line.split('=')
                        self.background = float(toks[1])
                    elif line.startswith('#has_bck='):
                        toks = line.split('=')
                        if int(toks[1]) == 1:
                            self.est_bck = True
                        else:
                            self.est_bck = False

                    # Now read in the parameters
                    elif line.startswith('#C_'):
                        toks = line.split('=')
                        p = re.compile('#C_([0-9]+)')
                        m = p.search(toks[0])
                        toks2 = toks[1].split('+-')
                        i = int(m.group(1))
                        self.out[i] = float(toks2[0])

                        self.cov[i][i] = float(toks2[1])

            except Exception as ex:
                msg = "Invertor.from_file: corrupted file\n%s" % ex
                raise RuntimeError(msg)
        else:
            msg = "Invertor.from_file: '%s' is not a file" % str(path)
            raise RuntimeError(msg)
