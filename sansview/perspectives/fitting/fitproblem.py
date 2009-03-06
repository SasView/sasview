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
        ## data used for fitting
        self.fit_data=None
        ## list containing couple of model and its name
        self.model_list=[]
        ## if 1 this fit problem will be selected to fit , if 0 
        ## it will not be selected for fit
        self.schedule=0
        ##list containing parameter name and value
        self.list_param=[]
        ## smear object to smear or not data1D
        self.smearer= None
        ## same as fit_data but with more info for plotting
        ## axis unit info and so on see plottables definition
        self.plotted_data=None
        
        
    def set_smearer(self, smearer):
        """
          save reference of  smear object on fitdata
          @param smear : smear object from DataLoader
        """
        self.smearer= smearer
       
    def get_smearer(self):
        """
            return smear object
        """
        return self.smearer
    
    
    def set_model(self,model,name):
        """ 
             associates each model with its new created name
             @param model: model selected
             @param name: name created for model
        """
        self.model_list=[model,name]

  
    def add_plotted_data(self,data):
        """ 
            save a copy of the data select to fit
            @param data: data selected
        """
        self.plotted_data = data
        
        
    def add_fit_data(self,data):
        """ 
            save a copy of the data select to fit
            @param data: data selected
        """
        self.fit_data = data
            
    def get_model(self):
        """ @return: saved model """
        return self.model_list
     
    def get_plotted_data(self):
        """ @return:  list of data dList"""
        return self.plotted_data
    
    
    def get_fit_data(self):
        return self.fit_data
    
    
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
            Store the name and value of a parameter of this fitproblem's model
            @param name: name of the given parameter
            @param value: value of that parameter
        """
        self.list_param.append([name,value])
        
        
    def get_model_param(self):
        """ 
            @return list of couple of parameter name and value
        """
        return self.list_param
        
        
    def reset_model(self,model):
        """ 
            reset a model when parameter has changed
            @param value: new model
        """
        self.model_list[0]=model
        
        
    def schedule_tofit(self, schedule=0):
        """
             set schedule to true to decide if this fit  must be performed
        """
        self.schedule=schedule
        
    def get_scheduled(self):
        """ return true or false if a problem as being schedule for fitting"""
        return self.schedule
    
    
    def clear_model_param(self):
        """
        clear constraint info
        """
        self.list_param=[]
        
        