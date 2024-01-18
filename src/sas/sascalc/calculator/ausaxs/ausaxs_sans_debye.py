import ctypes as ct
import numpy as np
import logging

from sas.sascalc.calculator.ausaxs.architecture import OS, determine_os
sys = determine_os()
if (sys is OS.WIN):
    path = "external/libausaxs.dll"
elif (sys is OS.LINUX):
    path = "external/libausaxs.so"
elif (sys is OS.MAC):
    path = "external/libausaxs.dylib"
else:
    path = ""

try:
    # evaluate_sans_debye func
    ausaxs = ct.CDLL(path)
    ausaxs.evaluate_sans_debye.argtypes = [
        ct.POINTER(ct.c_double), # q vector
        ct.POINTER(ct.c_double), # x vector
        ct.POINTER(ct.c_double), # y vector
        ct.POINTER(ct.c_double), # z vector
        ct.POINTER(ct.c_double), # w vector
        ct.c_int,                # nq (number of points in q)
        ct.c_int,                # nc (number of points in x, y, z, w)
        ct.c_int,                # status (0 = success, 1 = q range error, 2 = other error)
        ct.POINTER(ct.c_double)  # Iq vector for return value
    ]
    ausaxs.evaluate_sans_debye.restype = None # don't expect a return value
except:
    ausaxs = None

def evaluate_sans_debye(q, coords, w):
    if ausaxs is None:
        logging.warning("AUSAXS external library not found, using default Debye implementation")
        from sas.sascalc.calculator.ausaxs.sasview_sans_debye import sasview_sans_debye
        return sasview_sans_debye(q, coords, w)

    # convert numpy arrays to ctypes arrays
    Iq = (ct.c_double * len(q))()
    nq = ct.c_int(len(q))
    nc = ct.c_int(len(w))
    q = q.ctypes.data_as(ct.POINTER(ct.c_double))
    x = coords[:, 0].ctypes.data_as(ct.POINTER(ct.c_double))
    y = coords[:, 1].ctypes.data_as(ct.POINTER(ct.c_double))
    z = coords[:, 2].ctypes.data_as(ct.POINTER(ct.c_double))
    w = w.ctypes.data_as(ct.POINTER(ct.c_double))
    status = ct.c_int()

    # do the call
    ausaxs.evaluate_sans_debye(q, x, y, z, w, nq, nc, status, Iq)

    # check for errors
    if status.value != 0:
        if status.value == 1:
            logging.error("q range is outside what is currently supported by AUSAXS")
            raise ValueError("q range is outside what is currently supported by AUSAXS")
        elif status.value == 2:
            logging.error("AUSAXS calculator terminated unexpectedly")
            raise RuntimeError("AUSAXS calculator terminated unexpectedly")
    return np.array(Iq)