# This program is public domain
"""
Asynchronous monitoring service for wx applications.

Define a monitor using park.wxmonitor.wxMonitor(panel) where panel is
the window which will receive the monitor updates.

In panel, be sure to have methods for onMonitorStart(message), 
onMonitorProgress(message), etc., for the kinds of monitor messages 
the application will send.  The catch-all method is onMonitorMessage,
which by default will print the messages on the console.  If you 
don't catch onMonitorLog messages then the log messages will be 
sent to the standard python logger.

See `park.monitor` for details on the message types.

Example
=======

The following defines a panel which responds to monitor messages::

    import wx

    class Panel(wx.Panel):
        def __init__(self, *args, **kw):
            wx.Panel.__init__(self, *args, **kw)
            self.text = wx.TextCtrl(self, size=(200,100), style=wx.TE_MULTILINE)
            self.gauge = wx.Gauge(self, range=100)
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(self.text, 0, wx.LEFT | wx.EXPAND)
            sizer.Add(self.gauge, 0, wx.LEFT | wx.EXPAND)
            self.SetSizer(sizer)
            self.text.SetValue('starting value')
        def onMonitorMessage(self, message):
            self.text.SetValue(str(message))
        def onMonitorStart(self, message):
            self.text.SetValue(str(message))
            self.gauge.SetValue(0)
        def onMonitorProgress(self, message):
            self.text.SetValue(str(message))
            self.gauge.SetValue(int(100*message.complete/message.total))
        def onMonitorComplete(self, message):
            self.text.SetValue(str(message))
            self.gauge.SetValue(100)

We can put this panel in a simple app::

    app = wx.PySimpleApp()
    frame = wx.Frame(None, -1, 'Test Monitor')
    panel = Panel(frame)
    frame.Show()

Next we attach attach the monitor to this panel and feed some messages from
another thread::

    import time,thread
    import park.wxmonitor, park.monitor
    from park.monitor import Start, Progress, Improvement, Complete
    monitor = park.wxmonitor.wxMonitor(panel)
    msgs = [Start(), Progress(1,10), Progress(3,10), 
            Improvement('Better!'), Progerss(6,10), Complete('Best!')]:
    def message_stream(monitor,msgs):
        time.sleep(1)
        for message in msgs:
          monitor.put(message)
          time.sleep(1)
    thread.start_new_thread(message_stream, (monitor,msgs))
    app.MainLoop()
    
You should see the progress bar jump from 10% to 30% to 60% then all the way 
to the end.
"""
import logging
import time

import wx
import wx.lib.newevent

import park.monitor

(MonitorEvent, EVT_MONITOR) = wx.lib.newevent.NewEvent()

# For wx on Mac OS X we need to sleep after posting a message from
# a thread in order to give the GUI a chance to update itself.
SLEEP_TIME = 0.01
class wxMonitor(park.monitor.Monitor):
    """
    Attach a job monitor to a panel.
    
    The monitor will perform callbacks to onMonitorStart(message),
    onMonitorProgress(message), etc. if the associated method is
    defined.  If the type specific method is not defined, then the
    monitor will call onMonitorMessage(message).  Otherwise the
    message is dropped.
    
    See `park.monitor` for a description of the usual messages.
    """
    def __init__(self, win):
        """
        Window to receive the monitoring events.  This is running in the
        GUI thread.
        """
        self.win = win
        win.Bind(EVT_MONITOR, self.dispatch)

    def put(self, message):
        """
        Intercept an event received from an asynchronous monitor.  This is
        running in the asynchronous thread.
        """
        #print "dispatch",message
        event = MonitorEvent(message=message)
        wx.PostEvent(self.win, event)
        time.sleep(SLEEP_TIME)

    def dispatch(self, event):
        """
        Dispatch the event from the asynchronous monitor.  This is running
        in the GUI thread.
        """
        message = event.message
        #print "window dispatch",message
 
        # First check for a handler in the monitor window
        fn = getattr(self.win, 'onMonitor'+message.__class__.__name__, None)
        # If none, then check in our class (we have a default onMonitorLog)
        if fn is None:
            fn = getattr(self, 'onMonitor'+message.__class__.__name__, None)
        # If still none, then look for the generic handler
        if fn is None:
            fn = getattr(self.win, 'onMonitorMessage', self.onMonitorMessage)
        # Process the message
        fn(message)

    def onMonitorMessage(self, message):
        """
        Generic message handler: do nothing.
        """
        print ">",str(message)

    def onMonitorLog(self, message):
        """
        Called when the job sends a logging record.

        The logging record contains a normal python logging record.

        The default behaviour is to tie into the application logging
        system using::

            logger = logging.getLogger(message.record.name)
            logger.handle(message.record)

        Logging levels are set in the job controller.
        """
        logging.basicConfig()
        logger = logging.getLogger(message.record.name)
        logger.handle(message.record)


def demo(rate=0):
    import thread
    import time
    import sys
    import logging
    
    class Panel(wx.Panel):
        def __init__(self, *args, **kw):
            wx.Panel.__init__(self, *args, **kw)
            self.text = wx.TextCtrl(self, size=(200,100), style=wx.TE_MULTILINE)
            self.gauge = wx.Gauge(self, range=100)
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(self.text, 0, wx.LEFT | wx.EXPAND)
            sizer.Add(self.gauge, 0, wx.LEFT | wx.EXPAND)
            self.SetSizer(sizer)
            self.text.SetValue('starting value')
        def onMonitorMessage(self, message):
            self.text.SetValue(str(message))
        def onMonitorStart(self, message):
            self.text.SetValue(str(message))
            self.gauge.SetValue(0)
        def onMonitorProgress(self, message):
            self.text.SetValue(str(message))
            self.gauge.SetValue(int(100*message.complete/message.total))
        def onMonitorComplete(self, message):
            self.text.SetValue(str(message))
            self.gauge.SetValue(100)

    app = wx.PySimpleApp()
    frame = wx.Frame(None, -1, 'Test Monitor')
    panel = Panel(frame)
    frame.Show()
    monitor = wxMonitor(panel)

    def messagestream(monitor,rate,stream):
        for m in stream:
            time.sleep(rate)
            monitor.put(m)
        time.sleep(rate)
        wx.CallAfter(wx.Exit)
    R = logging.LogRecord('hi',60,'hello.py',3,'log message',(),None,'here')
    try: raise Exception('Test exception')
    except: trace = sys.exc_info()
    stream=[park.monitor.Start(),
            park.monitor.Progress(1,10),
            park.monitor.Progress(2,10),
            park.monitor.Progress(3,10),
            park.monitor.Improvement('Better!'),
            park.monitor.Abort('Abandoned'),
            park.monitor.Start(),
            park.monitor.Progress(1,10,'seconds'),
            park.monitor.Improvement('Better!'),
            park.monitor.Progress(8,10),
            park.monitor.Complete('Best!'),
            park.monitor.Start(),
            park.monitor.Log(R),
            park.monitor.Progress(6,10),
            park.monitor.Error(trace)]
    thread.start_new_thread(messagestream, (monitor,rate,stream))
    app.MainLoop()

if __name__  == "__main__": demo(rate=1)
