import ctypes as ct
import importlib.resources as resources
import logging
import multiprocessing
from enum import Enum

import numpy as np

from sas.sascalc.calculator.ausaxs.sasview_sans_debye import sasview_sans_debye


# we need to be able to differentiate between being uninitialized and failing to load
class lib_state(Enum):
    UNINITIALIZED = 0
    FAILED = 1
    READY = 2

def _attach_hooks():
    ausaxs = None
    ausaxs_state = lib_state.UNINITIALIZED
    from sas.sascalc.calculator.ausaxs.architecture import get_shared_lib_extension

    # as_file extracts the dll if it is in a zip file and probably deletes it afterwards,
    # so we have to do all operations on the dll inside the with statement
    with resources.as_file(resources.files("sas.sascalc.calculator.ausaxs.lib")) as loc:
        ext = get_shared_lib_extension()
        if (ext == ""):
            logging.info("AUSAXS: Unsupported OS. Using default Debye implementation.")
            return None, lib_state.FAILED

        path = loc.joinpath("libausaxs" + ext)
        ausaxs_state = lib_state.READY
        try:
            # evaluate_sans_debye func
            ausaxs = ct.CDLL(str(path))
            ausaxs.evaluate_sans_debye.argtypes = [
                ct.POINTER(ct.c_double), # q vector
                ct.POINTER(ct.c_double), # x vector
                ct.POINTER(ct.c_double), # y vector
                ct.POINTER(ct.c_double), # z vector
                ct.POINTER(ct.c_double), # w vector
                ct.c_int,                # nq (number of points in q)
                ct.c_int,                # nc (number of points in x, y, z, w)
                ct.POINTER(ct.c_int),    # status (0 = success, 1 = q range error, 2 = other error)
                ct.POINTER(ct.c_double)  # Iq vector for return value
            ]
            ausaxs.evaluate_sans_debye.restype = None # don't expect a return value
            ausaxs_state = lib_state.READY
        except Exception as e:
            ausaxs_state = lib_state.FAILED
            logging.warning("AUSAXS: Failed to hook into external library; using default Debye implementation")
            print(e)
    return ausaxs, ausaxs_state

def _prepare_invocation(q, coords, w):
    Iq = (ct.c_double * len(q))()
    nq = ct.c_int(len(q))
    nc = ct.c_int(len(w))
    q = q.ctypes.data_as(ct.POINTER(ct.c_double))
    x = coords[0:, :].ctypes.data_as(ct.POINTER(ct.c_double))
    y = coords[1:, :].ctypes.data_as(ct.POINTER(ct.c_double))
    z = coords[2:, :].ctypes.data_as(ct.POINTER(ct.c_double))
    w = w.ctypes.data_as(ct.POINTER(ct.c_double))
    status = ct.c_int()
    return Iq, nq, nc, q, x, y, z, w, status

ausaxs = None
ausaxs_state = lib_state.UNINITIALIZED
def _invoke(q, coords, w):
    """
    Invoke the AUSAXS library to compute I(q) for a set of points.
    """
    Iq, nq, nc, q, x, y, z, w, status = _prepare_invocation(q, coords, w)
    ausaxs.evaluate_sans_debye(q, x, y, z, w, nq, nc, ct.byref(status), Iq)
    return np.array(Iq), status.value

def _invoke_independent(q, coords, w, queue):
    """
    Import and invoke the AUSAXS library to compute I(q) for a set of points.
    This will redo the import every time it is called, and is only intended for use in a subprocess.
    """
    ausaxs, ausaxs_state = _attach_hooks()
    if ausaxs_state is not lib_state.READY:
        queue.put(None)
        queue.put(-1)
        return
    Iq, nq, nc, q, x, y, z, w, status = _prepare_invocation(q, coords, w)
    ausaxs.evaluate_sans_debye(q, x, y, z, w, nq, nc, ct.byref(status), Iq)
    queue.put(np.array(Iq))
    queue.put(status.value)

def ausaxs_available():
    """
    Check if the AUSAXS library is available.
    """
    global ausaxs, ausaxs_state
    if ausaxs_state is lib_state.UNINITIALIZED:
        ausaxs, ausaxs_state = _attach_hooks()
    return ausaxs_state is lib_state.READY

first_time = True
def evaluate_sans_debye(q, coords, w):
    """
    Compute I(q) for a set of points using Debye sums.
    This uses AUSAXS if available, otherwise it uses the default implementation.
    *q* is the q values for the calculation.
    *coords* are the sample points.
    *w* is the weight associated with each point.
    """

    global ausaxs, ausaxs_state, first_time
    # perform the first-time invocation in a separate process to avoid propagating segfaults
    # this is necessary since we are not doing any sort of checking on the machine compatibility
    if first_time:
        queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=_invoke_independent, args=(q, coords, w, queue))
        p.start()
        p.join()
        if p.exitcode == 0:
            Iq = queue.get_nowait()
            status = queue.get_nowait()
            first_time = False
        else:
            logging.warning(f"AUSAXS: External library seems to have crashed (exit code \"{p.exitcode}\"). Using default Debye implementation instead.")
            ausaxs_state = lib_state.FAILED
            return sasview_sans_debye(q, coords, w)

    # after the first time, we assume that the library is safe to call from the main thread and use it directly
    # to avoid the overhead of creating new processes and hooks every time
    else:
        if ausaxs_state is lib_state.UNINITIALIZED:
            ausaxs, ausaxs_state = _attach_hooks()
        if ausaxs_state is lib_state.FAILED:
            return sasview_sans_debye(q, coords, w)
        Iq, status = _invoke(q, coords, w)

    if (status != 0):
        logging.warning(f"AUSAXS: External library evaluation terminated unexpectedly (error code \"{status}\"). Using default Debye implementation instead.")
        return sasview_sans_debye(q, coords, w)

    return Iq
