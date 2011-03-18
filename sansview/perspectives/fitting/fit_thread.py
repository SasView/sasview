
import sys
from data_util.calcthread import CalcThread


class FitThread(CalcThread):
    """Thread performing the fit """
    
    def __init__(self, parent,
                  fn,
                  page_id,
                   handler,
                  pars=None,
                 completefn = None,
                 updatefn   = None,
                 yieldtime  = 0.01,
                 worktime   = 0.01
                 ):
        CalcThread.__init__(self,completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        self.parent = parent
        self.handler = handler
        self.fitter = fn
        self.pars = pars
        self.page_id = page_id
        self.starttime = 0
        self.updatefn = updatefn
   
    def isquit(self):
        """
        :raise KeyboardInterrupt: when the thread is interrupted
        
        """
        try:
            CalcThread.isquit(self)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
       
    def compute(self):
        """
        Perform a fit 
        """
        try: 
            #self.handler.starting_fit()
            #Result from the fit
            result = self.fitter.fit(handler=self.handler, curr_thread=self)
            self.complete(result= result,
                          page_id=self.page_id,
                          pars = self.pars)
           
        except KeyboardInterrupt, msg:
            # Thread was interrupted, just proceed and re-raise.
            # Real code should not print, but this is an example...
            #print "keyboard exception"
            #Stop on exception during fitting. Todo: need to put some mssg and reset progress bar.
            raise
            #if self.handler is not None:
            #    self.handler.error(msg=msg)
        except:
            raise
            #if self.handler is not None:
            #    self.handler.error(msg=str(sys.exc_value))
           
        
    