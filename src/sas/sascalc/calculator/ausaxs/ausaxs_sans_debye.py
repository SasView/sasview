import ctypes as ct
import numpy as np
import logging
from enum import Enum
import importlib.resources as resources
from cffi import FFI

# we need to be able to differentiate between being uninitialized and failing to load
class lib_state(Enum):
    UNINITIALIZED = 0
    FAILED = 1
    READY = 2

ausaxs_state = lib_state.UNINITIALIZED
ausaxs = None
ffi = FFI()

def attach_hooks():
    global ausaxs_state
    global ausaxs
    
    from sas.sascalc.calculator.ausaxs.architecture import OS, Arch, determine_os, determine_cpu_support
    sys = determine_os()
    arch = determine_cpu_support()

    # as_file extracts the dll if it is in a zip file and probably deletes it afterwards,
    # so we have to do all operations on the dll inside the with statement
    with resources.as_file(resources.files("sas.sascalc.calculator.ausaxs.lib")) as loc:
        if sys is OS.WIN:
            if arch is Arch.AVX:
                path = loc.joinpath("sasview_avx.exe")
            else:
                path = loc.joinpath("sasview_sse.exe")
        elif sys is OS.LINUX:
            if arch is Arch.AVX:
                path = loc.joinpath("libausaxs_avx.so")
            else:
                path = loc.joinpath("libausaxs_sse.so")
        elif sys is OS.MAC:
            if arch is Arch.AVX:
                path = loc.joinpath("libausaxs_avx.dylib")
            else:
                path = loc.joinpath("libausaxs_sse.dylib")
        else:
            path = ""

        # currently windows can only use the raw exe
        ausaxs_state = lib_state.READY
        if sys is not OS.WIN:
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
                logging.warning("Failed to hook into AUSAXS library, using default Debye implementation")
                print(e)
        else:
            ausaxs = str(path)

def ausaxs_available():
    """
    Check if the AUSAXS library is available.
    """
    if ausaxs_state is lib_state.UNINITIALIZED:
        attach_hooks()
    return ausaxs_state is lib_state.READY

def evaluate_sans_debye(q, coords, w):
    """
    Compute I(q) for a set of points using Debye sums.
    This uses AUSAXS if available, otherwise it uses the default implementation.
    *q* is the q values for the calculation.
    *coords* are the sample points.
    *w* is the weight associated with each point.
    """
    global ffi
    if ausaxs_state is lib_state.UNINITIALIZED:
        attach_hooks()
    if ausaxs_state is lib_state.FAILED or len(coords[0]) < 500:
        from sas.sascalc.calculator.ausaxs.sasview_sans_debye import sasview_sans_debye
        return sasview_sans_debye(q, coords, w)

    from sas.sascalc.calculator.ausaxs.architecture import determine_os, OS
    if determine_os() is OS.WIN:
        import os
        from pathlib import Path
        base_path = Path(os.getcwd())
        os.makedirs(base_path.joinpath("tmp"), exist_ok=True)
        file_c = open(base_path.joinpath("tmp", "coords.txt"), "w")
        file_q = open(base_path.joinpath("tmp", "q.txt"), "w")
        for _q in q:
            file_q.write(str(_q)+"\n")

        for [x, y, z, w] in zip(coords[0], coords[1], coords[2], w):
            file_c.write(str(x) + " " + str(y) + " " + str(z) + " " + str(w) + "\n")

        file_c.close()
        file_q.close()

        import subprocess
        subprocess.run([ausaxs, base_path.joinpath("tmp", "coords.txt"), base_path.joinpath("tmp", "q.txt"), base_path.joinpath("tmp", "Iq.txt")])
        file_Iq = open(base_path.joinpath("tmp", "Iq.txt"), "r")

        # format is | q | I(q) |
        # skip first line
        Iq = np.zeros(len(q))
        for i, line in enumerate(file_Iq):
            if (i == 0): continue
            if (1e-3 < abs(q[i-1] - float(line.split()[0]))):
                logging.error("ERROR: q values do not match")                
            Iq[i-1] = float(line.split()[1])
        return Iq

    _Iq = (ct.c_double * len(q))()
    _nq = ct.c_int(len(q))
    _nc = ct.c_int(len(w))
    _q = q.ctypes.data_as(ct.POINTER(ct.c_double))
    _x = coords[0:, :].ctypes.data_as(ct.POINTER(ct.c_double))
    _y = coords[1:, :].ctypes.data_as(ct.POINTER(ct.c_double))
    _z = coords[2:, :].ctypes.data_as(ct.POINTER(ct.c_double))
    _w = w.ctypes.data_as(ct.POINTER(ct.c_double))
    _status = ct.c_int()

    # do the call
    # void evaluate_sans_debye(double* _q, double* _x, double* _y, double* _z, double* _w, int _nq, int _nc, int* _return_status, double* _return_Iq) {
    ausaxs.evaluate_sans_debye(_q, _x, _y, _z, _w, _nq, _nc, ct.byref(_status), _Iq)

    # check for errors
    if _status != 0:
        if _status == 1:
            logging.error("q range is outside what is currently supported by AUSAXS. Using default Debye implementation instead.")
        elif _status == 2:
            logging.error("AUSAXS calculator terminated unexpectedly. Using default Debye implementation instead.")
        from sas.sascalc.calculator.ausaxs.sasview_sans_debye import sasview_sans_debye
        return sasview_sans_debye(q, coords, w)

    return np.array(_Iq)