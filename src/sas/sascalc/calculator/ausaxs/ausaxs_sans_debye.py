import logging

import pyausaxs as ausaxs

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
        Iq = ausaxs.sasview.debye_no_ff(q, coords[0,:], coords[1,:], coords[2,:], w)
        return Iq
    except Exception as e:
        logging.warning("AUSAXS Debye calculation failed: %s. Falling back to default implementation.", e)
        return sasview_sans_debye(q, coords, w)
