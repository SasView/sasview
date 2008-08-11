"""
    @organization: ScipyFitting module contains FitArrange , ScipyFit,
    Parameter classes.All listed classes work together to perform a 
    simple fit with scipy optimizer.
"""
from sans.guitools.plottables import Data1D
from Loader import Load
from scipy import optimize
from AbstractFitEngine import FitEngine, Parameter
from AbstractFitEngine import FitArrange

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
        self.paramList=[]
        
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
        # Protect against simultanous fitting attempts
        if len(self.fitArrangeList)>1: 
            raise RuntimeError, "Scipy can't fit more than a single fit problem at a time."
        
        # fitproblem contains first fitArrange object(one model and a list of data)
        fitproblem=self.fitArrangeList.values()[0]
        listdata=[]
        model = fitproblem.get_model()
        listdata = fitproblem.get_data()
        # Concatenate dList set (contains one or more data)before fitting
        xtemp,ytemp,dytemp=self._concatenateData( listdata)
        #Assign a fit range is not boundaries were given
        if qmin==None:
            qmin= min(xtemp)
        if qmax==None:
            qmax= max(xtemp) 
        #perform the fit 
        chisqr, out, cov = fitHelper(model,self.parameters, xtemp,ytemp, dytemp ,qmin,qmax)
        return chisqr, out, cov
    

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
            if x[j] >= qmin and x[j] <= qmax:
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
    #print info, mesg, success
    # Calculate chi squared
    if len(pars)>1:
        chisqr = chi2(out)
    elif len(pars)==1:
        chisqr = chi2([out])
        
    return chisqr, out, cov_x    

