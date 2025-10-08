import numpy as np
import logging
from pyausaxs import AUSAXS

from sas.sascalc.calculator.ausaxs.sasview_sans_debye import sasview_sans_debye

def evaluate_sans_debye(q, coords, w):
    """
    Compute I(q) for a set of points using Debye sums.
    This uses AUSAXS if available, otherwise it uses the default implementation.
    *q* is the q values for the calculation.
    *coords* are the sample points.
    *w* is the weight associated with each point.
    """
    try:
        ausaxs = AUSAXS()
        Iq = ausaxs.debye(q, coords[0,:], coords[1,:], coords[2,:], w)
        return Iq
    except Exception as e:
        logging.warning(f"AUSAXS Debye calculation failed: {e}. Falling back to default implementation.")
        return sasview_sans_debye(q, coords, w)
