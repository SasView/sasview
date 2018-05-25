import sys
import time
import copy
import traceback

from sas.sascalc.data_util.calcthread import CalcThread

def map_getattr(classInstance, classFunc, *args):
    """
    Take an instance of a class and a function name as a string.
    Execute class.function and return result
    """
    return  getattr(classInstance, classFunc)(*args)

def map_apply(arguments):
    return arguments[0](*arguments[1:])

class FitThread(CalcThread):
    """Thread performing the fit """

    def __init__(self,
                 fn,
                 page_id,
                 handler,
                 batch_outputs,
                 batch_inputs=None,
                 pars=None,
                 completefn=None,
                 updatefn=None,
                 yieldtime=0.03,
                 worktime=0.03,
                 reset_flag=False):
        CalcThread.__init__(self,
                 completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        self.handler = handler
        self.fitter = fn
        self.pars = pars
        self.batch_inputs = batch_inputs
        self.batch_outputs = batch_outputs
        self.page_id = page_id
        self.starttime = time.time()
        self.updatefn = updatefn
        #Relative error desired in the sum of squares.
        self.reset_flag = reset_flag

    def isquit(self):
        """
        :raise KeyboardInterrupt: when the thread is interrupted
        """
        try:
            CalcThread.isquit(self)
        except KeyboardInterrupt:
            msg = "Fitting: terminated by the user."
            raise KeyboardInterrupt(msg)

    def compute(self):
        """
        Perform a fit
        """
        msg = ""
        try:
            fitter_size = len(self.fitter)
            list_handler = [self.handler]*fitter_size
            list_curr_thread = [self]*fitter_size
            list_reset_flag = [self.reset_flag]*fitter_size
            list_map_get_attr = [map_getattr]*fitter_size
            list_fit_function = ['fit']*fitter_size
            list_q = [None]*fitter_size

            inputs = list(zip(list_map_get_attr, self.fitter, list_fit_function,
                         list_q, list_q, list_handler, list_curr_thread,
                         list_reset_flag))
            result = list(map(map_apply, inputs))
            results = (result, time.time()-self.starttime)
            if self.handler:
                self.completefn(results)
            else:
                return (results)

        except KeyboardInterrupt as msg:
            # Thread was interrupted, just proceed and re-raise.
            # Real code should not print, but this is an example...
            #print "keyboard exception"
            #Stop on exception during fitting. Todo: need to put 
            #some mssg and reset progress bar.

            # Shouldn't this be re-raising? ConsoleUpdate doesn't act on it.
            # raise KeyboardInterrupt
            if self.handler is not None:
                self.handler.stop(msg=msg)
        except Exception as ex:
            # print "ERROR IN FIT THREAD: ", traceback.format_exc()
            if self.handler is not None:
                self.handler.error(msg=str(ex))
                self.completefn(None)
            else:
                return(None)




