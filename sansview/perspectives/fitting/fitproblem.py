
class FitProblem:
    """  
    FitProblem class allows to link a model with the new name created in _on_model,
    a name theory created with that model  and the data fitted with the model.
    FitProblem is mostly used  as value of the dictionary by fitting module.
    """
    def __init__(self):
        """
        contains information about data and model to fit
        """
        ## data used for fitting
        self.fit_data=None
        ## the current model
        self.model = None
        self.model_index = None
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
        ## fitting range
        self.qmin = None
        self.qmax = None
        
    def clone(self):
        """
        copy fitproblem
        """
        import copy 
        obj          = FitProblem()
        model= None
        if self.model!=None:
            model = self.model.clone()
        obj.model = model
        obj.fit_data = copy.deepcopy(self.fit_data)
        obj.model = copy.deepcopy(self.model)
        obj.schedule = copy.deepcopy(self.schedule)
        obj.list_param = copy.deepcopy(self.list_param)
        obj.smearer = copy.deepcopy(self.smearer)
        obj.plotted_data = copy.deepcopy(self.plotted_data)
        obj.qmin = copy.deepcopy(self.qmin)
        obj.qmax = copy.deepcopy(self.qmax)
        return obj
        
    def set_smearer(self, smearer):
        """
        save reference of  smear object on fitdata
        
        :param smear: smear object from DataLoader
        
        """
        self.smearer= smearer
       
    def get_smearer(self):
        """
        return smear object
        """
        return self.smearer
    
    def save_model_name(self, name):
        """
        """  
        self.name_per_page= name
        
    def get_name(self):
        """
        """
        return self.name_per_page
    
    def set_model(self,model):
        """ 
        associates each model with its new created name
        
        :param model: model selected
        :param name: name created for model
        
        """
        self.model= model
        
    def get_model(self):
        """
        :return: saved model
        
        """
        return self.model
  
    def set_index(self, index):
        """
        set index of the model name
        """
        self.model_index = index
        
    def get_index(self):
        """
        get index of the model name
        """
        return self.model_index
    
    def add_plotted_data(self,data):
        """ 
        save a copy of the data select to fit
        
        :param data: data selected
        
        """
        self.plotted_data = data
        

    def get_plotted_data(self):
        """
        :return: list of data dList
        
        """
        return self.plotted_data

    def add_fit_data(self,data):
        """ 
        save a copy of the data select to fit
        
        :param data: data selected
        
        """
        self.fit_data = data
            
    def get_fit_data(self):
        """
        """
        return self.fit_data
    
    def set_model_param(self,name,value=None):
        """ 
        Store the name and value of a parameter of this fitproblem's model
        
        :param name: name of the given parameter
        :param value: value of that parameter
        
        """
        self.list_param.append([name,value])
        
    def get_model_param(self):
        """ 
        return list of couple of parameter name and value
        """
        return self.list_param
        
    def schedule_tofit(self, schedule=0):
        """
        set schedule to true to decide if this fit  must be performed
        """
        self.schedule=schedule
        
    def get_scheduled(self):
        """
        return true or false if a problem as being schedule for fitting
        """
        return self.schedule
    
    def set_range(self, qmin=None, qmax=None):
        """
        set fitting range 
        """
        self.qmin = qmin
        self.qmax = qmax
        
    def get_range(self):
        """
        :return: fitting range
        
        """
        return self.qmin, self.qmax
    
    def clear_model_param(self):
        """
        clear constraint info
        """
        self.list_param=[]
   