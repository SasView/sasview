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

    def restrict_by_index(self, max_index: int):
        """ Remove all points from data up to given index"""

        x = self.scattering_curve.x[:max_index]
        y = self.scattering_curve.y[:max_index]
        dy = self.scattering_curve.dy[:max_index]

        return ExperimentalData(
            scattering_curve=Data1D(x=x, y=y, dy=dy),
            applied_field=self.applied_field,
            saturation_magnetisation=self.saturation_magnetisation,
            demagnetising_field=self.demagnetising_field)
