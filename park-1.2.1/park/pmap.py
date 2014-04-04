"""
Parallel map-reduce implementation using threads.
"""

import traceback
import thread

class Collector(object):
    """
    Abstract interface to map-reduce accumulator function.
    """
    def __call__(self, part):
        """Receive next part, storing it in the accumulated result"""
    def finalize(self):
        """Called when all parts have been accumulated"""
    def error(self, part, msg):
        """
        Exception seen on executing map or reduce.  The collector
        can adjust the accumulated result appropriately to reflect
        the error.
        """

class Mapper(object):
    """
    Abstract interface to map-reduce mapper function.
    """
    def __call__(self, value):
        """Evaluate part"""
    def abort(self):
        """Stop the mapper"""

def pmap(mapper, inputs):
    """
    Apply function mapper to all inputs.
    
    This is the serial version of a parallel iterator, yielding the next 
    sequence value as soon as it is available.  There is no guarantee 
    that the order of the inputs will be preserved in the parallel
    version, so don't depend on it!
    """
    for item in inputs:
        yield mapper(item)

def preduce(collector, outputs):
    """
    Collect all outputs, calling collector(item) for each item in the sequence.
    """
    for item in outputs:
        collector(item)
    return collector

def _pmapreduce_thread(fn, collector, inputs):
    try:
        preduce(collector, pmap(fn,inputs))
        collector.finalize()
    except KeyboardInterrupt:
        fn.abort()
        thread.interrupt_main()
    #except:
    #    raise
    #    msg = traceback.format_exc()
    #    collector.error(msg)

def _pmapreduce_profile(fn, collector, inputs):
    import cProfile, pstats, os
    def mapr():
        _pmapreduce_thread(fn, collector, inputs)
    cProfile.runctx('mapr()', dict(mapr=mapr), {}, 'mapr.out')
    stats = pstats.Stats('mapr.out')
    #stats.sort_stats('time')
    stats.sort_stats('calls')
    stats.print_stats()
    os.unlink('mapr.out')

profile_mapper = False
"""True if the mapper cost should be profiled."""

def pmapreduce(mapper, collector, inputs):
    """
    Apply function mapper to inputs, accumulating the results in collector.
    
    Collector is a function which accepts the result of mapper(item) for 
    each item of inputs.  There is no guarantee that the outputs will be
    received in order.
    
    The map is executed in a separate thread so the function returns
    to the caller immediately.
    """
    global profile_mapper
    fn = _pmapreduce_profile if profile_mapper else _pmapreduce_thread        
    thread.start_new_thread(fn,(mapper,collector, inputs))

def main():
    import time,numpy
    class TestCollector(object):
        def __init__(self):
            self.done = False
        def __call__(self, part):
            print "collecting",part,'for',id(self)
        def finalize(self):
            self.done = True
            print "finalizing"
        def abort(self):
            self.done = True
            print "aborting"
        def error(self,msg):
            print "error",msg
    
    class TestMapper(object):
        def __call__(self, x): 
            print "mapping",x,'for',id(self)
            if x == 8: raise Exception('x is 8')
            time.sleep(4*numpy.random.rand())
            return x

    collector1 = TestCollector()
    collector2 = TestCollector()
    pmapreduce(TestMapper(), collector1, [1,2,3,4,5])
    pmapreduce(TestMapper(), collector2, [1,2,3,8])
    while not collector1.done and not collector2.done:
        time.sleep(1)
if __name__ == "__main__": main()

    
_ = '''
# The choice of job to do next is complicated.
# 1. Strongly prefer a job of the same type as is already running
# on the node.  If this job requires significant resources (e.g.,
# a large file transfer) increase that preference.
# 2. Strongly prefer sending a user's own job to their own machine.
# That way at least they can make progress even if the cluster is busy.
# 3. Try to start each job as soon as possible.  That way if there are
# errors, then the user gets feedback early in the process.
# 4. Try to balance the load across users.  Rather than first come
# first serve, jobs use round robin amongst users.
# 5. Prefer high priority jobs.


def map(apply,collect,items,priority=1):
    mapper = MapJob(apply, items, collect, priority)
    
class MapJob(object):
    """
    Keep track of which jobs have been submitted and which are complete
    """
    def __init__(self, workfn, worklist, manager, priority):
        self.workfn = workfn
        self.worklist = worklist
        self.manager = manager
        self.priority = priority
        self._priority_edge = 0
    def next_work(self):
        

class MapServer(object):
    """
    Keep track of work units.
    """
    def __init__(self):
        self.workingset = {}
        
    def add_work(self, workfn, worklist, manager, priority):
        """
        Add a new work list to distributed to worker objects.  The manager
        gathers the results of the work.  Work is assigned from the queue
        based on priority.
        """
        job = MapJob(workfn, worklist, manager, priority)

        # add work to the queue in priority order
        for i,job in enumerate(self.jobs):
            if job.priority < priority: break
        self.jobs.insert(i,job)
            
        # Create an entry in a persistent store for each job to
        # capture completed work units and to recover from server
        # reboot.

        # Assign _priority_edge to cumsum(priority)/total_priority.
        # This allows us to select the next job according to priority
        # with a random number generator.
        # NOTE: scalability is a bit of a concern --- the lookup
        # operation is linear in the number of active jobs.  This
        # can be mitigated by limiting the number of active jobs.
        total_priority = 0.
        for job in self.jobs: total_priority += job.priority
        edge = 0.
        for job in self.jobs:
            edge += job.priority/total_priority
            self.job._priority_edge = edge
        
    
    def register(self, pool=None):
        """
        Called by a worker when they are registering for work.
        
        Returns the next piece of work.
        """
        P = numpy.random.rand()
        for job in self.jobs:
            if P < j._priority_edge:
                return job.new_work()

        return NoWork

    def update(self, jobid, result):
        """
        Called by a worker when the work unit is complete.
        
        Returns the next piece of work.
        """
        current_job = self.lookup(jobid)
        current_job.reduce(result)
        if numpy.random.rand() < current_job.switch_probability:
            return current_job.next_work()
        
        P = numpy.random.rand()
        for job in self.jobs:
            if P < job._priority_edge:
                if job == current_job:
                    return curent_job.next_work()
                else:
                    return job.new_work()
        
        return NoWork
'''
