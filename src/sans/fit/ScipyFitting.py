"""
ScipyFitting module contains FitArrange , ScipyFit,
Parameter classes.All listed classes work together to perform a 
simple fit with scipy optimizer.
"""
import sys
import copy

import numpy 

from sans.fit.AbstractFitEngine import FitEngine
from sans.fit.AbstractFitEngine import FResult

class SansAssembly:
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
        self.true_res = []
        self.func_name = "Functor"
        self.theory = None

    def chisq(self):
        """
        Calculates chi^2

        :param params: list of parameter values

        :return: chi^2

        """
        total = 0
        for item in self.true_res:
            total += item * item
        if len(self.true_res) == 0:
            return None
        return total / len(self.true_res)

    def __call__(self, params):
        """
            Compute residuals
            :param params: value of parameters to fit
        """
        #import thread
        self.model.set_params(self.paramlist, params)
        #print "params", params
        self.true_res, theory = self.data.residuals(self.model.eval)
        self.theory = copy.deepcopy(theory)
        # check parameters range
        if self.check_param_range():
            # if the param value is outside of the bound
            # just silent return res = inf
            return self.res
        self.res = self.true_res

        if self.fitresult is not None:
            self.fitresult.set_model(model=self.model)
            self.fitresult.residuals = self.true_res
            self.fitresult.iterations += 1
            self.fitresult.theory = theory

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

class ScipyFit(FitEngine):
    """ 
    ScipyFit performs the Fit.This class can be used as follow:
    #Do the fit SCIPY
    create an engine: engine = ScipyFit()
    Use data must be of type plottable
    Use a sans model
    
    Add data with a dictionnary of FitArrangeDict where Uid is a key and data
    is saved in FitArrange object.
    engine.set_data(data,Uid)
    
    Set model parameter "M1"= model.name add {model.parameter.name:value}.
    
    :note: Set_param() if used must always preceded set_model()
         for the fit to be performed.In case of Scipyfit set_param is called in
         fit () automatically.
    
    engine.set_param( model,"M1", {'A':2,'B':4})
    
    Add model with a dictionnary of FitArrangeDict{} where Uid is a key and model
    is save in FitArrange object.
    engine.set_model(model,Uid)
    
    engine.fit return chisqr,[model.parameter 1,2,..],[[err1....][..err2...]]
    chisqr1, out1, cov1=engine.fit({model.parameter.name:value},qmin,qmax)
    """
    def __init__(self):
        """
        Creates a dictionary (self.fit_arrange_dict={})of FitArrange elements
        with Uid as keys
        """
        FitEngine.__init__(self)
        self.curr_thread = None
    #def fit(self, *args, **kw):
    #    return profile(self._fit, *args, **kw)

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
            msg = "Scipy can't fit more than a single fit problem at a time."
            raise RuntimeError, msg
        elif len(fitproblem) == 0 :
            raise RuntimeError, "No Assembly scheduled for Scipy fitting."
        model = fitproblem[0].get_model()
        if reset_flag:
            # reset the initial value; useful for batch
            for name in fitproblem[0].pars:
                ind = fitproblem[0].pars.index(name)
                model.model.setParam(name, fitproblem[0].vals[ind])
        listdata = []
        listdata = fitproblem[0].get_data()
        # Concatenate dList set (contains one or more data)before fitting
        data = listdata
       
        self.curr_thread = curr_thread
        ftol = ftol
        
        # Check the initial value if it is within range
        _check_param_range(model.model, self.param_list)
        
        result = FResult(model=model, data=data, param_list=self.param_list)
        result.pars = fitproblem[0].pars
        result.fitter_id = self.fitter_id
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
            # This import must be here; otherwise it will be confused when more
            # than one thread exist.
            from scipy import optimize
            
            out, cov_x, _, mesg, success = optimize.leastsq(functor,
                                            model.get_params(self.param_list),
                                            ftol=ftol,
                                            full_output=1)
        except:
            if hasattr(sys, 'last_type') and sys.last_type == KeyboardInterrupt:
                if handler is not None:
                    msg = "Fitting: Terminated!!!"
                    handler.stop(msg)
                    raise KeyboardInterrupt, msg
            else:
                raise
        chisqr = functor.chisq()

        if cov_x is not None and numpy.isfinite(cov_x).all():
            stderr = numpy.sqrt(numpy.diag(cov_x))
        else:
            stderr = []
            
        result.index = data.idx
        result.fitness = chisqr
        result.stderr  = stderr
        result.pvec = out
        result.success = success
        result.theory = functor.theory
        if handler is not None:
            handler.set_result(result=result)
            handler.update_fit(last=True)
        if q is not None:
            q.put(result)
            return q
        if success < 1 or success > 5:
            result.fitness = None
        return [result]

        
def _check_param_range(model, param_list):
    """
    Check parameter range and set the initial value inside
    if it is out of range.

    : model: park model object
    """
    # loop through parameterset
    for p in param_list:
        value = model.getParam(p)
        low,high = model.details[p][1:3]
        # if the range was defined, check the range
        if low is not None and value <= low:
            value = low + _get_zero_shift(low)
        if high is not None and value > high:
            value = high - _get_zero_shift(high)
            # Check one more time if the new value goes below
            # the low bound, If so, re-evaluate the value
            # with the mean of the range.
            if low is not None and value < low:
                value = 0.5 * (low+high)
        model.setParam(p, value)

def _get_zero_shift(limit):
    """
    Get 10% shift of the param value = 0 based on the range value

    : param range: min or max value of the bounds
    """
    return 0.1 (limit if limit != 0.0 else 1.0)

    
#def profile(fn, *args, **kw):
#    import cProfile, pstats, os
#    global call_result
#   def call():
#        global call_result
#        call_result = fn(*args, **kw)
#    cProfile.runctx('call()', dict(call=call), {}, 'profile.out')
#    stats = pstats.Stats('profile.out')
#    stats.sort_stats('time')
#    stats.sort_stats('calls')
#    stats.print_stats()
#    os.unlink('profile.out')
#    return call_result

      