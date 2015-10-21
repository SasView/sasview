import inspect
import wx
from wx import Timer
import wx._misc

def call_later_fix():
    # TODO: test if we need the fix
    wx.CallLater = CallLater
    wx.FutureCall = FutureCall
    wx.PyTimer = PyTimer

def trace_new_id():
    wx.NewId = NewId

def NewId():
    id = wx._misc.NewId()
    path, line, function = _get_caller()
    if path == "sas/guiframe/utils.py":
        # Special case: NewId is being called via an IdList request; we
        # want to which widget triggered the request, not that it was
        # triggered via IdList.
        path, line, function = _get_caller(2)
        tag = " via IdList"
    elif path.endswith("/wxcruft.py"):
        # Special case: NewId is being called via CallLater; we want to
        # know where the CallLater was invoked.
        path, line, function = _get_caller(1)
        tag = " via CallLater"
    else:
        tag = ""
    print "NewId %d from %s(%d):%s%s"%(id, path, line, function, tag)
    return id

def _get_caller(distance=0):
    frame = inspect.stack()[distance+2]
    path = frame[1]
    index = path.find('/sas/')
    if index == -1: index = path.find('\\sas\\')
    return path[index+1:], frame[2], frame[3]



# ==========================================================================
# Hacked versions of CallLater and PyTimer so that the main GUI loop doesn't
# eat wx ids.
# Changed lines are marked #PAK
# ==========================================================================

# For backwards compatibility with 2.4
class PyTimer(Timer):
    def __init__(self, notify, *args, **kw):  #PAK
        Timer.__init__(self, *args, **kw)     #PAK
        self.notify = notify

    def Notify(self):
        if self.notify:
            self.notify()


class CallLater:
    """
    A convenience class for `wx.Timer`, that calls the given callable
    object once after the given amount of milliseconds, passing any
    positional or keyword args.  The return value of the callable is
    availbale after it has been run with the `GetResult` method.

    If you don't need to get the return value or restart the timer
    then there is no need to hold a reference to this object.

    :see: `wx.CallAfter`
    """

    __RUNNING = set()

    def __init__(self, millis, callableObj, *args, **kwargs):
        # print "=================== entering CallLater constructor"
        assert callable(callableObj), "callableObj is not callable"
        self.millis = millis
        self.callable = callableObj
        self.SetArgs(*args, **kwargs)
        self.runCount = 0
        self.running = False
        self.hasRun = False
        self.result = None
        self.timer = None
        self.id = wx.NewId()  # PAK
        self.Start()


    def Start(self, millis=None, *args, **kwargs):
        """
        (Re)start the timer
        """
        self.hasRun = False
        if millis is not None:
            self.millis = millis
        if args or kwargs:
            self.SetArgs(*args, **kwargs)
        self.Stop()
        self.timer = PyTimer(self.Notify, id=self.id)  # PAK
        self.timer.Start(self.millis, wx.TIMER_ONE_SHOT)
        self.running = True
        self.__RUNNING.add(self)
    Restart = Start


    def Stop(self):
        """
        Stop and destroy the timer.
        """
        if self.timer is not None:
            self.timer.Stop()
            self.timer = None
        self.__RUNNING.discard(self)


    def GetInterval(self):
        if self.timer is not None:
            return self.timer.GetInterval()
        else:
            return 0


    def IsRunning(self):
        return self.timer is not None and self.timer.IsRunning()


    def SetArgs(self, *args, **kwargs):
        """
        (Re)set the args passed to the callable object.  This is
        useful in conjunction with Restart if you want to schedule a
        new call to the same callable object but with different
        parameters.
        """
        self.args = args
        self.kwargs = kwargs


    def HasRun(self):
        return self.hasRun


    def GetResult(self):
        return self.result


    def Notify(self):
        """
        The timer has expired so call the callable.
        """
        if self.callable and getattr(self.callable, 'im_self', True):
            self.runCount += 1
            self.running = False
            self.result = self.callable(*self.args, **self.kwargs)
        self.hasRun = True
        if not self.running:
            # if it wasn't restarted, then cleanup
            wx.CallAfter(self.Stop)

    Interval = property(GetInterval)
    Result = property(GetResult)


class FutureCall(CallLater):
    """A compatibility alias for `CallLater`."""
