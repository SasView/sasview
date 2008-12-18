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
        self.schedule=0
        self.list_param=[]
        self.name_per_page=None
    def save_model_name(self, name):  
        self.name_per_page= name
    def get_name(self):
        return self.name_per_page
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
        #print "fitproblem",self.model_list
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
        #print "fitproblem",name,value
        #self.model_list[0].setParam(name,value)
        self.list_param.append([name,value])
    def get_model_param(self):
        """ 
            set the value of a given parameter of this model
            @param name: name of the given parameter
            @param value: value of that parameter
        """
        #print self.param_name, self.param_value
        #self.model_list[0].setParam(name,value)
        return self.list_param
        
    def reset_model(self,model):
        """ 
            reset a model when parameter has changed
            @param value: new model
        """
        #print "fitproblem : reset model"
        self.model_list[0]=model
        
    def schedule_tofit(self, schedule=0):
        """
             set schedule to true to decide if this fit  must be performed
        """
        self.schedule=schedule
        
    def get_scheduled(self):
        """ return true or false if a problem as being schedule for fitting"""
        return self.schedule
    
    