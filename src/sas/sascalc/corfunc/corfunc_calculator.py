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

class CorfuncCalculator(object):

    # Helper class
    class _Struct:
        def __init__(self, **entries):
            self.__dict__.update(entries)

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
            if self._lastx == [] or x.tolist() != self._lastx.tolist():
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
        self.background = 0

    def set_data(self, data, scale=1):
        """
        Prepares the data for analysis

        :return: new_data = data * scale - background
        """
        if data is None:
            return
        # Only process data of the class Data1D
        if not issubclass(data.__class__, Data1D):
            raise ValueError, "Data must be of the type DataLoader.Data1D"

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
        elif upperq == 0: return 0
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

        s2 = self._fit_data(q, iq)
        qs = np.arange(0, q[-1]*100, (q[1]-q[0]))
        iqs = s2(qs)

        extrapolation = Data1D(qs, iqs)

        return extrapolation

    def compute_transform(self, extrapolation, background=None):
        """
        Transform an extrapolated scattering curve into a correlation function.

        :param extrapolation: The extrapolated data
        :param background: The background value (if not provided, previously
            calculated value will be used)
        :return: The transformed data
        """
        qs = extrapolation.x
        iqs = extrapolation.y
        q = self._data.x
        if background is None: background = self.background

        gamma = dct((iqs-background)*qs**2)
        gamma = gamma / gamma.max()
        xs = np.pi*np.arange(len(qs),dtype=np.float32)/(q[1]-q[0])/len(qs)

        transform = Data1D(xs, gamma)

        return transform

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
                         q, iq*q**2)[0]
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

        return s2
