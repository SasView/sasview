"""

Functions that get automatically included in the build window

"""


import numpy as np


def step(x: np.ndarray):
    """ Step function, 0 if input < 0, 1 if input >= 0"""
    out = np.ones_like(x)
    out[x < 0] = 0.0
    return out


def rect(x: np.ndarray):
    """ Rectangle function, zero if mod(input) > 1, 1 otherwise"""
    out = np.zeros_like(x)
    out[np.abs(x) <= 1] = 1.0
    return out


