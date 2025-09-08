# pylint: disable=invalid-name
#####################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#See the license text in license.txt
#copyright 2010, University of Tennessee
######################################################################
"""
This module implements invariant and its related computations.

:author: Gervaise B. Alina/UTK
:author: Mathieu Doucet/UTK
:author: Jae Cho/UTK
:author: Paul Butler/NIST/UD/UTK -- refactor in 2020

"""

import math

import numpy as np

from sasdata.dataloader.data_info import Data1D as LoaderData1D

# The minimum q-value to be used when extrapolating
Q_MINIMUM = 1e-5

# The maximum q-value to be used when extrapolating
Q_MAXIMUM = 10

# Number of steps in the extrapolation
INTEGRATION_NSTEPS = 1000

class Transform:
    """
    Define interface that need to compute a function or an inverse
    function given some x, y
    """

    def linearize_data(self, data):
        """
        Linearize data so that a linear fit can be performed.
        Filter out the data that can't be transformed.

        :param data: LoadData1D instance

        """
        # Check that the vector lengths are equal
        assert len(data.x) == len(data.y)
        if data.dy is not None:
            assert len(data.x) == len(data.dy)
            dy = data.dy
        else:
            dy = np.ones(len(data.y))

        # Transform the data
        data_points = zip(data.x, data.y, dy)

        output_points = [(self.linearize_q_value(p[0]),
                          math.log(p[1]),
                          p[2] / p[1]) for p in data_points if p[0] > 0 and \
                          p[1] > 0 and p[2] > 0]

        x_out, y_out, dy_out = zip(*output_points)

        # Create Data1D object
        x_out = np.asarray(x_out)
        y_out = np.asarray(y_out)
        dy_out = np.asarray(dy_out)
        linear_data = LoaderData1D(x=x_out, y=y_out, dy=dy_out)

        return linear_data

    def get_allowed_bins(self, data):
        """
        Goes through the data points and returns a list of boolean values
        to indicate whether each points is allowed by the model or not.

        :param data: Data1D object
        """
        return [p[0] > 0 and p[1] > 0 and p[2] > 0 for p in zip(data.x, data.y,
                                                                data.dy)]

    def linearize_q_value(self, value):
        """
        Transform the input q-value for linearization
        """
        return NotImplemented

    def extract_model_parameters(self, constant, slope, dconstant=0, dslope=0):
        """
        set private member
        """
        return NotImplemented

    def evaluate_model(self, x):
        """
        Returns an array f(x) values where f is the Transform function.
        """
        return NotImplemented

    def evaluate_model_errors(self, x):
        """
        Returns an array of I(q) errors
        """
        return NotImplemented

class Guinier(Transform):
    """
    class of type Transform that performs operations related to guinier
    function
    """
    def __init__(self, scale=1, radius=60):
        Transform.__init__(self)
        self.scale = scale
        self.radius = radius
        ## Uncertainty of scale parameter
        self.dscale = 0
        ## Unvertainty of radius parameter
        self.dradius = 0

    def linearize_q_value(self, value):
        """
        Transform the input q-value for linearization

        :param value: q-value

        :return: q*q
        """
        return value * value

    def extract_model_parameters(self, constant, slope, dconstant=0, dslope=0):
        """
        assign new value to the scale and the radius
        """
        self.scale = math.exp(constant)
        if slope > 0:
            slope = 0.0
        self.radius = math.sqrt(-3 * slope)
        # Errors
        self.dscale = math.exp(constant) * dconstant
        if slope == 0.0:
            n_zero = -1.0e-24
            self.dradius = -3.0 / 2.0 / math.sqrt(-3 * n_zero) * dslope
        else:
            self.dradius = -3.0 / 2.0 / math.sqrt(-3 * slope) * dslope

        return [self.radius, self.scale], [self.dradius, self.dscale]

    def evaluate_model(self, x):
        r"""
        return calculated I(q) for the model

        Calculates the Guinier expression
        $F(x)= s * \exp\left(-(r x)^{2/3}\right)$
        """
        return self._guinier(x)

    def evaluate_model_errors(self, x):
        """
        Returns the error on I(q) for the given array of q-values

        :param x: array of q-values
        """
        p1 = np.array([self.dscale * math.exp(-((self.radius * q) ** 2 / 3)) \
                          for q in x])
        p2 = np.array([self.scale * math.exp(-((self.radius * q) ** 2 / 3))\
                     * (-(q ** 2 / 3)) * 2 * self.radius * self.dradius for q in x])
        diq2 = p1 * p1 + p2 * p2
        return np.array([math.sqrt(err) for err in diq2])

    def _guinier(self, x):
        r"""
        Retrieve the guinier function after apply an inverse guinier function
        to x
        Compute $F(x) = s * \exp\left(-(r x)^{2/3}\right)$.

        :param x: a vector of q values

        Also uses:
         - self.scale: $s$, the scale value
         - self.radius: $r$, the guinier radius value

        :return: F(x)
        """
        # transform the radius of coming from the inverse guinier function to a
        # a radius of a guinier function
        if self.radius <= 0:
            msg = "Rg expected positive value, but got %s" % self.radius
            raise ValueError(msg)
        value = np.array([math.exp(-((self.radius * i) ** 2 / 3)) for i in x])
        return self.scale * value

class PowerLaw(Transform):
    """
    class of type transform that perform operation related to power_law
    function
    """
    def __init__(self, scale=1, power=4):
        Transform.__init__(self)
        self.scale = scale
        self.power = power
        self.dscale = 0.0
        self.dpower = 0.0

    def linearize_q_value(self, value):
        r"""
        Transform the input q-value for linearization

        :param value: q-value

        :return: $\log(q)$
        """
        return math.log(value)

    def extract_model_parameters(self, constant, slope, dconstant=0, dslope=0):
        """
        Assign new value to the scale and the power
        """
        self.power = -slope
        self.scale = math.exp(constant)

        # Errors
        self.dscale = math.exp(constant) * dconstant
        self.dpower = -dslope

        return [self.power, self.scale], [self.dpower, self.dscale]

    def evaluate_model(self, x):
        """
        given a scale and a radius transform x, y using a power_law
        function
        """
        return self._power_law(x)

    def evaluate_model_errors(self, x):
        """
        Returns the error on I(q) for the given array of q-values
        :param x: array of q-values
        """
        p1 = np.array([self.dscale * math.pow(q, -self.power) for q in x])
        p2 = np.array([self.scale * self.power * math.pow(q, -self.power - 1)\
                           * self.dpower for q in x])
        diq2 = p1 * p1 + p2 * p2
        return np.array([math.sqrt(err) for err in diq2])

    def _power_law(self, x):
        """
        F(x) = scale* (x)^(-power)
            when power= 4. the model is porod
            else power_law
        The model has three parameters: ::
            1. x: a vector of q values
            2. power: power of the function
            3. scale : scale factor value

        :param x: array
        :return: F(x)
        """
        if self.power <= 0:
            msg = "Power_law function expected positive power,"
            msg += " but got %s" % self.power
            raise ValueError(msg)
        if self.scale <= 0:
            msg = "scale expected positive value, but got %s" % self.scale
            raise ValueError(msg)

        value = np.array([math.pow(i, -self.power) for i in x])
        return self.scale * value

class Extrapolator:
    """
    Extrapolate I(q) distribution using a given model
    """
    def __init__(self, data, model=None):
        """
        Determine a and b given a linear equation y = ax + b

        If a model is given, it will be used to linearize the data before
        the extrapolation is performed. If None,
        a simple linear fit will be done.

        :param data: data containing x and y  such as  y = ax + b
        :param model: optional Transform object
        """
        self.data = data
        self.model = model

        # Set qmin as the lowest non-zero value
        self.qmin = Q_MINIMUM
        for q_value in self.data.x:
            if q_value > 0:
                self.qmin = q_value
                break
        self.qmax = max(self.data.x)

    def fit(self, power=None, qmin=None, qmax=None):
        """
        Fit data for $y = ax + b$  return $a$ and $b$

        :param power: a fixed, otherwise None
        :param qmin: Minimum Q-value
        :param qmax: Maximum Q-value
        """
        if qmin is None:
            qmin = self.qmin
        if qmax is None:
            qmax = self.qmax

        # Identify the bin range for the fit
        idx = (self.data.x >= qmin) & (self.data.x <= qmax)

        fx = np.zeros(len(self.data.x))

        # Uncertainty
        if isinstance(self.data.dy, np.ndarray) and \
            len(self.data.dy) == len(self.data.x) and \
                np.all(self.data.dy > 0):
            sigma = self.data.dy
        else:
            sigma = np.ones(len(self.data.x))

        # Compute theory data f(x)
        fx[idx] = self.data.y[idx]

        # Linearize the data
        if self.model is not None:
            linearized_data = self.model.linearize_data(\
                                            LoaderData1D(self.data.x[idx],
                                                         fx[idx],
                                                         dy=sigma[idx]))
        else:
            linearized_data = LoaderData1D(self.data.x[idx],
                                           fx[idx],
                                           dy=sigma[idx])

        ##power is given only for function = power_law
        if power is not None:
            sigma2 = linearized_data.dy * linearized_data.dy
            a = -(power)
            b = (np.sum(linearized_data.y / sigma2) \
                 - a * np.sum(linearized_data.x / sigma2)) / np.sum(1.0 / sigma2)


            deltas = linearized_data.x * a + \
                     np.ones(len(linearized_data.x)) * b - linearized_data.y
            residuals = np.sum(deltas * deltas / sigma2)

            err = np.fabs(residuals) / np.sum(1.0 / sigma2)
            return [a, b], [0, np.sqrt(err)]
        else:
            A = np.vstack([linearized_data.x / linearized_data.dy, 1.0 / linearized_data.dy]).T
            # CRUFT: numpy>=1.14.0 allows rcond=None for the following default
            rcond = np.finfo(float).eps * max(A.shape)
            p, residuals, _, _ = np.linalg.lstsq(A, linearized_data.y / linearized_data.dy,
                                                 rcond=rcond)

            # Get the covariance matrix, defined as inv_cov = a_transposed * a
            err = np.zeros(2)
            try:
                inv_cov = np.dot(A.transpose(), A)
                cov = np.linalg.pinv(inv_cov)
                err_matrix = np.fabs(residuals) * cov
                err = [np.sqrt(err_matrix[0][0]), np.sqrt(err_matrix[1][1])]
            except:
                err = [-1.0, -1.0]

            return p, err


class InvariantCalculator:
    """
    Compute invariant if data is given.
    Can provide volume fraction and surface area if the user provides
    Porod constant  and contrast values.

    :precondition:  the user must send a data of type DataLoader.Data1D
                    the user provide background and scale values.

    :note: Some computations depends on each others.
    """
    def __init__(self, data, background=0, scale=1):
        """
        Initialize variables.

        :param data: data must be of type DataLoader.Data1D
        :param background: Background value. The data will be corrected
            before processing
        :param scale: Scaling factor for I(q). The data will be corrected
            before processing
        """
        # Background and scale should be private data member if the only way to
        # change them are by instantiating a new object.
        self._background = background
        self._scale = scale
        # slit height for smeared data
        self._smeared = None
        # The data should be private
        self._data = self._get_data(data)
        # get the dxl if the data is smeared: This is done only once on init.
        if self._data.dxl is not None and self._data.dxl.all() > 0:
            # assumes constant dxl
            self._smeared = self._data.dxl[0]

        # Since there are multiple variants of Q*, you should force the
        # user to use the get method and keep Q* a private data member
        self._qstar = None

        # You should keep the error on Q* so you can reuse it without
        # recomputing the whole thing.
        self._qstar_err = 0

        # Extrapolation parameters
        self._low_extrapolation_npts = 4
        self._low_extrapolation_function = Guinier()
        self._low_extrapolation_power = None
        self._low_extrapolation_power_fitted = None

        self._high_extrapolation_npts = 4
        self._high_extrapolation_function = PowerLaw()
        self._high_extrapolation_power = None
        self._high_extrapolation_power_fitted = None

        # Extrapolation range
        self._low_q_limit = Q_MINIMUM

    @property
    def background(self):
        return self._background

    @background.setter
    def background(self, value):
        self._background = value

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = value

    def set_data(self, data):
        self._data = self._get_data(data)

    def _get_data(self, data):
        """
        :note: this function must be call before computing any type
         of invariant

        :return: new data = self._scale x data - self._background
        """
        if not issubclass(data.__class__, LoaderData1D):
            #Process only data that inherited from DataLoader.Data_info.Data1D
            raise ValueError("Data must be of type DataLoader.Data1D")
        #from copy import deepcopy
        new_data = (self._scale * data) - self._background

        # Check that the vector lengths are equal
        assert len(new_data.x) == len(new_data.y)

        # Verify that the errors are set correctly
        if new_data.dy is None or len(new_data.x) != len(new_data.dy) or \
            (min(new_data.dy) == 0 and max(new_data.dy) == 0):
            new_data.dy = np.ones(len(new_data.x))
        return new_data

    def _fit(self, model, qmin=Q_MINIMUM, qmax=Q_MAXIMUM, power=None):
        """
        fit data with function using
        data = self._get_data()
        fx = Functor(data , function)
        y = data.y
        slope, constant = linalg.lstsq(y,fx)

        :param qmin: data first q value to consider during the fit
        :param qmax: data last q value to consider during the fit
        :param power: power value to consider for power-law
        :param function: the function to use during the fit

        :return a: the scale of the function
        :return b: the other parameter of the function for guinier will be radius
                for power_law will be the power value
        """
        extrapolator = Extrapolator(data=self._data, model=model)
        p, dp = extrapolator.fit(power=power, qmin=qmin, qmax=qmax)

        return model.extract_model_parameters(constant=p[1], slope=p[0],
                                              dconstant=dp[1], dslope=dp[0])

    def _get_qstar(self, data):
        """
        Compute invariant for pinhole data.
        This invariant is given by: ::

            q_star = x0**2 *y0 *dx0 +x1**2 *y1 *dx1
                        + ..+ xn**2 *yn *dxn    for non smeared data

            q_star = dxl0 *x0 *y0 *dx0 +dxl1 *x1 *y1 *dx1
                        + ..+ dlxn *xn *yn *dxn    for smeared data

            where n >= len(data.x)-1
            dxl = slit height dQl
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = (x1 - x0)/2
            dxn = (xn - xn-1)/2

        :param data: the data to use to compute invariant.

        :return q_star: invariant value for pinhole data. q_star > 0
        """
        if len(data.x) <= 1 or len(data.y) <= 1 or len(data.x) != len(data.y):
            msg = "Length x and y must be equal"
            msg += " and greater than 1; got x=%s, y=%s" % (len(data.x), len(data.y))
            raise ValueError(msg)
        else:
            # Take care of smeared data
            if self._smeared is None:
                gx = data.x * data.x
            # assumes that len(x) == len(dxl).
            else:
                gx = data.dxl * data.x

            n = len(data.x) - 1
            #compute the first delta q
            dx0 = (data.x[1] - data.x[0]) / 2
            #compute the last delta q
            dxn = (data.x[n] - data.x[n - 1]) / 2
            total = 0
            total += gx[0] * data.y[0] * dx0
            total += gx[n] * data.y[n] * dxn

            if len(data.x) == 2:
                return total
            else:
                #iterate between for element different
                #from the first and the last
                for i in range(1, n - 1):
                    dxi = (data.x[i + 1] - data.x[i - 1]) / 2
                    total += gx[i] * data.y[i] * dxi
                return total

    def _get_qstar_uncertainty(self, data):
        """
        Compute invariant uncertainty with with pinhole data.
        This uncertainty is given as follows::

           dq_star = math.sqrt[(x0**2*(dy0)*dx0)**2 +
                (x1**2 *(dy1)*dx1)**2 + ..+ (xn**2 *(dyn)*dxn)**2 ]

        where n >= len(data.x)-1
        dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
        dx0 = (x1 - x0)/2
        dxn = (xn - xn-1)/2
        dyn: error on dy

        :param data:
        :note: if data doesn't contain dy return "None"
        """
        if len(data.x) <= 1 or len(data.y) <= 1 or \
            len(data.x) != len(data.y) or \
            (data.dy is not None and (len(data.dy) != len(data.y))):
            msg = "Length of data.x and data.y must be equal"
            msg += " and greater than 1; got x=%s, y=%s" % (len(data.x), len(data.y))
            raise ValueError(msg)
        else:
            # For reduced data sqrt(I) is incorrect! if the data has no dy
            # then we should not invent it and then propogate that completely
            # bogus value.  So changed behaviour on Mar 23, 2020 to return
            # None instead
            if data.dy is None:
                return None
            dy = data.dy
            # Take care of smeared data
            if self._smeared is None:
                gx = data.x * data.x
            # assumes that len(x) == len(dxl).
            else:
                gx = data.dxl * data.x

            n = len(data.x) - 1
            #compute the first delta
            dx0 = (data.x[1] - data.x[0]) / 2
            #compute the last delta
            dxn = (data.x[n] - data.x[n - 1]) / 2
            total = 0
            total += (gx[0] * dy[0] * dx0) ** 2
            total += (gx[n] * dy[n] * dxn) ** 2
            if len(data.x) == 2:
                return math.sqrt(total)
            else:
                #iterate between for element different
                #from the first and the last
                for i in range(1, n - 1):
                    dxi = (data.x[i + 1] - data.x[i - 1]) / 2
                    total += (gx[i] * dy[i] * dxi) ** 2
                return math.sqrt(total)

    def _get_extrapolated_data(self, model, npts=INTEGRATION_NSTEPS,
                               q_start=Q_MINIMUM, q_end=Q_MAXIMUM):
        """
        :return: extrapolate data create from data
        """
        #create new Data1D to compute the invariant
        q = np.linspace(start=q_start,
                           stop=q_end,
                           num=npts,
                           endpoint=True)
        iq = model.evaluate_model(q)
        diq = model.evaluate_model_errors(q)

        result_data = LoaderData1D(x=q, y=iq, dy=diq)
        if self._smeared is not None:
            result_data.dxl = self._smeared * np.ones(len(q))
        return result_data

    def get_data(self):
        """
        :return: self._data
        """
        return self._data

    def get_extrapolation_power(self, range='high'):
        """
        :return: the fitted power for power law function for a given
            extrapolation range
        """
        if range == 'low':
            return self._low_extrapolation_power_fitted
        return self._high_extrapolation_power_fitted

    def get_qstar_low(self, low_q_limit=None):
        """
        Compute the invariant for extrapolated data at low q range.

        Implementation: ::

            data = self._get_extra_data_low()
            return self._get_qstar()

        :return q_star: the invariant for data extrapolated at low q.
        """
        # Data boundaries for fitting
        qmax = self._data.x[int(self._low_extrapolation_npts - 1)]
        # Allow minimum q to be passed as an argument
        if not low_q_limit or low_q_limit < self._data.x[0] or low_q_limit >= qmax:
            qmin = self._data.x[0]
        else:
            qmin = low_q_limit
        # Distribution starting point
        self._low_q_limit = low_q_limit if low_q_limit else Q_MINIMUM

        # Extrapolate the low-Q data
        p, _ = self._fit(model=self._low_extrapolation_function,
                         qmin=qmin,
                         qmax=qmax,
                         power=self._low_extrapolation_power)
        self._low_extrapolation_power_fitted = p[0]

        data = self._get_extrapolated_data(
            model=self._low_extrapolation_function,
            npts=INTEGRATION_NSTEPS, q_start=self._low_q_limit, q_end=qmin)

        # Systematic error
        # If we have smearing, the shape of the I(q) distribution at low Q will
        # may not be a Guinier or simple power law. The following is
        # a conservative estimation for the systematic error.
        err = qmin * qmin * math.fabs((qmin - self._low_q_limit) * (data.y[0] - data.y[INTEGRATION_NSTEPS - 1]))
        return self._get_qstar(data), self._get_qstar_uncertainty(data) + err

    def get_qstar_high(self, high_q_limit=None):
        """
        Compute the invariant for extrapolated data at high q range.

        Implementation: ::

            data = self._get_extra_data_high()
            return self._get_qstar()

        :return q_star: the invariant for data extrapolated at high q.
        """
        # Data boundaries for fitting
        x_len = int(len(self._data.x) - 1)
        qmin = self._data.x[int(x_len - self._high_extrapolation_npts)]
        if not high_q_limit or high_q_limit > self._data.x[x_len] or high_q_limit <= qmin:
            qmax = self._data.x[x_len]
        else:
            qmax = high_q_limit

        high_q_limit = high_q_limit if high_q_limit else Q_MAXIMUM

        # fit the data with a model to get the appropriate parameters
        p, _ = self._fit(model=self._high_extrapolation_function,
                         qmin=qmin,
                         qmax=qmax,
                         power=self._high_extrapolation_power)
        self._high_extrapolation_power_fitted = p[0]

        #create new Data1D to compute the invariant
        data = self._get_extrapolated_data(
            model=self._high_extrapolation_function,
            npts=INTEGRATION_NSTEPS, q_start=qmax, q_end=high_q_limit)

        return self._get_qstar(data), self._get_qstar_uncertainty(data)

    def get_extra_data_low(self, npts_in=None, q_start=None, npts=20):
        """
        Returns the extrapolated data used for the loew-Q invariant calculation.
        By default, the distribution will cover the data points used for the
        extrapolation. The number of overlap points is a parameter (npts_in).
        By default, the maximum q-value of the distribution will be
        the minimum q-value used when extrapolating for the purpose of the
        invariant calculation.

        :param npts_in: number of data points for which
            the extrapolated data overlap
        :param q_start: is the minimum value to uses for extrapolated data
        :param npts: the number of points in the extrapolated distribution

        """
        # Get extrapolation range
        if q_start is None:
            q_start = self._low_q_limit

        if npts_in is None:
            npts_in = self._low_extrapolation_npts
        q_end = self._data.x[max(0, int(npts_in - 1))]

        if q_start >= q_end:
            return np.zeros(0), np.zeros(0)

        return self._get_extrapolated_data(\
                                    model=self._low_extrapolation_function,
                                    npts=npts,
                                    q_start=q_start, q_end=q_end)

    def get_extra_data_high(self, npts_in=None, q_end=Q_MAXIMUM, npts=20):
        """
        Returns the extrapolated data used for the high-Q invariant calculation.
        By default, the distribution will cover the data points used for the
        extrapolation. The number of overlap points is a parameter (npts_in).
        By default, the maximum q-value of the distribution will be Q_MAXIMUM,
        the maximum q-value used when extrapolating for the purpose of the
        invariant calculation.

        :param npts_in: number of data points for which the
            extrapolated data overlap
        :param q_end: is the maximum value to uses for extrapolated data
        :param npts: the number of points in the extrapolated distribution
        """
        # Get extrapolation range
        if npts_in is None:
            npts_in = int(self._high_extrapolation_npts)
        _npts = len(self._data.x)
        q_start = self._data.x[min(_npts, int(_npts - npts_in))]

        if q_start >= q_end:
            return np.zeros(0), np.zeros(0)

        return self._get_extrapolated_data(\
                                model=self._high_extrapolation_function,
                                npts=npts,
                                q_start=q_start, q_end=q_end)

    def set_extrapolation(self, range, npts=4, function=None, power=None):
        """
        Set the extrapolation parameters for the high or low Q-range.
        Note that this does not turn extrapolation on or off.

        :param range: a keyword set the type of extrapolation . type string
        :param npts: the numbers of q points of data to consider
            for extrapolation
        :param function: a keyword to select the function to use
            for extrapolation.
            of type string.
        :param power: an power to apply power_low function

        """
        range = range.lower()
        if range not in ['high', 'low']:
            raise ValueError("Extrapolation range should be 'high' or 'low'")
        function = function.lower()
        if function not in ['power_law', 'guinier']:
            msg = "Extrapolation function should be 'guinier' or 'power_law'"
            raise ValueError(msg)

        if range == 'high':
            if function != 'power_law':
                msg = "Extrapolation only allows a power law at high Q"
                raise ValueError(msg)
            self._high_extrapolation_npts = npts
            self._high_extrapolation_power = power
            self._high_extrapolation_power_fitted = power
        else:
            if function == 'power_law':
                self._low_extrapolation_function = PowerLaw()
            else:
                self._low_extrapolation_function = Guinier()
            self._low_extrapolation_npts = npts
            self._low_extrapolation_power = power
            self._low_extrapolation_power_fitted = power

    def get_qstar(self, extrapolation=None):
        """
        Compute the invariant of the local copy of data.

        :param extrapolation: string to apply optional extrapolation

        :return q_star: invariant of the data within data's q range

        :warning: When using setting data to Data1D ,
            the user is responsible of
            checking that the scale and the background are
            properly apply to the data

        """
        self._qstar = self._get_qstar(self._data)
        self._qstar_err = self._get_qstar_uncertainty(self._data)

        if extrapolation is None:
            return self._qstar

        # Compute invariant plus invariant of extrapolated data
        extrapolation = extrapolation.lower()
        if extrapolation == "low":
            qs_low, dqs_low = self.get_qstar_low()
            qs_hi, dqs_hi = 0, 0

        elif extrapolation == "high":
            qs_low, dqs_low = 0, 0
            qs_hi, dqs_hi = self.get_qstar_high()

        elif extrapolation == "both":
            qs_low, dqs_low = self.get_qstar_low()
            qs_hi, dqs_hi = self.get_qstar_high()

        self._qstar += qs_low + qs_hi
        self._qstar_err = math.sqrt(self._qstar_err * self._qstar_err \
                                    + dqs_low * dqs_low + dqs_hi * dqs_hi)

        return self._qstar

    def get_surface(self, contrast, porod_const, extrapolation=None):
        """
        Compute the specific surface from the data.

        Historically, Sv was computed with the invariant and the Porod
        constant so as not to have to know the contrast in order to get the
        Sv as: ::

            surface = (pi * V * (1- V) * porod_const) / q_star

        However, that turns out to be a pointless exercise since it
        also requires a knowledge of the volume fractions and from the
        volume fraction and the invariant the contrast can be calculated
        as: ::

            contrast**2 = q_star / (2 * pi**2 * V * (1- V))

        Thus either way, mathematically it is always identical to computing
        with only the contrast and the Porod Constant. up to and including
        SasView versions 4.2.2 and 5.0.1 the implementation used the traditional
        circular approach.

        Implementation: ::

            Given the above, as of SasView 4.3 and 5.0.2 we compute Sv simply
            from the Porod Constant and the contrast between the two phases as:

            surface = porod_const / (2 * pi contrast**2)

        :param contrast: contrast between the two phases
        :param porod_const: Porod constant
        :param extrapolation: string to apply optional extrapolation. This will
               only be needed if and when the contrast term is calculated from
               the invariant.

        :return: specific surface
        """
        # convert porod_const to units of A^-5 instead of cm^-1 A^-4 so that
        # s is returned in units of 1/A.
        _porod_const = 1.0e-8 * porod_const
        return _porod_const / (2 * math.pi * math.fabs(contrast)**2)

    def get_volume_fraction(self, contrast, extrapolation=None):
        """
        Compute volume fraction is deduced as follows: ::

            q_star = 2*(pi*contrast)**2* volume( 1- volume)
            for k = 10^(-8)*q_star/(2*(pi*|contrast|)**2)
            we get 2 values of volume:
                 with   1 - 4 * k >= 0
                 volume1 = (1- sqrt(1- 4*k))/2
                 volume2 = (1+ sqrt(1- 4*k))/2

            q_star: the invariant value included extrapolation is applied
                         unit  1/A^(3)*1/cm
                    q_star = self.get_qstar()

            the result returned will be 0 <= volume <= 1

        :param contrast: contrast value provides by the user of type float.
                 contrast unit is 1/A^(2)= 10^(16)cm^(2)
        :param extrapolation: string to apply optional extrapolation

        :return: volume fraction

        :note: volume fraction must have no unit
        """
        if contrast <= 0:
            raise ValueError("The contrast parameter must be greater than zero")

        # Make sure Q star is up to date
        self.get_qstar(extrapolation)

        if self._qstar <= 0:
            msg = "Invalid invariant: Invariant Q* must be greater than zero\n"
            msg += "Please check if scale and background values are correct"
            raise RuntimeError(msg)

        # Compute intermediate constant
        k = 1.e-8 * self._qstar / (2 * (math.pi * math.fabs(float(contrast))) ** 2)
        # Check discriminant value
        discrim = 1 - 4 * k

        # Compute volume fraction
        if discrim < 0:
            msg = "Could not compute the volume fraction: negative discriminant"
            raise RuntimeError(msg)
        elif discrim == 0:
            return 1 / 2
        else:
            volume1 = 0.5 * (1 - math.sqrt(discrim))
            volume2 = 0.5 * (1 + math.sqrt(discrim))

            if volume1 >= 0 and volume1 <= 1:
                return volume1
            elif volume2 >= 0 and volume2 <= 1:
                return volume2
            msg = "Could not compute the volume fraction: inconsistent results"
            raise RuntimeError(msg)

    def get_qstar_with_error(self, extrapolation=None):
        """
        Compute the invariant uncertainty.
        This uncertainty computation depends on whether or not the data is
        smeared.

        :param extrapolation: string to apply optional extrapolation

        :return: invariant, the invariant uncertainty
        """
        self.get_qstar(extrapolation)
        return self._qstar, self._qstar_err

    def get_volume_fraction_with_error(self, contrast, extrapolation=None):
        """
        Compute uncertainty on volume value as well as the volume fraction
        This uncertainty is given by the following equation: ::

            sigV = dV/dq_star * sigq_star

        so that: ::

            sigV = (k * sigq_star) /(q_star * math.sqrt(1 - 4 * k))

            for k = 10^(-8)*q_star/(2*(pi*|contrast|)**2)

        Notes:

        - 10^(-8) converts from cm^-1 to A^-1
        - q_star: the invariant, in cm^-1A^-3, including extrapolated values
          if they have been requested
        - dq_star: the invariant uncertainty
        - dV: the volume uncertainty

        The uncertainty will be set to -1 if it can't be computed.

        :param contrast: contrast value
        :param extrapolation: string to apply optional extrapolation

        :return: V, dV = volume fraction, error on volume fraction
        """
        volume = self.get_volume_fraction(contrast, extrapolation)

        # Compute error
        k = 1.e-8 * self._qstar / (2 * (math.pi * \
                                        math.fabs(float(contrast)))** 2)
        # Check value inside the sqrt function
        value = 1 - k * self._qstar
        if (value) <= 0:
            uncertainty = -1
        else:
            # Compute uncertainty
            uncertainty = math.fabs((k * self._qstar_err)
                                    / (self._qstar * math.sqrt(1 - 4 * k)))

        return volume, uncertainty

    def get_surface_with_error(self, contrast, porod_const, extrapolation=None):
        """
        As of SasView 4.3 and 5.0.3, the specific surface is computed directly
        from the contrast and porod_constant wich are currently user inputs
        with no option for any uncertainty so no uncertainty can be calculated.
        However we include the uncertainty computation for future use if and
        when these values get an uncertainty. This is given as: ::

            ds = sqrt[(s\'_cp)**2 * dcp**2 + (s\'_contrast)**2 * dcontrast**2]

        where s'_x is the partial derivative of S with respect to x

        which gives (this should be checked before using in anger): ::

            ds = sqrt((dporod_const**2 * contrast**2 + 4 * (porod_const *
                          dcontrast)**2) / (4 * pi**2 * contrast**6))

        We also assume some users will never enter a value for uncertainty so
        allow for None even when it is an option.

        :param contrast: contrast value eventually with the error
        :param porod_const: porod constant value eventually with the error
        :param extrapolation: string to apply optional extrapolation. This will
               only be needed if and when the contrast term is calculated from
               the invariant.

        :return s, ds: the surface, with its uncertainty
        """
        # until contrast and porod_constant are given with uncertainties set
        # them to 0
        dcontrast = None
        dporod_const = None
        # IMPORTATN: the porod constant (and eventually its uncertainty) are
        # given in units of cm^-1 A^-4.  We need to be mindfult of units when
        # writing equations. Thus for computing ds both the porod constant and
        # its uncertainty need to be converted to A^-5 so they play well with
        # the contrast which is in A-2.
        # Note that the porod constant is converted in self.get_surface method
        #so do NOT convert before calling here
        s = self.get_surface(contrast=contrast, porod_const=porod_const)
        # Until uncertainties in contrast and the Porod Constant are provided
        # just return nothing.
        ds = None
        # When they are available, use the following:
        # if dporod_const is None:
        #     _dporod_const = 0.
        # else:
        #     _dporod_const = dporod_const * 1e-8
        # if dcontrast is None:
        #    dcontrast = 0.
        # For this new computation we DO need to convert the units
        # _porod_const = porod_const * 1e-8
        #ds = math.sqrt((_dporod_const**2 * contrast**2 + 4 * (_porod_const *
        #                 dcontrast)**2 / (4 * math.pi**2 * constrast**6))

        return s, ds
