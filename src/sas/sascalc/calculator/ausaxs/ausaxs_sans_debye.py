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
                path = loc.joinpath("libausaxs_avx.exe")
            else:
                path = loc.joinpath("libausaxs_sse.exe")
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
                ffi.cdef("void evaluate_sans_debye(double* _q, double* _x, double* _y, double* _z, double* _w, int _nq, int _nc, int* _return_status, double* _return_Iq);")
                ffi.cdef("int debug();")
                ausaxs = ffi.dlopen(str(path))
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
        os.makedirs("tmp", exist_ok=True)
        file_c = open("tmp/coords.txt", "w")
        file_q = open("tmp/q.txt", "w")
        for _q in q:
            file_q.write(str(_q)+"\n")

        for [x, y, z, w] in zip(coords[0], coords[1], coords[2], w):
            file_c.write(str(x) + " " + str(y) + " " + str(z) + " " + str(w) + "\n")

        file_c.close()
        file_q.close()

        import subprocess
        subprocess.call([ausaxs, "tmp/coords.txt", "tmp/q.txt", "tmp/Iq.txt"])
        file_Iq = open("tmp/Iq.txt", "r")

        # format is | q | I(q) |
        # skip first line
        for i, line in enumerate(file_Iq):
            if (i == 0): continue
            if (1e-3 < abs(q[i-1] - float(line.split()[0]))):
                logging.error("ERROR: q values do not match")                
            Iq[i-1] = float(line.split()[1])
        return Iq

    n = len(coords[0])
    # convert numpy arrays to cffi arrays
    Iq = ffi.new(f"double[{len(q)}]")
    nq = ffi.cast("int", len(q))
    nc = ffi.cast("int", len(w))
    q = ffi.cast("double*", q.ctypes.data)
    x = ffi.cast("double*", coords[0:, :].ctypes.data)
    y = ffi.cast("double*", coords[1:, :].ctypes.data)
    z = ffi.cast("double*", coords[2:, :].ctypes.data)
    w = ffi.cast("double*", w.ctypes.data)
    status = ffi.new("int*", 0)

    # do the call
    ausaxs.evaluate_sans_debye(q, x, y, z, w, nq, nc, status, Iq)

    # check for errors
    if status[0] != 0:
        if status[0] == 1:
            logging.error("q range is outside what is currently supported by AUSAXS. Using default Debye implementation instead.")
        elif status[0] == 2:
            logging.error("AUSAXS calculator terminated unexpectedly. Using default Debye implementation instead.")
        from sas.sascalc.calculator.ausaxs.sasview_sans_debye import sasview_sans_debye
        return sasview_sans_debye(q, coords, w)

    return np.array(ffi.buffer(Iq, n*ffi.sizeof("double"))).copy()

if __name__ == "__main__":
    q = np.array([0.001, 0.002, 0.003])
    coords = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [-1, 0, 1]])
    w = np.array([1.0, 1.0, 1.0])
    print(evaluate_sans_debye(q, coords, w))

# if __name__ == "__main__":
#     from cffi import FFI

#     # Create an ffi object
#     ffi = FFI()

#     # Include the C header file content
#     ffi.cdef("""
#         void evaluate_sans_debye(double* _q, double* _x, double* _y, double* _z, double* _w, int _nq, int _nc, int* _return_status, double* _return_Iq);
#     """)

#     ffi.set_source("""
#         #include "ausaxs.h"
#     """)

#     # Load your library using ffibuilder and link against it
#     ffibuilder = ffi.verify("""
#         #include "ausaxs.h"
#     """)

#     # Compile and link the wrapper
#     ffibuilder.compile(verbose=True)