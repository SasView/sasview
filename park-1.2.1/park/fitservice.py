# This program is public domain
"""
Interface to the PARK fitting service.

*** WARNING *** This is a design sketch and is not presently used.
"""

class FitClient(object):
    """
    Client-side view of the fitting service.
    """
    def __init__(self, url=DEFAULT_URL,user=DEFAULT_USER):
        self.url = url
        self.user = user
        self.server = xmlrpclib.Server(self.server)
        self.context = self.server.welcome(self.user)

    # User management
    def notify(self,email=None,rate=None):
        """Set the email address and update frequency for user notification"""
        if email is not None:
            self.server.setemail(self.context, email)
        if rate is not None:
            self.server.setrate(self.context, rate)

    # Job management
    def find_by_name(self, name):
        return self.server.find_by_name(self.context,status)
    def find_jobs(self,status='active'):
        """List active and recently completed jobs"""
        return self.server.find_jobs(self.context,status)
    def stop(self, jobid):
        """Delete job"""
        self.server.delete(self.context, jobid)
    def start(self, job):
        s = encode(job)
        return self.server.submit(self.context, jobname, job)
    def fetch_job(self, jobid):
        """Retrieve job"""
        text = self.server.retrieve(self.context, jobid)
        return encode(text)
    def status(self, jobid):
        """Return the current job status"""
        return self.server.status(self.context, jobid)
    
    # Message Queue
    def _listener(self, callback):
        while True:
            message = self.server.next_message(self.user)
            event,result = pickle.loads(text)
            callback(event, self, result)

    def listen(self, callback=on_message):
        """
        Listen to the message queue for information about running jobs.

        The listener runs in a separate thread, allowing the listen
        call to return immediately.  The callback is called each time
        there is a new message on the queue.  If no callback is
        supplied, then a simple print is used.
        """
        thread.start_new_thread(self._listener,(callback,))



class Fit(object): 
    """ 
    Coordinate the fit.
    """
    update = on_fit_update
    complete = on_fit_complete
    def __init__(self, models = [],
                 optimizer = None,
                 service = None,
                 update = None,
                 complete = None):
        """
        Set up the fit.

        models []
           List of models which make up the assembly.
        optimizer
           Optimizer to use for the fit
        """
        self.assembly = assembly.Assembly(models)
        self.optimizer = optimizer
        self.complete = complete
        self.update = update
        self.isrunning = False
        self._stopping = False

    def stop(self):
        """
        Interrupt a running fit.
        """
        self._stopping = True
        self.service.stop()

    def start(self):
        """
        Start the fit.
        """
        self.service.start()

    def _update(self, result):
        self.result = result
        if self.update: self.update(self,result)

    def _complete(self, result):
        self.result = result
        if self.complete: self.complete(self,result)

    def wait(self):
        """
        Wait for a fit to complete.
        """
        while self.isrunning: time.sleep(0.1)

    def fit(self):
        """ 
        Start the fit and wait for the result.
        Returns the result.
        """
        self.start()
        self.wait()
        return self.result
