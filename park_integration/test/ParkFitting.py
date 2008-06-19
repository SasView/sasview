#class Fitting
import time

import numpy
import park
from scipy import optimize
from park import fit,fitresult
from park import assembly

from sans.guitools.plottables import Data1D
#from sans.guitools import plottables
from Loader import Load

class SansParameter(park.Parameter):
    """
    SANS model parameters for use in the PARK fitting service.
    The parameter attribute value is redirected to the underlying
    parameter value in the SANS model.
    """
    def __init__(self, name, model):
         self._model, self._name = model,name
    def _getvalue(self): return self._model.getParam(self.name)
    def _setvalue(self,value): self._model.setParam(self.name, value)
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
    def __init__(self, sans_data):
        self.x= sans_data.x
        self.y= sans_data.y
        self.dx= sans_data.dx
        self.dy= sans_data.dy
        self.qmin=None
        self.qmax=None
       
    def setFitRange(self,mini=None,maxi=None):
        """ to set the fit range"""
        self.qmin=mini
        self.qmax=maxi
        
    def residuals(self, fn):
        
        x,y,dy = [numpy.asarray(v) for v in (self.x,self.y,self.dy)]
        if self.qmin==None and self.qmax==None: 
            return (y - fn(x))/dy
        
        else:
            idx = x>=self.qmin & x <= self.qmax
            return (y[idx] - fn(x[idx]))/dy[idx]
            
         
    def residuals_deriv(self, model, pars=[]):
        """ Return residual derivatives .in this case just return empty array"""
        return []
    
class FitArrange:
    def __init__(self):
        """
            Store a set of data for a given model to perform the Fit
            @param model: the model selected by the user
            @param Ldata: a list of data what the user want to fit
        """
        self.model = None
        self.dList =[]
        
    def set_model(self,model):
        """ set the model """
        self.model = model
        
    def add_data(self,data):
        """ 
            @param data: Data to add in the list
            fill a self.dataList with data to fit
        """
        if not data in self.dList:
            self.dList.append(data)
            
    def get_model(self):
        """ Return the model"""
        return self.model   
     
    def get_data(self):
        """ Return list of data"""
        return self.dList 
      
    def remove_data(self,data):
        """
            Remove one element from the list
            @param data: Data to remove from the the lsit of data
        """
        if data in self.dList:
            self.dList.remove(data)
            
class ParkFit:
    """ 
        Performs the Fit.he user determine what kind of data 
    """
    def __init__(self,data=[]):
        #this is a dictionary of FitArrange elements
        self.fitArrangeList={}
        #the constraint of the Fit
        self.constraint =None
        #Specify the use of scipy or park fit
        self.fitType =None
        
    def createProblem(self,pars={}):
        """
            Check the contraint value and specify what kind of fit to use
            return (M1,D1)
        """
        mylist=[]
        for k,value in self.fitArrangeList.iteritems():
            couple=()
            model=value.get_model()
            parameters= self.set_param(model, pars)
            model = Model(model)
            #print "model created",model.parameterset[0].value,model.parameterset[1].value
            # Make all parameters fitting parameters
            for p in model.parameterset:
                p.set([-numpy.inf,numpy.inf])
                #p.set([-10,10])
            Ldata=value.get_data()
            data=self._concatenateData(Ldata)
            #print "this data",data
            #print "data.residuals in createProblem",Ldata[0].residuals
            #print "data.residuals in createProblem",data.residuals
            #couple1=(model,Ldata[0])
            #mylist.append(couple1)
            couple=(model,data)
            mylist.append(couple)
        #print mylist
        return mylist
        #return model,data
    
    def fit(self,pars, qmin=None, qmax=None):
        """
             Do the fit 
        """
        
        modelList=self.createProblem(pars)
        #model,data=self.createProblem()
        #fitness=assembly.Fitness(model,data)
        
        problem =  park.Assembly(modelList)
        #print "problem :",problem[0].parameterset,problem[0].parameterset.fitted
        #problem[0].parameterset['A'].set([0,1000])
        #print "problem :",problem[0].parameterset,problem[0].parameterset.fitted
        fit.fit(problem, handler= fitresult.ConsoleUpdate(improvement_delta=0.1))
        #return fit.fit(problem)
        #fit.fit(problem, handler= fitresult.ConsoleUpdate(improvement_delta=0.1))
       
    
    def set_model(self,model,Uid):
        """ Set model """
        
        if self.fitArrangeList.has_key(Uid):
            self.fitArrangeList[Uid].set_model(model)
        else:
            fitproblem= FitArrange()
            fitproblem.set_model(model)
            self.fitArrangeList[Uid]=fitproblem
        
    def set_data(self,data,Uid):
        """ Receive plottable and create a list of data to fit"""
        data=Data(data)
        if self.fitArrangeList.has_key(Uid):
            self.fitArrangeList[Uid].add_data(data)
        else:
            fitproblem= FitArrange()
            fitproblem.add_data(data)
            self.fitArrangeList[Uid]=fitproblem
            
    def get_model(self,Uid):
        """ return list of data"""
        return self.fitArrangeList[Uid]
    
    def set_param(self,model, pars):
        """ Recieve a dictionary of parameter and save it """
        parameters=[]
        if model==None:
            raise ValueError, "Cannot set parameters for empty model"
        else:
            #for key ,value in pars:
            for key, value in pars.iteritems():
                param = Parameter(model, key, value)
                parameters.append(param)
        return parameters
    
    def add_constraint(self, constraint):
        """ User specify contraint to fit """
        self.constraint = str(constraint)
        
    def get_constraint(self):
        """ return the contraint value """
        return self.constraint
   
    def set_constraint(self,constraint):
        """ 
            receive a string as a constraint
            @param constraint: a string used to constraint some parameters to get a 
                specific value
        """
        self.constraint= constraint
    def _concatenateData(self, listdata=[]):
        """ concatenate each fields of all Data contains ins listdata
         return data
        """
        if listdata==[]:
            raise ValueError, " data list missing"
        else:
            xtemp=[]
            ytemp=[]
            dytemp=[]
            resid=[]
            resid_deriv=[]
            
            for data in listdata:
                for i in range(len(data.x)):
                    if not data.x[i] in xtemp:
                        xtemp.append(data.x[i])
                       
                    if not data.y[i] in ytemp:
                        ytemp.append(data.y[i])
                        
                    if not data.dy[i] in dytemp:
                        dytemp.append(data.dy[i])
                    
                   
            newplottable= Data1D(xtemp,ytemp,None,dytemp)
            newdata=Data(newplottable)
           
            #print "this is new data",newdata.dy
            return newdata
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
    

      
if __name__ == "__main__": 
    load= Load()
    
    # test fit one data set one model
    load.set_filename("testdata_line.txt")
    load.set_values()
    data1 = Data1D(x=[], y=[], dx=None,dy=None)
    data1.name = "data1"
    load.load_data(data1)
    fitter =ParkFit()
    
    from sans.guitools.LineModel import LineModel
    model  = LineModel()
    fitter.set_model(model,1)
    fitter.set_data(data1,1)
    
    print"PARK fit result \n",fitter.fit({'A':2,'B':1},None,None)
   
    
   
    