"""
BumpsFitting module runs the bumps optimizer.
"""
import time

import numpy

from bumps import fitters
from bumps.mapper import SerialMapper

from sans.fit.AbstractFitEngine import FitEngine
from sans.fit.AbstractFitEngine import FResult

class BumpsMonitor(object):
    def __init__(self, handler, max_step=0):
        self.handler = handler
        self.max_step = max_step
    def config_history(self, history):
        history.requires(time=1, value=2, point=1, step=1)
    def __call__(self, history):
        self.handler.progress(history.step[0], self.max_step)
        if len(history.step)>1 and history.step[1] > history.step[0]:
            self.handler.improvement()
        self.handler.update_fit()

class SasProblem(object):
    """
    Wrap the SAS model in a form that can be understood by bumps.
    """
    def __init__(self, param_list, model=None, data=None, fitresult=None,
                 handler=None, curr_thread=None, msg_q=None):
        """
        :param Model: the model wrapper fro sans -model
        :param Data: the data wrapper for sans data
        """
        self.model = model
        self.data = data
        self.param_list = param_list
        self.res = None
        self.theory = None

    @property
    def name(self):
        return self.model.name

    @property
    def dof(self):
        return self.data.num_points - len(self.param_list)

    def summarize(self):
        """
        Return a stylized list of parameter names and values with range bars
        suitable for printing.
        """
        output = []
        bounds = self.bounds()
        for i,p in enumerate(self.getp()):
            name = self.param_list[i]
            low,high = bounds[:,i]
            range = ",".join((("[%g"%low if numpy.isfinite(low) else "(-inf"),
                              ("%g]"%high if numpy.isfinite(high) else "inf)")))
            if not numpy.isfinite(p):
                bar = "*invalid* "
            else:
                bar = ['.']*10
                if numpy.isfinite(high-low):
                    position = int(9.999999999 * float(p-low)/float(high-low))
                    if position < 0: bar[0] = '<'
                    elif position > 9: bar[9] = '>'
                    else: bar[position] = '|'
                bar = "".join(bar)
            output.append("%40s %s %10g in %s"%(name,bar,p,range))
        return "\n".join(output)

    def nllf(self, p=None):
        residuals = self.residuals(p)
        return 0.5*numpy.sum(residuals**2)

    def setp(self, p):
        for k,v in zip(self.param_list, p):
            self.model.setParam(k,v)
        #self.model.set_params(self.param_list, params)

    def getp(self):
        return numpy.array([self.model.getParam(k) for k in self.param_list])
        #return numpy.asarray(self.model.get_params(self.param_list))

    def bounds(self):
        return numpy.array([self._getrange(p) for p in self.param_list]).T

    def labels(self):
        return self.param_list

    def _getrange(self, p):
        """
        Override _getrange of park parameter
        return the range of parameter
        """
        lo, hi = self.model.details[p][1:3]
        if lo is None: lo = -numpy.inf
        if hi is None: hi = numpy.inf
        return lo, hi

    def randomize(self, n):
        p = self.getp()
        # since randn is symmetric and random, doesn't matter
        # point value is negative.
        # TODO: throw in bounds checking!
        return numpy.random.randn(n, len(self.param_list))*p + p

    def chisq(self):
        """
        Calculates chi^2

        :param params: list of parameter values

        :return: chi^2

        """
        return numpy.sum(self.res**2)/self.dof

    def residuals(self, params=None):
        """
        Compute residuals
        :param params: value of parameters to fit
        """
        if params is not None: self.setp(params)
        #import thread
        #print "params", params
        self.res, self.theory = self.data.residuals(self.model.evalDistribution)
        return self.res

BOUNDS_PENALTY = 1e6 # cost for going out of bounds on unbounded fitters
class MonitoredSasProblem(SasProblem):
    """
    SAS problem definition for optimizers which do not have monitoring or bounds.
    """
    def __init__(self, param_list, model=None, data=None, fitresult=None,
                 handler=None, curr_thread=None, msg_q=None, update_rate=1):
        """
        :param Model: the model wrapper fro sans -model
        :param Data: the data wrapper for sans data
        """
        SasProblem.__init__(self, param_list, model, data)
        self.msg_q = msg_q
        self.curr_thread = curr_thread
        self.handler = handler
        self.fitresult = fitresult
        #self.last_update = time.time()
        #self.func_name = "Functor"
        #self.name = "Fill in proper name!"

    def residuals(self, p):
        """
        Cost function for scipy.optimize.leastsq, which does not have a monitor
        built into the algorithm, and instead relies on a monitor built into
        the cost function.
        """
        # Note: technically, unbounded fitters and unmonitored fitters are
        self.setp(x)

        # Compute penalty for being out of bounds which increases the farther
        # you get out of bounds.  This allows derivative following algorithms
        # to point back toward the feasible region.
        penalty = self.bounds_penalty()
        if penalty > 0:
            self.theory = numpy.ones(self.data.num_points)
            self.res = self.theory*(penalty/self.data.num_points) + BOUNDS_PENALTY
            return self.res

        # If no penalty, then we are not out of bounds and we can use the
        # normal residual calculation
        SasProblem.residuals(self, p)

        # send update to the application
        if True:
            #self.fitresult.set_model(model=self.model)
            # copy residuals into fit results
            self.fitresult.residuals = self.res+0
            self.fitresult.iterations += 1
            self.fitresult.theory = self.theory+0

            self.fitresult.p = numpy.array(p) # force copy, and coversion to array
            self.fitresult.set_fitness(fitness=self.chisq())
            if self.msg_q is not None:
                self.msg_q.put(self.fitresult)

            if self.handler is not None:
                self.handler.set_result(result=self.fitresult)
                self.handler.update_fit()

            if self.curr_thread != None:
                try:
                    self.curr_thread.isquit()
                except:
                    #msg = "Fitting: Terminated...       Note: Forcing to stop "
                    #msg += "fitting may cause a 'Functor error message' "
                    #msg += "being recorded in the log file....."
                    #self.handler.stop(msg)
                    raise

        return self.res

    def bounds_penalty(self):
        from numpy import sum, where
        p, bounds = self.getp(), self.bounds()
        return (sum(where(p<bounds[:,0], bounds[:,0]-p, 0)**2)
              + sum(where(p>bounds[:,1], bounds[:,1]-p, 0)**2) )

class BumpsFit(FitEngine):
    """
    Fit a model using bumps.
    """
    def __init__(self):
        """
        Creates a dictionary (self.fit_arrange_dict={})of FitArrange elements
        with Uid as keys
        """
        FitEngine.__init__(self)
        self.curr_thread = None

    def fit(self, msg_q=None,
            q=None, handler=None, curr_thread=None,
            ftol=1.49012e-8, reset_flag=False):
        """
        """
        fitproblem = []
        for fproblem in self.fit_arrange_dict.itervalues():
            if fproblem.get_to_fit() == 1:
                fitproblem.append(fproblem)
        if len(fitproblem) > 1 :
            msg = "Bumps can't fit more than a single fit problem at a time."
            raise RuntimeError, msg
        elif len(fitproblem) == 0 :
            raise RuntimeError, "No problem scheduled for fitting."
        model = fitproblem[0].get_model()
        if reset_flag:
            # reset the initial value; useful for batch
            for name in fitproblem[0].pars:
                ind = fitproblem[0].pars.index(name)
                model.setParam(name, fitproblem[0].vals[ind])
        data = fitproblem[0].get_data()

        self.curr_thread = curr_thread

        result = FResult(model=model, data=data, param_list=self.param_list)
        result.pars = fitproblem[0].pars
        result.fitter_id = self.fitter_id
        result.index = data.idx
        if handler is not None:
            handler.set_result(result=result)

        if True: # bumps
            problem = SasProblem(param_list=self.param_list,
                                 model=model.model,
                                 data=data)
            run_bumps(problem, result, ftol,
                      handler, curr_thread, msg_q)
        else:
            problem = SasProblem(param_list=self.param_list,
                                 model=model.model,
                                 data=data,
                                 handler=handler,
                                 fitresult=result,
                                 curr_thread=curr_thread,
                                 msg_q=msg_q)
            run_levenburg_marquardt(problem, result, ftol)

        if handler is not None:
            handler.update_fit(last=True)
        if q is not None:
            q.put(result)
            return q
        #if success < 1 or success > 5:
        #    result.fitness = None
        return [result]

def run_bumps(problem, result, ftol, handler, curr_thread, msg_q):
    def abort_test():
        if curr_thread is None: return False
        try: curr_thread.isquit()
        except KeyboardInterrupt:
            if handler is not None:
                handler.stop("Fitting: Terminated!!!")
            return True
        return False

    fitopts = fitters.FIT_OPTIONS[fitters.FIT_DEFAULT]
    fitclass = fitopts.fitclass
    options = fitopts.options.copy()
    max_steps = fitopts.options.get('steps', 0) + fitopts.options.get('burn', 0)
    if 'monitors' not in options:
        options['monitors'] = [BumpsMonitor(handler, max_steps)]
    options['ftol'] = ftol
    fitdriver = fitters.FitDriver(fitclass, problem=problem,
                                  abort_test=abort_test, **options)
    mapper = SerialMapper 
    fitdriver.mapper = mapper.start_mapper(problem, None)
    try:
        best, fbest = fitdriver.fit()
    except:
        import traceback; traceback.print_exc()
        raise
    finally:
        mapper.stop_mapper(fitdriver.mapper)
    #print "best,fbest",best,fbest,problem.dof
    result.fitness = 2*fbest/problem.dof
    #print "fitness",result.fitness
    result.stderr  = fitdriver.stderr()
    result.pvec = best
    # TODO: track success better
    result.success = True
    result.theory = problem.theory

def run_levenburg_marquardt(problem, result, ftol):
    # This import must be here; otherwise it will be confused when more
    # than one thread exist.
    from scipy import optimize

    out, cov_x, _, mesg, success = optimize.leastsq(problem.residuals,
                                                    problem.getp(),
                                                    ftol=ftol,
                                                    full_output=1)
    if cov_x is not None and numpy.isfinite(cov_x).all():
        stderr = numpy.sqrt(numpy.diag(cov_x))
    else:
        stderr = []
    result.fitness = problem.chisq()
    result.stderr  = stderr
    result.pvec = out
    result.success = success
    result.theory = problem.theory

