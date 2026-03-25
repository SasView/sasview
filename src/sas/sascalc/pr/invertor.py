import logging
import math
import time
from collections.abc import Callable
from copy import copy
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt
from numpy.linalg import lstsq

if TYPE_CHECKING:
    from sas.qtgui.Perspectives.Inversion.InversionLogic import InversionLogic

# Default Values for inputs
NUMBER_OF_TERMS = 10
REGULARIZATION = 0.0

logger = logging.getLogger(__name__)


class Invertor:
    def __init__(self, logic: "InversionLogic"):

        # Chisqr of the last computation
        self.chi2: float = 0
        # Time elapsed for last computation
        self.elapsed: float = 0
        # Alpha to get the reg term the same size as the signal
        self.suggested_alpha: float = 0.0
        # Last number of base functions used
        self.nfunc: int = 10
        # Last output values
        self.out: npt.NDArray[np.float64] | None = None
        # Last errors on output values
        self.cov: npt.NDArray[np.float64] | None = None
        # Background value
        self.background: float = 0
        # Information dictionary for application use
        self.info: dict = {}

        # Maximum distance between any two points in the system
        self.dmax: float = 180.0
        # Minimum q to include in inversion
        self.q_min: float = 0.0
        # Maximum q to include in inversion
        self.q_max: float = np.inf
        # Flag for whether or not to evaluate a constant background while inverting
        self.est_bck: bool = True
        # TODO: Is there a reason this is called alpha, and not just regularization.
        self.alpha: float = REGULARIZATION
        # Slit height in units of q [A-1]
        self.slit_height: float = 0.0
        # Slit width in units of q [A-1]
        self.slit_width: float = 0.0

        # Number of terms to use in the expansion
        self.noOfTerms: int = NUMBER_OF_TERMS

        self.logic = logic

    @property
    def x(self) -> npt.NDArray[np.float64]:
        """Returns the x values of the data to be inverted."""
        return self.logic.data.x

    @property
    def y(self) -> npt.NDArray[np.float64]:
        """Returns the y values of the data to be inverted."""
        return self.logic.data.y

    @property
    def err(self) -> npt.NDArray[np.float64]:
        """Returns the error values of the data to be inverted."""
        return self.logic.data.dy

    @property
    def npoints(self) -> int:
        """Returns the number of x values in the data to be inverted."""
        return len(self.x)

    @property
    def ny(self) -> int:
        """Returns the number of y values in the data to be inverted."""
        return len(self.y)

    @property
    def nerr(self) -> int:
        """Returns the number of error values in the data to be inverted."""
        return len(self.err)

    def is_valid(self) -> bool:
        """Check whether the number of x, y, and error values are all the same."""
        return self.npoints == self.ny and self.npoints == self.nerr

    def clone(self) -> "Invertor":
        """Returns a copy of the invertor."""
        return copy(self)

    def lstsq(self, nfunc: int = 5, nr: int = 20) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """
        The problem is solved by posing the problem as Ax = b,
        where x is the set of coefficients we are looking for.

        Npts is the number of points.

        In the following, i refers to the ith base function coefficient.
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
        If the result does not allow us to compute the covariance matrix,
        a matrix filled with zeros will be returned.

        :param nfunc: number of base functions to use.
        :param nr: number of r points to evaluate the 2nd derivative at for the reg. term.

        :return: c_out, c_cov - the coefficients with covariance matrix
        """

        if not self.is_valid():
            logger.error("Invertor: invalid data; incompatible data lengths.")
            return np.zeros(nfunc), np.zeros((nfunc, nfunc))

        self.nfunc = nfunc
        # a -- An M x N matrix.
        # b -- An M x nrhs matrix or M vector.
        npts = self.npoints
        nq = nr
        sqrt_alpha = math.sqrt(math.fabs(self.alpha))
        if sqrt_alpha < 0.0:
            nq = 0

        # If we need to fit the background, add a term
        if self.est_bck:
            nfunc += 1

        # Construct the a matrix and b vector that represent the problem
        t_0 = time.time()
        try:
            a, b = self._get_matrix(nfunc, nq)
        except Exception as exc:
            logger.error("Invertor: could not invert I(Q)\n  %s" % str(exc))
            return np.zeros(nfunc), np.zeros((nfunc, nfunc))

        # Perform the inversion (least square fit)
        c, residuals, _, _ = lstsq(a, b, rcond=None)
        chi2 = residuals[0] if residuals.shape == (1,) else -1.0
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
            err = np.zeros((nfunc, nfunc))

        # Keep a copy of the last output
        if not self.est_bck:
            self.out = c
            self.cov = err
        else:
            # c is a vector of length nfunc+1; background is the first term, rest are the coefficients
            self.background = c[0]

            err_0 = np.zeros((nfunc, nfunc))
            c_0 = np.zeros(nfunc)

            c_0[:-1] = c[1:]
            err_0[:-1, :-1] = err[1:, 1:]

            self.out = c_0
            self.cov = err_0

        # Store computation time
        self.elapsed = time.time() - t_0

        return self.out, self.cov

    def invert(self, nfunc: int = 10, nr: int = 20) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """
        Perform inversion to P(r).

        This is a thin wrapper around :meth:`lstsq` that handles temporary
        background subtraction when ``est_bck`` is disabled.

        See :meth:`lstsq` for details of the linear system construction
        (including regularization) and the least-squares solve.

        :param nfunc: number of base functions to use.
        :param nr: number of r points to evaluate the 2nd derivative at for the reg. term.

        :return: c_out, c_cov - the coefficients with covariance matrix.
        """
        if not self.est_bck:
            self.logic.data.y -= self.background
        out, cov = self.lstsq(nfunc, nr=nr)
        if not self.est_bck:
            self.logic.data.y += self.background
        return out, cov

    def iq(self, pars: npt.ArrayLike, q: npt.ArrayLike) -> np.float64 | npt.NDArray[np.float64]:
        """
        Calculates the scattering intensity I(q) from the expansion coefficients.

        :param pars: c-parameters
        :param q: q, scalar or vector.

        :return: I(q), either scalar or vector depending on q.
        """
        from . import calc

        pars = np.atleast_1d(np.asarray(pars, dtype=np.float64))
        q = np.atleast_1d(np.asarray(q, dtype=np.float64))

        iq_val = calc.iq(pars, self.dmax, q) + self.background
        if iq_val.shape[0] == 1:
            return iq_val[0]
        return iq_val

    def get_iq_smeared(self, pars: npt.ArrayLike, q: npt.ArrayLike) -> np.float64 | npt.NDArray[np.float64]:
        """
        Calculates the slit-smeared scattering intensity I(q) from the expansion coefficients.

        :param pars: c-parameters
        :param q: q, scalar or vector.

        :return: I(q), either scalar or vector depending on q.
        """
        from . import calc

        pars = np.atleast_1d(np.asarray(pars, dtype=np.float64))
        q = np.atleast_1d(np.asarray(q, dtype=np.float64))

        npts = 21
        iq_val = calc.iq_smeared(pars, q, self.dmax, self.slit_height, self.slit_width, npts)

        if iq_val.shape[0] == 1:
            return iq_val[0]
        return iq_val

    def pr(self, pars: npt.ArrayLike, r: npt.ArrayLike) -> np.float64 | npt.NDArray[np.float64]:
        """
        Evaluates P(r).

        :param pars: c-parameters.
        :param r: r-value to evaluate P(r) at.

        :return: P(r).
        """
        from . import calc

        pars = np.atleast_1d(np.asarray(pars, dtype=np.float64))
        r = np.atleast_1d(np.asarray(r, dtype=np.float64))

        pr_val = calc.pr(pars, self.dmax, r)

        if len(pr_val) == 1:
            return pr_val[0]
        return pr_val

    def pr_err(self, c: npt.ArrayLike, c_cov: npt.ArrayLike | None, r: npt.ArrayLike) -> tuple[np.float64, np.float64]:
        """
        Returns the value of P(r) for a given r, and base function coefficients, with error.

        :param c: base function coefficients.
        :param c_cov: covariance matrix of the base function coefficients.
            If None, no error will be calculated.
        :param r: r-value(s) at which P(r) is evaluated.

        :return: (P(r), dP(r))
        """
        from . import calc

        pars = np.atleast_1d(np.asarray(c, dtype=np.float64))
        r = np.atleast_1d(np.asarray(r, dtype=np.float64))

        if c_cov is None:
            return calc.pr(pars, self.dmax, r), 0.0

        cov = np.ascontiguousarray(np.asarray(c_cov, dtype=np.float64))
        return calc.pr_err(pars, cov, self.dmax, r)

    def basefunc_ft(
        self, d_max: float, n: int, q: float | npt.NDArray[np.float64]
    ) -> np.float64 | npt.NDArray[np.float64]:
        """
        Returns the value of the nth Fourier transformed base function.

        :param d_max: d_max.
        :param n: n.
        :param q: q, scalar or vector.

        :return: nth Fourier transformed base function, evaluated at q,
            as a scalar or vector depending on q.
        """
        from . import calc

        d_max = np.float64(d_max)
        n = int(n)
        q = np.atleast_1d(np.asarray(q, dtype=np.float64))

        ortho_val = calc.ortho_transformed(q, d_max, n)

        if ortho_val.shape[0] == 1:
            return ortho_val[0]
        return ortho_val

    def oscillations(self, pars: npt.ArrayLike) -> float:
        """
        Returns the value of the oscillation figure of merit for
        the given set of coefficients. For a sphere, the oscillation
        figure of merit is 1.1.

        :param pars: c-parameters.
        :return: oscillation figure of merit.
        """
        from . import calc

        nslice: int = 100
        pars = np.atleast_1d(np.asarray(pars, dtype=np.float64))

        oscill = calc.reg_term(pars, self.dmax, nslice)
        norm = calc.int_pr_square(pars, self.dmax, nslice)

        if norm == 0:
            return 0
        return np.sqrt(oscill / norm) / np.pi * self.dmax

    def get_peaks(self, pars: npt.ArrayLike) -> int:
        """
        Returns the number of peaks in the output P(r) distribution
        for the given set of coefficients.

        :param pars: c-parameters.
        :return: number of P(r) peaks.
        """
        from . import calc

        nslice: int = 100
        pars = np.asarray(pars, dtype=np.float64)
        count = calc.npeaks(pars, self.dmax, nslice)

        return count

    def get_positive(self, pars: npt.ArrayLike) -> float:
        """
        Returns the fraction of P(r) that is positive over
        the full range of r for the given set of coefficients.

        :param pars: c-parameters.
        :return: fraction of P(r) that is positive.
        """
        from . import calc

        nslice: int = 100
        pars = np.atleast_1d(np.asarray(pars, dtype=np.float64))
        fraction = calc.positive_integral(pars, self.dmax, nslice)

        return fraction

    def get_pos_err(self, pars: npt.ArrayLike, pars_err: npt.ArrayLike) -> float:
        """
        Returns the fraction of P(r) that is 1 standard deviation
        above zero over the full range of r for the given set of coefficients.

        :param pars: c-parameters.
        :param pars_err: pars_err.

        :return: fraction of P(r) that is positive.
        """
        from . import calc

        nslice: int = 51
        pars = np.atleast_1d(np.asarray(pars, dtype=np.float64))
        pars_err = np.asarray(pars_err, dtype=np.float64)

        fraction = calc.positive_errors(pars, pars_err, self.dmax, nslice)

        return fraction

    def rg(self, pars: npt.ArrayLike) -> float:
        """
        Returns the value of the radius of gyration, Rg.

        :param pars: c-parameters.
        :return: Rg, the radius of gyration.
        """
        from . import calc

        nslice: int = 101
        pars = np.atleast_1d(np.asarray(pars, dtype=np.float64))

        val = calc.rg(pars, self.dmax, nslice)

        return val

    def iq0(self, pars: npt.ArrayLike) -> float:
        """
        Returns the value of I(q=0).

        :param pars: c-parameters.
        :return: I(q=0)
        """
        from . import calc

        nslice: int = 101
        pars = np.atleast_1d(np.asarray(pars, dtype=np.float64))

        val = np.float64(4.0 * np.pi * calc.int_pr(pars, self.dmax, nslice))

        return val

    def accept_q(self, q: npt.ArrayLike) -> bool | npt.NDArray[np.bool_]:
        """
        Check whether a q-value is within acceptable limits.

        :return: Boolean or boolean array indicating acceptance.
            True where q is within [q_min, q_max].
        """
        if self.q_min <= 0 and self.q_max <= 0:
            return True
        return (q >= self.q_min) & (q <= self.q_max)

    def check_for_zero(self, x: npt.ArrayLike) -> bool:
        """
        Check whether any value in the array is zero.

        :param x: array to check.
        :return: True if any value in x is zero, False otherwise.
        """
        return (x == 0).any()

    def estimate_numterms(self, isquit_func: Callable | None = None):
        """
        Returns a reasonable guess for the number of terms.

        :param isquit_func: reference to thread function
            to call to check whether the computation needs to be stopped.

        :return: number of terms, alpha, message.
        """
        from .num_term import NTermEstimator

        estimator = NTermEstimator(self.clone())
        try:
            return estimator.num_terms(isquit_func)
        except Exception as exc:
            # If we fail, estimate alpha and return the default  number of terms
            best_alpha, _, _ = self.estimate_alpha(self.nfunc)
            logger.warning("Invertor.estimate_numterms: %s" % exc)
            return self.nfunc, best_alpha, "Could not estimate number of terms"

    def estimate_alpha(self, nfunc: int) -> tuple[float, str | None, float]:
        """
        Returns a reasonable guess for the regularization constant, alpha.

        :param nfunc: number of terms to use in the expansion.

        :return: alpha, message, elapsed
            where, alpha is the estimate for alpha,
            message is a message for the user,
            elapsed is the computation time
        """
        message = None
        elapsed: float = 0.0

        try:
            pr = self.clone()

            # T_0 for computation time
            starttime = time.time()

            # If the current alpha is zero, try another value
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
            # if more than one peak to start with, just return the estimate
            if npeaks > 1:
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
                # the initial alpha already had only one peak, just return that
                if not found and initial_peaks == 1 and initial_alpha < best_alpha:
                    best_alpha = initial_alpha

                # Check whether the size makes sense
                if found and (best_alpha >= 0.5 * pr.suggested_alpha):
                    # best alpha is too big, return a reasonable value
                    message = "The estimated alpha for your system is too large."
                    message += "Try increasing your maximum distance."

                return best_alpha, message, elapsed
        except Exception as exc:
            message = "Invertor.estimate_alpha: %s" % exc
            return 0, message, elapsed

    def _get_matrix(self, nfunc: int, nr: int) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """
        Returns A matrix and b vector for least square problem.

        :param nfunc: number of base functions.
        :param nr: number of r-points used when evaluating reg term.

        :return: A, b - the A matrix and b vector for least square problem.
        """
        from . import calc

        nfunc = int(nfunc)
        nr = int(nr)
        a_obj = np.zeros([self.npoints + nr, nfunc])
        b_obj = np.zeros(self.npoints + nr)

        sqrt_alpha = np.sqrt(math.fabs(self.alpha))
        pi = np.pi
        offset: int = 0 if self.est_bck else 1

        if self.check_for_zero(self.err):
            logger.error("Pinvertor.get_matrix: Some I(Q) points have no error.")
            return np.zeros((nfunc, nfunc)), np.zeros(nfunc)

        # Compute A
        # Whether or not to use ortho_transformed_smeared.
        smeared = False
        if self.slit_width > 0 or self.slit_height > 0:
            smeared = True

        npts: int = 21
        # Get accept_q vector across all q.
        q_accept_x = self.accept_q(self.x)

        if isinstance(q_accept_x, bool):
            # In the case of q_min and q_max <= 0, so returns scalar, and returns True
            q_accept_x = np.ones(self.npoints, dtype=bool)
        # The x and a that will be used for the first part of 'a' calculation, given to ortho_transformed
        x_use = self.x[q_accept_x]
        a_use = a_obj[0 : self.npoints, :]

        for j in range(nfunc):
            if self.est_bck and j == 0:
                a_use[q_accept_x, j] = 1.0 / self.err[q_accept_x]
            elif smeared:
                a_use[q_accept_x, j] = (
                    calc.ortho_transformed_smeared(
                        x_use, self.dmax, j + offset, self.slit_height, self.slit_width, npts
                    )
                    / self.err[q_accept_x]
                )
            else:
                a_use[q_accept_x, j] = calc.ortho_transformed(x_use, self.dmax, j + offset) / self.err[q_accept_x]

        a_obj[0 : self.npoints, :] = a_use

        for j in range(nfunc):
            i_r = np.arange(nr, dtype=np.float64)

            # Implementing second stage A as a python vector operation with shape = [nr]
            r = (self.dmax / nr) * i_r
            tmp = pi * (j + offset) / self.dmax
            res = (2.0 * sqrt_alpha * self.dmax / nr * tmp) * (2.0 * np.cos(tmp * r) + tmp * r * np.sin(tmp * r))
            # Res should now be np vector size i_r.
            a_obj[self.npoints : self.npoints + nr, j] = res

        # Compute B
        x_accept_index = self.accept_q(self.x)
        # The part of b used for the vector operations, of the accepted q values.
        b_used = b_obj[0 : self.npoints]
        b_used[x_accept_index] = self.y[x_accept_index] / self.err[x_accept_index]
        b_obj[0 : self.npoints] = b_used

        return a_obj, b_obj

    def _get_invcov_matrix(self, nfunc: int, nr: int, a_obj: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """
        Compute the inverse covariance matrix, defined as inv_cov = a_transposed x a.

        :param nfunc: number of base functions.
        :param nr: number of r-points used when evaluating reg term.
        :param a_obj: A array to compute inverse covariance matrix of.

        :return: inv_cov matrix.
        """
        nfunc = int(nfunc)
        nr = int(nr)
        cov_obj = np.zeros([nfunc, nfunc])
        n_a = a_obj.size

        if not n_a >= (nfunc * (nr + self.npoints)):
            logger.error("Pinvertor._get_invcov_matrix: a array too small.")
            return np.zeros((nfunc, nfunc))

        cov_obj[:, :] = np.dot(a_obj.T, a_obj)
        return cov_obj

    def _get_reg_size(self, nfunc: int, nr: int, a_obj: npt.NDArray[np.float64]) -> tuple[float, float]:
        """
        Computes sum_sig and sum_reg of input array given.

        :param nfunc: number of base functions.
        :param nr: number of r-points used when evaluating reg term.
        :param a_obj: Array to compute sum_sig and sum_reg of.

        :return: Tuple of sum of signal and sum of regularization term, for the given array.
        """
        nfunc = int(nfunc)
        nr = int(nr)

        if not a_obj.size >= nfunc * (nr + self.npoints):
            logger.error("Pinvertor._get_reg_size: input array too short for data.")
            return 0.0, 0.0

        a_pass = self.accept_q(self.x)
        a_use = a_obj[0 : self.npoints, :]
        a_use = a_use[a_pass, :]
        sum_sig = np.sum(a_use**2)
        sum_reg = np.sum(a_obj[self.npoints : self.npoints + nr, :] ** 2)

        return sum_sig, sum_reg
