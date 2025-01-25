import ctypes as ct
import numpy as np
import logging
import multiprocessing
import importlib.resources as resources
from enum import Enum
from sas.sascalc.calculator.ausaxs.sasview_sans_debye import sasview_sans_debye

class AUSAXSLIB: 
    class STATE(Enum):
        UNINITIALIZED = 0
        FAILED = 1
        READY = 2

    def __init__(self):
        self.functions = None
        self.state = self.STATE.UNINITIALIZED
        self.lib_path = None

        # only initialize hooks in main thread to avoid recursion
        if __name__ == "__main__":
            self._attach_hooks()
            self._test_integration()

    def _attach_hooks(self):
        from sas.sascalc.calculator.ausaxs.architecture import get_shared_lib_extension

        # as_file extracts the dll if it is in a zip file and probably deletes it afterwards,
        # so we have to do all operations on the dll inside the with statement
        with resources.as_file(resources.files("sas.sascalc.calculator.ausaxs.lib")) as loc:
            ext = get_shared_lib_extension()
            if (ext == ""):
                logging.warning("AUSAXS: Unsupported OS. Library cannot be loaded.")
                self.state = self.STATE.FAILED

            self.lib_path = loc.joinpath("libausaxs" + ext)
            self.state = self.STATE.READY
            try:
                self.functions = ct.CDLL(str(self.lib_path))

                # test_integration
                self.functions.test_integration.argtypes = [
                    ct.POINTER(ct.c_int) # test val
                ]
                self.functions.test_integration.restype = None # returns void

                # evaluate_sans_debye
                self.functions.evaluate_sans_debye.argtypes = [
                    ct.POINTER(ct.c_double), # q vector
                    ct.POINTER(ct.c_double), # atom x vector
                    ct.POINTER(ct.c_double), # atom y vector
                    ct.POINTER(ct.c_double), # atom z vector
                    ct.POINTER(ct.c_double), # atom weight vector
                    ct.c_int,                # nq (number of points in q)
                    ct.c_int,                # nc (number of points in x, y, z, w)
                    ct.POINTER(ct.c_int),    # status (0 = success)
                    ct.POINTER(ct.c_double)  # Iq vector for return value
                ]
                self.functions.evaluate_sans_debye.restype = None # returns void

                # evaluate_saxs_debye
                self.functions.evaluate_saxs_debye.argtypes = [
                    ct.POINTER(ct.c_double), # data q vector
                    ct.POINTER(ct.c_double), # data I vector
                    ct.POINTER(ct.c_double), # data Ierr vector
                    ct.c_int,                # n_data (number of points in q, I, Ierr)
                    ct.POINTER(ct.c_double), # pdb x vector
                    ct.POINTER(ct.c_double), # pdb y vector
                    ct.POINTER(ct.c_double), # pdb z vector
                    ct.c_int,                # pdb atom form factor type
                    ct.c_int,                # n_pdb (number of atoms)
                    ct.POINTER(ct.c_double), # return I vector for return value
                    ct.POINTER(ct.c_int)     # return status (0 = success)
                ]
                self.functions.evaluate_saxs_debye.restype = None # returns void

                self.state = self.STATE.READY

            except Exception as e:
                logging.warning("AUSAXS: Failed to hook into external library. Fallback methods will be used where possible.")
                print(e)
                self.state = self.STATE.FAILED

    def _test_integration(self):
        '''
            Test the integration of the AUSAXS library by running a simple test function in a separate process. 
            This protects the main thread from potential segfaults.
        '''
        if (self.state != self.STATE.READY):
            return

        try: 
            # we need a queue to access the return value
            queue = multiprocessing.Queue()
            p = multiprocessing.Process(target=_run, args=(self.lib_path, queue))
            p.start()
            p.join()
            if p.exitcode == 0: # process successfully terminated
                val = queue.get_nowait() # get the return value
                if (val != 6): # test_integration increments the test value by 1
                    raise Exception("AUSAXS integration test failed. Test value was not incremented")
            else:
                raise Exception(f"External AUSAXS library seems to have crashed (exit code \"{p.exitcode}\").")

        except Exception as e:
            logging.warning("AUSAXS: Integration test failed. Library cannot be used. Fallback methods will be used where possible.")
            print(e)
            self.state = self.STATE.FAILED

    def ready(self):
        return self.state == self.STATE.READY

    def evaluate_sans_debye(self, q, coords, w):
        if (self.state != self.STATE.READY):
            return sasview_sans_debye(q, coords, w)

        Iq = (ct.c_double * len(q))()
        nq = ct.c_int(len(q))
        nc = ct.c_int(len(w))
        q = q.ctypes.data_as(ct.POINTER(ct.c_double))
        x = coords[0:, :].ctypes.data_as(ct.POINTER(ct.c_double))
        y = coords[1:, :].ctypes.data_as(ct.POINTER(ct.c_double))
        z = coords[2:, :].ctypes.data_as(ct.POINTER(ct.c_double))
        w = w.ctypes.data_as(ct.POINTER(ct.c_double))
        status = ct.c_int()
        self.functions.evaluate_sans_debye(q, x, y, z, w, nq, nc, ct.byref(status), Iq)

        # check if the external call was successful
        if (status.value != 0):
            logging.warning(f"AUSAXS: External library evaluation terminated unexpectedly (error code \"{status.value}\"). Using default Debye implementation instead.")
            return sasview_sans_debye(q, coords, w)

        return np.array(Iq)
    
    def evaluate_saxs_debye(self, q, I, Ierr, pdb, atom_form_factor_type):
        raise NotImplementedError("SAXS Debye calculation is not yet implemented in the AUSAXS library.")

def _run(lib_path, queue):
    ''''
        Helper method for AUSAXSLIB._test_integration, which must be defined in global scope to be picklable.
    '''
    func = ct.CDLL(str(lib_path))
    func.test_integration.argtypes = [ct.POINTER(ct.c_int)]
    func.test_integration.restype = None
    test_val = ct.c_int(5)
    func.test_integration(ct.byref(test_val))
    queue.put(test_val.value)

ausaxs = AUSAXSLIB()
def evaluate_sans_debye(q, coords, w):
    """
    Compute I(q) for a set of points using Debye sums.
    This uses AUSAXS if available, otherwise it uses the default implementation.
    *q* is the q values for the calculation.
    *coords* are the sample points.
    *w* is the weight associated with each point.
    """
    if (ausaxs.ready()):
        return ausaxs.evaluate_sans_debye(q, coords, w)
    return sasview_sans_debye(q, coords, w)