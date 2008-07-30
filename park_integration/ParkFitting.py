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
from AbstractFitEngine import FitEngine, Parameter, FitArrange
class SansParameter(park.Parameter):
    """
        SANS model parameters for use in the PARK fitting service.
        The parameter attribute value is redirected to the underlying
        parameter value in the SANS model.
    """
    def __init__(self, name, model):
         self._model, self._name = model,name
         self.set(model.getParam(name))
         
    def _getvalue(self): return self._model.getParam(self.name)
    
    def _setvalue(self,value): 
        self._model.setParam(self.name, value)
        
    value = property(_getvalue,_setvalue)
    
    def _getrange(self):
        lo,hi = self._model.details[self.name][1:]
        if lo is None: lo = -numpy.inf
        if hi is None: hi = numpy.inf
        return lo,hi
    
    def _setrange(self,r):
        self._model.details[self.name][1:] = r
    range = property(_getrange,_setrange)


class Model(object):
    """
        PARK wrapper for SANS models.
    """
    def __init__(self, sans_model):
        self.model = sans_model
        print "ParkFitting:sans model",self.model
        sansp = sans_model.getParamList()
        print "ParkFitting: sans model parameter list",sansp
        parkp = [SansParameter(p,sans_model) for p in sansp]
        print "ParkFitting: park model parameter ",parkp
        self.parameterset = park.ParameterSet(sans_model.name,pars=parkp)
        
    def eval(self,x):
        print "eval",self.parameterset[0].value,self.parameterset[1].value
        print "model run ",self.model.run(x)
        return self.model.run(x)
    
class Data(object):
    """ Wrapper class  for SANS data """
    def __init__(self,x=None,y=None,dy=None,dx=None,sans_data=None):
        if not sans_data==None:
            self.x= sans_data.x
            self.y= sans_data.y
            self.dx= sans_data.dx
            self.dy= sans_data.dy
        else:
            if x!=None and y!=None and dy!=None:
                self.x=x
                self.y=y
                self.dx=dx
                self.dy=dy
            else:
                raise ValueError,\
                "Data is missing x, y or dy, impossible to compute residuals later on"
        self.qmin=None
        self.qmax=None
       
    def setFitRange(self,mini=None,maxi=None):
        """ to set the fit range"""
        self.qmin=mini
        self.qmax=maxi
        
    def residuals(self, fn):
        """ @param fn: function that return model value
            @return residuals
        """
        x,y,dy = [numpy.asarray(v) for v in (self.x,self.y,self.dy)]
        if self.qmin==None and self.qmax==None: 
            self.fx = fn(x)
            return (y - fn(x))/dy
        
        else:
            self.fx = fn(x[idx])
            idx = x>=self.qmin & x <= self.qmax
            return (y[idx] - fn(x[idx]))/dy[idx]
            
         
    def residuals_deriv(self, model, pars=[]):
        """ 
            @return residuals derivatives .
            @note: in this case just return empty array
        """
        return []

            
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
        
    def createProblem(self):
        """
        Extract sansmodel and sansdata from self.FitArrangelist ={Uid:FitArrange}
        Create parkmodel and park data ,form a list couple of parkmodel and parkdata
        create an assembly self.problem=  park.Assembly([(parkmodel,parkdata)])
        """
        print "ParkFitting: In createproblem"
        mylist=[]
        listmodel=[]
        
        for k,value in self.fitArrangeList.iteritems():
            sansmodel=value.get_model()
            #wrap sans model
            parkmodel = Model(sansmodel)
            print "ParkFitting: createproblem: just create a model",parkmodel.parameterset
            for p in parkmodel.parameterset:
                #self.param_list.append(p._getname())
                if p.isfixed() and p._getname()in self.paramList:
                    p.set([-numpy.inf,numpy.inf])
            
            Ldata=value.get_data()
            x,y,dy=self._concatenateData(Ldata)
            #wrap sansdata
            parkdata=Data(x,y,dy,None)
            couple=(parkmodel,parkdata)
            print "Parkfitting: fitness",couple   
            mylist.append(couple)
        print "mylist",mylist
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
        print "Parkfitting: fit method probably breaking just right before \
        call fit"
        self.createProblem()
        pars=self.problem.fit_parameters()
        self.problem.eval()
        #print "M0.B",self.problem[1].parameterset['B'].value,self.problem[0].parameterset['B'].value

        localfit = FitSimplex()
        localfit.ftol = 1e-8
        fitter = FitMC(localfit=localfit)
        try:
            
            result = fit.fit(self.problem,
                         fitter=fitter,
                         handler= fitresult.ConsoleUpdate(improvement_delta=0.1))
          
            for p in result.parameters:
                print "fit in park fitting", p.name, p.value
            return result.fitness,result.pvec,result.cov
           
        except :
            raise
            return
        
    
   