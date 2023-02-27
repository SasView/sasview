from typing import Tuple, NamedTuple

import numpy as np

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Utilities.GuiUtils import enum

WIDGETS = enum( 'W_QMIN',
                'W_QMAX',
                'W_QCUTOFF',
                'W_BACKGROUND',
                'W_TRANSFORM',
                'W_GUINIERA',
                'W_GUINIERB',
                'W_PORODK',
                'W_PORODSIGMA',
                'W_CORETHICK',
                'W_INTTHICK',
                'W_HARDBLOCK',
                'W_SOFTBLOCK',
                'W_CRYSTAL',
                'W_POLY_RYAN',
                'W_POLY_STRIBECK',
                'W_PERIOD',
                'W_FILENAME'
                )

def safe_float(x: str):
    try:
        return float(x)
    except:
        return 0.0


class TransformedData(NamedTuple):
    """ Container for the data that is returned by the corfunc transform method"""
    gamma_1: Data1D
    gamma_3: Data1D
    idf: Data1D
    q_range: Tuple[float, float]


class LineThroughPoints:
    """ Helper class representing a line that passes through two points"""
    def __init__(self, p1, p2):
        self.p1 = np.array(p1)
        self.p2 = np.array(p2)

        self.gradient = (self.p2[1] - self.p1[1])/(self.p2[0] - self.p1[0])

        self.intercept = self.p1[1] - self.gradient*self.p1[0]

    def __call__(self, x):
        return self.intercept + self.gradient * x