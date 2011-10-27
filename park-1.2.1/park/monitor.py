# This program is public domain
"""
Asychronous execution monitoring service.

Long running computations need to convey status information to the user.
This status can take multiple forms, such as output to the console or
activity on a GUI, or even mail to your inbox.

park.monitor defines several standard message types::

    `Start` for job start
    `Join` first message when joining an already running job
    `Progress` for job activity
    `Improvement` for partial results
    `Complete` for final result
    `Abort` when job is killed
    `Error` when job has an error
    `Log` for various debugging messages

Individual services may have specialized message types.

park.monitor also defines `Monitor` to process the various kinds of messages,
and dispatch them to the various user defined handlers.

For each message type, the Monitor dispatcher will look for a function
named onMonitorQQQ where QQQ is the message type.  For example,
onMonitorStart(self, message) will be called in response to a Start message.
If onMonitorQQQ is not defined, then onMonitorMessage will be called.  The
default behaviour of onMonitorMessage is to print the message on the console.

Log messages are sent to the standard system logger.  See logging in the
python standard library for details.

The Monitor class has methods for onMonitorStart(message), etc.
In panel, be sure to have methods for onMonitorStart(message), 
onMonitorProgress(message), etc., for the kinds of monitor messages 
the application will send.  The catch-all method is onMonitorMessage.

See `park.monitor` for details on the message types.  Individual services
may have additional message types.

"""
__all__ = ['Monitor']

import sys
import logging
import traceback

class Message(object):
    """
    Message type
    """

class Start(Message):
    """
    Start.

    Sent when the job has started processing.
    """
    def __str__(self): return "Start"

class Join(Message):
    """
    Join: k units of n with partial result
    
    Sent when the listener is attached to a running job.  This is
    a combination of Progress and Improvement.
    """
    def __init__(self, k, n, partial):
        self.total = n
        """Total work to complete"""
        self.complete = k
        """Amount of work complete"""
        self.result = partial
        """The partial result completed; this is job specific"""
    def __str__(self): return "Join: "+str(self.result)
    
class Progress(Message):
    """
    Progress: k units of n.

    Sent when a certain amount of progress has happened.

    Use the job controller to specify the reporting
    frequency (time and/or percentage).
    """
    def __init__(self, k, n, units=None):
        self.total = n
        """Total work to complete"""
        self.complete = k
        """Amount of work complete"""
        self.units = units
        """Units of work, or None"""
    def __str__(self):
        if self.units is not None:
            return "Progress: %s %s of %s"%(self.complete, self.units, self.total)
        else:
            return "Progress: %s of %s"%(self.complete, self.total)

class Improvement(Message):
    """
    Improvement: partial result.

    Use the job controller to specify the improvement frequency
    (time and/or percentage).
    """
    def __init__(self, partial):
        self.result = partial
        """The partial result completed; this is job specific"""
    def __str__(self):
        return "Improvement: "+str(self.result)

class Complete(Message):
    """
    Complete: final result.
    """
    def __init__(self, final):
        self.result = final
        """The final completed result; this is job specific"""
    def __str__(self):
        return "Complete: "+str(self.result)

class Error(Message):
    """
    Traceback stack trace.
    """
    def __init__(self, trace=None):
        if trace == None: trace = sys.exc_info()
        self.trace = trace
        """The stack trace returned from exc_info()"""
    def __str__(self):
        #print "traceback",traceback.format_exception(*self.trace)
        try:
            return "".join(traceback.format_exception(*self.trace))
        except TypeError:
            return "Error: "+str(self.trace)

class Abort(Message):
    """
    Abort: partial result

    Use the job controller to signal an abort.
    """
    def __init__(self, partial):
        self.result = partial
        """The partial result completed; this is job specific"""
    def __str__(self):
        return "Abort: "+str(self.result)

class Log(Message):
    """
    Log module.function: log record
    """
    formatter = logging.Formatter("Log %(module)s.%(funcName)s: %(message)s")
    def __init__(self, record):
        self.record = record
        """The partial result completed; this is job specific"""
    def __str__(self):
        return self.formatter.format(self.record)

class Monitor(object):
    """
    Messages that are received during the processing of the job.

    Standard message types::

        `Start`, `Progress`, `Improvement`, `Complete`, `Error`, `Abort`, `Log`

    Specific job types may have their own monitor messages.

    The messages themselves should all produce nicely formatted results
    in response to str(message).

    The message dispatch calls on<Class>(message) if the on<Class>
    method exists for the message type.  If not, then dispatch
    calls otherwise(message).  By default onLog(message) submits the
    log record to the logger.

    Subclass Monitor to define your own behaviours.
    """
    def put(self, message):
        """
        Called from thread when new message has arrived.
        """
        fn = getattr(self, 
                     "onMonitor"+message.__class__.__name__, 
                     self.onMonitorMessage)
        fn(message)

    def onMonitorMessage(self, message):
        """
        What to do if the message handler is not found.

        Default is to ignore the message.
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
    import sys, time, thread, logging
    import park.monitor

    monitor = Monitor()
    def messagestream(monitor,rate,stream):
        for m in stream:
            time.sleep(rate)
            monitor.put(m)
        time.sleep(rate)
    R = logging.LogRecord('hi',60,'hello.py',3,'log message',(),None,'here')
    try: raise Exception('Test exception')
    except: trace = sys.exc_info()
    stream=[park.monitor.Start(),
            park.monitor.Progress(1,10),
            park.monitor.Progress(2,10),
            park.monitor.Progress(3,10),
            park.monitor.Join('Good'),
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

    time.sleep(20*(rate+0.01))

if __name__ == "__main__": demo(rate=0.1)
