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
        sansp = sans_model.getParamList()
        parkp = [SansParameter(p,sans_model) for p in sansp]
        self.parameterset = park.ParameterSet(sans_model.name,pars=parkp)
        
    def eval(self,x):
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
class FitArrange:
    def __init__(self):
        """
            Class FitArrange contains a set of data for a given model
            to perform the Fit.FitArrange must contain exactly one model
            and at least one data for the fit to be performed.
            model: the model selected by the user
            Ldata: a list of data what the user wants to fit
            
        """
        self.model = None
        self.dList =[]
        
    def set_model(self,model):
        """ 
            set_model save a copy of the model
            @param model: the model being set
        """
        self.model = model
    def remove_model(self):
        """ remove model """
        self.model=None
    def add_data(self,data):
        """ 
            add_data fill a self.dList with data to fit
            @param data: Data to add in the list  
        """
        if not data in self.dList:
            self.dList.append(data)
            
    def get_model(self):
        """ @return: saved model """
        return self.model   
     
    def get_data(self):
        """ @return:  list of data dList"""
        return self.dList 
      
    def remove_data(self,data):
        """
            Remove one element from the list
            @param data: Data to remove from dList
        """
        if data in self.dList:
            self.dList.remove(data)
    def remove_datalist(self):
        """ empty the complet list dLst"""
        self.dList=[]
            
            
class ParkFit:
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
       
    def createProblem(self,pars={}):
        """
        Extract sansmodel and sansdata from self.FitArrangelist ={Uid:FitArrange}
        Create parkmodel and park data ,form a list couple of parkmodel and parkdata
        create an assembly self.problem=  park.Assembly([(parkmodel,parkdata)])
        """
        mylist=[]
        listmodel=[]
        for k,value in self.fitArrangeList.iteritems():
            sansmodel=value.get_model()
            #wrap sans model
            parkmodel = Model(sansmodel)
            for p in parkmodel.parameterset:
                if p.isfixed():
                    p.set([-numpy.inf,numpy.inf])
                
            Ldata=value.get_data()
            x,y,dy,dx=self._concatenateData(Ldata)
            #wrap sansdata
            parkdata=Data(x,y,dy,dx)
            couple=(parkmodel,parkdata)
            mylist.append(couple)
        
        self.problem =  park.Assembly(mylist)
        
    
    def fit(self,pars=None, qmin=None, qmax=None):
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

       
        self.createProblem(pars)
        pars=self.problem.fit_parameters()
        self.problem.eval()
    
        localfit = FitSimplex()
        localfit.ftol = 1e-8
        fitter = FitMC(localfit=localfit)

        result = fit.fit(self.problem,
                         fitter=fitter,
                         handler= fitresult.ConsoleUpdate(improvement_delta=0.1))
        
        return result.fitness,result.pvec,result.cov
    
    def set_model(self,model,Uid):
        """ 
            Set model in a FitArrange object and add that object in a dictionary
            with key Uid.
            @param model: the model added
            @param Uid: unique key corresponding to a fitArrange object with model
        """
        #A fitArrange is already created but contains dList only at Uid
        if self.fitArrangeList.has_key(Uid):
            self.fitArrangeList[Uid].set_model(model)
        else:
        #no fitArrange object has been create with this Uid
            fitproblem= FitArrange()
            fitproblem.set_model(model)
            self.fitArrangeList[Uid]=fitproblem
        
    def set_data(self,data,Uid):
        """ Receives plottable, creates a list of data to fit,set data
            in a FitArrange object and adds that object in a dictionary 
            with key Uid.
            @param data: data added
            @param Uid: unique key corresponding to a fitArrange object with data
            """
        #A fitArrange is already created but contains model only at Uid
        if self.fitArrangeList.has_key(Uid):
            self.fitArrangeList[Uid].add_data(data)
        else:
        #no fitArrange object has been create with this Uid
            fitproblem= FitArrange()
            fitproblem.add_data(data)
            self.fitArrangeList[Uid]=fitproblem
            
    def get_model(self,Uid):
        """ 
            @param Uid: Uid is key in the dictionary containing the model to return
            @return  a model at this uid or None if no FitArrange element was created
            with this Uid
        """
        if self.fitArrangeList.has_key(Uid):
            return self.fitArrangeList[Uid].get_model()
        else:
            return None
    
    def set_param(self,model,name, pars):
        """ 
            Recieve a dictionary of parameter and save it 
            @param model: model on with parameter values are set
            @param name: model name
            @param pars: dictionary of paramaters name and value
            pars={parameter's name: parameter's value}
            @return list of Parameter instance
        """
        parameters=[]
        if model==None:
            raise ValueError, "Cannot set parameters for empty model"
        else:
            model.name=name
            for key, value in pars.iteritems():
                param = Parameter(model, key, value)
                parameters.append(param)
        return parameters
    
    def remove_data(self,Uid,data=None):
        """ remove one or all data.if data ==None will remove the whole
            list of data at Uid; else will remove only data in that list.
            @param Uid: unique id containing FitArrange object with data
            @param data:data to be removed
        """
        if data==None:
        # remove all element in data list
            if self.fitArrangeList.has_key(Uid):
                self.fitArrangeList[Uid].remove_datalist()
        else:
        #remove only data in dList
            if self.fitArrangeList.has_key(Uid):
                self.fitArrangeList[Uid].remove_data(data)
                
    def remove_model(self,Uid):
        """ 
            remove model in FitArrange object with Uid.
            @param Uid: Unique id corresponding to the FitArrange object 
            where model must be removed.
        """
        if self.fitArrangeList.has_key(Uid):
            self.fitArrangeList[Uid].remove_model()
    def remove_Fit_Problem(self,Uid):
        """remove   fitarrange in Uid"""
        if self.fitArrangeList.has_key(Uid):
            del self.fitArrangeList[Uid]
    def _concatenateData(self, listdata=[]):
        """  
            _concatenateData method concatenates each fields of all data contains ins listdata.
            @param listdata: list of data 
            
            @return xtemp, ytemp,dytemp:  x,y,dy respectively of data all combined
                if xi,yi,dyi of two or more data are the same the second appearance of xi,yi,
                dyi is ignored in the concatenation.
                
            @raise: if listdata is empty  will return None
            @raise: if data in listdata don't contain dy field ,will create an error
            during fitting
        """
        if listdata==[]:
            raise ValueError, " data list missing"
        else:
            xtemp=[]
            ytemp=[]
            dytemp=[]
            dx=None 
            for data in listdata:
                for i in range(len(data.x)):
                    if not data.x[i] in xtemp:
                        xtemp.append(data.x[i])
                       
                    if not data.y[i] in ytemp:
                        ytemp.append(data.y[i])
                    if data.dy and len(data.dy)>0:   
                        if not data.dy[i] in dytemp:
                            dytemp.append(data.dy[i])
                    else:
                        raise ValueError,"dy is missing will not be able to fit later on"
            return xtemp, ytemp,dytemp,dx
 
           
class Parameter:
    """
        Class to handle model parameters
    """
    def __init__(self, model, name, value=None):
            self.model = model
            self.name = name
            if not value==None:
                self.model.setParam(self.name, value)
           
    def set(self, value):
        """
            Set the value of the parameter
        """
        self.model.setParam(self.name, value)

    def __call__(self):
        """ 
            Return the current value of the parameter
        """
        return self.model.getParam(self.name)
    


    
   
    