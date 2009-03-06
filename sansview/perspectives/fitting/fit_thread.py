
import sys, wx, logging
import string, numpy, math
from sans.guicomm.events import NewPlotEvent, StatusEvent  
from sans.guiframe.calcthread import CalcThread
import park
from park.fitresult import FitHandler
DEFAULT_BEAM = 0.005
import time
import thread
 
class ConsoleUpdate(FitHandler):
    """
    Print progress to the console.
    """
    isbetter = False
    """Record whether results improved since last update"""
    progress_delta =  60
    """Number of seconds between progress updates"""
    improvement_delta = 5
    """Number of seconds between improvement updates"""
    def __init__(self,parent, quiet=False,progress_delta=60,improvement_delta=5):
        """
        If quiet is true, only print out final summary, not progress and
        improvements.
        """
        self.parent= parent
        self.progress_time = time.time()
        self.progress_percent = 0
        self.improvement_time = self.progress_time
        self.isbetter = False
        self.quiet = quiet
        self.progress_delta = progress_delta
        self.improvement_delta = improvement_delta

    def progress(self, k, n):
        """
        Report on progress.
        """
        if self.quiet: return
        t = time.time()
        p = int((100*k)//n)
        
        # Show improvements if there are any
        dt = t - self.improvement_time
        if self.isbetter and dt > self.improvement_delta:
            self.result.print_summary()
            self.isbetter = False
            self.improvement_time = t
            
            wx.PostEvent(self.parent, StatusEvent(status=\
             "%d%% complete ..."%(p),type="update"))
       
        # Update percent complete
        dp = p-self.progress_percent
        if dp < 1: return
        dt = t - self.progress_time
        if dt > self.progress_delta:
            if 1 <= dp <= 2:
                self.progress_percent = p
                self.progress_time = t
                wx.PostEvent(self.parent, StatusEvent(status=\
                                                      "%d%% complete ..."%(p),type="update"))
       
            elif 2 < dp <= 5:
                if p//5 != self.progress_percent//5:
                    wx.PostEvent(self.parent, StatusEvent(status=\
                       "%d%% complete ..."%(5*(p//5)),type="update"))
                    self.progress_percent = p
                    self.progress_time = t
            else:
                if p//10 != self.progress_percent//10:
                    self.progress_percent = p
                    self.progress_time = t
                    wx.PostEvent(self.parent, StatusEvent(status=\
                   "%d%% complete ..."%(10*(p//10)),type="update"))
        
    def improvement(self):
        """
        Called when a result is observed which is better than previous
        results from the fit.
        """
        self.isbetter = True
    
    def error(self, msg):
        """
        Model had an error; print traceback
        """
        if self.isbetter:
            self.result.print_summary()
        print msg

    def finalize(self):
        if self.isbetter:
            self.result.print_summary()

    def abort(self):
        if self.isbetter:
            self.result.print_summary()

class FitThread(CalcThread):
    """Thread performing the fit """
    
    def __init__(self,parent, fn,pars=None,cpage=None, qmin=None,qmax=None,ymin=None, ymax=None,
                 xmin=None,xmax=None,
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
        self.fitter= fn
        self.cpage= cpage
        self.pars = pars
        self.starttime = 0
        self.qmin = qmin
        self.qmax = qmax
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.done= False
        wx.PostEvent(self.parent, StatusEvent(status=\
                       "Start the computation  ",curr_thread=self,type="start"))
    def isquit(self):
        """
             @raise KeyboardInterrupt: when the thread is interrupted
        """
        try:
            CalcThread.isquit(self)
        except KeyboardInterrupt:
            wx.PostEvent(self.parent, StatusEvent(status=\
                       "Calc %g interrupted"))
            raise KeyboardInterrupt
        
    def update(self):
        """
            Is called when values of result are available
        """
        wx.PostEvent(self.parent, StatusEvent(status="Computing \
        ... " ,curr_thread=self,type="update"))
            
    def compute(self):
        """
            Perform a fit 
        """
        try: 
            self.starttime = time.time()
            #Sending a progess message to the status bar
            wx.PostEvent(self.parent, StatusEvent(status=\
                       "Computing . ...",curr_thread=self,type="progress"))
            #Handler used for park engine displayed message
            handler= ConsoleUpdate(parent= self.parent,improvement_delta=0.1)
            #Result from the fit
            result = self.fitter.fit(handler= handler)
        
            elapsed = time.time()-self.starttime
            self.complete(result= result,
                          pars = self.pars,
                          cpage= self.cpage,
                          qmin = self.qmin,
                          qmax = self.qmax,
                          xmin= self.xmin,
                          xmax= self.xmax,
                          ymin = self.ymin,
                          ymax = self.ymax, 
                          elapsed=elapsed )
        except KeyboardInterrupt:
            # Thread was interrupted, just proceed and re-raise.
            # Real code should not print, but this is an example...
            raise
        except:
            raise
            #wx.PostEvent(self.parent, StatusEvent(status="Fitting error: %s" % sys.exc_value))
            #return 
    