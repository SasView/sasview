# This program is public domain
"""
Fitting service interface.

A fit consists of a set of models and a fitting engine.  The models are
collected in an assembly, which manages the parameter set and the
constraints between them.  The models themselves are tightly coupled
to the data that they are modeling and the data is invisible to the fit.

The fitting engine can use a variety of methods depending on model.


Usage
=====

The fitter can be run directly on the local machine::

    import park
    M1 = park.models.Peaks(datafile=park.sampledata('peak.dat'))
    M1.add_peak('P1', 'gaussian', A=[4,6], mu=[0.2, 0.5], sigma=0.1)
    result = park.fit(models=[M1])
    print result

The default settings print results every time the fit improves, and
print a global result when the fit is complete.  This is a suitable
interface for a fitting script.

For larger fit jobs you will want to run the fit on a remote server.
The model setup is identical, but the fit call is different::

    service = park.FitService('server:port')
    result = park.fit(models=[M1], service=service)
    print result

Again, the default settings print results every time the fit improves,
and print a global result when the fit is complete.

For long running fit jobs, you want to be able to disconnect from
the server after submitting the job, and later reconnect to fetch
the results.  An additional email field will send notification by
email when the fit starts and ends, and daily updates on the status
of all fits::

    service = park.FitService('server:port')
    service.notify(email='me@my.email.address',update='daily')
    fit = park.Fit(models=[M1])
    id = service.submit_job(fit, jobname='peaks')
    print id

The results can be retrieved either by id returned from the server,
or by the given jobname::

    import park
    service = park.FitService('server:port',user='userid')
    fitlist = service.retrieve('peaks')
    for fit in fitlist:
        print fit.summary()

The fit itself is a complicated object, including the model, the
optimizer, and the type of uncertainty analysis to perform.

GUI Usage
=========

When used from a graphical user interface, a different programming
interface is needed.  In this case, the user may want to watch
the progress of the fit and perhaps stop it.  Also, as fits can
take some time to complete, the user would like to be able to
set up additional fits and run them at the same time, switching
between them as necessary to monitor progress.

"""
import time, thread

import numpy

import assembly, fitresult

class Objective(object):
    """
    Abstract interface to the fitness function for the park minimizer
    classes.

    Park provides a specific implementation `park.assembly.Assembly`.

    TODO: add a results() method to return model specific info to the
    TODO: fit handler.
    """
    def residuals(self, p):
        """
        Some fitters, notably Levenberg-Marquardt, operate directly on the
        residuals vector.  If the individual residuals are not available,
        then LM cannot be used.

        This method is optional.
        """
        raise NotImplementedError

    def residuals_deriv(self, p):
        """
        Returns residuals and derivatives with respect to the given
        parameters.

        If these are unavailable in the model, then they can be approximated
        by numerical derivatives, though it is generally better to use a
        derivative free optimizer such as coliny or cobyla which can use the
        function evaluations more efficiently.  In any case, your objective
        function is responsible for calculating these.

        This method is optional.
        """
        raise NotImplementedError

    def fit_parameters(self):
        """
        Returns a list of fit parameters.  Each parameter has a name,
        an initial value and a range.

        See `park.fitresult.FitParameter` for an example.

        On each function evaluation a new parameter set will be passed
        to the fitter, with values in the same order as the list of
        parameters.
        """
        raise NotImplementedError

    def __call__(self, p):
        """
        Returns the objective value for parameter set p .
        """
        raise NotImplementedError

    def abort(self):
        """
        Halts the current function evaluation, and has it return inf.
        This will be called from a separate thread.  If the function
        contains an expensive calculation, it should reset an abort
        flag before each evaluation and test it periodically.

        This method is optional.
        """

class Fitter(object):
    """Abstract interface for a fitness optimizer.

    A fitter has a single method, fit, which takes an objective
    function (`park.fit.Objective`) and a handler.

    For a concrete instance see `park.fitmc.FitMC`.
    """
    def __init__(self, **kw):
        for k,v in kw.items():
            if hasattr(self,k):
                setattr(self,k,v)
            else:
                raise AttributeError(k+" is not an attribute of "+self.__class__.__name__)

    def _threaded(self, fn, *args, **kw):
        thread.start_new_thread(fn,args,kw)


    def _fit(self, objective, x0, bounds):
        """
        Run the actual fit in a separate thread

        Each cycle k of n:
            self.handler.progress(k,n)
        Each improvement:
            self.handler.result.update(x,fx,ncalls)
            self.handler.improvement()
        On completion (if not already performed):
            self.hander.result.update(x,fx,ncalls)
            self.handler.done
            self.handler.finalize()
        """
        raise NotImplementedError

    def fit(self, fitness, handler):
        """
        Global optimizer.

        This function should return immediately
        """
        # Determine initial value and bounds
        pars = fitness.fit_parameters()
        bounds = numpy.array([p.range for p in pars]).T
        x0 = [p.value for p in pars]

        # Initialize the monitor and results.
        # Need to make our own copy of the fit results so that the
        # values don't get stomped on by the next fit iteration.
        handler.done = False
        self.handler = handler
        fitpars = [fitresult.FitParameter(pars[i].name,pars[i].range,v)
                   for i,v in enumerate(x0)]
        handler.result = fitresult.FitResult(fitpars, 0, numpy.NaN)

        # Run the fit (fit should perform _progress and _improvement updates)
        # This function may return before the fit is complete.
        self._fit(fitness, x0, bounds)

class FitJob(object):
    """
    Fit job.

    This implements `park.job.Job`.
    """
    def __init__(self, objective=None, fitter=None, handler=None):
        self.fitter = fitter
        self.objective = objective
        self.handler = handler
    def run(self):
        self.fitter.fit(self.objective, self.handler)

class LocalQueue(object):
    """
    Simple interface to the local job queue.  Currently supports start and
    wait.  Needs to support stop and status.  Also, needs to be a proper queue,
    and needs to allow jobs to run in separate processes according to priority,
    etc.  All the essentials of the remote queuing system without the remote
    calls.

    Unlike the remote queue, the local queue need not maintain persistence.
    """
    running = False
    def start(self, job):
        self.job = job
        job.run()
        return id(job)

    def wait(self, interval=.1):
        """
        Wait for the job to complete.  This is used in scripts to impose
        a synchronous interface to the fitting service.
        """
        while not self.job.handler.done:
            time.sleep(interval)
        return self.job.handler.result

def fit(models=None, fitter=None, service=None, handler=None):
    """
    Start a fit with a set of models.  The model set must be
    in a form accepted by `park.assembly.Assembly`.

    This is a convenience function which sets up the default
    optimizer and uses the local fitting engine to do the work.
    Progress reports are printed as they are received.

    The choice of fitter, service and handler can be specified
    by the caller.

    The default fitter is FitMC, which is a monte carlo Nelder-Mead
    simplex local optimizer with 100 random start points.

    The default handler does nothing.  Instead, ConsoleUpdate could
    be used to report progress during the fit.

    The default service is to run in a separate thread with FitThread.
    Note that this will change soon to run in a separate process on
    the local machine so that python's global interpreter lock does
    not interfere with parallelism.
    """
    if models is None: raise RuntimeError('fit expected a list of models')
    if service is None: service = LocalQueue()
    if fitter is None:
        import fitmc
        fitter = fitmc.FitMC()
    if handler is None: handler = fitresult.FitHandler()

    objective = assembly.Assembly(models) if isinstance(models,list) else models
    job = FitJob(objective,fitter,handler)
    service.start(job)
    return service.wait()


def assembly_example():
    import park, time
    problem = park.assembly.example()
    #result = fit(problem)
    #result.print_summary()
    handler=fitresult.ConsoleUpdate(improvement_delta=0.1,progress_delta=1)
    #result = fit(problem, handler=handler)
    result = fit(problem)
    print "=== Fit complete ==="
    result.print_summary()
    print "=== Target values ==="
    print "M1: a=1, c=1.5"
    print "M2: a=2.5, c=3"

    if False:  # Detailed results
        print "parameter vector",result.pvec
        problem(result.pvec)
        print "residuals",problem.residuals
        for k,m in enumerate(problem.parts):
            print "Model",k,"chisq",m.chisq,"weight",m.weight
            print "pars",m.fitness.model.a,m.fitness.model.c
            print "x",m.fitness.data.fit_x
            print "y",m.fitness.data.fit_y
            print "f(x)",m.fitness.data.fx
            print "(y-f(x))/dy",m.residuals


def demo(fitter=None):
    """Multiple minima example"""
    import time, math
    class MultiMin(object):
        def fit_parameters(self):
            return [fitresult.FitParameter('x1',[-5,5],1)]
        def __call__(self, p):
            x=p[0]
            fx = x**2 + math.sin(2*math.pi*x+3*math.pi/2)
            return fx
    handler = fitresult.ConsoleUpdate() # Show updates on the console
    handler.progress_delta = 1          # Update user every second
    handler.improvement_delta = 0.1     # Show improvements almost immediately
    fitter.fit(MultiMin(), handler)
    while not handler.done: time.sleep(1)

def demo2(fitter=None):
    import park, time
    problem = park.assembly.example()
    handler = fitresult.ConsoleUpdate() # Show updates on the console
    handler.progress_delta = 1          # Update user every second
    handler.improvement_delta = 1       # Show improvements at the same rate
    fitter.fit(problem, handler)
    while not handler.done: time.sleep(1)



if __name__ == "__main__":
    #main()
    assembly_example()
