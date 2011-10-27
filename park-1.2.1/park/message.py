# This program is public domain
"""
Asynchronous message streams.

When you have multiple listeners to a process, some of which can connect and
disconnect at different times, you need to dispatch the incoming messages to 
all the listeners.  When a listener joins a running stream, they need to get 
an immediate status update for the computation.  This is stored as the 
stream header. Then, without dropping any messages, the listeners should 
receive all subsequent messages in the stream in order.

The message stream is multi-channelled, and indexed by a key.  Within 
the service framework the key is likely to be the jobid associated with 
the message stream.

The contents of the message stream are expected to be monitor messages
(see `park.monitor` for details), with the stream header being a
`park.monitor.Join` message.  When a new listener is registered,
the header is immediately put on the queue (if there is one), then all
subsequent message are sent until the listener calls hangup().

To attach to a message stream you need an object which accepts put().
An asynchronous queue object is a good choice since it allows you to
buffer the messages in one thread and pull them off as needed in another.
You can also use a `park.monitor.Monitor` object to process the messages
directly.
"""
from __future__ import with_statement

__all__ = ['message_stream']

import thread


# Design note: we cannot buffer the messages in the stream.  The only
# logical buffer size in this case would be the entire stream history
# and that may large.  Furthermore, leading messages in the stream are
# not of value to the computation.  The final result will be available
# for as long as the job is stored on the server, which is a lifetime
# much longer than the message queue.

class MessageStream:
    """
    Message streams.

    For each active job on the system there is a message stream
    containing the job header and a list of listening objects.
    Listeners should accept a put() message to process the next
    item in the stream.
    """
    def __init__(self):
        self._lock = thread.allocate_lock()
        self.listeners = {}
        self.headers = {}

    def __getitem__(self, stream):
        """Get the header for message stream 'stream'."""
        with self._lock:
            return self.headers.get(stream, None)
    def __setitem__(self, stream, message):
        """Set the header for message stream 'stream'."""
        with self._lock:
            self.headers[stream] = message
    def __delitem__(self, stream):
        """Delete the message stream 'stream'."""
        self.headers.pop(stream,None)
        self.listeners.pop(stream,None)

    def put(self, stream, message):
        """
        Put a message on stream 'stream', transfering it to all listening queues.
        """
        #print "post message on",stream,message
        with self._lock:
            #print "post",stream,message,"->",self.listeners.get(stream,[])
            for queue in self.listeners.get(stream,[]):
                queue.put(message)

    def listen(self, stream, queue):
        """
        Listen to message stream 'stream', adding all new messages to queue.

        The stream header will be the first message queued.
        """
        #print "listening on",stream
        with self._lock:
            queues = self.listeners.setdefault(stream,[])
            queues.append(queue)
            #print "listen",stream,"->",self.listeners.get(stream,[])
            # Make sure that the Join header is the first item in the queue.
            header = self.headers.get(stream, None)
            if header is not None:
                queue.put(header)

    def hangup(self, stream, queue):
        """
        Stop listening to message stream 'stream' with queue.

        If stream is None then remove queue from all message streams.
        """
        with self._lock:
            if stream is not None:
                try:
                    queuelist = self.listeners[stream]
                    queuelist.remove(queue)
                    if queuelist == []: del self.listeners[stream]
                except KeyError:
                    pass
                except ValueError:
                    pass
            else:
                purge = []
                for stream,queuelist in self.listeners.iteritems():
                    try:
                        queuelist.remove(queue)
                        if queuelist == []: purge.append(stream)
                    except ValueError:
                        pass
                for stream in purge: del self.listeners[stream]

message_stream = MessageStream()
stream = message_stream # so message.stream works


def demo():
    import Queue
    import time
    t0 = time.time()
    class NamedQueue(Queue.Queue):
        def __init__(self, name):
            Queue.Queue.__init__(self)
            self.name = name
        def __str__(self): return self.name
        def __repr__(self): return "Queue('%s')"%self.name
    def process_queue(queue):
        print ">>>",queue
        while True:
            value = queue.get()
            print "recv",queue,":",value[2],"<-",value[:2],"time",time.time()-t0
    def post(id, stream, deltas):
        for k,t in enumerate(deltas):
            time.sleep(t)
            print "       send ",id,":",stream,"<-",(id,k)
            message_stream.put(stream,(id,k,stream))
    def listen(stream,queue):
        print "+++",queue,":",stream
        message_stream.listen(stream,queue)
    def hangup(stream,queue):
        print "---",queue,":",stream
        message_stream.hangup(stream,queue)

    q1 = NamedQueue('Q1')
    q2 = NamedQueue('Q2')
    q3 = NamedQueue('Q3')
    for q in [q1,q2,q3]: thread.start_new_thread(process_queue,(q,))
    message_queue['M2'] = ('H2',0,'M2')
    thread.start_new_thread(post,('S1','M1',[1,2,1,2,3,2]))
    thread.start_new_thread(post,('S2','M1',[1,2,1,2,3,2]))
    thread.start_new_thread(post,('S3','M2',[1,2,1,2,3,2]))
    thread.start_new_thread(post,('S4','M2',[1,2,1,2,3,2]))
    listen('M1',q1)
    listen('M1',q3)
    listen('M2',q3)
    time.sleep(5)
    hangup(None,q3)
    hangup('M1',q1)
    listen('M2',q2)
    time.sleep(5)
    time.sleep(15)

if __name__ == "__main__": demo()
