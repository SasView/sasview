import sys
import time
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
        CalcThread.__init__(self, completefn, updatefn, yieldtime, worktime)
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
            import copy
            list_handler = []
            list_curr_thread = []
            list_reset_flag = []
            list_map_get_attr = []
            list_fit_function = []
            list_q = []
            for i in range(len(self.fitter)):
                list_handler.append(self.handler)
                list_q.append(None)
                list_curr_thread.append(self)
                list_reset_flag.append(self.reset_flag)
                list_fit_function.append('fit')
                list_map_get_attr.append(map_getattr)
            #from multiprocessing import Pool
            inputs = list(zip(list_map_get_attr, self.fitter, list_fit_function,
                         list_q, list_q, list_handler, list_curr_thread,
                         list_reset_flag))
            result = list(map(map_apply, inputs))

            self.complete(result=result,
                          batch_inputs=self.batch_inputs,
                          batch_outputs=self.batch_outputs,
                          page_id=self.page_id,
                          pars=self.pars,
                          elapsed=time.time() - self.starttime)

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
        except:  # catch-all: show every exception which stops the thread
            import traceback
            if self.handler is not None:
                self.handler.error(msg=traceback.format_exc())
