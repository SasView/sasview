"""
This module implements corfunc
"""


from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import numpy as np
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
from scipy.signal import argrelextrema
from numpy.linalg import lstsq

from sas.sascalc.corfunc.calculation_data import (TransformedData,
                                                  ExtractedParameters,
                                                  SupplementaryParameters,
                                                  TangentMethod,
                                                  LongPeriodMethod)

from sas.sascalc.corfunc.extrapolation_data import ExtrapolationParameters

from sasdata.dataloader.data_info import Data1D
from sas.sascalc.corfunc.transform_thread import FourierThread
from sas.sascalc.corfunc.transform_thread import HilbertThread
from sas.sascalc.corfunc.smoothing import SmoothJoin



class CorfuncCalculator:

    def __init__(self,
                 data: Optional[Data1D]=None,
                 lowerq: Optional[float]=None,
                 upperq: Optional[Tuple[float, float]]=None,
                 scale: float=1.0):
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

    @property
    def extrapolation_parameters(self) -> Optional[ExtrapolationParameters]:
        if self._data is None or self.lowerq is None or self.upperq is None:
            return None
        else:
            return ExtrapolationParameters(
                min(self._data.x),
                self.lowerq,
                self.upperq[0],
                self.upperq[1],
                max(self._data.x))

    @extrapolation_parameters.setter
    def extrapolation_parameters(self, extrap: ExtrapolationParameters):
        self.lowerq = extrap.point_1
        self.upperq = (extrap.point_2, extrap.point_3)


    def set_data(self, data: Optional[Data1D], scale: float=1):
        """
        Prepares the data for analysis

        :return: new_data = data * scale - background
        """
        if data is None:
            return
        # Only process data of the class Data1D
        if not issubclass(data.__class__, Data1D):
            raise ValueError("Correlation function cannot be computed with 2D data.")

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
        if self._transform_thread is None:
            return False

        return self._transform_thread.isrunning()

    def stop_transform(self):
        if self._transform_thread.isrunning():
            self._transform_thread.stop()

    def extract_parameters(self,
                           transformed_data: TransformedData,
                           tangent_method: Optional[TangentMethod]=None,
                           long_period_method: Optional[LongPeriodMethod]=None
                           ) -> Optional[Tuple[ExtractedParameters, SupplementaryParameters]]:
        """
        Extract the interesting measurements from a correlation function

        :param transformed_data: TransformedData object
        :param tangent_method: Optional string that selects the method used to calculate the point where the
                               tangent is measured, either 'inflection' to use the first inflection point,
                               or 'half-min' to use the point half way between zero and minimum.
                               Default of None will automatically select based on the existence of an inflection
                               point before the first minimum.
        :param long_period_method: Optional string that selects the method used for determining the long period,
                                 either 'max' to use the maximum, or 'double-min' to use 2x the minimum,
                                 Default of None will do it automatically based on the existence of a maximum.

        """

        gamma_1 = transformed_data.gamma_1  # 1D transform
        idf = transformed_data.idf

        # Calculate indexes of maxima and minima
        z = gamma_1.x
        gamma = gamma_1.y
        gamma_fun = interp1d(z, gamma)

        maxs = argrelextrema(gamma, np.greater)[0]
        mins = argrelextrema(gamma, np.less)[0]

        # If there are no maxima, return None
        if len(maxs) == 0:
            return None

        gamma_min = gamma[mins[0]]  # The value at the first minimum
        z_at_min = z[mins[0]]

        dgamma_dz = (gamma[2:]-gamma[:-2])/(z[2:]-z[:-2])  # 1st derivative of y


        # Find where the second derivative goes to zero
        #  * the IDF is the second derivative of gamma_1
        #  * ... but has a large DC component that needs to be ignored

        above_zero = idf.y[1:] > 0

        zero_crossings = \
            np.argwhere(
                np.logical_xor(
                    above_zero[1:],
                    above_zero[:-1]))[:, 0]

        inflection_point_index = zero_crossings[0] + 1 # +1 for ignoring DC, left side of crossing, not right

        #
        # Work out the tangent index based on the method specified
        #

        if tangent_method is None:
            if inflection_point_index < mins[0]:
                tangent_method = TangentMethod.INFLECTION
            else:
                tangent_method = TangentMethod.HALF_MIN

        if tangent_method == TangentMethod.INFLECTION:
            tangent_index = inflection_point_index
        elif tangent_method == TangentMethod.HALF_MIN:
            tangent_index = mins[0] // 2
        else:
            raise ValueError(f"Unknown tangent calculation method: '{tangent_method}', options are {TangentMethod.options}")

        #
        # Work out the long period index based on the method specified
        #

        if long_period_method is None:
            if len(maxs) > 0:
                long_period_method = LongPeriodMethod.MAX
            else:
                long_period_method = LongPeriodMethod.DOUBLE_MIN

        if long_period_method == LongPeriodMethod.MAX:
            long_period = z[maxs[0]]
        elif long_period_method == LongPeriodMethod.DOUBLE_MIN:
            long_period = z_at_min * 2
        else:
            raise ValueError(f"Unknown long period calculation method: '{long_period_method}', options are {LongPeriodMethod.options}")

        # Try to calculate slope around linear_point using 80 data points
        tangent_region_lower = tangent_index - 40
        tangent_region_upper = tangent_index + 40

        # If too few data points to the left, use linear_point*2 data points
        if tangent_region_lower < 0:
            tangent_region_lower = 0
            tangent_region_upper = inflection_point_index * 2

        # If too few to right, use 2*(dy.size - linear_point) data points
        elif tangent_region_upper > len(dgamma_dz):
            tangent_region_upper = len(dgamma_dz)
            tangent_region_lower = 2*inflection_point_index - dgamma_dz.size

        # Slope at inflection point calculated by mean over inflection region
        tangent_slope = np.mean(dgamma_dz[tangent_region_lower:tangent_region_upper])  # Linear slope
        tangent_intercept = gamma[1:-1][tangent_index]-tangent_slope*z[1:-1][tangent_index]  # Linear intercept

        hard_block_thickness = (gamma_min - tangent_intercept) / tangent_slope  # Hard block thickness
        soft_block_thickness = long_period - hard_block_thickness

        # Find the data points where the graph is linear to within 1%
        mask = np.where(np.abs((gamma-(tangent_slope*z+tangent_intercept))/gamma) < 0.01)[0]

        if len(mask) == 0:  # Return garbage for bad fits
            return None

        interface_thickness = z[mask[0]]  # Beginning of Linear Section
        core_thickness = z[mask[-1]]  # End of Linear Section

        local_crystallinity = hard_block_thickness / long_period

        gamma_max = gamma[mask[-1]]

        polydispersity_ryan = np.abs(gamma_min / gamma_max)  # Normalized depth of minimum
        polydispersity_stribeck = np.abs(local_crystallinity / ((local_crystallinity - 1) * gamma_max))  # Normalized depth of minimum


        supplementary_parameters = SupplementaryParameters(
            tangent_point_z=z[tangent_index],
            tangent_point_gamma=gamma[tangent_index],
            tangent_gradient=float(tangent_slope),
            first_minimum_z=z_at_min,
            first_minimum_gamma=gamma_min,
            first_maximum_z=long_period,
            first_maximum_gamma=gamma_fun(long_period),
            hard_block_z=hard_block_thickness,
            hard_block_gamma=gamma_min,
            interface_z=interface_thickness,
            core_z=core_thickness,
            z_range=(1 / transformed_data.q_range[1], 1 / transformed_data.q_range[0]),
            gamma_range=(np.min(gamma), np.max(gamma))
        )

        extracted_parameters = ExtractedParameters(
                    long_period,
                    interface_thickness,
                    hard_block_thickness,
                    soft_block_thickness,
                    core_thickness,
                    polydispersity_ryan,
                    polydispersity_stribeck,
                    local_crystallinity)

        return extracted_parameters, supplementary_parameters


    def _porod(self, q, K, sigma, bg):
        """Equation for the Porod region of the data"""
        return bg + (K*q**(-4))*np.exp(-q**2*sigma**2)

    def _fit_guinier(self, q, iq):
        """Fit the Guinier region of the curve"""
        A = np.vstack([q**2, np.ones(q.shape)]).T
        # CRUFT: numpy>=1.14.0 allows rcond=None for the following default
        rcond = np.finfo(float).eps * max(A.shape)
        return lstsq(A, np.log(iq), rcond=rcond)

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
        s1 = SmoothJoin(data,
                        lambda x: self._porod(x, k, sigma, bg), self.upperq[0], self.upperq[1])

        mask = np.logical_and(q < self.lowerq, 0 < q)

        # Returns parameters for the best-fit Guinier function
        g = self._fit_guinier(q[mask], iq[mask])[0]

        # Smooths between the best-fit Guinier function and the Porod curve
        s2 = SmoothJoin((lambda x: (np.exp(g[1] + g[0] * x ** 2))), s1, q[0],
                        self.lowerq)

        params = {'A': g[1], 'B': g[0], 'K': k, 'sigma': sigma}

        return params, s2
