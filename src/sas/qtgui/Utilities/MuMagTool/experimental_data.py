from dataclasses import dataclass

import numpy as np

from sas.qtgui.Plotting.PlotterData import Data1D


@dataclass
class ExperimentalData:
    input_data: Data1D

    applied_field: float
    saturation_magnetisation: float
    demagnetising_field: float
