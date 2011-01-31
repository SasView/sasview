

"""
ScipyFitting module contains FitArrange , ScipyFit,
Parameter classes.All listed classes work together to perform a 
simple fit with scipy optimizer.
"""

import numpy 
from scipy import optimize

from sans.fit.AbstractFitEngine import FitEngine
from sans.fit.AbstractFitEngine import SansAssembly
#from sans.fit.AbstractFitEngine import FitAbort

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
        msg = [" [Iteration #: %s] | P%-3d  %s......|.....%s" % \
               (self.iterations, p[0], p[1], p[1].value)\
              for p in result_param if p[1].name in self.param_list]
        msg.append("=== goodness of fit: %s" % (str(self.fitness)))
        return "\n".join(msg)
    
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

    def fit(self, q=None, handler=None, curr_thread=None):
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
        result = fitresult(model=model, param_list=self.param_list)
        if handler is not None:
            handler.set_result(result=result)
        #try:
        functor = SansAssembly(self.param_list, model, data, handler=handler,
                         fitresult=result, curr_thread= self.curr_thread)
        out, cov_x, _, _, success = optimize.leastsq(functor,
                                            model.get_params(self.param_list),
                                                    full_output=1,
                                                    warning=True)
        
        #chisqr = functor.chisq(out)
        chisqr = functor.chisq()
        if cov_x is not None and numpy.isfinite(cov_x).all():
            stderr = numpy.sqrt(numpy.diag(cov_x))
        else:
            stderr = None
        if not (numpy.isnan(out).any()) or (cov_x != None):
            result.fitness = chisqr
            result.stderr  = stderr
            result.pvec = out
            result.success = success
            #print result
            if q is not None:
                #print "went here"
                q.put(result)
                #print "get q scipy fit enfine",q.get()
                return q
            return result
        else:  
            raise ValueError, "SVD did not converge" + str(success)
    


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

      