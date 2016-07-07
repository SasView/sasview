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


    def __init__(self, data, lowerq, upperq, background=0, scale=1):
        """
        Initialize the class.

        :param data: Data of the type DataLoader.Data1D
        :param background: Background value. Will be subtracted from the data
            before processing
        :param scale: Scaling factor for I(q)
        """
        print "Before: {}".format(data.y[0])
        self._data = self._get_data(data, background, scale)
        print "After: {}".format(self._data.y[0])
        self.lowerq = lowerq
        self.upperq = upperq

    def compute_extrapolation(self):
        q = self._data.x
        iq = self._data.y

        s2 = self._fit_data(q, iq)
        qs = np.arange(0, q[-1]*100, (q[1]-q[0]))
        iqs = s2(qs)

        extrapolation = Data1D(qs, iqs)

        return extrapolation

    def compute_transform(self, extrapolation):
        """
        Transform an extrapolated scattering curve into a correlation function.
        """
        qs = extrapolation.x
        iqs = extrapolation.y

        gamma = dct(iqs*qs**2)
        gamma = gamma / gamma.max()
        xs = np.pi*np.arange(len(qs),dtype=np.float32)/(q[1]-q[0])/len(qs)

        transform = Data1D(xs, gamma)

        return transform

    def _porod(self, q, K, sigma):
        """Equation for the Porod region of the data"""
        return (K*q**(-4))*np.exp(-q**2*sigma**2)

    def _fit_guinier(self, q, iq):
        """Fit the Guinier region of the curve"""
        A = np.vstack([q**2, np.ones(q.shape)]).T
        return lstsq(A, np.log(iq))

    def _get_data(self, data, background, scale):
        """
        Prepares the data for analysis

        :return: new_data = data * scale - background
        """
        # Only process data of the class Data1D
        if not issubclass(data.__class__, Data1D):
            raise ValueError, "Data must be of the type DataLoader.Data1D"

        # Prepare the data
        new_data = (scale * data)
        new_data.y -= background

        # Check the vector lengths are equal
        assert len(new_data.x) == len(new_data.y)

        # Ensure the errors are set correctly
        if new_data.dy is None or len(new_data.x) != len(new_data.dy) or \
            (min(new_data.dy) == 0 and max(new_data.dy) == 0):
            new_data.dy = np.ones(len(new_data.x))

        return new_data

    def _fit_data(self, q, iq):
        """Given a data set, extrapolate out to large q with Porod
        and to q=0 with Guinier"""
        mask = np.logical_and(q > self.upperq[0], q < self.upperq[1])

        # Returns an array where the 1st and 2nd elements are the values of k
        # and sigma for the best-fit Porod function
        fitp = curve_fit(lambda q, k, sig: self._porod(q, k, sig)*q**2,
                         q[mask], iq[mask]*q[mask]**2)[0]

        # Smooths between the best-fit porod function and the data to produce a
        # better fitting curve
        data = interp1d(q, iq)
        s1 = self._Interpolator(data,
            lambda x: self._porod(x, fitp[0], fitp[1]), self.upperq[0], q[-1])

        mask = np.logical_and(q < self.lowerq, 0 < q)

        # Returns parameters for the best-fit Guinier function
        g = self._fit_guinier(q[mask], iq[mask])[0]

        # Smooths between the best-fit Guinier function and the Porod curve
        s2 = self._Interpolator((lambda x: (np.exp(g[1]+g[0]*x**2))), s1, q[0],
            self.lowerq)

        return s2
