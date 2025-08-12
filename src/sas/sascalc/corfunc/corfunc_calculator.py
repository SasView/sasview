"""
This module implements corfunc
"""


from collections.abc import Callable

import numpy as np
import scipy.optimize
from scipy.fftpack import dct
from scipy.integrate import cumulative_trapezoid, trapezoid
from scipy.interpolate import interp1d
from scipy.signal import argrelextrema

from sasdata.dataloader.data_info import Data1D

from sas.sascalc.corfunc.calculation_data import (
    ExtrapolationParameters,
    Fittable,
    GuinierData,
    LamellarParameters,
    LongPeriodMethod,
    PorodData,
    SettableExtrapolationParameters,
    SupplementaryParameters,
    TangentMethod,
    TransformedData,
)
from sas.sascalc.corfunc.smoothing import SmoothJoin


class CalculationError(Exception):
    """ Error doing calculation"""
    def __init__(self, msg: str):
        self.msg = msg
        super().__init__(msg)

class CorfuncCalculator:

    def __init__(self,
                 data: Data1D | None = None,
                 extrapolation_parameters: SettableExtrapolationParameters | None = None,
                 long_period_method: LongPeriodMethod | None = None,
                 tangent_method: TangentMethod | None = None):

        """
        Back-end for corfunc calculations

        :param data: Input data (Data1D)
        :param extrapolation_parameters: SettableExtrapolationParameters object containing the q values use to extrapolate
        """

        # Input data
        self._data = data

        # Input parameters
        self._extrapolation_parameters: SettableExtrapolationParameters | None = extrapolation_parameters
        self.tangent_method: TangentMethod | None = tangent_method
        self.long_period_method: LongPeriodMethod | None = long_period_method

        # Fittable parameters
        self._background: Fittable[float] = Fittable()
        self._porod: Fittable[PorodData] = Fittable()
        self._guinier: Fittable[GuinierData] = Fittable()

        # Derived quantities
        self._background_subtracted: np.ndarray | None = None
        self._extrapolation_function: SmoothJoin | None = None
        self._extrapolation_data: Data1D | None = None
        self._transformed_data: TransformedData | None = None
        self._lamellar_parameters: LamellarParameters | None = None
        self._supplementary_parameters: SupplementaryParameters | None = None

    def reset_calculated_values(self):

        """ Resets the calculated values, but does not clear the data or reset the user specified parameters """

        # Fitted parameters
        self._background.clear()
        self._porod.clear()
        self._guinier.clear()

        # Derived quantities
        self._background_subtracted: np.ndarray | None = None
        self._extrapolation_function: SmoothJoin | None = None
        self._extrapolation_data: Data1D | None = None
        self._transformed_data: TransformedData | None = None
        self._lamellar_parameters: LamellarParameters | None = None
        self._supplementary_parameters: SupplementaryParameters | None = None



    #
    # Getters and setters
    #

    @property
    def extrapolation_parameters(self) -> ExtrapolationParameters | None:
        if self._data is None or self._extrapolation_parameters is None:
            return None
        else:
            return ExtrapolationParameters(
                min(self._data.x),
                self._extrapolation_parameters.point_1,
                self._extrapolation_parameters.point_2,
                self._extrapolation_parameters.point_3,
                max(self._data.x))

    @extrapolation_parameters.setter
    def extrapolation_parameters(self, extrap: ExtrapolationParameters):
        self._extrapolation_parameters = SettableExtrapolationParameters(
            extrap.point_1,
            extrap.point_2,
            extrap.point_3)


    @property
    def data(self) -> Data1D | None:
        return self._data

    @data.setter
    def data(self, data: Data1D | None):
        if data is None:
            return

        # Only process data of the class Data1D
        if not issubclass(data.__class__, Data1D):
            raise ValueError("Correlation function cannot be computed with 2D data.")

        self._data = data

    @property
    def q_range(self) -> tuple[float, float]:
        return self.data.x[0], self.data.x[-1]
    @property
    def background(self):
        if self._background is None:
            return None

        return self._background.data

    @background.setter
    def background(self, value: float | None):
        self._background.data = value

    @property
    def guinier(self):
        if self._guinier is None:
            return None

        return self._guinier.data

    @guinier.setter
    def guinier(self, value: GuinierData | None):
        self._guinier.data = value

    @property
    def porod(self):
        if self._porod is None:
            return None

        return self._porod.data

    @porod.setter
    def porod(self, value: PorodData | None):
        self._porod.data = value

    @property
    def transformed(self):
        return self._transformed_data

    @property
    def lamellar_parameters(self) -> LamellarParameters:
        return self._lamellar_parameters

    @property
    def supplementary_parameters(self) -> SupplementaryParameters | None:
        return self._supplementary_parameters

    @property
    def extrapolation_function(self) -> Callable | None:
        return self._extrapolation_function

    @property
    def min_extrapolated(self) -> float | None:
        if self._extrapolation_data is None:
            return None
        else:
            return np.min(self._extrapolation_data.y)

    @property
    def fit_background(self):
        return self._background.allow_fit

    @fit_background.setter
    def fit_background(self, value: bool):
        self._background.allow_fit = value

    @property
    def fit_guinier(self):
        return self._guinier.allow_fit

    @fit_guinier.setter
    def fit_guinier(self, value: bool):
        self._guinier.allow_fit = value

    @property
    def fit_porod(self):
        return self._porod.allow_fit

    @fit_porod.setter
    def fit_porod(self, value: bool):
        self._porod.allow_fit = value

    @property
    def extrapolated(self):
        return self._extrapolation_data

    #
    # Calculation Steps
    #


    def run(self):
        """ Execute the calculation"""
        self._calculate_background()
        self._calculate_background_subtracted()
        self._calculate_porod_parameters()
        self._calculate_guinier_parameters()
        self._calculate_extrapolation_function()
        self._calculate_extrapolation_data()
        self._calculate_transforms()
        self._calculate_parameters()



    # Calculation components

    def _calculate_background(self):
        """
        Compute the background level from the Porod region of the data,
        only do this if background fitting is allowed
        """
        if self._data is None:
            raise ValueError("Data not set")

        if self._extrapolation_parameters is None:
            raise ValueError("Extrapolation settings not specified")

        if self._background.allow_fit:

            q = self._data.x

            # Fit the last section only
            point_2 = self._extrapolation_parameters.point_2
            point_3 = self._extrapolation_parameters.point_3
            mask = np.logical_and(q > point_2, q < point_3)

            _, _, background = CorfuncCalculator.calculate_porod_parameters(q[mask], self._data.y[mask])

            self._background.data = background

    def _calculate_background_subtracted(self):
        """ Calculate the data with the background removed"""

        if self._data is None:
            raise ValueError("Data not set")

        if self._background.data is None:
            raise ValueError("Background value not set")

        self._background_subtracted = self._data.y - self._background.data


    def _calculate_porod_parameters(self):
        """
        Calculate the Porod parameters
        """

        if self._data is None:
            raise ValueError("Data not set")

        if self._extrapolation_parameters is None:
            raise ValueError("Extrapolation settings not specified")

        if self._porod.allow_fit:
            # Fit the last section only

            q = self.data.x

            point_2 = self._extrapolation_parameters.point_2
            point_3 = self._extrapolation_parameters.point_3
            mask = np.logical_and(q > point_2, q < point_3)

            # Returns an array where the 1st and 2nd elements are the values of k
            # and sigma for the best-fit Porod function
            K, sigma, _ = CorfuncCalculator.calculate_porod_parameters(q[mask], self.data.y[mask])

            self._porod.data = PorodData(K=K, sigma=sigma)



    def _calculate_guinier_parameters(self):
        # Smooths between the best-fit porod function and the data to produce a
        # better fitting curve
        # Returns parameters for the best-fit Guinier function


        if self._data is None:
            raise ValueError("Data not set")

        if self._extrapolation_parameters is None:
            raise ValueError("Extrapolation settings not specified")

        if self._background_subtracted is None:
            raise ValueError("Backgroundless data not set")

        if self._guinier.allow_fit:

            q = self.data.x
            mask = np.logical_and(q < self._extrapolation_parameters.point_1, q > 0)

            g = CorfuncCalculator.calculate_guinier_parameters(q[mask], self._background_subtracted[mask])

            self._guinier.data = GuinierData(A=g[0], B=g[1])

    def _calculate_extrapolation_function(self):

        if self.data is None:
            raise ValueError("Data not set")

        if self._background.data is None:
            raise ValueError("Background is not set")

        if self._porod.data is None:
            raise ValueError("Porod parameters not set")

        if self._guinier.data is None:
            raise ValueError("Guinier parameters not set")

        data_function = interp1d(self.data.x, self.data.y) # Note that this still has background values

        # Smooth between data and Porod
        s1 = SmoothJoin(
                data_function,
                CorfuncCalculator.porod_function(
                    self._porod.data.K,
                    self._porod.data.sigma,
                    self._background.data),
                self._extrapolation_parameters.point_2,
                self._extrapolation_parameters.point_3)

        # Smooth between the previous function and Guinier
        s2 = SmoothJoin(
                CorfuncCalculator.guinier_function(
                    self._guinier.data.A,
                    self._guinier.data.B,
                    self._background.data),
                s1,
                self.data.x[0],
                self._extrapolation_parameters.point_1)

        self._extrapolation_function = s2

        # params = {'A': g[1], 'B': g[0], 'K': k, 'sigma': sigma}



    def _calculate_extrapolation_data(self):
        """ Numerically evaluate the extrapolation curve """

        if self.data is None:
            raise ValueError("Data not set")

        if self._extrapolation_function is None:
            raise ValueError("Extrapolation function not set")

        q = self.data.x

        extrapolated_q = np.arange(0, q[-1]*100, (q[1]-q[0]))
        extrapolated_I = self._extrapolation_function(extrapolated_q)

        self._extrapolation_data = Data1D(extrapolated_q, extrapolated_I)

    def _calculate_transforms(self):

        """ Calculate the transforms """

        if self.data is None:
            raise ValueError("Data not set")

        if self._background.data is None:
            raise ValueError("Background not set")

        if self._extrapolation_data is None:
            raise ValueError("Extrapolation data not set")


        qs = self._extrapolation_data.x
        iqs = self._extrapolation_data.y
        q = self.data.x
        background = self._background.data

        xs = np.pi * np.arange(len(qs), dtype=np.float32) / (q[1] - q[0]) / len(qs)

        # 1D Correlation Function
        gamma1 = dct((iqs - background) * (qs ** 2))
        Q = np.max(gamma1)
        gamma1 /= Q

        # 3D Correlation Function
        # gamma3(R) = 1/R int_{0}^{R} gamma1(x) dx
        # numerical approximation for increasing R using the trapezium rule
        # Note: SasView 4.x series limited the range to xs <= 1000.0

        gamma3 = cumulative_trapezoid(gamma1, xs) / xs[1:]
        gamma3 = np.hstack((1.0, gamma3))  # gamma3(0) is defined as 1

        # Interface Distribution function
        idf = dct(-qs ** 4 * (iqs - background))

        # Manually calculate IDF(0.0), since scipy DCT tends to give us a
        # very large negative value.

        #    IDF(x) = int_0^inf q^4 * I(q) * cos(q*x) * dq
        # => IDF(0) = int_0^inf q^4 * I(q) * dq

        idf[0] = trapezoid(-qs ** 4 * (iqs - background), qs)
        idf /= Q  # Normalise using scattering invariant

        transform1d = Data1D(xs, gamma1)
        transform3d = Data1D(xs, gamma3)
        idf = Data1D(xs, idf)

        self._transformed_data = TransformedData(transform1d, transform3d, idf)


    def _calculate_parameters(self):
        """
        Extract the interesting measurements from a correlation function
        """

        gamma_1 = self._transformed_data.gamma_1  # 1D transform
        idf = self._transformed_data.idf

        # Calculate indexes of maxima and minima
        z = gamma_1.x
        gamma = gamma_1.y
        gamma_fun = interp1d(z, gamma)

        maxs = argrelextrema(gamma, np.greater)[0]
        mins = argrelextrema(gamma, np.less)[0]

        # If there are no maxima, return None
        if len(maxs) == 0:
            raise CalculationError("No maxima found in data")

        max_values = gamma[maxs]
        largest_max = np.argmax(max_values)

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

        tangent_method = self.tangent_method

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

        long_period_method = self.long_period_method

        if long_period_method is None:
            if len(maxs) > 0:
                long_period_method = LongPeriodMethod.MAX
            else:
                long_period_method = LongPeriodMethod.DOUBLE_MIN

        if long_period_method == LongPeriodMethod.MAX:
            long_period = z[maxs[largest_max]]
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
            raise CalculationError("No tangent values found")

        interface_thickness = z[mask[0]]  # Beginning of Linear Section
        core_thickness = z[mask[-1]]  # End of Linear Section

        local_crystallinity = hard_block_thickness / long_period

        gamma_max = gamma[mask[-1]]

        polydispersity_ryan = np.abs(gamma_min / gamma_max)  # Normalized depth of minimum
        polydispersity_stribeck = np.abs(local_crystallinity / ((local_crystallinity - 1) * gamma_max))  # Normalized depth of minimum

        self._supplementary_parameters = SupplementaryParameters(
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
            z_range=(1 / self.data.x[-1], 1 / self.data.x[0]),
            gamma_range=(np.min(gamma), np.max(gamma)))

        self._lamellar_parameters = LamellarParameters(
            long_period=long_period,
            interface_thickness=interface_thickness,
            hard_block_thickness=hard_block_thickness,
            soft_block_thickness=soft_block_thickness,
            core_thickness=core_thickness,
            polydispersity_ryan=polydispersity_ryan,
            polydispersity_stribeck=polydispersity_stribeck,
            local_crystallinity=local_crystallinity)


    #
    # Utility functions / Static methods
    #

    @staticmethod
    def porod_function(K, sigma, background):
        def fun(q):
            return CorfuncCalculator.porod_fitting_function(q, K, sigma, background)

        return fun

    @staticmethod
    def guinier_function(A, B, background):
        def fun(q):
            return np.exp(A + B*q*q) + background

        return fun

    @staticmethod
    def porod_fitting_function(q, K, sigma, background):
        """Equation for the Porod region of the data"""
        return background + (K * q ** (-4)) * np.exp(-q ** 2 * sigma ** 2)

    @staticmethod
    def porod_fitting_function_expected(q, K, sigma, background):
        """ Expected value function used for fitting Porod region (has a q^2 weighting)"""
        return CorfuncCalculator.porod_fitting_function(q, K, sigma, background) * (q * q)

    @staticmethod
    def porod_fitting_function_observed(q, I):
        """ Observed value function used for fitting Porod region"""
        return I * q * q

    @staticmethod
    def calculate_guinier_parameters(q, I):
        """Fit the Guinier region of the curve using linear least squares"""
        A = np.vstack([np.ones(q.shape), q**2]).T

        return np.linalg.lstsq(A, np.log(I))[0]

    @staticmethod
    def calculate_porod_parameters(q, I):
        """Fit the Porod region of the curve"""
        fitp = scipy.optimize.curve_fit(
            CorfuncCalculator.porod_fitting_function_expected, q,
            CorfuncCalculator.porod_fitting_function_observed(q, I),
            bounds=([-np.inf, 0, -np.inf], [np.inf, np.inf, np.inf]))[0]

        k, sigma, bg = fitp
        return k, sigma, bg


def extract_lamellar_parameters(
        data: Data1D,
        guinier_to_data_transition_right: float,
        data_to_porod_transition_left: float,
        data_to_porod_transition_right: float,
        long_period_method: LongPeriodMethod | None=None,
        tangent_method: TangentMethod | None=None):

    """
    Extract lamellar parameters from data using the corfunc calculator

    :param data: Data1D object containing QSpace data
    :param guinier_to_data_transition_right: Q value at which to end the extrapolation from Guiner to data
    :param data_to_porod_transition_left: Q value at which to begin the extrapolation from data to Porod
    :param data_to_porod_transition_right: Q value at which to end the extrapolation from data to Porod
    :param long_period_method: LongPeriodMethod enum value specifying how to calculate the long period (None autodetects)
    :param tangent_method: TangentMethod enum value specifying how to calculate the long period (None autodetects)

    :returns: LamellarParameters object with calculated lamellar parameters
    """

    parameters = SettableExtrapolationParameters(
        guinier_to_data_transition_right,
        data_to_porod_transition_left,
        data_to_porod_transition_right)

    calculator = CorfuncCalculator(
                    data, parameters,
                    long_period_method=long_period_method,
                    tangent_method=tangent_method)

    calculator.run()

    return calculator.lamellar_parameters
