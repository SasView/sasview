


from sas.sasgui.guiframe.events import StatusEvent
import time
import wx
from sas.sascalc.fit import FitHandler

class ConsoleUpdate(FitHandler):
    """
    Print progress to the console.
    """
    isbetter = False
    """Record whether results improved since last update"""
    progress_delta = 60
    """Number of seconds between progress updates"""
    improvement_delta = 5
    """Number of seconds between improvement updates"""
    def __init__(self, parent, manager=None,
                 quiet=False, progress_delta=60, improvement_delta=5):
        """
        If quiet is true, only print out final summary, not progress and
        improvements.

        :attr parent: the object that handle the messages

        """
        self.parent = parent
        self.manager = manager
        self.progress_time = time.time()
        self.progress_percent = 0
        self.improvement_time = self.progress_time
        self.isbetter = False
        self.quiet = quiet
        self.progress_delta = progress_delta
        self.improvement_delta = improvement_delta
        self.elapsed_time = time.time()
        self.update_duration = time.time()
        self.fit_duration = 0


    def progress(self, k, n):
        """
        Report on progress.
        """
        if self.quiet: return

        t = time.time()
        p = int((100 * k) // n)

        # Show improvements if there are any
        dt = t - self.improvement_time
        if self.isbetter and dt > self.improvement_delta:
            #self.result.print_summary()
            self.update_fit()
            self.isbetter = False
            self.improvement_time = t

        # Update percent complete
        dp = p - self.progress_percent
        if dp < 1: return
        dt = t - self.progress_time
        if dt > self.progress_delta:
            if 1 <= dp <= 2:
                self.progress_percent = p
                self.progress_time = t
                self.update_fit()
            elif 2 < dp <= 5:
                if p // 5 != self.progress_percent // 5:
                    self.progress_percent = p
                    self.progress_time = t
            else:
                if p // 10 != self.progress_percent // 10:
                    self.progress_percent = p
                    self.progress_time = t
                    self.update_fit()

    def improvement(self):
        """
        Called when a result is observed which is better than previous
        results from the fit.
        """
        self.isbetter = True

    def print_result(self):
        """
        Print result object
        """
        msg = " \n %s \n" % str(self.result)
        wx.PostEvent(self.parent, StatusEvent(status=msg))

    def error(self, msg):
        """
        Model had an error; print traceback
        """
        if self.isbetter:
            #self.result.print_summary()
            self.update_fit()

        message = str(msg) + " \n %s \n" % self.result.__str__()
        wx.PostEvent(self.parent, StatusEvent(status=message,
                                   info="error", type="stop"))
    def stop(self, msg):
        """
        Post event msg and stop
        """
        if self.isbetter:
            #self.result.print_summary()
            self.update_fit()

        message = str(msg) + " \n %s \n" % self.result.__str__()
        wx.PostEvent(self.parent, StatusEvent(status=message,
                                   info="info", type="stop"))

    def finalize(self):
        """
        """
        if self.isbetter:
            #self.result.print_summary()
            self.update_fit()

    def abort(self):
        """
        """
        if self.isbetter:
            #self.result.print_summary()
            self.update_fit()


    def update_fit(self, last=False):
        """
        """
        t1 = time.time()
        self.elapsed_time = t1 - self.update_duration
        self.update_duration = t1
        self.fit_duration += self.elapsed_time
        str_time = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime(t1))
        UPDATE_INTERVAL = 5.0
        u_flag = False
        if self.fit_duration >= UPDATE_INTERVAL:
            self.fit_duration = 0
            u_flag = True
        msg = str_time
        if u_flag or last:
            if self.result is not None:
                data_name, model_name = None, None
                d_flag = (hasattr(self.result, "data") and \
                    self.result.data is not None and \
                    hasattr(self.result.data, "sas_data") and
                    self.result.data.sas_data is not None)
                m_flag = (hasattr(self.result, "model") and \
                          self.result.model is not None)
                if d_flag:
                    data_name = self.result.data.sas_data.name
                if m_flag:
                    model_name = str(self.result.model.name)
                if m_flag and d_flag:
                    msg += "Data : %s \n" % (str(data_name))#,
                                                     #str(model_name))
                msg += str(self.result)
                msg += "\n"
            else:
                msg += "No result available\n"
            wx.PostEvent(self.parent, StatusEvent(status=msg, info="info",
                                              type="progress"))

    def starting_fit(self):
        """
        """
        wx.PostEvent(self.parent, StatusEvent(status="Starting the Fit...",
                                        info="info", type="progress"))

    def set_result(self, result):
        """
        """
        self.result = result

    def get_result(self):
        """
        """
        return self.result


