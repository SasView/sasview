import ctypes as ct
import numpy as np
import logging
from sas.sascalc.calculator.ausaxs.ausaxs import ausaxslib

def evaluate_saxs_debye(q, I, Ierr, coords, atom_names, residue_names, elements):
    """
    Compute the X-ray scattering profile of the given atomic structure, and fit it to the given data.
    *q* is the q values for the calculation.
    *I* is the data intensity values.
    *Ierr* is the data intensity error values.
    *coords* are the sample points.
    *atom_names* are the PDB atom names.
    *residue_names* are the PDB residue names.
    *elements* are the PDB elements. These are necessary as atom_names by itself can be ambiguous.
    """

    if not ausaxslib.ready():
        raise NotImplementedError("AUSAXS is not available. Refer to previous log messages for more information.")

    Iq = (ct.c_double * len(q))()
    nq = ct.c_int(len(q))
    nc = ct.c_int(coords.shape[1])
    q = q.ctypes.data_as(ct.POINTER(ct.c_double))
    I = I.ctypes.data_as(ct.POINTER(ct.c_double))
    Ierr = Ierr.ctypes.data_as(ct.POINTER(ct.c_double))
    x = coords[0:, :].ctypes.data_as(ct.POINTER(ct.c_double))
    y = coords[1:, :].ctypes.data_as(ct.POINTER(ct.c_double))
    z = coords[2:, :].ctypes.data_as(ct.POINTER(ct.c_double))
    atom_names = atom_names.ctypes.data_as(ct.POINTER(ct.c_char_p))
    residue_names = residue_names.ctypes.data_as(ct.POINTER(ct.c_char_p))
    elements = elements.ctypes.data_as(ct.POINTER(ct.c_char_p))
    status = ct.c_int()
    ausaxslib.functions.fit_saxs(q, I, Ierr, nq, x, y, z, atom_names, residue_names, elements, nc, Iq, ct.byref(status))

    if (status.value == 0):
        return np.array(Iq)

    logging.warning(f"AUSAXS: External library evaluation terminated unexpectedly (error code \"{status.value}\"). Using default Debye implementation instead.")