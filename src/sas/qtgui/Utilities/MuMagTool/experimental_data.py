from dataclasses import dataclass

import numpy as np

from sas.qtgui.Plotting.PlotterData import Data1D


@dataclass
class ExperimentalData:
    """ Datapoint used as input for the MuMag tool"""

    scattering_curve: Data1D

    applied_field: float
    saturation_magnetisation: float
    demagnetising_field: float
