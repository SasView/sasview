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
from sans.guitools.plottables import Data1D
from Loader import Load
from AbstractFitEngine import FitEngine,FitArrange,Model

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
    def __init__(self,data=[]):
        """
            Creates a dictionary (self.fitArrangeList={})of FitArrange elements
            with Uid as keys
        """
        self.fitArrangeList={}
        self.paramList=[]
        
    def createProblem(self):
        """
        Extract sansmodel and sansdata from self.FitArrangelist ={Uid:FitArrange}
        Create parkmodel and park data ,form a list couple of parkmodel and parkdata
        create an assembly self.problem=  park.Assembly([(parkmodel,parkdata)])
        """
        print "ParkFitting: In createproblem"
        mylist=[]
        listmodel=[]
        i=0
        for k,value in self.fitArrangeList.iteritems():
            #sansmodel=value.get_model()
            #wrap sans model
            #parkmodel = Model(sansmodel)
            parkmodel = value.get_model()
            #print "ParkFitting: createproblem: just create a model",parkmodel.parameterset
            for p in parkmodel.parameterset:
                #self.param_list.append(p._getname())
                #if p.isfixed():
                #print 'parameters',p.name
                print "parkfitting: self.paramList",self.paramList
                if p.isfixed() and p._getname()in self.paramList:
                    p.set([-numpy.inf,numpy.inf])
            i+=1    
            Ldata=value.get_data()
            parkdata=self._concatenateData(Ldata)
            
            couple=(parkmodel,parkdata)
            #print "Parkfitting: fitness",couple   
            mylist.append(couple)
        #print "mylist",mylist
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
        #from numpy.linalg.linalg.LinAlgError import LinAlgError
        #print "Parkfitting: fit method probably breaking just right before \
        #call fit"
        self.createProblem()
        pars=self.problem.fit_parameters()
        self.problem.eval()
        #print "M0.B",self.problem[1].parameterset['B'].value,self.problem[0].parameterset['B'].value

        localfit = FitSimplex()
        localfit.ftol = 1e-8
        fitter = FitMC(localfit=localfit)
        print "ParkFitting: result1"
        result = fit.fit(self.problem,
                     fitter=fitter,
                     handler= fitresult.ConsoleUpdate(improvement_delta=0.1))
        print "ParkFitting: result",result
        if result !=None:
            #for p in result.parameters:
            #    print "fit in park fitting", p.name, p.value,p.stderr
            #return result.fitness,result.pvec,result.cov,result
            return result
        else:
            raise ValueError, "SVD did not converge"
            
        
        
    
   