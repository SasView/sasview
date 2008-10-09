"""
    @organization: ParkFitting module contains SansParameter,Model,Data
    FitArrange, ParkFit,Parameter classes.All listed classes work together to perform a 
    simple fit with park optimizer.
"""
import time
import numpy
import park
from park import fit,fitresult
from park import assembly
from park.fitmc import FitSimplex, FitMC

from Loader import Load
from AbstractFitEngine import FitEngine


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
        @note: Set_param() if used must always preceded set_model()
             for the fit to be performed.
        engine.set_param( model,"M1", {'A':2,'B':4})
        
        Add model with a dictionnary of FitArrangeList{} where Uid is a key and model
        is save in FitArrange object.
        engine.set_model(model,Uid)
        
        engine.fit return chisqr,[model.parameter 1,2,..],[[err1....][..err2...]]
        chisqr1, out1, cov1=engine.fit({model.parameter.name:value},qmin,qmax)
        @note: {model.parameter.name:value} is ignored in fit function since 
        the user should make sure to call set_param himself.
    """
    def __init__(self):
        """
            Creates a dictionary (self.fitArrangeList={})of FitArrange elements
            with Uid as keys
        """
        self.fitArrangeDict={}
        self.paramList=[]
        
    def createAssembly(self):
        """
        Extract sansmodel and sansdata from self.FitArrangelist ={Uid:FitArrange}
        Create parkmodel and park data ,form a list couple of parkmodel and parkdata
        create an assembly self.problem=  park.Assembly([(parkmodel,parkdata)])
        """
        mylist=[]
        listmodel=[]
        i=0
        fitproblems=[]
        for id ,fproblem in self.fitArrangeDict.iteritems():
            if fproblem.get_to_fit()==1:
                fitproblems.append(fproblem)
                
        if len(fitproblems)==0 : 
            raise RuntimeError, "No Assembly scheduled for Park fitting."
            return
        for item in fitproblems:
            parkmodel = item.get_model()
            for p in parkmodel.parameterset:
                if p._getname()in self.paramList and not p.iscomputed():
                    p.status = 'fitted' # make it a fitted parameter
                            #iscomputed  paramter with string inside
               
            i+=1
            Ldata=item.get_data()
            #parkdata=self._concatenateData(Ldata)
            parkdata=Ldata
            fitness=(parkmodel,parkdata)
            mylist.append(fitness)
    
        self.problem =  park.Assembly(mylist)
        
    
    def fit(self, qmin=None, qmax=None):
        """
            Performs fit with park.fit module.It can  perform fit with one model
            and a set of data, more than two fit of  one model and sets of data or 
            fit with more than two model associated with their set of data and constraints
            
            
            @param pars: Dictionary of parameter names for the model and their values.
            @param qmin: The minimum value of data's range to be fit
            @param qmax: The maximum value of data's range to be fit
            @note:all parameter are ignored most of the time.Are just there to keep ScipyFit
            and ParkFit interface the same.
            @return result.fitness: Value of the goodness of fit metric
            @return result.pvec: list of parameter with the best value found during fitting
            @return result.cov: Covariance matrix
        """
        self.createAssembly()
    
        localfit = FitSimplex()
        localfit.ftol = 1e-8
        # fitmc(fitness,localfit,n,handler):
        #Run a monte carlo fit.
        #This procedure maps a local optimizer across a set of n initial points.
        #The initial parameter value defined by the fitness parameters defines
        #one initial point.  The remainder are randomly generated within the
        #bounds of the problem.
        #localfit is the local optimizer to use.  It should be a bounded
        #optimizer following the `park.fitmc.LocalFit` interface.
        #handler accepts updates to the current best set of fit parameters.
        # See `park.fitresult.FitHandler` for details.
        fitter = FitMC(localfit=localfit)
        #result = fit.fit(self.problem,
        #             fitter=fitter,
        #            handler= GuiUpdate(window))
        result = fit.fit(self.problem,
                         fitter=fitter,
                         handler= fitresult.ConsoleUpdate(improvement_delta=0.1))
        #handler = fitresult.ConsoleUpdate(improvement_delta=0.1)
        #models=self.problem
        #service=None
        #if models is None: raise RuntimeError('fit expected a list of models')
        #from park.fit import LocalQueue,FitJob
        #if service is None: service = LocalQueue()
        #if fitter is None: fitter = fitmc.FitMC()
        #if handler is None: handler = fitresult.FitHandler()
    
        #objective = assembly.Assembly(models) if isinstance(models,list) else models
        #job = FitJob(self.problem,fitter,handler)
        #service.start(job)
        #import wx
        #while not self.job.handler.done:
        #    time.sleep(interval)
        #    wx.Yield()
        #result=service.job.handler.result
        
        if result !=None:
            return result
        else:
            raise ValueError, "SVD did not converge"
            
        
        
    
   