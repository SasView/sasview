"""
Module for performing size distribution analysis using the Maximum Entropy method.
This module defines a `sizeDistribution` class that encapsulates the data and parameters
needed to perform size distribution analysis. The class includes methods for preparing
the data, running the Maximum Entropy method, and calculating statistics from the resulting
size distribution.
"""

import logging

import numpy as np
import numpy.typing as npt
from scipy import integrate, optimize, stats

from sasdata.dataloader.data_info import Data1D
from sasmodels.core import load_model
from sasmodels.direct_model import DirectModel

from sas.sascalc.size_distribution.maxEnt_method import maxEntMethod

logger = logging.getLogger(__name__)


def add_gaussian_noise(x: npt.ArrayLike, dx: npt.ArrayLike, seed: int | None = None) -> npt.NDArray:
    """
    Add Gaussian noise to data based on the sigma of the Gaussian uncertainty
    value associated with the data.

    :param x: input intensity values
    :param dx: sigma of Gaussian uncertainties associated with the intensities
    :param seed: random seed for reproducibility (default: None)
    :return: data with added Gaussian noise
    """
    # Convert inputs to numpy arrays
    data = np.array(x)
    std_dev = np.array(dx)

    # Validate inputs
    if len(data) != len(std_dev):
        raise ValueError("Data and sigmas must have same length")
    if np.any(std_dev <= 0):
        raise ValueError("All sigma values must be positive")

    # Generate and add noise
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, std_dev)
    noisy_data = data + noise

    return noisy_data


def line_func(x: npt.ArrayLike, b: float, m: float) -> npt.ArrayLike:
    """
    Linear function for curve fitting.

    .. math:: y = A x^m
    ln(y) = ln(A) + m*ln(x)
    where b = ln(A)

    :param x: independent variable
    :param b: ln(A) where A is the scale factor
    :param m: power law exponent
    :return: dependent variable
    """
    return b + m * x


def background_fit(
    data: Data1D,
    power: float | None = None,
    qmin: float | None = None,
    qmax: float | None = None,
) -> tuple[npt.NDArray, npt.NDArray]:
    """
    Fit data for $y = ax + b$  return $a$ and $b$

    :param Data1D data: data to fit
    :param power: a fixed, otherwise None
    :param qmin: Minimum Q-value
    :param qmax: Maximum Q-value

    If performing a linear fit for background, then set power = 0.0 and type = "fixed".
    """
    if qmin is None:
        qmin = min(data.x)
    if qmax is None:
        qmax = max(data.x)

    if not qmax > qmin:
        raise ValueError("Fit range Qmin must be smaller than Qmax")

    # Identify the bin range for the fit
    idx = (data.x >= qmin) & (data.x <= qmax)

    # Check that the fit range contains enough data points
    if (power is None and sum(idx) < 2) or (power is not None and sum(idx) < 1):
        raise ValueError("Need more data points than fitting parameters")

    fx = np.zeros(len(data.x))

    # Uncertainty
    if isinstance(data.dy, np.ndarray) and len(data.dy) == len(data.x) and np.all(data.dy > 0):
        sigma = data.dy
    else:
        sigma = np.ones(len(data.x))

    # Compute theory data f(x)
    fx[idx] = data.y[idx]

    # Linearize the data
    linearized_data = Data1D(np.log(data.x[idx]), np.log(fx[idx]), dy=sigma[idx] / fx[idx])
    # Get values of scale and if required power
    if power is not None:
        # Fit only scale
        def fit_func(x: npt.ArrayLike, b: float) -> npt.ArrayLike:
            return line_func(x, b, power)
        init_guess = linearized_data.y[0]

    else:
        # Fit both the power and scale

        fit_func = line_func
        init_guess = (linearized_data.y[0], 4.0)

    param_result, pcov = optimize.curve_fit(
        fit_func, linearized_data.x, linearized_data.y, init_guess, sigma=linearized_data.dy
    )
    param_err = np.sqrt(np.diag(pcov))

    if len(param_err) > 1:
        param_err[0] = np.exp(param_result[0]) * param_err[0]
    else:
        param_err[0] = np.exp(param_result[0]) * param_err[0]

    # Transform scale back to non-linearized
    param_result[0] = np.exp(param_result[0])

    return param_result, param_err


def ellipse_volume(rp: float, re: float) -> float:
    """
    Calculate the volume of an ellipsoid given the polar and equatorial radii.
    :param rp: polar radius
    :param re: equatorial radius
    :return: volume of the ellipsoid
    """
    return (4.0 * np.pi / 3.0) * rp * re**2


class sizeDistribution:
    """Class for performing size distribution analysis using the Maximum Entropy method."""

    def __init__(self, data: Data1D):
        # Data Manipulation
        self._data: Data1D = data
        self._qMin: float = data.x[0]
        self._qMax: float = data.x[-1]
        self._ndx_qmin: int = 0
        self._ndx_qmax: int = -1

        # MaxEntropy bin parameters
        self._diamMin: float = 10.0
        self._diamMax: float = 100000.0
        self._nbins: int = 2
        self._logbin: bool = True
        self._bins: np.ndarray | None = None

        # sasmodels
        self._model: str = "ellipsoid"
        self._aspectRatio: float = 1.0

        self._contrast: float = 1.0  # sld - sld_solvent=0.0
        self._background: float = 0.0  # Not For Model !
        self._scale: float = 1.0  # Fix to 1.0 for models
        # Resolution is for future implementation. For now, only use data with resolution information.
        self._resolution: float | None = None

        self.model_matrix: np.ndarray | None = None

        # Advanced parameters for MaxEnt
        self._iterMax: int = 5000
        self._skyBackground: float = 1e-6
        self._weightType: str = "dI"
        self._weightFactor: float = 1.0
        self._weightPercent: float = 1.0
        self._weights: np.ndarray | None = np.array(data.dy)

        self._bin_edges: np.ndarray = np.array([])
        self._binDiff: np.ndarray = np.array([])
        self._volumes: np.ndarray | None = None

        # Return Values after the MaxEnt fit
        self.BinMagnitude_maxEnt: np.ndarray = np.array([], dtype=float)
        self.BinMagnitude_Errs: np.ndarray | None = None
        self.BinMag_numberDist: np.ndarray | None = None
        self.number_cdf: np.ndarray | None = None
        self.volumefrac_cdf: np.ndarray | None = None
        self.volume_fraction: np.ndarray | None = None
        self.volume_fraction_errs: np.ndarray | None = None
        self.chiSq_maxEnt: float = np.inf
        self.Iq_maxEnt: np.ndarray | None = None

        self.MaxEnt_statistics: dict[str, float] = {
            "volume": 0.0,
            "volume_err": 0.0,
            "mean": 0.0,
            "median": 0.0,
            "mode": 0.0,
        }

        # initialize bins and derived arrays
        self.set_bins()

    @property
    def data(self) -> Data1D:
        """Return the data."""
        return self._data

    @data.setter
    def data(self, value: Data1D) -> None:
        """Set the data."""
        self._data = value

    @property
    def qMin(self) -> float:
        """Return the minimum q value for the fit."""
        return self._qMin

    @qMin.setter
    def qMin(self, value: float) -> None:
        """Set the minimum q value for the fit and update the corresponding index."""
        self._qMin = value
        self._ndx_qmin = np.searchsorted(self._data.x, value)

    @property
    def qMax(self) -> float:
        """Return the maximum q value for the fit."""
        return self._qMax

    @qMax.setter
    def qMax(self, value: float) -> None:
        """Set the maximum q value for the fit and update the corresponding index."""
        self._qMax = value
        self._ndx_qmax = np.searchsorted(self._data.x, value)

    @property
    def ndx_qmin(self) -> int:
        """Return the index corresponding to the minimum q value for the fit."""
        return self._ndx_qmin

    @ndx_qmin.setter
    def ndx_qmin(self, value: int):
        """Set the ndx_qmin value and update q_min variable."""
        self._ndx_qmin = value
        self._qMin = self._data.x[value]

    @property
    def ndx_qmax(self) -> int:
        """Return the index corresponding to the maximum q value for the fit."""
        return self._ndx_qmax

    @ndx_qmax.setter
    def ndx_qmax(self, value: int) -> None:
        """Set the ndx_qmax value and update q_max variable."""
        self._ndx_qmax = value
        self._qMax = self._data.x[value]

    @property
    def diamMax(self) -> float:
        """Return the maximum diameter for the size distribution."""
        return self._diamMax

    @diamMax.setter
    def diamMax(self, value: float) -> None:
        """Set the maximum diameter for the size distribution and update the bins."""
        self._diamMax = value
        self.set_bins()

    @property
    def diamMin(self) -> float:
        """Return the minimum diameter for the size distribution."""
        return self._diamMin

    @diamMin.setter
    def diamMin(self, value: float) -> None:
        """Set the minimum diameter for the size distribution and update the bins."""
        self._diamMin = value
        self.set_bins()

    @property
    def nbins(self) -> int:
        """Return the number of bins for the size distribution."""
        return self._nbins

    @nbins.setter
    def nbins(self, value: int) -> None:
        """Set the number of bins for the size distribution and update the bins."""
        self._nbins = value
        self.set_bins()

    @property
    def logbin(self) -> bool:
        """
        Return the logbin flag for the size distribution.
        If True, bins are logarithmically spaced; if False, bins are linearly spaced.
        """
        return self._logbin

    @logbin.setter
    def logbin(self, value: bool) -> None:
        """Set the logbin flag for the size distribution and update the bins."""
        self._logbin = value
        self.set_bins()

    @property
    def bins(self) -> np.ndarray | None:
        """Return the bins for the size distribution."""
        return self._bins

    def set_bins(self) -> None:
        """Set the bins for the size distribution based on the current diamMin, diamMax, nbins, and logbin settings."""
        # Bins are in radius distances, so half of diamMin and diamMax
        if self.logbin:
            self._bins = np.logspace(np.log10(self.diamMin), np.log10(self.diamMax), self.nbins + 1, True) * 0.5
        else:
            self._bins = np.linspace(self.diamMin, self.diamMax, self.nbins + 1, True) * 0.5

        self._bin_edges = self._bins
        self._binDiff = np.diff(self._bins)
        self._bins = self._bins[:-1] + self._binDiff * 0.5

    @property
    def model(self) -> str:
        """Return the model for the size distribution."""
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        """Set the model for the size distribution. Currently hard coded to 'ellipsoid'."""
        if value != "ellipsoid":
            logger.info(
                "Model is hard coded to ellipsoid for the time being. "
                "Please only use ellipsoid. Setting model to ellipsoid."
            )
            self._model = "ellipsoid"
        else:
            self._model = value

    @property
    def aspectRatio(self) -> float:
        """Return the aspect ratio for the size distribution."""
        return self._aspectRatio

    @aspectRatio.setter
    def aspectRatio(self, value: float) -> None:
        """Set the aspect ratio for the size distribution."""
        self._aspectRatio = value

    @property
    def contrast(self) -> float:
        """Return the contrast for the size distribution."""
        return self._contrast

    @contrast.setter
    def contrast(self, value: float) -> None:
        """Set the contrast for the size distribution."""
        self._contrast = value

    @property
    def resolution(self) -> float | None:
        """Return the resolution for the size distribution."""
        return self._resolution

    @resolution.setter
    def resolution(self, value: float) -> None:
        """Set the resolution for the size distribution."""
        self._resolution = value

    @property
    def background(self) -> float:
        """Return the background for the size distribution."""
        return self._background

    @background.setter
    def background(self, value: float) -> None:
        """Set the background for the size distribution."""
        self._background = value

    @property
    def scale(self) -> float:
        """Return the scale for the size distribution."""
        return self._scale

    @scale.setter
    def scale(self, value: float) -> None:
        """Set the scale for the size distribution."""
        self._scale = value

    @property
    def iterMax(self) -> int:
        """Return the maximum number of iterations for the size distribution."""
        return self._iterMax

    @iterMax.setter
    def iterMax(self, value: int) -> None:
        """Set the maximum number of iterations for the size distribution."""
        self._iterMax = value

    @property
    def skyBackground(self) -> float:
        """Return the sky background for the size distribution."""
        return self._skyBackground

    @skyBackground.setter
    def skyBackground(self, value: float) -> None:
        """Set the sky background for the size distribution."""
        self._skyBackground = value

    @property
    def weightFactor(self) -> float:
        """Return the weight factor for the size distribution."""
        return self._weightFactor

    @weightFactor.setter
    def weightFactor(self, value: float) -> None:
        """Set the weight factor for the size distribution."""
        self._weightFactor = value

    @property
    def weightPercent(self) -> float:
        """Return the weight percent for the size distribution."""
        return self._weightPercent

    @weightPercent.setter
    def weightPercent(self, value: float) -> None:
        """Set the weight percent for the size distribution."""
        self._weightPercent = value

    @property
    def weightType(self) -> str:
        """Return the weight type for the size distribution."""
        return self._weightType

    @weightType.setter
    def weightType(self, value: str) -> None:
        """Set the weight type for the size distribution."""
        self._weightType = value
        self.update_weights()

    @property
    def weights(self) -> np.ndarray | None:
        """Return the weights for the size distribution."""
        return self._weights

    def update_weights(self, sigma: Data1D | None = None) -> None:
        """Update the weights based on the current weightType and the provided sigma or data uncertainties."""
        if sigma is None:
            wdata = self.data
        else:
            wdata = sigma

        if self.weightType == "None":
            self._weights = np.ones_like(wdata.y)
        elif self.weightType == "dI":
            self._weights = np.array(wdata.dy)
        elif self.weightType == "sqrt(I Data)":
            self._weights = np.sqrt(wdata.y)
        elif self.weightType == "percentI":
            weight_fraction = self.weightPercent / 100.0
            self._weights = np.abs(weight_fraction * wdata.y)
        else:
            logger.error(
                "weightType doesn't match the possible strings for weight selection. "
                "Please check the value entered or use 'dI'."
            )

    def generate_model_matrix(self, moddata: Data1D) -> None:
        """
        Generate a matrix of intensities from a specific sasmodels model;
        probably should be generalized to a class to use maxent on any parameter of interest w/in the model.
        For now, the pars are fixed.
        :param moddata: Data1D object that has the data trimmed depending on background
            subtraction or power law subtracted from the data. Also self.qMin and self.qMax.
        """
        model = load_model(self.model)

        pars = {
            "sld": self.contrast,
            "sld_solvent": 0.0,
            "background": 0.0,
            "scale": 1.0,
        }

        kernel = DirectModel(moddata, model)

        intensities = []
        for bin in self.bins:
            pars["radius_equatorial"] = bin
            pars["radius_polar"] = bin * self.aspectRatio
            intensities.append(kernel(**pars))

        self.model_matrix = np.vstack(intensities).T

    def calc_volume_weighted_dist(self, binmag: np.ndarray) -> None:
        """
        This is not used right now.
        Calculate the volume weighted distribution.
        """
        if self.logbin:
            radbins = np.logspace(np.log10(self.diamMin), np.log10(self.diamMax), self.nbins + 1, True) * 0.5

        else:
            radbins = np.linspace(self.diamMin, self.diamMax, self.nbins + 1, True) * 0.5

        self.volume_bins = ellipse_volume(self.aspectRatio * radbins, radbins)
        self.vbin_diff = np.diff(self.volume_bins)
        self.volume_bins = self.volume_bins[:-1] + self.vbin_diff * 0.5
        self.volume_fraction = binmag * self.volume_bins / (2.0 * self.vbin_diff)

        if self.BinMagnitude_Errs is not None:
            self.volume_fraction_errs = self.BinMagnitude_Errs * (self.volume_bins / (2.0 * self.vbin_diff))
        else:
            self.volume_fraction_errs = None

    def prep_maxEnt(
        self,
        sub_intensities: Data1D,
        full_fit: bool = False,
        nreps: int = 10,
        rngseed: int | None = None,
    ) -> tuple[Data1D, list[npt.NDArray], npt.NDArray, npt.NDArray]:
        """
        1. Subtract intensities from the raw data.
        2. Trim the data to the correct q-range for maxEnt; create new trimmed Data1D object to return after MaxEnt.
        3. Generate Model Data based of the trimmed data.
        4. Create a list of intensities for maxEnt; if full_fit == True, call add_gaussian_noise nreps times;
            if False, pass just the subtracted intensities.
        5. Calculate initial bin weights, sigma, and return.

        :param sub_intensities: Data1D object with y=A*x^M + B; should have dy as well
        :param full_fit: bool,
            - if True, add Gaussian noise to the subtracted intensities and run maxEnt for nreps
                iterations to get a distribution of bin magnitudes
            - if False, just run maxEnt once with the subtracted intensities.
        :param nreps: int, number of repetitions to run maxEnt with different noise realizations if full_fit is True
        :param rngseed: random seed for reproducibility when adding Gaussian noise (default: None)
        :return: tuple of (trimmed Data1D object, list of intensities for maxEnt, initial bin weights, sigma)
        """
        pars_keys = ["x", "y", "dx", "dy"]
        trim_data_pars = {}

        if len(sub_intensities.y) != len(self._data.y):
            logger.error("The length of the subtracted intensities does not match the length of the data. ")

        for pkey in pars_keys:
            check_data = pkey in list(self._data.__dict__.keys())

            if check_data:
                item = self._data.__dict__[pkey]
                try:
                    if pkey == "y":
                        item = item - sub_intensities.y
                    elif pkey == "dy":
                        item = item + sub_intensities.dy

                    data_vals = item[self.ndx_qmin : self.ndx_qmax]

                except Exception as e:
                    logger.exception("Error trimming data in prep_maxEnt: %s", e)
                trim_data_pars[pkey] = data_vals

        trim_data = Data1D(**trim_data_pars)
        trim_data.__dict__["qmin"] = self.qMin
        trim_data.__dict__["qmax"] = self.qMax

        self.generate_model_matrix(trim_data)

        intensities = []
        if full_fit:
            for _ in range(nreps):
                intensities.append(add_gaussian_noise(trim_data.y, trim_data.dy, seed=rngseed))
        else:
            intensities.append(trim_data.y)

        self.update_weights(trim_data)
        init_binsBack = np.ones_like(self.bins) * self.skyBackground * self.scale / self.contrast
        sigma = self.weightFactor * self.weights

        return trim_data, intensities, init_binsBack, sigma

    def run_maxEnt(
        self,
        maxEntData: Data1D,
        intensities: list[npt.NDArray],
        BinsBack: npt.NDArray,
        sigma: npt.NDArray,
    ) -> list[tuple[bool, int]]:
        """
        Run the Maximum Entropy method on the provided intensities and return the results.
        :param maxEntData: Data1D object that will be updated with the results of the MaxEnt fit (y and dy)
        :param intensities: list of intensity arrays to run MaxEnt on
        :param BinsBack: initial bin magnitudes for the MaxEnt fit
        :param sigma: array of weights for the MaxEnt fit
        :return: list of convergence information for each MaxEnt fit
        """
        ChiSq = []
        BinMag = []
        IMaxEnt = []
        convergence = []

        # Run MaxEnt
        for intensity in intensities:
            MethodCall = maxEntMethod()
            try:
                chisq, bin_magnitude, icalc, converged, conv_iter = MethodCall.MaxEnt_SB(
                    intensity, sigma, self.model_matrix, BinsBack, self.iterMax, report=False
                )
            except ZeroDivisionError:
                logger.error(
                    "Divide by Zero Error occurred in maximum entropy fitting. "
                    "Try increasing the weight factor to increase the error weighting"
                )
            else:
                ChiSq.append(chisq)
                BinMag.append(bin_magnitude)
                IMaxEnt.append(icalc)
                convergence.append((converged, conv_iter))
                if not converged:
                    logger.warning(
                        "Maximum Entropy did not converge. Try increasing the weight factor "
                        "to increase the weighting effect."
                    )

        # If all bin magnitudes are NaN, raise an error and let the caller handle it
        if np.isnan(BinMag).all():
            raise ValueError("Maximum Entropy fitting failed. Try different input values.")

        # Check len of intensities for full vs. quick fit
        if len(intensities) == 1:
            self.chiSq_maxEnt = np.mean(ChiSq)
            self.BinMagnitude_maxEnt = np.mean(BinMag, axis=0) / (2.0 * self._binDiff)

            self.BinMagnitude_Errs = None
            maxEntData.y = np.mean(IMaxEnt, axis=0)
            maxEntData.dy = None
            self.Iq_maxEnt = maxEntData

        elif len(intensities) > 1:
            self.chiSq_maxEnt = np.mean(ChiSq)
            self.BinMagnitude_maxEnt = np.mean(BinMag, axis=0) / (2.0 * self._binDiff)

            self.BinMagnitude_Errs = np.std(BinMag, axis=0) / (2.0 * self._binDiff)
            maxEntData.y = np.mean(IMaxEnt, axis=0)
            maxEntData.dy = np.std(IMaxEnt, axis=0)
            self.Iq_maxEnt = maxEntData

        else:
            logger.error(
                "The length of the intensity array is 0. Did you run prep_maxEnt before run_maxEnt? "
                "Check that intensities is an array of at least length 1."
            )

        self.calculate_statistics(BinMag)

        return convergence

    def calculate_statistics(self, bin_mag: npt.ArrayLike) -> None:
        """
        Calculate statistics from the MaxEnt results, including volume fraction cumulative distribution function (CDF),
        number distribution, and related statistics such as mean, median, and mode.
        
        :param bin_mag: list of bin magnitudes from the MaxEnt fits
        """
        bin_mag = np.asarray(bin_mag)
        maxent_cdf_array = integrate.cumulative_trapezoid(bin_mag / (2.0 * self._binDiff), 2.0 * self.bins, axis=1)
        self.BinMag_numberDist = self.BinMagnitude_maxEnt / ellipse_volume(self.aspectRatio * self.bins, self.bins)

        rvdist = stats.rv_histogram(
            (self.BinMagnitude_maxEnt, self._bin_edges * 2.0), density=True
        )  # volume fraction weighted
        number_cdf = integrate.cumulative_trapezoid(self.BinMag_numberDist, 2.0 * self.bins)
        self.number_cdf = number_cdf / number_cdf[-1]

        self.volumefrac_cdf = np.mean(maxent_cdf_array, axis=0) / np.mean(maxent_cdf_array[:, -1])
        self.MaxEnt_statistics["volume"] = np.mean(maxent_cdf_array[:, -1])
        self.MaxEnt_statistics["volume_err"] = np.std(maxent_cdf_array[:, -1])
        self.MaxEnt_statistics["mode"] = 2.0 * self.bins[np.argmax(self.BinMag_numberDist)]  # number density
        ndx_med = np.where(self.volumefrac_cdf >= 0.5)[0][0]
        self.MaxEnt_statistics["median"] = 2.0 * self.bins[ndx_med]  # volume fraction weighted Median
        self.MaxEnt_statistics["mean"] = rvdist.mean()  # volume fraction weighted mean
