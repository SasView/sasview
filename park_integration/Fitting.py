"""
    @organization: Class Fit contains ScipyFit and ParkFit methods declaration
    allows to create instance of type ScipyFit or ParkFit to perform either
    a park fit or a scipy fit.
"""
from sans.guitools.plottables import Data1D
from Loader import Load
from scipy import optimize
from ScipyFitting import ScipyFit
from ParkFitting import ParkFit


class Fit:
    """ 
        Wrap class that allows to select the fitting type.this class 
        can be used as follow :
        
        from sans.fit.Fitting import Fit
        fitter= Fit()
        fitter.fit_engine('scipy') or fitter.fit_engine('park')
        engine = fitter.returnEngine()
        engine.set_data(data,Uid)
        engine.set_param( model,model.name, pars)
        engine.set_model(model,Uid)
        
        chisqr1, out1, cov1=engine.fit(pars,qmin,qmax)
    """  
    def __init__(self):
        """
            self._engine will contain an instance of ScipyFit or ParkFit
        """
        self._engine=None
          
    def fit_engine(self,word):
        """
            Select the type of Fit 
            @param word: the keyword to select the fit type 
            @raise: if the user does not enter 'scipy' or 'park',
             a valueError is rase
        """
        if word=="scipy":
            self._engine=ScipyFit()
        elif word=="park":
            self._engine=ParkFit()
        else:
            raise ValueError, "enter the keyword scipy or park"
    def returnEngine(self):
        """ @return self._engine""" 
        return self._engine
    
    def fit(self,pars, qmin=None, qmax=None):
        """Perform the fit """
      
    def set_model(self,model,Uid):
        """ Set model """
       
    def set_data(self,data,Uid):
        """ Receive plottable and create a list of data to fit"""
            
    def get_model(self,Uid):
        """ return list of data"""
    
    def set_param(self,model,name, pars):
        """ Recieve a dictionary of parameter and save it """
   
    def remove_data(self,Uid,data=None):
        """ remove one or all data"""
                 
    def remove_model(self,Uid):
        """ remove model """
        
        """
