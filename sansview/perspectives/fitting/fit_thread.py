

from data_util.calcthread import CalcThread

class FitThread(CalcThread):
    """Thread performing the fit """
    
    def __init__(self, parent,
                  fn,
                   handler,
                  pars=None,
                 cpage=None,
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
        self.cpage= cpage
        self.pars = pars
        self.starttime = 0
        self.updatefn = updatefn
   
    def isquit(self):
        """
             @raise KeyboardInterrupt: when the thread is interrupted
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
            self.handler.starting_fit()
            self.updatefn()
            #Result from the fit
            result = self.fitter.fit(handler=self.handler, curr_thread=self)
            self.updatefn()
            self.complete(result= result,
                          pars = self.pars,
                          cpage= self.cpage)
           
        except KeyboardInterrupt, msg:
            # Thread was interrupted, just proceed and re-raise.
            # Real code should not print, but this is an example...
            #print "keyboard exception"
            #Stop on exception during fitting. Todo: need to put some mssg and reset progress bar.
            self.handler.error(msg=msg)
        
            
         
            
    