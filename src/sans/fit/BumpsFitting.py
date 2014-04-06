"""
BumpsFitting module runs the bumps optimizer.
"""
import sys
import copy

import numpy

from bumps import fitters
from bumps.mapper import SerialMapper

from sans.fit.AbstractFitEngine import FitEngine
from sans.fit.AbstractFitEngine import FResult

class SansAssembly(object):
    """
    Sans Assembly class a class wrapper to be call in optimizer.leastsq method
    """
    def __init__(self, paramlist, model=None, data=None, fitresult=None,
                 handler=None, curr_thread=None, msg_q=None):
        """
        :param Model: the model wrapper fro sans -model
        :param Data: the data wrapper for sans data
        """
        self.model = model
        self.data = data
        self.paramlist = paramlist
        self.msg_q = msg_q
        self.curr_thread = curr_thread
        self.handler = handler
        self.fitresult = fitresult
        self.res = []
        self.func_name = "Functor"
        self.theory = None
        self.name = "Fill in proper name!"

    @property
    def dof(self):
        return self.data.num_points - len(self.paramlist)

    def summarize(self):
        return "summarize"

    def nllf(self, pvec=None):
        residuals = self.residuals(pvec)
        return 0.5*numpy.sum(residuals**2)

    def setp(self, params):
        self.model.set_params(self.paramlist, params)

    def getp(self):
        return numpy.asarray(self.model.get_params(self.paramlist))

    def bounds(self):
        return numpy.array([self._getrange(p) for p in self.paramlist]).T

    def labels(self):
        return self.paramlist

    def _getrange(self, p):
        """
        Override _getrange of park parameter
        return the range of parameter
        """
        lo, hi = self.model.model.details[p][1:3]
        if lo is None: lo = -numpy.inf
        if hi is None: hi = numpy.inf
        return lo, hi

    def randomize(self, n):
        pvec = self.getp()
        # since randn is symmetric and random, doesn't matter
        # point value is negative.
        # TODO: throw in bounds checking!
        return numpy.random.randn(n, len(self.paramlist))*pvec + pvec

    def chisq(self):
        """
        Calculates chi^2

        :param params: list of parameter values

        :return: chi^2

        """
        total = 0
        for item in self.res:
            total += item * item
        if len(self.res) == 0:
            return None
        return total / len(self.res)

    def residuals(self, params=None):
        """
        Compute residuals
        :param params: value of parameters to fit
        """
        if params is not None: self.setp(params)
        #import thread
        #print "params", params
        self.res, self.theory = self.data.residuals(self.model.eval)

        if self.fitresult is not None:
            self.fitresult.set_model(model=self.model)
            self.fitresult.residuals = self.res+0
            self.fitresult.iterations += 1
            self.fitresult.theory = self.theory+0

            #fitness = self.chisq(params=params)
            fitness = self.chisq()
            self.fitresult.pvec = params
            self.fitresult.set_fitness(fitness=fitness)
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
    __call__ = residuals

    def check_param_range(self):
        """
        Check the lower and upper bound of the parameter value
        and set res to the inf if the value is outside of the
        range
        :limitation: the initial values must be within range.
        """

        #time.sleep(0.01)
        is_outofbound = False
        # loop through the fit parameters
        model = self.model.model
        for p in self.paramlist:
            value = model.getParam(p)
            low,high = model.details[p][1:3]
            if low is not None and numpy.isfinite(low):
                if p.value == 0:
                    # This value works on Scipy
                    # Do not change numbers below
                    value = _SMALLVALUE
                # For leastsq, it needs a bit step back from the boundary
                val = low - value * _SMALLVALUE
                if value < val:
                    self.res *= 1e+6
                    is_outofbound = True
                    break
            if high is not None and numpy.isfinite(high):
                # This value works on Scipy
                # Do not change numbers below
                if value == 0:
                    value = _SMALLVALUE
                # For leastsq, it needs a bit step back from the boundary
                val = high + value * _SMALLVALUE
                if value > val:
                    self.res *= 1e+6
                    is_outofbound = True
                    break

        return is_outofbound

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
            raise RuntimeError, "No Assembly scheduled for Scipy fitting."
        model = fitproblem[0].get_model()
        if reset_flag:
            # reset the initial value; useful for batch
            for name in fitproblem[0].pars:
                ind = fitproblem[0].pars.index(name)
                model.setParam(name, fitproblem[0].vals[ind])
        listdata = []
        listdata = fitproblem[0].get_data()
        # Concatenate dList set (contains one or more data)before fitting
        data = listdata

        self.curr_thread = curr_thread
        ftol = ftol

        result = FResult(model=model, data=data, param_list=self.param_list)
        result.pars = fitproblem[0].pars
        result.fitter_id = self.fitter_id
        result.index = data.idx
        if handler is not None:
            handler.set_result(result=result)
        functor = SansAssembly(paramlist=self.param_list,
                               model=model,
                               data=data,
                               handler=handler,
                               fitresult=result,
                               curr_thread=curr_thread,
                               msg_q=msg_q)
        try:
            run_bumps(functor, result)
        except:
            if hasattr(sys, 'last_type') and sys.last_type == KeyboardInterrupt:
                if handler is not None:
                    msg = "Fitting: Terminated!!!"
                    handler.stop(msg)
                    raise KeyboardInterrupt, msg
            else:
                raise

        if handler is not None:
            handler.set_result(result=result)
            handler.update_fit(last=True)
        if q is not None:
            q.put(result)
            return q
        #if success < 1 or success > 5:
        #    result.fitness = None
        return [result]

def run_bumps(problem, result):
    fitopts = fitters.FIT_OPTIONS[fitters.FIT_DEFAULT]
    fitdriver = fitters.FitDriver(fitopts.fitclass, problem=problem, 
        abort_test=lambda: False, **fitopts.options)
    mapper = SerialMapper 
    fitdriver.mapper = mapper.start_mapper(problem, None)
    try:
        best, fbest = fitdriver.fit()
    except:
        import traceback; traceback.print_exc()
        raise
    mapper.stop_mapper(fitdriver.mapper)
    fitdriver.show()
    #fitdriver.plot()
    result.fitness = fbest * 2. / len(result.pars) 
    result.stderr  = numpy.ones(len(result.pars))
    result.pvec = best 
    result.success = True
    result.theory = problem.theory

def run_scipy(model, result):
    # This import must be here; otherwise it will be confused when more
    # than one thread exist.
    from scipy import optimize

    out, cov_x, _, mesg, success = optimize.leastsq(functor,
                                                    model.get_params(self.param_list),
                                                    ftol=ftol,
                                                    full_output=1)
    if cov_x is not None and numpy.isfinite(cov_x).all():
        stderr = numpy.sqrt(numpy.diag(cov_x))
    else:
        stderr = []
    result.fitness = functor.chisqr()
    result.stderr  = stderr
    result.pvec = out
    result.success = success
    result.theory = functor.theory

