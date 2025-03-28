import numpy as np
import time

# TODO: Add docstrings later

class NewInvertor():

    def __init__(self):
        self.init_default_values()

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
        self.est_bck = 0
        self.alpha = 0.0
        #q data
        self.x = np.empty(0, dtype=np.float64)
        #I(q) data
        self.y = np.empty(0, dtype=np.float64)
        #dI(q) data
        self.err = np.empty(0, dtype=np.float64)
        #Number of q points
        self.npoints = 0
        #Number of I(q) points
        self.ny = 0
        #Number of dI(q) points
        self.nerr = 0
        #Slit height in units of q [A-1]
        self.slit_height = 0.0
        #Slit width in units of q [A-1]
        self.slit_width = 0.0

    def is_valid(self) -> bool:
        return self.npoints == self.ny and self.npoints == self.nerr

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
        if rcond ==None:
            rcond =-1
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
            self.y -= self.background
        out, cov = self.lstsq(nfunc, nr=nr)
        if not self.est_bck:
            self.y += self.background
        return out, cov
