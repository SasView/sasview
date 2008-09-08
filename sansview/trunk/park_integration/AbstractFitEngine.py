
import park,numpy

class SansParameter(park.Parameter):
    """
        SANS model parameters for use in the PARK fitting service.
        The parameter attribute value is redirected to the underlying
        parameter value in the SANS model.
    """
    def __init__(self, name, model):
         self._model, self._name = model,name
         self.set(model.getParam(name))
         
    def _getvalue(self): return self._model.getParam(self.name)
    
    def _setvalue(self,value): 
        self._model.setParam(self.name, value)
        
    value = property(_getvalue,_setvalue)
    
    def _getrange(self):
        lo,hi = self._model.details[self.name][1:]
        if lo is None: lo = -numpy.inf
        if hi is None: hi = numpy.inf
        return lo,hi
    
    def _setrange(self,r):
        self._model.details[self.name][1:] = r
    range = property(_getrange,_setrange)


class Model(object):
    """
        PARK wrapper for SANS models.
    """
    def __init__(self, sans_model):
        self.model = sans_model
        self.name=sans_model.name
        #print "ParkFitting:sans model",self.model
        self.sansp = sans_model.getParamList()
        #print "ParkFitting: sans model parameter list",sansp
        self.parkp = [SansParameter(p,sans_model) for p in self.sansp]
        #print "ParkFitting: park model parameter ",self.parkp
        self.parameterset = park.ParameterSet(sans_model.name,pars=self.parkp)
        self.pars=[]
        
    def getParams(self,fitparams):
        list=[]
        self.pars=[]
        self.pars=fitparams
        for item in fitparams:
            for element in self.parkp:
                 if element.name ==str(item):
                     list.append(element.value)
        #print "abstractfitengine: getparams",list
        return list
    
    def setParams(self, params):
        list=[]
        for item in self.parkp:
            list.append(item.name)
        list.sort()
        for i in range(len(params)):
            #self.parkp[i].value = params[i]
            #print "abstractfitengine: set-params",list[i],params[i]
            
            self.model.setParam(list[i],params[i])
  
    def eval(self,x):
       
        return self.model.runXY(x)
       

class Data(object):
    """ Wrapper class  for SANS data """
    def __init__(self,x=None,y=None,dy=None,dx=None,sans_data=None):
        
        if  sans_data !=None:
            self.x= sans_data.x
            self.y= sans_data.y
            self.dx= sans_data.dx
            self.dy= sans_data.dy
           
        elif (x!=None and y!=None and dy!=None):
                self.x=x
                self.y=y
                self.dx=dx
                self.dy=dy
        else:
            raise ValueError,\
            "Data is missing x, y or dy, impossible to compute residuals later on"
        self.qmin=None
        self.qmax=None
       
    def setFitRange(self,mini=None,maxi=None):
        """ to set the fit range"""
        self.qmin=mini
        self.qmax=maxi
    def getFitRange(self):
         return self.qmin, self.qmax
    def residuals(self, fn):
        """ @param fn: function that return model value
            @return residuals
        """
        x,y,dy = [numpy.asarray(v) for v in (self.x,self.y,self.dy)]
        if self.qmin==None and self.qmax==None: 
            fx =[fn(v) for v in x]
            return (y - fx)/dy
        else:
            idx = (x>=self.qmin) & (x <= self.qmax)
            fx = [fn(item)for item in x[idx ]]
            return (y[idx] - fx)/dy[idx]
          
            
         
    def residuals_deriv(self, model, pars=[]):
        """ 
            @return residuals derivatives .
            @note: in this case just return empty array
        """
        return []
    
class sansAssembly:
    def __init__(self,Model=None , Data=None):
       self.model = Model
       self.data  = Data
       self.res=[]
    def chisq(self, params):
        """
            Calculates chi^2
            @param params: list of parameter values
            @return: chi^2
        """
        sum = 0
        for item in self.res:
            sum += item*item
        return sum
    def __call__(self,params):
        self.model.setParams(params)
        self.res= self.data.residuals(self.model.eval)
        return self.res
    
class FitEngine:
    def __init__(self):
        self.paramList=[]
    def _concatenateData(self, listdata=[]):
        """  
            _concatenateData method concatenates each fields of all data contains ins listdata.
            @param listdata: list of data 
            
            @return Data:
                
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
            self.mini=None
            self.maxi=None
               
            for data in listdata:
                mini,maxi=data.getFitRange()
                if self.mini==None and self.maxi==None:
                    self.mini=mini
                    self.maxi=maxi
                else:
                    if mini < self.mini:
                        self.mini=mini
                    if self.maxi < maxi:
                        self.maxi=maxi
                        
                    
                for i in range(len(data.x)):
                    xtemp.append(data.x[i])
                    ytemp.append(data.y[i])
                    if data.dy is not None and len(data.dy)==len(data.y):   
                        dytemp.append(data.dy[i])
                    else:
                        raise RuntimeError, "Fit._concatenateData: y-errors missing"
            #return xtemp, ytemp,dytemp
            data= Data(x=xtemp,y=ytemp,dy=dytemp)
            data.setFitRange(self.mini, self.maxi)
            return data
    def set_model(self,model,name,Uid,pars=[]):
        if len(pars) >0:
            self.paramList = []
            if model==None:
                raise ValueError, "AbstractFitEngine: Specify parameters to fit"
            else:
                model.model.name = name
                model.name = name
                self.paramList=pars
            #A fitArrange is already created but contains dList only at Uid
            if self.fitArrangeList.has_key(Uid):
                self.fitArrangeList[Uid].set_model(model)
            else:
            #no fitArrange object has been create with this Uid
                fitproblem = FitArrange()
                fitproblem.set_model(model)
                self.fitArrangeList[Uid] = fitproblem
        else:
            raise ValueError, "park_integration:missing parameters"
    
    def set_data(self,data,Uid,qmin=None,qmax=None):
        """ Receives plottable, creates a list of data to fit,set data
            in a FitArrange object and adds that object in a dictionary 
            with key Uid.
            @param data: data added
            @param Uid: unique key corresponding to a fitArrange object with data
            """
        if qmin !=None and qmax !=None:
            data.setFitRange(mini=qmin,maxi=qmax)
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
    


    