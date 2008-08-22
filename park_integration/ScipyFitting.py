"""
    @organization: ScipyFitting module contains FitArrange , ScipyFit,
    Parameter classes.All listed classes work together to perform a 
    simple fit with scipy optimizer.
"""
#import scipy.linalg
import numpy 
from sans.guitools.plottables import Data1D
from Loader import Load
from scipy import optimize

from AbstractFitEngine import FitEngine, sansAssembly
from AbstractFitEngine import FitArrange,Data
class fitresult:
    """
        Storing fit result
    """
    calls     = None
    fitness   = None
    chisqr    = None
    pvec      = None
    cov       = None
    info      = None
    mesg      = None
    success   = None
    stderr    = None
    parameters= None
    
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
         # Protect against simultanous fitting attempts
        if len(self.fitArrangeList)>1: 
            raise RuntimeError, "Scipy can't fit more than a single fit problem at a time."
        
        # fitproblem contains first fitArrange object(one model and a list of data)
        fitproblem=self.fitArrangeList.values()[0]
        listdata=[]
        model = fitproblem.get_model()
        listdata = fitproblem.get_data()
        # Concatenate dList set (contains one or more data)before fitting
        data=self._concatenateData( listdata)
        #Assign a fit range is not boundaries were given
        if qmin==None:
            qmin= min(data.x)
        if qmax==None:
            qmax= max(data.x) 
        functor= sansAssembly(model,data)
        print "scipyfitting:param list",model.getParams(self.paramList)
        print "scipyfitting:functor",functor(model.getParams(self.paramList))
    
        out, cov_x, info, mesg, success = optimize.leastsq(functor,model.getParams(self.paramList), full_output=1, warning=True)
        chisqr = functor.chisq(out)
        
        print "scipyfitting: info",mesg
        print"scipyfitting : success",success
        print "scipyfitting: out", out
        print "scipyfitting: cov_x", cov_x
        print "scipyfitting: chisqr", chisqr
        
        if not (numpy.isnan(out).any()):
                result = fitresult()
                result.fitness = chisqr
                result.cov  = cov_x
                
                result.pvec = out
                result.success =success
               
                return result
        else:  
            raise ValueError, "SVD did not converge"
        
       
              
            
      