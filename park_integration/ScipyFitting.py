"""
    @organization: ScipyFitting module contains FitArrange , ScipyFit,
    Parameter classes.All listed classes work together to perform a 
    simple fit with scipy optimizer.
"""
from sans.guitools.plottables import Data1D
from Loader import Load
from scipy import optimize
from AbstractFitEngine import FitEngine, Parameter

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
            
class ScipyFit(FitEngine):
    """ 
        ScipyFit performs the Fit.This class can be used as follow:
        #Do the fit SCIPY
        create an engine: engine = ScipyFit()
        Use data must be of type plottable
        Use a sans model
        
        Add data with a dictionnary of FitArrangeList where Uid is a key and data
        is saved in FitArrange object.
        engine.set_data(data,Uid)
        
        Set model parameter "M1"= model.name add {model.parameter.name:value}.
        @note: Set_param() if used must always preceded set_model()
             for the fit to be performed.In case of Scipyfit set_param is called in
             fit () automatically.
        engine.set_param( model,"M1", {'A':2,'B':4})
        
        Add model with a dictionnary of FitArrangeList{} where Uid is a key and model
        is save in FitArrange object.
        engine.set_model(model,Uid)
        
        engine.fit return chisqr,[model.parameter 1,2,..],[[err1....][..err2...]]
        chisqr1, out1, cov1=engine.fit({model.parameter.name:value},qmin,qmax)
    """
    def __init__(self):
        """
            Creates a dictionary (self.fitArrangeList={})of FitArrange elements
            with Uid as keys
        """
        self.fitArrangeList={}
        
    def fit(self,qmin=None, qmax=None):
        """
            Performs fit with scipy optimizer.It can only perform fit with one model
            and a set of data.
            @note: Cannot perform more than one fit at the time.
            
            @param pars: Dictionary of parameter names for the model and their values
            @param qmin: The minimum value of data's range to be fit
            @param qmax: The maximum value of data's range to be fit
            @return chisqr: Value of the goodness of fit metric
            @return out: list of parameter with the best value found during fitting
            @return cov: Covariance matrix
        """
        # fitproblem contains first fitArrange object(one model and a list of data)
        fitproblem=self.fitArrangeList.values()[0]
        listdata=[]
        model = fitproblem.get_model()
        listdata = fitproblem.get_data()
        
       
        # Concatenate dList set (contains one or more data)before fitting
        xtemp,ytemp,dytemp=self._concatenateData( listdata)
        
        #print "dytemp",dytemp
        #Assign a fit range is not boundaries were given
        if qmin==None:
            qmin= min(xtemp)
        if qmax==None:
            qmax= max(xtemp) 
        
        #perform the fit 
        chisqr, out, cov = fitHelper(model,self.parameters, xtemp,ytemp, dytemp ,qmin,qmax)
        
        return chisqr, out, cov
    
    def set_model(self,model,name,Uid,pars={}):
        """ 
      
            Receive a dictionary of parameter and save it Parameter list
            For scipy.fit use.
            Set model in a FitArrange object and add that object in a dictionary
            with key Uid.
            @param model: model on with parameter values are set
            @param name: model name
            @param Uid: unique key corresponding to a fitArrange object with model
            @param pars: dictionary of paramaters name and value
            pars={parameter's name: parameter's value}
            
        """
        self.parameters=[]
        if model==None:
            raise ValueError, "Cannot set parameters for empty model"
        else:
            model.name=name
            for key, value in pars.iteritems():
                param = Parameter(model, key, value)
                self.parameters.append(param)
        
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
    
    
    
    def remove_Fit_Problem(self,Uid):
        """remove   fitarrange in Uid"""
        if self.fitArrangeList.has_key(Uid):
            del self.fitArrangeList[Uid]
      
def fitHelper(model, pars, x, y, err_y ,qmin=None, qmax=None):
    """
        Fit function
        @param model: sans model object
        @param pars: list of parameters
        @param x: vector of x data
        @param y: vector of y data
        @param err_y: vector of y errors 
        @return chisqr: Value of the goodness of fit metric
        @return out: list of parameter with the best value found during fitting
        @return cov: Covariance matrix
    """
    def f(params):
        """
            Calculates the vector of residuals for each point 
            in y for a given set of input parameters.
            @param params: list of parameter values
            @return: vector of residuals
        """
        i = 0
        for p in pars:
            p.set(params[i])
            i += 1
        
        residuals = []
        for j in range(len(x)):
            if x[j]>qmin and x[j]<qmax:
                residuals.append( ( y[j] - model.runXY(x[j]) ) / err_y[j] )
            
        return residuals
        
    def chi2(params):
        """
            Calculates chi^2
            @param params: list of parameter values
            @return: chi^2
        """
        sum = 0
        res = f(params)
        for item in res:
            sum += item*item
        return sum
        
    p = [param() for param in pars]
    out, cov_x, info, mesg, success = optimize.leastsq(f, p, full_output=1, warning=True)
    print info, mesg, success
    # Calculate chi squared
    if len(pars)>1:
        chisqr = chi2(out)
    elif len(pars)==1:
        chisqr = chi2([out])
        
    return chisqr, out, cov_x    

