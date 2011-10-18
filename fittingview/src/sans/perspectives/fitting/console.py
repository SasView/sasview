


from sans.guiframe.events import StatusEvent 
import time
import wx
import park
from park.fitresult import FitHandler

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
    def __init__(self, parent, manager=None,
                 quiet=False,progress_delta=60,improvement_delta=5):
        """
        If quiet is true, only print out final summary, not progress and
        improvements.
        
        :attr parent: the object that handle the messages
        
        """
        self.parent= parent
        self.manager = manager
        self.progress_time = time.time()
        self.progress_percent = 0
        self.improvement_time = self.progress_time
        self.isbetter = False
        self.quiet = quiet
        self.progress_delta = progress_delta
        self.improvement_delta = improvement_delta
        self.elapsed_time = self.progress_time
        
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
             "%d%% complete ..."%(p),type="progress"))
       
        # Update percent complete
        dp = p-self.progress_percent
        if dp < 1: return
        dt = t - self.progress_time
        if dt > self.progress_delta:
            if 1 <= dp <= 2:
                self.progress_percent = p
                self.progress_time = t
                wx.PostEvent(self.parent, StatusEvent(status=\
                                                      "%d%% complete ..."%(p),
                                                      type="progress"))
       
            elif 2 < dp <= 5:
                if p//5 != self.progress_percent//5:
                    wx.PostEvent(self.parent, StatusEvent(status=\
                        "%d%% complete ..."%(5*(p//5)),type="progress"))
                    self.progress_percent = p
                    self.progress_time = t
            else:
                if p//10 != self.progress_percent//10:
                    self.progress_percent = p
                    self.progress_time = t
                    wx.PostEvent(self.parent, StatusEvent(status=\
                   "%d%% complete ..."%(10*(p//10)),type="progress"))
        
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
        message = "Fit Abort:"
        message = str(msg)+ " \n %s"%self.result.__str__()
        wx.PostEvent(self.parent, StatusEvent(status=message,
                                   info="error", type="stop"))
    def finalize(self):
        """
        """
        if self.isbetter:
            self.result.print_summary()

    def abort(self):
        """
        """
        if self.isbetter:
            self.result.print_summary()
            
        
    def update_fit(self, msg=""):
        """
        """
        self.elapsed_time = time.time() - self.elapsed_time
        dt = self.elapsed_time - self.progress_time
        if dt > 5:
            msg = " Updating fit... \n Chi2/Npts = %s \n"\
                           % (self.result.fitness)
            wx.PostEvent(self.parent, StatusEvent(status=msg, info="info",
                                              type="progress"))
            #time.sleep(0.001)
        
    def starting_fit(self):
        """
        """
        wx.PostEvent(self.parent, StatusEvent(status="Starting the Fit...",
                                        info="info",type="progress"))
        
    def set_result(self, result):
        """
        """
        self.result = result
    
    def get_result(self):
        """
        """
        return self.result
        
    
