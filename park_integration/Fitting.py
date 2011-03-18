"""
Class Fit contains ScipyFit and ParkFit methods declaration
allows to create instance of type ScipyFit or ParkFit to perform either
a park fit or a scipy fit.
"""

#from scipy import optimize
from sans.fit.ScipyFitting import ScipyFit
from sans.fit.ParkFitting import ParkFit


class Fit:
    """ 
    Wrap class that allows to select the fitting type.this class 
    can be used as follow : ::
    
        from sans.fit.Fitting import Fit
        fitter= Fit()
        fitter.fit_engine('scipy') or fitter.fit_engine('park')
        engine = fitter.returnEngine()
        engine.set_data(data,id)
        engine.set_param( model,model.name, pars)
        engine.set_model(model,id)
        
        chisqr1, out1, cov1=engine.fit(pars,qmin,qmax)
        
    """  
    def __init__(self, engine='scipy'):
        """
        """
        #self._engine will contain an instance of ScipyFit or ParkFit
        self._engine = None
        self.set_engine(engine)
          
    def set_engine(self, word):
        """
        Select the type of Fit 
        
        :param word: the keyword to select the fit type 
        
        :raise: if the user does not enter 'scipy' or 'park',
             a valueError is raised 
             
        """
        if word == "scipy":
            self._engine = ScipyFit()
        elif word == "park":
            self._engine = ParkFit()
        else:
            raise ValueError, "enter the keyword scipy or park"

    def fit(self, q=None, handler=None, curr_thread=None):
        """Perform the fit """
        return self._engine.fit(q, handler, curr_thread=curr_thread)
     
    def set_model(self, model, id, pars=[], constraints=[]):
        """
        store a model model to fit at the position id of the fit engine
        """
        self._engine.set_model(model, id, pars, constraints)
   
    def set_data(self, data, id, smearer=None, qmin=None, qmax=None):
        """
        Store data to fit at the psotion id of the fit engine
        
        :param data: data to fit
        :param smearer: smearerobject to smear data
        :param qmin: the minimum q range to fit 
        :param qmax: the minimum q range to fit
        
        """
        self._engine.set_data(data, id, smearer, qmin, qmax)
        
    def get_model(self, id):
        """ return list of data"""
        self._engine.get_model(id)


    def remove_fit_problem(self, id):
        """remove fitarrange in id"""
        self._engine.remove_fit_problem(id)
        
    def select_problem_for_fit(self, id, value):
        """
        select a couple of model and data at the id position in dictionary
        and set in self.selected value to value
        
        :param value: the value to allow fitting.
             can only have the value one or zero
        """
        self._engine.select_problem_for_fit(id, value)
        
    def get_problem_to_fit(self, id):
        """
        return the self.selected value of the fit problem of id
           
        :param id: the id of the problem
        
        """
        return self._engine.get_problem_to_fit(id)
