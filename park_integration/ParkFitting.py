


"""
ParkFitting module contains SansParameter,Model,Data
FitArrange, ParkFit,Parameter classes.All listed classes work together
to perform a simple fit with park optimizer.
"""
#import time
import numpy
#import park
from park import fit
from park import fitresult
from park.assembly import Assembly
from park.fitmc import FitSimplex 
import park.fitmc
from park.fitmc import FitMC

#from Loader import Load
from sans.fit.AbstractFitEngine import FitEngine



class MyAssembly(Assembly):
    def __init__(self, models, curr_thread=None):
        Assembly.__init__(self, models)
        self.curr_thread = curr_thread
        
    def eval(self):
        """
        Recalculate the theory functions, and from them, the
        residuals and chisq.

        :note: Call this after the parameters have been updated.
        """
        # Handle abort from a separate thread.
        self._cancel = False
        if self.curr_thread != None:
            try:
                self.curr_thread.isquit()
            except:
                self._cancel = True

        # Evaluate the computed parameters
        self._fitexpression()

        # Check that the resulting parameters are in a feasible region.
        if not self.isfeasible(): return numpy.inf

        resid = []
        k = len(self._fitparameters)
        for m in self.parts:
            # In order to support abort, need to be able to propagate an
            # external abort signal from self.abort() into an abort signal
            # for the particular model.  Can't see a way to do this which
            # doesn't involve setting a state variable.
            self._current_model = m
            if self._cancel: return numpy.inf
            if m.isfitted and m.weight != 0:
                m.residuals = m.fitness.residuals()
                N = len(m.residuals)
                m.degrees_of_freedom = N-k if N>k else 1
                m.chisq = numpy.sum(m.residuals**2)
                resid.append(m.weight*m.residuals)
        self.residuals = numpy.hstack(resid)
        N = len(self.residuals)
        self.degrees_of_freedom = N-k if N>k else 1
        self.chisq = numpy.sum(self.residuals**2)
        return self.chisq
    
class ParkFit(FitEngine):
    """ 
    ParkFit performs the Fit.This class can be used as follow:
    #Do the fit Park
    create an engine: engine = ParkFit()
    Use data must be of type plottable
    Use a sans model
    
    Add data with a dictionnary of FitArrangeList where Uid is a key and data
    is saved in FitArrange object.
    engine.set_data(data,Uid)
    
    Set model parameter "M1"= model.name add {model.parameter.name:value}.
    
    :note: Set_param() if used must always preceded set_model()
         for the fit to be performed.
    engine.set_param( model,"M1", {'A':2,'B':4})
    
    Add model with a dictionnary of FitArrangeList{} where Uid is a key
    and model
    is save in FitArrange object.
    engine.set_model(model,Uid)
    
    engine.fit return chisqr,[model.parameter 1,2,..],[[err1....][..err2...]]
    chisqr1, out1, cov1=engine.fit({model.parameter.name:value},qmin,qmax)
    
    :note: {model.parameter.name:value} is ignored in fit function since 
        the user should make sure to call set_param himself.
        
    """
    def __init__(self):
        """
        Creates a dictionary (self.fitArrangeList={})of FitArrange elements
        with Uid as keys
        """
        FitEngine.__init__(self)
        self.fit_arrange_dict = {}
        self.param_list = []
        
    def create_assembly(self, curr_thread):
        """
        Extract sansmodel and sansdata from 
        self.FitArrangelist ={Uid:FitArrange}
        Create parkmodel and park data ,form a list couple of parkmodel 
        and parkdata
        create an assembly self.problem=  park.Assembly([(parkmodel,parkdata)])
        """
        mylist = []
        #listmodel = []
        #i = 0
        fitproblems = []
        for fproblem in self.fit_arrange_dict.itervalues():
            if fproblem.get_to_fit() == 1:
                fitproblems.append(fproblem)
        if len(fitproblems) == 0: 
            raise RuntimeError, "No Assembly scheduled for Park fitting."
            return
        for item in fitproblems:
            parkmodel = item.get_model()
            for p in parkmodel.parameterset:
                ## does not allow status change for constraint parameters
                if p.status != 'computed':
                    if p.get_name()in item.pars:
                        ## make parameters selected for 
                        #fit will be between boundaries
                        p.set(p.range)         
                    else:
                        p.status = 'fixed'
            data_list = item.get_data()
            parkdata = data_list
            fitness = (parkmodel, parkdata)
            mylist.append(fitness)
        self.problem = MyAssembly(models=mylist, curr_thread=curr_thread)
        
  
    def fit(self, q=None, handler=None, curr_thread=None, ftol=None):
        """
        Performs fit with park.fit module.It can  perform fit with one model
        and a set of data, more than two fit of  one model and sets of data or 
        fit with more than two model associated with their set of data and 
        constraints
        
        :param pars: Dictionary of parameter names for the model and their 
            values.
        :param qmin: The minimum value of data's range to be fit
        :param qmax: The maximum value of data's range to be fit
        
        :note: all parameter are ignored most of the time.Are just there 
            to keep ScipyFit and ParkFit interface the same.
            
        :return: result.fitness Value of the goodness of fit metric
        :return: result.pvec list of parameter with the best value 
            found during fitting
        :return: result.cov Covariance matrix
        
        """
        self.create_assembly(curr_thread=curr_thread)
        localfit = FitSimplex()
        localfit.ftol = 1e-8
        
        # See `park.fitresult.FitHandler` for details.
        fitter = FitMC(localfit=localfit, start_points=1)
        if handler == None:
            handler = fitresult.ConsoleUpdate(improvement_delta=0.1)
        result = fit.fit(self.problem, fitter=fitter, handler=handler)
        self.problem.all_results(result)
        if result != None:
            if q != None:
                q.put(result)
                return q
            return result
        else:
            raise ValueError, "SVD did not converge"
            