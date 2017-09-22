# This program is public domain

## \file
#  \brief Abstract class for defining calculation threads.
#
from __future__ import print_function

import traceback
import sys
import logging
try:
    import _thread as thread
except ImportError: # CRUFT: python 2 support
    import thread

if sys.platform.count("darwin") > 0:
    import time
    stime = time.time()

    def clock():
        return time.time() - stime

    def sleep(t):
        return time.sleep(t)
else:
    from time import clock
    from time import sleep

logger = logging.getLogger(__name__)


class CalcThread:
    """Threaded calculation class.  Inherit from here and specialize
    the compute() method to perform the appropriate operations for the
    class.

    If you specialize the __init__ method be sure to call
    CalcThread.__init__, passing it the keyword arguments for
    yieldtime, worktime, update and complete.

    When defining the compute() method you need to include code which
    allows the GUI to run.  They are as follows: ::

        self.isquit()          # call frequently to check for interrupts
        self.update(kw=...)    # call when the GUI could be updated
        self.complete(kw=...)  # call before exiting compute()

    The update() and complete() calls accept field=value keyword
    arguments which are passed to the called function.  complete()
    should be called before exiting the GUI function.  A KeyboardInterrupt
    event is triggered if the GUI signals that the computation should
    be halted.

    The following documentation should be included in the description
    of the derived class.

    The user of this class will call the following: ::

        thread = Work(...,kw=...)  # prepare the work thread.
        thread.queue(...,kw=...)   # queue a work unit
        thread.requeue(...,kw=...) # replace work unit on the end of queue
        thread.reset(...,kw=...)   # reset the queue to the given work unit
        thread.stop()              # clear the queue and halt
        thread.interrupt()         # halt the current work unit but continue
        thread.ready(delay=0.)     # request an update signal after delay
        thread.isrunning()         # returns true if compute() is running

    Use queue() when all work must be done.  Use requeue() when intermediate
    work items don't need to be done (e.g., in response to a mouse move
    event).  Use reset() when the current item doesn't need to be completed
    before the new event (e.g., in response to a mouse release event).  Use
    stop() to halt the current and pending computations (e.g., in response to
    a stop button).

    The methods queue(), requeue() and reset() are proxies for the compute()
    method in the subclass.  Look there for a description of the arguments.
    The compute() method can be called directly to run the computation in
    the main thread, but it should not be called if isrunning() returns true.

    The constructor accepts additional keywords yieldtime=0.01 and
    worktime=0.01 which determine the cooperative multitasking
    behaviour.  Yield time is the duration of the sleep period
    required to give other processes a chance to run.  Work time
    is the duration between sleep periods.

    Notifying the GUI thread of work in progress and work complete
    is done with updatefn=updatefn and completefn=completefn arguments
    to the constructor.  Details of the parameters to the functions
    depend on the particular calculation class, but they will all
    be passed as keyword arguments.  Details of how the functions
    should be implemented vary from framework to framework.

    For wx, something like the following is needed::

        import wx, wx.lib.newevent
        (CalcCompleteEvent, EVT_CALC_COMPLETE) = wx.lib.newevent.NewEvent()

        # methods in the main window class of your application
        def __init__():
            ...
            # Prepare the calculation in the GUI thread.
            self.work = Work(completefn=self.CalcComplete)
            self.Bind(EVT_CALC_COMPLETE, self.OnCalcComplete)
            ...
            # Bind work queue to a menu event.
            self.Bind(wx.EVT_MENU, self.OnCalcStart, id=idCALCSTART)
            ...

        def OnCalcStart(self,event):
            # Start the work thread from the GUI thread.
            self.work.queue(...work unit parameters...)

        def CalcComplete(self,**kwargs):
            # Generate CalcComplete event in the calculation thread.
            # kwargs contains field1, field2, etc. as defined by
            # the Work thread class.
            event = CalcCompleteEvent(**kwargs)
            wx.PostEvent(self, event)

        def OnCalcComplete(self,event):
            # Process CalcComplete event in GUI thread.
            # Use values from event.field1, event.field2 etc. as
            # defined by the Work thread class to show the results.
            ...
    """

    def __init__(self, completefn=None, updatefn=None,
                 yieldtime=0.01, worktime=0.01,
                 exception_handler=None):
        """Prepare the calculator"""
        self.yieldtime     = yieldtime
        self.worktime      = worktime
        self.completefn    = completefn
        self.updatefn      = updatefn
        self.exception_handler = exception_handler
        self._interrupting = False
        self._running      = False
        self._queue        = []
        self._lock         = thread.allocate_lock()
        self._delay        = 1e6

    def queue(self,*args,**kwargs):
        """Add a work unit to the end of the queue.  See the compute()
        method for details of the arguments to the work unit."""
        self._lock.acquire()
        self._queue.append((args, kwargs))
        # Cannot do start_new_thread call within the lock
        self._lock.release()
        if not self._running:
            self._time_for_update = clock() + 1e6
            thread.start_new_thread(self._run, ())

    def requeue(self, *args, **kwargs):
        """Replace the work unit on the end of the queue.  See the compute()
        method for details of the arguments to the work unit."""
        self._lock.acquire()
        self._queue = self._queue[:-1]
        self._lock.release()
        self.queue(*args, **kwargs)

    def reset(self, *args, **kwargs):
        """Clear the queue and start a new work unit.  See the compute()
        method for details of the arguments to the work unit."""
        self.stop()
        self.queue(*args, **kwargs)

    def stop(self):
        """Clear the queue and stop the thread.  New items may be
        queued after stop.  To stop just the current work item, and
        continue the rest of the queue call the interrupt method"""
        self._lock.acquire()
        self._interrupting = True
        self._queue = []
        self._lock.release()

    def interrupt(self):
        """Stop the current work item.  To clear the work queue as
        well call the stop() method."""
        self._lock.acquire()
        self._interrupting = True
        self._lock.release()

    def isrunning(self):
        return self._running

    def ready(self, delay=0.):
        """Ready for another update after delay=t seconds.  Call
        this for threads which can show intermediate results from
        long calculations."""
        self._delay = delay
        self._lock.acquire()
        self._time_for_update = clock() + delay
        # print "setting _time_for_update to ",self._time_for_update
        self._lock.release()

    def isquit(self):
        """Check for interrupts.  Should be called frequently to
        provide user responsiveness.  Also yields to other running
        threads, which is required for good performance on OS X."""

        # Only called from within the running thread so no need to lock
        if self._running and self.yieldtime > 0 \
            and clock() > self._time_for_nap:
            sleep(self.yieldtime)
            self._time_for_nap = clock() + self.worktime
        if self._interrupting:
            raise KeyboardInterrupt

    def update(self, **kwargs):
        """Update GUI with the lastest results from the current work unit."""
        if self.updatefn is not None and clock() > self._time_for_update:
            self._lock.acquire()
            self._time_for_update = clock() + self._delay
            self._lock.release()
            self._time_for_update += 1e6  # No more updates

            self.updatefn(**kwargs)
            sleep(self.yieldtime)
            if self._interrupting:
                raise KeyboardInterrupt
        else:
            self.isquit()
        return

    def complete(self, **kwargs):
        """Update the GUI with the completed results from a work unit."""
        if self.completefn is not None:
            self.completefn(**kwargs)
            sleep(self.yieldtime)
        return

    def compute(self, *args, **kwargs):
        """Perform a work unit.  The subclass will provide details of
        the arguments."""
        raise NotImplemented("Calculation thread needs compute method")

    def exception(self):
        """
        An exception occurred during computation, so call the exception handler
        if there is one.  If not, then log the exception and continue.
        """
        # If we have an exception handler, let it try to handle the exception.
        # If it fails fall through to log the failure to handle the exception
        # (the original exception will be lost).  If there is no exception
        # handler, just log the exception in compute that we are responding to.
        if self.exception_handler:
            try:
                self.exception_handler(*sys.exc_info())
                return
            except Exception:
                pass
        logger.error(traceback.format_exc())
        #print 'CalcThread exception',

    def _run(self):
        """Internal function to manage the thread."""
        # The code for condition wait in the threading package is
        # implemented using polling.  I'll accept for now that the
        # authors of this code are clever enough that polling is
        # difficult to avoid.  Rather than polling, I will exit the
        # thread when the queue is empty and start a new thread when
        # there is more work to be done.
        while 1:
            self._lock.acquire()
            self._time_for_nap = clock() + self.worktime
            self._running = True
            if self._queue == []:
                break
            self._interrupting = False
            args, kwargs = self._queue[0]
            self._queue = self._queue[1:]
            self._lock.release()
            try:
                self.compute(*args, **kwargs)
            except KeyboardInterrupt:
                pass
            except:
                self.exception()
        self._running = False


# ======================================================================
# Demonstration of calcthread in action
class CalcDemo(CalcThread):
    """Example of a calculation thread."""
    def compute(self, n):
        total = 0.
        for i in range(n):
            self.update(i=i)
            for j in range(n):
                self.isquit()
                total += j
        self.complete(total=total)


class CalcCommandline:
    """
        Test method
    """
    def __init__(self, n=20000):
        print(thread.get_ident())
        self.starttime = clock()
        self.done = False
        self.work = CalcDemo(completefn=self.complete,
                             updatefn=self.update, yieldtime=0.001)
        self.work2 = CalcDemo(completefn=self.complete,
                             updatefn=self.update)
        self.work3 = CalcDemo(completefn=self.complete,
                             updatefn=self.update)
        self.work.queue(n)
        self.work2.queue(n)
        self.work3.queue(n)
        print("Expect updates from Main every second and from thread every 2.5 seconds")
        print("")
        self.work.ready(.5)
        while not self.done:
            sleep(1)
            print("Main thread %d at %.2f" % (thread.get_ident(),
                                              clock() - self.starttime))

    def update(self, i=0):
        print("Update i=%d from thread %d at %.2f" % (i, thread.get_ident(),
                                                      clock() - self.starttime))
        self.work.ready(2.5)

    def complete(self, total=0.0):
        print("Complete total=%g from thread %d at %.2f" % (total,
                                                    thread.get_ident(),
                                                    clock() - self.starttime))
        self.done = True
