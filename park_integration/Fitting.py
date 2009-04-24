"""
    @organization: Class Fit contains ScipyFit and ParkFit methods declaration
    allows to create instance of type ScipyFit or ParkFit to perform either
    a park fit or a scipy fit.
"""
#from sans.guitools.plottables import Data1D
#from danse.common.plottools.plottables import Data1D
#from Loader import Load
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
    def __init__(self, engine='scipy'):
        """
            self._engine will contain an instance of ScipyFit or ParkFit
        """
        self._engine = None
        self.set_engine(engine)
          
          
    def set_engine(self,word):
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
        
   
    
    def fit(self,handler=None, curr_thread=None):
        """Perform the fit """
    
        return self._engine.fit(handler, curr_thread= curr_thread)
    
    
    def set_model(self,model,Uid,pars=[]):
        """
        store a model model to fit at the position Uid of the fit engine
        """
        self._engine.set_model(model,Uid,pars)
   
   
    def set_data(self,data,Uid,smearer=None,qmin=None, qmax=None):
        """
            Store data to fit at the psotion Uid of the fit engine
            @param data: data to fit
            @param smearer: smearerobject to smear data
            @param qmin: the minimum q range to fit 
            @param qmax: the minimum q range to fit
        """
        self._engine.set_data(data,Uid,smearer,qmin, qmax)
        
        
    def get_model(self,Uid):
        """ return list of data"""
        self._engine.get_model(Uid)


    def remove_Fit_Problem(self,Uid):
        """remove   fitarrange in Uid"""
        self._engine.remove_Fit_Problem(Uid)
        
        
    def select_problem_for_fit(self,Uid,value):
        """
            select a couple of model and data at the Uid position in dictionary
            and set in self.selected value to value
            @param value: the value to allow fitting. can only have the value one or zero
        """
        self._engine.select_problem_for_fit(Uid,value)
        
        
    def get_problem_to_fit(self,Uid):
        """
            return the self.selected value of the fit problem of Uid
           @param Uid: the Uid of the problem
        """
        return self._engine.get_problem_to_fit(Uid)
