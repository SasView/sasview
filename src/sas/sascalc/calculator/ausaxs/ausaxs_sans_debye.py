import ctypes as ct
import numpy as np
import logging
from sas.sascalc.calculator.ausaxs.ausaxs import ausaxslib
from sas.sascalc.calculator.ausaxs.sasview_sans_debye import sasview_sans_debye

def evaluate_sans_debye(q, coords, w):
    """
    Compute I(q) for a set of points using Debye sums.
    This uses AUSAXS if available, otherwise it uses the default implementation.
    *q* is the q values for the calculation.
    *coords* are the sample points.
    *w* is the weight associated with each point.
    """
    if (ausaxslib.ready()):
        Iq = (ct.c_double * len(q))()
        nq = ct.c_int(len(q))
        nc = ct.c_int(len(w))
        q = q.ctypes.data_as(ct.POINTER(ct.c_double))
        x = coords[0:, :].ctypes.data_as(ct.POINTER(ct.c_double))
        y = coords[1:, :].ctypes.data_as(ct.POINTER(ct.c_double))
        z = coords[2:, :].ctypes.data_as(ct.POINTER(ct.c_double))
        w = w.ctypes.data_as(ct.POINTER(ct.c_double))
        status = ct.c_int()
        ausaxslib.functions.evaluate_sans_debye(q, x, y, z, w, nq, nc, Iq, ct.byref(status))

        if (status.value == 0):
            return np.array(Iq)

        logging.warning(f"AUSAXS: External library evaluation terminated unexpectedly (error code \"{status.value}\"). Using default Debye implementation instead.")

    return sasview_sans_debye(q, coords, w)