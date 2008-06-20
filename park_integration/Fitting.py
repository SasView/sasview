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
    
    def set_param(self,model, pars):
        """ Recieve a dictionary of parameter and save it """
   
    def add_constraint(self, constraint):
        """ User specify contraint to fit """
        
    def get_constraint(self):
        """ return the contraint value """
  
    def set_constraint(self,constraint):
        """ 
            receive a string as a constraint
            @param constraint: a string used to constraint some parameters to get a 
                specific value
        """
if __name__ == "__main__": 
    load= Load()
    # test scipy 
    """test fit one data set one model with scipy """
    #load data 
    load.set_filename("testdata_line.txt")
    load.set_values()
    data1 = Data1D(x=[], y=[], dx=None,dy=None)
    data1.name = "data1"
    load.load_data(data1)
    #choose a model
    from sans.guitools.LineModel import LineModel
    model  = LineModel()
    #Create a Fit engine
    fitter =Fit()
    fitter.fit_engine('scipy')
    engine = fitter.returnEngine()
    
    #set the model
    engine.set_model(model,1)
    engine.set_data(data1,1)
    
    print"fit only one data SCIPY:",engine.fit({'A':2,'B':1},None,None)
    
    
    """ test fit one data set one model with park """
    fitter.fit_engine('scipy')
    engine = fitter.returnEngine()
    #set the model
    engine.set_model(model,1)
    engine.set_data(data1,1)
    
    print"fit only one data PARK:",engine.fit({'A':2,'B':1},None,None)
    
    
    """test fit with 2 data and one model SCIPY:"""
    # reinitialize the fitter
    fitter =Fit()
    #create an engine
    fitter.fit_engine("scipy")
    engine=fitter.returnEngine()
    #set the model for fit
    engine.set_model(model,2 )
    #load 1 st data
    load.set_filename("testdata1.txt")
    load.set_values()
    data2 = Data1D(x=[], y=[], dx=None,dy=None)
    data2.name = "data2"
    load.load_data(data2)
    #load  2nd data
    load.set_filename("testdata2.txt")
    load.set_values()
    data3 = Data1D(x=[], y=[], dx=None,dy=None)
    data3.name = "data2"
    load.load_data(data3)
    
    #set data in the engine
    engine.set_data(data2,2)
    engine.set_data(data3,2)
    print"fit two data SCIPY:",engine.fit({'A':2,'B':1},None,None)
    
    """ test fit with 2 data and one model PARK:"""
    fitter.fit_engine("park")
    engine=fitter.returnEngine()
    #set the model for fit
    engine.set_model(model,2 )
    #load 1 st data
    load.set_filename("testdata1.txt")
    load.set_values()
    data2 = Data1D(x=[], y=[], dx=None,dy=None)
    data2.name = "data2"
    load.load_data(data2)
    #load  2nd data
    load.set_filename("testdata2.txt")
    load.set_values()
    data3 = Data1D(x=[], y=[], dx=None,dy=None)
    data3.name = "data2"
    load.load_data(data3)
    
    #set data in the engine
    engine.set_data(data2,2)
    engine.set_data(data3,2)
    print"fit two data PARK:",engine.fit({'A':2,'B':1},None,None)
    
  