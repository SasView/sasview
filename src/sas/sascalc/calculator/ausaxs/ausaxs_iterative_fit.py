import ctypes as ct
import numpy as np
import logging
from sas.sascalc.calculator.ausaxs.ausaxs import ausaxslib

I_size = None
def ausaxs_iterative_fit_start(q, I, Ierr, coords, atom_names, residue_names, elements):
    """
    Initialize the iterative fitting process for AUSAXS.
    *q* is the q values for the calculation.
    *I* is the data intensity values.
    *Ierr* is the data intensity error values.
    *coords* are the sample points.
    *atom_names* are the PDB atom names.
    *residue_names* are the PDB residue names.
    *elements* are the PDB elements. These are necessary as atom_names by itself can be ambiguous.
    """

    global I_size
    if not ausaxslib.ready():
        raise NotImplementedError("AUSAXS is not available. Refer to previous log messages for more information.")

    assert(len(q) == len(I) == len(Ierr))
    assert(coords.shape[0] == 3)
    assert(coords.shape[1] == len(atom_names) == len(residue_names) == len(elements))

    I_size = len(q)
    nq    = ct.c_int(len(q))
    nc    = ct.c_int(coords.shape[1])
    q     = q.ctypes.data_as(ct.POINTER(ct.c_double))
    I     = I.ctypes.data_as(ct.POINTER(ct.c_double))
    Ierr  = Ierr.ctypes.data_as(ct.POINTER(ct.c_double))
    x     = coords[0:, :].ctypes.data_as(ct.POINTER(ct.c_double))
    y     = coords[1:, :].ctypes.data_as(ct.POINTER(ct.c_double))
    z     = coords[2:, :].ctypes.data_as(ct.POINTER(ct.c_double))

    atom_names    = (ct.c_char_p * len(atom_names))(*[s.encode('utf-8') for s in atom_names])
    residue_names = (ct.c_char_p * len(residue_names))(*[s.encode('utf-8') for s in residue_names])
    elements      = (ct.c_char_p * len(elements))(*[s.encode('utf-8') for s in elements])

    status = ct.c_int()
    ausaxslib.functions.iterative_fit_start(q, I, Ierr, nq, x, y, z, atom_names, residue_names, elements, nc, ct.byref(status))

    if (status.value == 0):
        return

    logging.warning(f"AUSAXS: \"iterative_fit_start\" terminated unexpectedly (error code \"{status.value}\"). The SAXS model is unavailable for use.")

def ausaxs_iterative_fit_step(pars):
    """
    Perform an iteration step.
    *params* is the parameter values for the current iteration.
    """

    if not ausaxslib.ready():
        raise NotImplementedError("AUSAXS is not available. Refer to previous log messages for more information.")

    if I_size is None:
        raise RuntimeError("AUSAXS iterative fitting has not been initialized. Call \"ausaxs_iterative_fit_start\" first.")

    I_out = (ct.c_double * I_size)()
    pars  = pars.ctypes.data_as(ct.POINTER(ct.c_double))
    status = ct.c_int()
    ausaxslib.functions.iterative_fit_step(pars, I_out, ct.byref(status))

    if (status.value == 0):
        return np.array(I_out)

    logging.warning(f"AUSAXS: \"iterative_fit_step\" terminated unexpectedly (error code \"{status.value}\").")

def ausaxs_iterative_fit_end(pars):
    """
    End the iterative optimization. This writes out the final hydrated model. 
    *params* is the parameter values for the current iteration.
    """

    if not ausaxslib.ready():
        raise NotImplementedError("AUSAXS is not available. Refer to previous log messages for more information.")

    if I_size is None:
        raise RuntimeError("AUSAXS iterative fitting has not been initialized. Call \"ausaxs_iterative_fit_start\" first.")

    I_out = (ct.c_double * I_size)()
    pars  = pars.ctypes.data_as(ct.POINTER(ct.c_double))
    status = ct.c_int()
    ausaxslib.functions.iterative_fit_end(pars, I_out, ct.byref(status))

    if (status.value == 0):
        return np.array(I_out)

    logging.warning(f"AUSAXS: \"iterative_fit_end\" terminated unexpectedly (error code \"{status.value}\").")