import copy 

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
        self.fit_data = None
        #list of data  in case of batch mode
        self.data_list = []
        #dictionary of data id and location to corresponding fitproblem
        self.fitproblem_pointers = {}
        self.theory_data = None
        ## the current model
        self.model = None
        self.model_index = None
        ## if 1 this fit problem will be selected to fit , if 0 
        ## it will not be selected for fit
        self.schedule = 0
        ##list containing parameter name and value
        self.list_param = []
        ## smear object to smear or not data1D
        self.smearer = None
        self.fit_tab_caption = ''
        ## fitting range
        self.qmin = None
        self.qmax = None
        self.result = []
        
        # 1D or 2D
        self.enable2D = False
        
    def clone(self):
        """
        copy fitproblem
        """
        
        obj          = FitProblem()
        model= None
        if self.model!=None:
            model = self.model.clone()
        obj.model = model
        obj.fit_data = copy.deepcopy(self.fit_data)
        obj.theory_data = copy.deepcopy(self.theory_data)
        obj.model = copy.deepcopy(self.model)
        obj.schedule = copy.deepcopy(self.schedule)
        obj.list_param = copy.deepcopy(self.list_param)
        obj.smearer = copy.deepcopy(self.smearer)
        obj.plotted_data = copy.deepcopy(self.plotted_data)
        obj.qmin = copy.deepcopy(self.qmin)
        obj.qmax = copy.deepcopy(self.qmax)
        obj.enable2D = copy.deepcopy(self.enable2D)
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
    
    def set_theory_data(self, data):
        """ 
        save a copy of the data select to fit
        
        :param data: data selected
        
        """
        self.theory_data = copy.deepcopy(data)
        
    def set_enable2D(self, enable2D):
        """
        """
        self.enable2D = enable2D
         
    def get_theory_data(self):
        """
        :return: list of data dList
        
        """
        return self.theory_data

    def set_fit_data(self,data):
        """ 
        save a copy of the data select to fit
        
        :param data: data selected
        
        """
        self.fit_data = data
            
    def get_fit_data(self):
        """
        """
        return self.fit_data
    
    def set_fit_data_list(self, data_list):
        """ 
        save a copy of a list of data
        
        :param data_list: list of data
        
        """
        self.data_list = data_list
            
    def get_fit_data_list(self):
        """
        """
        return self.data_list
    
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
        
    def set_fit_tab_caption(self, caption):
        """
        """
        self.fit_tab_caption = str(caption)
        
    def get_fit_tab_caption(self):
        """
        """
        return self.fit_tab_caption
    
    def get_enable2D(self):
        """
        """
        return self.enable2D
    
    def get_pointer_to_fitproblem(self):
        """
        return dictionary of id of fitproblem
        """
        return self.fitproblem_pointers
    
    def set_pointer_to_fitproblem(self, data_id, page_id):
        """
        """
        self.fitproblem_pointers[data_id] = page_id
        
    def set_result(self, result):
        """
        set a list of result
        """
        self.result = result
        
    def get_result(self):
        """
        get result 
        """
        return self.result
        
   