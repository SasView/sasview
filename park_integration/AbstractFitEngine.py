
class FitEngine:
    
    def _concatenateData(self, listdata=[]):
        """  
            _concatenateData method concatenates each fields of all data contains ins listdata.
            @param listdata: list of data 
            
            @return xtemp, ytemp,dytemp:  x,y,dy respectively of data all combined
                if xi,yi,dyi of two or more data are the same the second appearance of xi,yi,
                dyi is ignored in the concatenation.
                
            @raise: if listdata is empty  will return None
            @raise: if data in listdata don't contain dy field ,will create an error
            during fitting
        """
        if listdata==[]:
            raise ValueError, " data list missing"
        else:
            xtemp=[]
            ytemp=[]
            dytemp=[]
               
            for data in listdata:
                for i in range(len(data.x)):
                    xtemp.append(data.x[i])
                    ytemp.append(data.y[i])
                    if data.dy is not None and len(data.dy)==len(data.y):   
                        dytemp.append(data.dy[i])
                    else:
                        raise RuntimeError, "Fit._concatenateData: y-errors missinge"
            return xtemp, ytemp,dytemp
    
    def set_model(self,model,name,Uid,pars={}):
        """ 
      
            Receive a dictionary of parameter and save it Parameter list
            For scipy.fit use.
            Set model in a FitArrange object and add that object in a dictionary
            with key Uid.
            @param model: model on with parameter values are set
            @param name: model name
            @param Uid: unique key corresponding to a fitArrange object with model
            @param pars: dictionary of paramaters name and value
            pars={parameter's name: parameter's value}
            
        """
        print "AbstractFitEngine:  fitting parmater",pars
        temp=[]
        if pars !={}:
            self.parameters=[]
            self.paramList=[]
            if model==None:
                raise ValueError, "Cannot set parameters for empty model"
            else:
                model.name=name
                for key, value in pars.iteritems():
                    param = Parameter(model, key, value)
                    self.parameters.append(param)
                    temp.append(key)
            self.paramList.append(temp)
            print "AbstractFitEngine: self.paramList2", self.paramList
            #A fitArrange is already created but contains dList only at Uid
            if self.fitArrangeList.has_key(Uid):
                self.fitArrangeList[Uid].set_model(model)
            else:
            #no fitArrange object has been create with this Uid
                fitproblem= FitArrange()
                fitproblem.set_model(model)
                self.fitArrangeList[Uid]=fitproblem
        else:
            raise ValueError, "park_integration:missing parameters"
        
        
    def set_data(self,data,Uid):
        """ Receives plottable, creates a list of data to fit,set data
            in a FitArrange object and adds that object in a dictionary 
            with key Uid.
            @param data: data added
            @param Uid: unique key corresponding to a fitArrange object with data
            """
        #A fitArrange is already created but contains model only at Uid
        if self.fitArrangeList.has_key(Uid):
            self.fitArrangeList[Uid].add_data(data)
        else:
        #no fitArrange object has been create with this Uid
            fitproblem= FitArrange()
            fitproblem.add_data(data)
            self.fitArrangeList[Uid]=fitproblem
            
    def get_model(self,Uid):
        """ 
            @param Uid: Uid is key in the dictionary containing the model to return
            @return  a model at this uid or None if no FitArrange element was created
            with this Uid
        """
        if self.fitArrangeList.has_key(Uid):
            return self.fitArrangeList[Uid].get_model()
        else:
            return None
    
    def remove_Fit_Problem(self,Uid):
        """remove   fitarrange in Uid"""
        if self.fitArrangeList.has_key(Uid):
            del self.fitArrangeList[Uid]
            
      
   
   
class Parameter:
    """
        Class to handle model parameters
    """
    def __init__(self, model, name, value=None):
            self.model = model
            self.name = name
            if not value==None:
                self.model.setParam(self.name, value)
           
    def set(self, value):
        """
            Set the value of the parameter
        """
        self.model.setParam(self.name, value)

    def __call__(self):
        """ 
            Return the current value of the parameter
        """
        return self.model.getParam(self.name)
    
class FitArrange:
    def __init__(self):
        """
            Class FitArrange contains a set of data for a given model
            to perform the Fit.FitArrange must contain exactly one model
            and at least one data for the fit to be performed.
            model: the model selected by the user
            Ldata: a list of data what the user wants to fit
            
        """
        self.model = None
        self.dList =[]
        
    def set_model(self,model):
        """ 
            set_model save a copy of the model
            @param model: the model being set
        """
        self.model = model
        
    def add_data(self,data):
        """ 
            add_data fill a self.dList with data to fit
            @param data: Data to add in the list  
        """
        if not data in self.dList:
            self.dList.append(data)
            
    def get_model(self):
        """ @return: saved model """
        return self.model   
     
    def get_data(self):
        """ @return:  list of data dList"""
        return self.dList 
      
    def remove_data(self,data):
        """
            Remove one element from the list
            @param data: Data to remove from dList
        """
        if data in self.dList:
            self.dList.remove(data)
    


    