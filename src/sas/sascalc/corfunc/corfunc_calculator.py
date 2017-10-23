"""
This module implements corfunc
"""
import warnings
import numpy as np
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
from scipy.fftpack import dct
from scipy.signal import argrelextrema
from numpy.linalg import lstsq
from sas.sascalc.dataloader.data_info import Data1D
from sas.sascalc.corfunc.transform_thread import FourierThread
from sas.sascalc.corfunc.transform_thread import HilbertThread

class CorfuncCalculator(object):

    class _Interpolator(object):
        """
        Interpolates between curve f and curve g over the range start:stop and
        caches the result of the function when it's called

        :param f: The first curve to interpolate
        :param g: The second curve to interpolate
        :param start: The value at which to start the interpolation
        :param stop: The value at which to stop the interpolation
        """
        def __init__(self, f, g, start, stop):
            self.f = f
            self.g = g
            self.start = start
            self.stop = stop
            self._lastx = []
            self._lasty = []

        def __call__(self, x):
            # If input is a single number, evaluate the function at that number
            # and return a single number
            if type(x) == float or type(x) == int:
                return self._smoothed_function(np.array([x]))[0]
            # If input is a list, and is different to the last input, evaluate
            # the function at each point. If the input is the same as last time
            # the function was called, return the result that was calculated
            # last time instead of explicity evaluating the function again.
            elif self._lastx == [] or x.tolist() != self._lastx.tolist():
                self._lasty = self._smoothed_function(x)
                self._lastx = x
            return self._lasty

        def _smoothed_function(self,x):
            ys = np.zeros(x.shape)
            ys[x <= self.start] = self.f(x[x <= self.start])
            ys[x >= self.stop] = self.g(x[x >= self.stop])
            with warnings.catch_warnings():
                # Ignore divide by zero error
                warnings.simplefilter('ignore')
                h = 1/(1+(x-self.stop)**2/(self.start-x)**2)
            mask = np.logical_and(x > self.start, x < self.stop)
            ys[mask] = h[mask]*self.g(x[mask])+(1-h[mask])*self.f(x[mask])
            return ys


    def __init__(self, data=None, lowerq=None, upperq=None, scale=1):
        """
        Initialize the class.

        :param data: Data of the type DataLoader.Data1D
        :param lowerq: The Q value to use as the boundary for
            Guinier extrapolation
        :param upperq: A tuple of the form (lower, upper).
            Values between lower and upper will be used for Porod extrapolation
        :param scale: Scaling factor for I(q)
        """
        self._data = None
        self.set_data(data, scale)
        self.lowerq = lowerq
        self.upperq = upperq
        self.background = self.compute_background()
        self._transform_thread = None

    def set_data(self, data, scale=1):
        """
        Prepares the data for analysis

        :return: new_data = data * scale - background
        """
        if data is None:
            return
        # Only process data of the class Data1D
        if not issubclass(data.__class__, Data1D):
            raise ValueError("Data must be of the type DataLoader.Data1D")

        # Prepare the data
        new_data = Data1D(x=data.x, y=data.y)
        new_data *= scale

        # Ensure the errors are set correctly
        if new_data.dy is None or len(new_data.x) != len(new_data.dy) or \
            (min(new_data.dy) == 0 and max(new_data.dy) == 0):
            new_data.dy = np.ones(len(new_data.x))

        self._data = new_data

    def compute_background(self, upperq=None):
        """
        Compute the background level from the Porod region of the data
        """
        if self._data is None: return 0
        elif upperq is None and self.upperq is not None: upperq = self.upperq
        elif upperq is None and self.upperq is None: return 0
        q = self._data.x
        mask = np.logical_and(q > upperq[0], q < upperq[1])
        _, _, bg = self._fit_porod(q[mask], self._data.y[mask])

        return bg

    def compute_extrapolation(self):
        """
        Extrapolate and interpolate scattering data

        :return: The extrapolated data
        """
        q = self._data.x
        iq = self._data.y

        params, s2 = self._fit_data(q, iq)
        # Extrapolate to 100*Qmax in experimental data
        qs = np.arange(0, q[-1]*100, (q[1]-q[0]))
        iqs = s2(qs)

        extrapolation = Data1D(qs, iqs)

        return params, extrapolation, s2

    def compute_transform(self, extrapolation, trans_type, background=None,
        completefn=None, updatefn=None):
        """
        Transform an extrapolated scattering curve into a correlation function.

        :param extrapolation: The extrapolated data
        :param background: The background value (if not provided, previously
            calculated value will be used)
        :param extrap_fn: A callable function representing the extraoplated data
        :param completefn: The function to call when the transform calculation
            is complete
        :param updatefn: The function to call to update the GUI with the status
            of the transform calculation
        :return: The transformed data
        """
        if self._transform_thread is not None:
            if self._transform_thread.isrunning(): return

        if background is None: background = self.background

        if trans_type == 'fourier':
            self._transform_thread = FourierThread(self._data, extrapolation,
            background, completefn=completefn,
            updatefn=updatefn)
        elif trans_type == 'hilbert':
            self._transform_thread = HilbertThread(self._data, extrapolation,
            background, completefn=completefn, updatefn=updatefn)
        else:
            err = ("Incorrect transform type supplied, must be 'fourier'",
                " or 'hilbert'")
            raise ValueError(err)

        self._transform_thread.queue()

    def transform_isrunning(self):
        if self._transform_thread is None: return False
        return self._transform_thread.isrunning()

    def stop_transform(self):
        if self._transform_thread.isrunning():
            self._transform_thread.stop()

    def extract_parameters(self, transformed_data):
        """
        Extract the interesting measurements from a correlation function

        :param transformed_data: Fourier transformation of the extrapolated data
        """
        # Calculate indexes of maxima and minima
        x = transformed_data.x
        y = transformed_data.y
        maxs = argrelextrema(y, np.greater)[0]
        mins = argrelextrema(y, np.less)[0]

        # If there are no maxima, return None
        if len(maxs) == 0:
            return None

        GammaMin = y[mins[0]]  # The value at the first minimum

        ddy = (y[:-2]+y[2:]-2*y[1:-1])/(x[2:]-x[:-2])**2  # 2nd derivative of y
        dy = (y[2:]-y[:-2])/(x[2:]-x[:-2])  # 1st derivative of y
        # Find where the second derivative goes to zero
        zeros = argrelextrema(np.abs(ddy), np.less)[0]
        # locate the first inflection point
        linear_point = zeros[0]

        # Try to calculate slope around linear_point using 80 data points
        lower = linear_point - 40
        upper = linear_point + 40

        # If too few data points to the left, use linear_point*2 data points
        if lower < 0:
            lower = 0
            upper = linear_point * 2
        # If too few to right, use 2*(dy.size - linear_point) data points
        elif upper > len(dy):
            upper = len(dy)
            width = len(dy) - linear_point
            lower = 2*linear_point - dy.size

        m = np.mean(dy[lower:upper])  # Linear slope
        b = y[1:-1][linear_point]-m*x[1:-1][linear_point]  # Linear intercept

        Lc = (GammaMin-b)/m  # Hard block thickness

        # Find the data points where the graph is linear to within 1%
        mask = np.where(np.abs((y-(m*x+b))/y) < 0.01)[0]
        if len(mask) == 0:  # Return garbage for bad fits
            return { 'max': self._round_sig_figs(x[maxs[0]], 6) }
        dtr = x[mask[0]]  # Beginning of Linear Section
        d0 = x[mask[-1]]  # End of Linear Section
        GammaMax = y[mask[-1]]
        A = np.abs(GammaMin/GammaMax)  # Normalized depth of minimum

        params = {
            'max': x[maxs[0]],
            'dtr': dtr,
            'Lc': Lc,
            'd0': d0,
            'A': A,
            'fill': Lc/x[maxs[0]]
        }

        return params


    def _porod(self, q, K, sigma, bg):
        """Equation for the Porod region of the data"""
        return bg + (K*q**(-4))*np.exp(-q**2*sigma**2)

    def _fit_guinier(self, q, iq):
        """Fit the Guinier region of the curve"""
        A = np.vstack([q**2, np.ones(q.shape)]).T
        return lstsq(A, np.log(iq))

    def _fit_porod(self, q, iq):
        """Fit the Porod region of the curve"""
        fitp = curve_fit(lambda q, k, sig, bg: self._porod(q, k, sig, bg)*q**2,
                         q, iq*q**2, bounds=([-np.inf, 0, -np.inf], [np.inf, np.inf, np.inf]))[0]
        k, sigma, bg = fitp
        return k, sigma, bg

    def _fit_data(self, q, iq):
        """
        Given a data set, extrapolate out to large q with Porod and
        to q=0 with Guinier
        """
        mask = np.logical_and(q > self.upperq[0], q < self.upperq[1])

        # Returns an array where the 1st and 2nd elements are the values of k
        # and sigma for the best-fit Porod function
        k, sigma, _ = self._fit_porod(q[mask], iq[mask])
        bg = self.background

        # Smooths between the best-fit porod function and the data to produce a
        # better fitting curve
        data = interp1d(q, iq)
        s1 = self._Interpolator(data,
            lambda x: self._porod(x, k, sigma, bg), self.upperq[0], q[-1])

        mask = np.logical_and(q < self.lowerq, 0 < q)

        # Returns parameters for the best-fit Guinier function
        g = self._fit_guinier(q[mask], iq[mask])[0]

        # Smooths between the best-fit Guinier function and the Porod curve
        s2 = self._Interpolator((lambda x: (np.exp(g[1]+g[0]*x**2))), s1, q[0],
            self.lowerq)

        params = {'A': g[1], 'B': g[0], 'K': k, 'sigma': sigma}

        return params, s2
