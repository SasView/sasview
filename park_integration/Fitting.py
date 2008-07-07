#class Fitting
from sans.guitools.plottables import Data1D
from Loader import Load
from scipy import optimize
from ScipyFitting import ScipyFit
from ParkFitting import ParkFit


class Fit:
    """ 
        Wrap class that allows to select the fitting type 
    """  
    def __init__(self):
        
        # To initialize a type of Fit
        self._engine=None
          
    def fit_engine(self,word):
        """
            Select the type of Fit 
            @param word: the keyword to select the fit type 
        """
        if word=="scipy":
            self._engine=ScipyFit()
        elif word=="park":
            self._engine=ParkFit()
        else:
            raise ValueError, "enter the keyword scipy or park"
    def returnEngine(self):
        return self._engine
    
    def fit(self,pars, qmin=None, qmax=None):
        """ Do the fit """
      
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
