from dataclasses import dataclass
from enum import StrEnum

from sasdata.dataloader.data_info import Data1D

from sas.qtgui.Utilities.GuiUtils import enum

WIDGETS = enum(
    "W_NAME",
    "W_QMIN",
    "W_QMAX",
    "W_MODEL_NAME",
    "W_ASPECT_RATIO",
    "W_DMIN",
    "W_DMAX",
    "W_DBINS",
    "W_ASPECT_RATIO",
    "W_LOG_BINNING",
    "W_CONTRAST",
    "W_BACKGROUND",
    "W_SKY_BACKGROUND",
    "W_SUBTRACT_LOW_Q",
    "W_POWER_LOW_Q",
    "W_SCALE_LOW_Q",
    "W_NUM_ITERATIONS",
    "W_WEIGHT_FACTOR",
    "W_WEIGHT_PERCENT",
)


class WeightType(StrEnum):
    NONE = "None"
    DI = "dI"
    SQRT_I = "sqrt(I Data)"
    PERCENT_I = "percentI"


@dataclass
class MaxEntParameters:
    qmin: float = 0.0
    qmax: float = 0.1
    dmin: float = 10.0
    dmax: float = 1000.0
    num_bins: int = 100
    log_binning: bool = True
    model: str = "ellipsoid"
    aspect_ratio: float = 1.0
    contrast: float = 1.0
    sky_background: float = 1.0e-6
    max_iterations: int = 100
    use_weights: bool = True
    weight_type: WeightType = WeightType.DI
    weight_factor: float = 1.0
    weight_percent: float = 1.0
    full_fit: bool = True


@dataclass
class MaxEntResult:
    convergences: list[bool]
    num_iters: list[int]
    chisq: float
    bins: list[float]
    bin_mag: list[float]
    bin_diff: list[float]
    bin_err: list[float]
    data_max_ent: Data1D
    statistics: dict
