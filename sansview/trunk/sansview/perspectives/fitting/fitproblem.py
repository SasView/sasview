from sans.fit.AbstractFitEngine import Model

class FitProblem:
    """  
        FitProblem class allows to link a model with the new name created in _on_model,
        a name theory created with that model  and the data fitted with the model.
        FitProblem is mostly used  as value of the dictionary by fitting module.
    """
    
    def __init__(self):
        
        """
            @ self.data :is the data selected to perform the fit
            @ self.theory_name: the name of the theory created with self.model
            @ self.model_list:  is a list containing a model as first element 
            and its name assign example [lineModel, M0]
        """
        self.data=None
        self.theory_name=None
        self.model_list=[]
        
    def set_model(self,model,name):
        """ 
             associates each model with its new created name
             @param model: model selected
             @param name: name created for model
        """
        self.model_list=[model,name]

  
    def add_data(self,data):
        """ 
            save a copy of the data select to fit
            @param data: data selected
        """
        self.data = data
            
    def get_model(self):
        """ @return: saved model """
        return self.model_list
     
    def get_data(self):
        """ @return:  list of data dList"""
        return self.data
      
      
    def get_theory(self):
        """ @return the name of theory for plotting purpose"""
        return self.theory_name
    
    
    def set_theory(self,name):
        """
            Set theory name
            @param name: name of the theory
        """
        self.theory_name = name

        
    def set_model_param(self,name,value):
        """ 
            set the value of a given parameter of this model
            @param name: name of the given parameter
            @param value: value of that parameter
        """
        
        self.model_list[0].setParam(name,value)
       
        
    def reset_model(self,model):
        """ 
            reset a model when parameter has changed
            @param value: new model
        """
        print "fitproblem : reset model"
        self.model_list[0]=model
        
        