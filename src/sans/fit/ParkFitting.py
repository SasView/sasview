


"""
ParkFitting module contains SansParameter,Model,Data
FitArrange, ParkFit,Parameter classes.All listed classes work together
to perform a simple fit with park optimizer.
"""
#import time
import numpy
import math
from  numpy.linalg.linalg import LinAlgError
#import park
from park import fit
from park import fitresult
from  park.fitresult import FitParameter
import park.simplex
from park.assembly import Assembly
from park.assembly import Part
from park.fitmc import FitSimplex 
import park.fitmc
from park.fit import Fitter
from park.formatnum import format_uncertainty
from sans.fit.AbstractFitEngine import FitEngine
from sans.fit.AbstractFitEngine import FResult
  
class SansFitResult(fitresult.FitResult):
    def __init__(self, *args, **kwrds):
        fitresult.FitResult.__init__(self, *args, **kwrds)
        self.theory = None
        self.inputs = []
        
class SansFitSimplex(FitSimplex):
    """
    Local minimizer using Nelder-Mead simplex algorithm.

    Simplex is robust and derivative free, though not very efficient.

    This class wraps the bounds contrained Nelder-Mead simplex
    implementation for `park.simplex.simplex`.
    """
    radius = 0.05
    """Size of the initial simplex; this is a portion between 0 and 1"""
    xtol = 1
    #xtol = 1e-4
    """Stop when simplex vertices are within xtol of each other"""
    ftol = 5e-5
    """Stop when vertex values are within ftol of each other"""
    maxiter = None
    """Maximum number of iterations before fit terminates"""
    def __init__(self, ftol=5e-5):
        self.ftol = ftol
        
    def fit(self, fitness, x0):
        """Run the fit"""
        self.cancel = False
        pars = fitness.fit_parameters()
        bounds = numpy.array([p.range for p in pars]).T
        result = park.simplex.simplex(fitness, x0, bounds=bounds,
                                 radius=self.radius, xtol=self.xtol,
                                 ftol=self.ftol, maxiter=self.maxiter,
                                 abort_test=self._iscancelled)
        #print "calls:",result.calls
        #print "simplex returned",result.x,result.fx
        # Need to make our own copy of the fit results so that the
        # values don't get stomped on by the next fit iteration.
        fitpars = [SansFitParameter(pars[i].name,pars[i].range,v, pars[i].model, pars[i].data)
                   for i,v in enumerate(result.x)]
        res = SansFitResult(fitpars, result.calls, result.fx)
        res.inputs = [(pars[i].model, pars[i].data) for i,v in enumerate(result.x)]
        # Compute the parameter uncertainties from the jacobian
        res.calc_cov(fitness)
        return res
      
class SansFitter(Fitter):
    """
    """
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
        fitpars = [SansFitParameter(pars[i].name, pars[i].range, v,
                                     pars[i].model, pars[i].data)
                   for i,v in enumerate(x0)]
        handler.result = fitresult.FitResult(fitpars, 0, numpy.NaN)

        # Run the fit (fit should perform _progress and _improvement updates)
        # This function may return before the fit is complete.
        self._fit(fitness, x0, bounds)
        
class SansFitMC(SansFitter):
    """
    Monte Carlo optimizer.

    This implements `park.fit.Fitter`.
    """
    localfit = SansFitSimplex()
    start_points = 10
    def __init__(self, localfit, start_points=10):
        self.localfit = localfit
        self.start_points = start_points
        
    def _fit(self, objective, x0, bounds):
        """
        Run a monte carlo fit.

        This procedure maps a local optimizer across a set of initial points.
        """
        try:
            park.fitmc.fitmc(objective, x0, bounds, self.localfit,
                             self.start_points, self.handler)
        except:
            raise ValueError, "Fit did not converge.\n"
        
class SansPart(Part):
    """
    Part of a fitting assembly.  Part holds the model itself and
    associated data.  The part can be initialized with a fitness
    object or with a pair (model,data) for the default fitness function.

    fitness (Fitness)
        object implementing the `park.assembly.Fitness` interface.  In
        particular, fitness should provide a parameterset attribute
        containing a ParameterSet and a residuals method returning a vector
        of residuals.
    weight (dimensionless)
        weight for the model.  See comments in assembly.py for details.
    isfitted (boolean)
        True if the model residuals should be included in the fit.
        The model parameters may still be used in parameter
        expressions, but there will be no comparison to the data.
    residuals (vector)
        Residuals for the model if they have been calculated, or None
    degrees_of_freedom
        Number of residuals minus number of fitted parameters.
        Degrees of freedom for individual models does not make
        sense in the presence of expressions combining models,
        particularly in the case where a model has many parameters
        but no data or many computed parameters.  The degrees of
        freedom for the model is set to be at least one.
    chisq
        sum(residuals**2); use chisq/degrees_of_freedom to
        get the reduced chisq value.

        Get/set the weight on the given model.

        assembly.weight(3) returns the weight on model 3 (0-origin)
        assembly.weight(3,0.5) sets the weight on model 3 (0-origin)
    """

    def __init__(self, fitness, weight=1., isfitted=True):
        Part.__init__(self, fitness=fitness, weight=weight,
                       isfitted=isfitted)
       
        self.model, self.data = fitness[0], fitness[1]

class SansFitParameter(FitParameter):
    """
    Fit result for an individual parameter.
    """
    def __init__(self, name, range, value, model, data):
        FitParameter.__init__(self, name, range, value)
        self.model = model
        self.data = data
        
    def summarize(self):
        """
        Return parameter range string.

        E.g.,  "       Gold .....|.... 5.2043 in [2,7]"
        """
        bar = ['.']*10
        lo,hi = self.range
        if numpy.isfinite(lo)and numpy.isfinite(hi):
            portion = (self.value-lo)/(hi-lo)
            if portion < 0: portion = 0.
            elif portion >= 1: portion = 0.99999999
            barpos = int(math.floor(portion*len(bar)))
            bar[barpos] = '|'
        bar = "".join(bar)
        lostr = "[%g"%lo if numpy.isfinite(lo) else "(-inf"
        histr = "%g]"%hi if numpy.isfinite(hi) else "inf)"
        valstr = format_uncertainty(self.value, self.stderr)
        model_name = str(None)
        if self.model is not None:
            model_name = self.model.name
        data_name = str(None)
        if self.data is not None:
            data_name = self.data.name
            
        return "%25s %s %s in %s,%s, %s, %s"  % (self.name,bar,valstr,lostr,histr, 
                                                 model_name, data_name)
    def __repr__(self):
        #return "FitParameter('%s')"%self.name
        return str(self.__class__)
    
class MyAssembly(Assembly):
    def __init__(self, models, curr_thread=None):
        """Build an assembly from a list of models."""
        self.parts = []
        for m in models:
            self.parts.append(SansPart(m))
        self.curr_thread = curr_thread
        self.chisq = None
        self._cancel = False
        self.theory = None
        self._reset()
        
    def fit_parameters(self):
        """
        Return an alphabetical list of the fitting parameters.

        This function is called once at the beginning of a fit,
        and serves as a convenient place to precalculate what
        can be precalculated such as the set of fitting parameters
        and the parameter expressions evaluator.
        """
        self.parameterset.setprefix()
        self._fitparameters = self.parameterset.fitted
        self._restraints = self.parameterset.restrained
        pars = self.parameterset.flatten()
        context = self.parameterset.gather_context()
        self._fitexpression = park.expression.build_eval(pars,context)
        #print "constraints",self._fitexpression.__doc__

        self._fitparameters.sort(lambda a,b: cmp(a.path,b.path))
        # Convert to fitparameter a object
        
        fitpars = [SansFitParameter(p.path,p.range,p.value, p.model, p.data)
                   for p in self._fitparameters]
        #print "fitpars", fitpars
        return fitpars
    
    def all_results(self, result):
        """
        Extend result from the fit with the calculated parameters.
        """
        calcpars = [SansFitParameter(p.path,p.range,p.value, p.model, p.data)
                    for p in self.parameterset.computed]
        result.parameters += calcpars
        result.theory = self.theory

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
        try:
            self._fitexpression()
        except NameError:
            pass

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
                m.residuals, self.theory = m.fitness.residuals()
                N = len(m.residuals)
                m.degrees_of_freedom = N-k if N>k else 1
                # dividing residuals by N in order to be consistent with Scipy
                m.chisq = numpy.sum(m.residuals**2/N) 
                resid.append(m.weight*m.residuals/math.sqrt(N))
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
    
    ..note::
       Set_param() if used must always preceded set_model() for the fit to be performed.
      ``engine.set_param( model,"M1", {'A':2,'B':4})``
    
    Add model with a dictionnary of FitArrangeList{} where Uid is a key
    and model
    is save in FitArrange object.
    engine.set_model(model,Uid)
    
    engine.fit return chisqr,[model.parameter 1,2,..],[[err1....][..err2...]]
    chisqr1, out1, cov1=engine.fit({model.parameter.name:value},qmin,qmax)
    
    ..note::
        {model.parameter.name:value} is ignored in fit function since 
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
        
    def create_assembly(self, curr_thread, reset_flag=False):
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
            if reset_flag:
                # reset the initial value; useful for batch
                for name in item.pars:
                    ind = item.pars.index(name)
                    parkmodel.model.setParam(name, item.vals[ind])
            
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
        
  
    def fit(self, msg_q=None, 
            q=None, handler=None, curr_thread=None, 
                                        ftol=1.49012e-8, reset_flag=False):
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
        self.create_assembly(curr_thread=curr_thread, reset_flag=reset_flag)
        localfit = SansFitSimplex()
        localfit.ftol = ftol
        
        # See `park.fitresult.FitHandler` for details.
        fitter = SansFitMC(localfit=localfit, start_points=1)
        if handler == None:
            handler = fitresult.ConsoleUpdate(improvement_delta=0.1)
        
        result_list = []
        try:
            result = fit.fit(self.problem, fitter=fitter, handler=handler)
            self.problem.all_results(result)
            
        except LinAlgError:
            raise ValueError, "SVD did not converge"
    
        for m in self.problem.parts:
            residuals, theory = m.fitness.residuals()
            small_result = FResult(model=m.model, data=m.data.sans_data)
            small_result.fitter_id = self.fitter_id
            small_result.theory = theory
            small_result.residuals = residuals
            small_result.pvec = []
            small_result.cov = []
            small_result.stderr = []
            small_result.param_list = []
            small_result.residuals = m.residuals
            if result is not None:
                for p in result.parameters:
                    if p.data.name == small_result.data.name and \
                            p.model.name == small_result.model.name:
                        small_result.index = m.data.idx
                        small_result.fitness = result.fitness
                        small_result.pvec.append(p.value)
                        small_result.stderr.append(p.stderr)
                        name_split = p.name.split('.')
                        name = name_split[1].strip()
                        if len(name_split) > 2:
                            name += '.' + name_split[2].strip()
                        small_result.param_list.append(name)
            result_list.append(small_result)    
        if q != None:
            q.put(result_list)
            return q
        return result_list
       