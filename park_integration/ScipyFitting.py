

"""
ScipyFitting module contains FitArrange , ScipyFit,
Parameter classes.All listed classes work together to perform a 
simple fit with scipy optimizer.
"""

import numpy 
import sys
from scipy import optimize

from sans.fit.AbstractFitEngine import FitEngine
from sans.fit.AbstractFitEngine import SansAssembly
from sans.fit.AbstractFitEngine import FitAbort
IS_MAC = True
if sys.platform.count("win32") > 0:
    IS_MAC = False
    
class fitresult(object):
    """
    Storing fit result
    """
    def __init__(self, model=None, param_list=None):
        self.calls = None
        self.fitness = None
        self.chisqr = None
        self.pvec = None
        self.cov = None
        self.info = None
        self.mesg = None
        self.success = None
        self.stderr = None
        self.parameters = None
        self.is_mac = IS_MAC
        self.model = model
        self.param_list = param_list
        self.iterations = 0
     
    def set_model(self, model):
        """
        """
        self.model = model
        
    def set_fitness(self, fitness):
        """
        """
        self.fitness = fitness
        
    def __str__(self):
        """
        """
        if self.pvec == None and self.model is None and self.param_list is None:
            return "No results"
        n = len(self.model.parameterset)
        self.iterations += 1
        result_param = zip(xrange(n), self.model.parameterset)
        msg1 = ["[Iteration #: %s ]" % self.iterations]
        msg3 = ["=== goodness of fit: %s ===" % (str(self.fitness))]
        if not self.is_mac:
            msg2 = ["P%-3d  %s......|.....%s" % \
                (p[0], p[1], p[1].value)\
                  for p in result_param if p[1].name in self.param_list]
            msg =  msg1 + msg3 + msg2
        else:
            msg = msg1 + msg3
        msg = "\n".join(msg)
        return msg
    
    def print_summary(self):
        """
        """
        print self   

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
        self.fit_arrange_dict = {}
        self.param_list = []
        self.curr_thread = None
    #def fit(self, *args, **kw):
    #    return profile(self._fit, *args, **kw)

    def fit(self, q=None, handler=None, curr_thread=None, ftol=1.49012e-8):
        """
        """
        fitproblem = []
        for fproblem in self.fit_arrange_dict.itervalues():
            if fproblem.get_to_fit() == 1:
                fitproblem.append(fproblem)
        if len(fitproblem) > 1 : 
            msg = "Scipy can't fit more than a single fit problem at a time."
            raise RuntimeError, msg
            return
        elif len(fitproblem) == 0 : 
            raise RuntimeError, "No Assembly scheduled for Scipy fitting."
            return
    
        listdata = []
        model = fitproblem[0].get_model()
        listdata = fitproblem[0].get_data()
        # Concatenate dList set (contains one or more data)before fitting
        data = listdata
       
        self.curr_thread = curr_thread
        ftol = ftol
        
        # Check the initial value if it is within range
        self._check_param_range(model)
        
        result = fitresult(model=model, param_list=self.param_list)
        if handler is not None:
            handler.set_result(result=result)
        #try:
        functor = SansAssembly(self.param_list, model, data, handler=handler,
                         fitresult=result, curr_thread= self.curr_thread)
        try:
            out, cov_x, _, mesg, success = optimize.leastsq(functor,
                                            model.get_params(self.param_list),
                                                    ftol=ftol,
                                                    full_output=1,
                                                    warning=True)
        except KeyboardInterrupt:
            msg = "Fitting: Terminated!!!"
            handler.error(msg)
            raise KeyboardInterrupt, msg #<= more stable
            #less stable below
            """
            if hasattr(sys, 'last_type') and sys.last_type == KeyboardInterrupt:
                if handler is not None:
                    msg = "Fitting: Terminated!!!"
                    handler.error(msg)
                    result = handler.get_result()
                    return result
            else:
                raise 
            """
        except:
            raise
        print "result0",result.pvec
        chisqr = functor.chisq()
        if cov_x is not None and numpy.isfinite(cov_x).all():
            stderr = numpy.sqrt(numpy.diag(cov_x))
        else:
            stderr = None

        if not (numpy.isnan(out).any()) and (cov_x != None):
            result.fitness = chisqr
            result.stderr  = stderr
            result.pvec = out
            result.success = success
            print "result1",result.pvec
            if q is not None:
                q.put(result)
                return q
            if success < 1 or success > 4:
                result = None
            return result
        else:
            return None
        # Error will be present to the client, not here 
        #else:  
        #    raise ValueError, "SVD did not converge" + str(mesg)
        
    def _check_param_range(self, model):
        """
        Check parameter range and set the initial value inside 
        if it is out of range.
        
        : model: park model object
        """
        is_outofbound = False
        # loop through parameterset
        for p in model.parameterset:        
            param_name = p.get_name()
            # proceed only if the parameter name is in the list of fitting
            if param_name in self.param_list:
                # if the range was defined, check the range
                if numpy.isfinite(p.range[0]):
                    if p.value <= p.range[0]: 
                        # 10 % backing up from the border if not zero
                        # for Scipy engine to work properly.
                        shift = self._get_zero_shift(p.range[0])
                        new_value = p.range[0] + shift
                        p.value =  new_value
                        is_outofbound = True
                if numpy.isfinite(p.range[1]):
                    if p.value >= p.range[1]:
                        shift = self._get_zero_shift(p.range[1])
                        # 10 % backing up from the border if not zero
                        # for Scipy engine to work properly.
                        new_value = p.range[1] - shift
                        # Check one more time if the new value goes below
                        # the low bound, If so, re-evaluate the value 
                        # with the mean of the range.
                        if numpy.isfinite(p.range[0]):
                            if new_value < p.range[0]:
                                new_value = (p.range[0] + p.range[1]) / 2.0
                        # Todo: 
                        # Need to think about when both min and max are same.
                        p.value =  new_value
                        is_outofbound = True
                        
        return is_outofbound
    
    def _get_zero_shift(self, range):
        """
        Get 10% shift of the param value = 0 based on the range value
        
        : param range: min or max value of the bounds
        """
        if range == 0:
            shift = 0.1
        else:
            shift = 0.1 * range
            
        return shift
    
    
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

      