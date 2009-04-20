
import park,numpy,math, copy

class SansParameter(park.Parameter):
    """
        SANS model parameters for use in the PARK fitting service.
        The parameter attribute value is redirected to the underlying
        parameter value in the SANS model.
    """
    def __init__(self, name, model):
        """
            @param name: the name of the model parameter
            @param model: the sans model to wrap as a park model
        """
        self._model, self._name = model,name
        #set the value for the parameter of the given name
        self.set(model.getParam(name))
         
    def _getvalue(self):
        """
            override the _getvalue of park parameter
            @return value the parameter associates with self.name
        """
        return self._model.getParam(self.name)
    
    def _setvalue(self,value):
        """
            override the _setvalue pf park parameter
            @param value: the value to set on a given parameter
        """
        self._model.setParam(self.name, value)
        
    value = property(_getvalue,_setvalue)
    
    def _getrange(self):
        """
            Override _getrange of park parameter
            return the range of parameter
        """
        if not  self.name in self._model.getDispParamList():
            lo,hi = self._model.details[self.name][1:]
            if lo is None: lo = -numpy.inf
            if hi is None: hi = numpy.inf
        else:
            lo= -numpy.inf
            hi= numpy.inf
        if lo >= hi:
            raise ValueError,"wrong fit range for parameters"
        
        return lo,hi
    
    def _setrange(self,r):
        """
            override _setrange of park parameter
            @param r: the value of the range to set
        """
        self._model.details[self.name][1:] = r
    range = property(_getrange,_setrange)
    
class Model(park.Model):
    """
        PARK wrapper for SANS models.
    """
    def __init__(self, sans_model, **kw):
        """
            @param sans_model: the sans model to wrap using park interface
        """
        park.Model.__init__(self, **kw)
        self.model = sans_model
        self.name = sans_model.name
        #list of parameters names
        self.sansp = sans_model.getParamList()
        #list of park parameter
        self.parkp = [SansParameter(p,sans_model) for p in self.sansp]
        #list of parameterset 
        self.parameterset = park.ParameterSet(sans_model.name,pars=self.parkp)
        self.pars=[]
  
  
    def getParams(self,fitparams):
        """
            return a list of value of paramter to fit
            @param fitparams: list of paramaters name to fit
        """
        list=[]
        self.pars=[]
        self.pars=fitparams
        for item in fitparams:
            for element in self.parkp:
                 if element.name ==str(item):
                     list.append(element.value)
        return list
    
    
    def setParams(self,paramlist, params):
        """
            Set value for parameters to fit
            @param params: list of value for parameters to fit 
        """
        try:
            for i in range(len(self.parkp)):
                for j in range(len(paramlist)):
                    if self.parkp[i].name==paramlist[j]:
                        self.parkp[i].value = params[j]
                        self.model.setParam(self.parkp[i].name,params[j])
        except:
            raise
  
    def eval(self,x):
        """
            override eval method of park model. 
            @param x: the x value used to compute a function
        """
        return self.model.runXY(x)
   
   


class Data(object):
    """ Wrapper class  for SANS data """
    def __init__(self,x=None,y=None,dy=None,dx=None,sans_data=None):
        """
            Data can be initital with a data (sans plottable)
            or with vectors.
        """
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
        """
            @return the range of data.x to fit
        """
        return self.qmin, self.qmax
     
     
    def residuals(self, fn):
        """ @param fn: function that return model value
            @return residuals
        """
        x,y,dy = [numpy.asarray(v) for v in (self.x,self.y,self.dy)]
        if self.qmin==None and self.qmax==None: 
            fx =numpy.asarray([fn(v) for v in x])
            return (y - fx)/dy
        else:
            idx = (x>=self.qmin) & (x <= self.qmax)
            fx = numpy.asarray([fn(item)for item in x[idx ]])
            return (y[idx] - fx)/dy[idx]
        
    def residuals_deriv(self, model, pars=[]):
        """ 
            @return residuals derivatives .
            @note: in this case just return empty array
        """
        return []
    
    
class FitData1D(object):
    """ Wrapper class  for SANS data """
    def __init__(self,sans_data1d, smearer=None):
        """
            Data can be initital with a data (sans plottable)
            or with vectors.
            
            self.smearer is an object of class QSmearer or SlitSmearer
            that will smear the theory data (slit smearing or resolution 
            smearing) when set.
            
            The proper way to set the smearing object would be to
            do the following:
            
            from DataLoader.qsmearing import smear_selection
            fitdata1d = FitData1D(some_data)
            fitdata1d.smearer = smear_selection(some_data)
            
            Note that some_data _HAS_ to be of class DataLoader.data_info.Data1D
            
            Setting it back to None will turn smearing off.
            
        """
        
        self.smearer = smearer
      
        # Initialize from Data1D object
        self.data=sans_data1d
        self.x= sans_data1d.x
        self.y= sans_data1d.y
        self.dx= sans_data1d.dx
        self.dy= sans_data1d.dy
        
        ## Min Q-value
        #Skip the Q=0 point, especially when y(q=0)=None at x[0].
        if min (self.data.x) ==0.0 and self.data.x[0]==0 and not numpy.isfinite(self.data.y[0]):
            self.qmin = min(self.data.x[self.data.x!=0])
        else:                              
            self.qmin= min (self.data.x)
        ## Max Q-value
        self.qmax= max (self.data.x)
       
       
    def setFitRange(self,qmin=None,qmax=None):
        """ to set the fit range"""
        
        # Remove or do not allow fitting on the Q=0 point, especially when y(q=0)=None at x[0].
        #ToDo: Fix this.
        if qmin==0.0 and self.data.x[0]==0 and not numpy.isfinite(self.data.y[0]):
            self.qmin = min(self.data.x[self.data.x!=0])
        elif qmin!=None:                       
            self.qmin = qmin            

        if qmax !=None:
            self.qmax = qmax
        
        
    def getFitRange(self):
        """
            @return the range of data.x to fit
        """
        return self.qmin, self.qmax
     
     
    def residuals(self, fn):
        """ 
            Compute residuals.
            
            If self.smearer has been set, use if to smear
            the data before computing chi squared.
            
            @param fn: function that return model value
            @return residuals
        """
        x,y = [numpy.asarray(v) for v in (self.x,self.y)]
        if self.dy ==None or self.dy==[]:
            dy= numpy.zeros(len(y))  
        else:
            dy= copy.deepcopy(self.dy)
            dy= numpy.asarray(dy)
        dy[dy==0]=1
        idx = (x>=self.qmin) & (x <= self.qmax)
  
        # Compute theory data f(x)
        fx = numpy.zeros(len(x))
        fx[idx] = numpy.asarray([fn(v) for v in x[idx]])
        
        # Smear theory data
     
        if self.smearer is not None:
            fx = self.smearer(fx)
       
        # Sanity check
        if numpy.size(dy) < numpy.size(x):
            raise RuntimeError, "FitData1D: invalid error array"
        return (y[idx] - fx[idx])/dy[idx]
     
  
        
    def residuals_deriv(self, model, pars=[]):
        """ 
            @return residuals derivatives .
            @note: in this case just return empty array
        """
        return []
    
    
class FitData2D(object):
    """ Wrapper class  for SANS data """
    def __init__(self,sans_data2d):
        """
            Data can be initital with a data (sans plottable)
            or with vectors.
        """
        self.data=sans_data2d
        self.image = sans_data2d.data
        self.err_image = sans_data2d.err_data
        self.x_bins= sans_data2d.x_bins
        self.y_bins= sans_data2d.y_bins
       
        x = max(self.data.xmin, self.data.xmax)
        y = max(self.data.ymin, self.data.ymax)
        
        ## fitting range
        self.qmin = 1e-16
        self.qmax = math.sqrt(x*x +y*y)
       
       
       
    def setFitRange(self,qmin=None,qmax=None):
        """ to set the fit range"""
        if qmin==0.0:
            self.qmin = 1e-16
        elif qmin!=None:                       
            self.qmin = qmin            
        if qmax!=None:
            self.qmax= qmax
      
        
    def getFitRange(self):
        """
            @return the range of data.x to fit
        """
        return self.qmin, self.qmax
     
     
    def residuals(self, fn):
        """ @param fn: function that return model value
            @return residuals
        """
        res=[]
        if self.err_image== None or self.err_image ==[]:
            err_image= numpy.zeros(len(self.y_bins),len(self.x_bins))
        else:
            err_image = copy.deepcopy(self.err_image)
            
        err_image[err_image==0]=1
        for i in range(len(self.x_bins)):
            for j in range(len(self.y_bins)):
                temp = math.pow(self.data.x_bins[i],2)+math.pow(self.data.y_bins[j],2)
                radius= math.sqrt(temp)
                if self.qmin <= radius and radius <= self.qmax:
                    res.append( (self.image[j][i]- fn([self.x_bins[i],self.y_bins[j]]))\
                            /err_image[j][i] )
        
        return numpy.array(res)
       
          
    def residuals_deriv(self, model, pars=[]):
        """ 
            @return residuals derivatives .
            @note: in this case just return empty array
        """
        return []
    
class sansAssembly:
    """
         Sans Assembly class a class wrapper to be call in optimizer.leastsq method
    """
    def __init__(self,paramlist,Model=None , Data=None):
        """
            @param Model: the model wrapper fro sans -model
            @param Data: the data wrapper for sans data
        """
        self.model = Model
        self.data  = Data
        self.paramlist=paramlist
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
       
        return sum/ len(self.res)
    
    def __call__(self,params):
        """
            Compute residuals
            @param params: value of parameters to fit
        """
        #import thread
        self.model.setParams(self.paramlist,params)
        self.res= self.data.residuals(self.model.eval)
        #print "residuals",thread.get_ident()
        return self.res
    
class FitEngine:
    def __init__(self):
        """
            Base class for scipy and park fit engine
        """
        #List of parameter names to fit
        self.paramList=[]
        #Dictionnary of fitArrange element (fit problems)
        self.fitArrangeDict={}
        
    def _concatenateData(self, listdata=[]):
        """  
            _concatenateData method concatenates each fields of all data contains ins listdata.
            @param listdata: list of data 
            @return Data: Data is wrapper class for sans plottable. it is created with all parameters
             of data concatenanted
            @raise: if listdata is empty  will return None
            @raise: if data in listdata don't contain dy field ,will create an error
            during fitting
        """
        #TODO: we have to refactor the way we handle data.
        # We should move away from plottables and move towards the Data1D objects
        # defined in DataLoader. Data1D allows data manipulations, which should be
        # used to concatenate. 
        # In the meantime we should switch off the concatenation.
        #if len(listdata)>1:
        #    raise RuntimeError, "FitEngine._concatenateData: Multiple data files is not currently supported"
        #return listdata[0]
        
        if listdata==[]:
            raise ValueError, " data list missing"
        else:
            xtemp=[]
            ytemp=[]
            dytemp=[]
            self.mini=None
            self.maxi=None
               
            for item in listdata:
                data=item.data
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
            data= Data(x=xtemp,y=ytemp,dy=dytemp)
            data.setFitRange(self.mini, self.maxi)
            return data
        
        
    def set_model(self,model,Uid,pars=[]):
        """
            set a model on a given uid in the fit engine.
            @param model: the model to fit
            @param Uid :is the key of the fitArrange dictionnary where model is saved as a value
            @param pars: the list of parameters to fit 
            @note : pars must contains only name of existing model's paramaters
        """
        if len(pars) >0:
            if model==None:
                raise ValueError, "AbstractFitEngine: Specify parameters to fit"
            else:
                temp=[]
                for item in pars:
                    if item in model.model.getParamList():
                        temp.append(item)
                        self.paramList.append(item)
                    else:
                        raise ValueError,"wrong paramter %s used to set model %s. Choose\
                            parameter name within %s"%(item, model.model.name,str(model.model.getParamList()))
                        return
            #A fitArrange is already created but contains dList only at Uid
            if self.fitArrangeDict.has_key(Uid):
                self.fitArrangeDict[Uid].set_model(model)
                self.fitArrangeDict[Uid].pars= pars
            else:
            #no fitArrange object has been create with this Uid
                fitproblem = FitArrange()
                fitproblem.set_model(model)
                fitproblem.pars= pars
                self.fitArrangeDict[Uid] = fitproblem
                
        else:
            raise ValueError, "park_integration:missing parameters"
    
    def set_data(self,data,Uid,smearer=None,qmin=None,qmax=None):
        """ Receives plottable, creates a list of data to fit,set data
            in a FitArrange object and adds that object in a dictionary 
            with key Uid.
            @param data: data added
            @param Uid: unique key corresponding to a fitArrange object with data
        """
        if data.__class__.__name__=='Data2D':
            fitdata=FitData2D(data)
        else:
            fitdata=FitData1D(data, smearer)
       
        fitdata.setFitRange(qmin=qmin,qmax=qmax)
        #A fitArrange is already created but contains model only at Uid
        if self.fitArrangeDict.has_key(Uid):
            self.fitArrangeDict[Uid].add_data(fitdata)
        else:
        #no fitArrange object has been create with this Uid
            fitproblem= FitArrange()
            fitproblem.add_data(fitdata)
            self.fitArrangeDict[Uid]=fitproblem    
   
    def get_model(self,Uid):
        """ 
            @param Uid: Uid is key in the dictionary containing the model to return
            @return  a model at this uid or None if no FitArrange element was created
            with this Uid
        """
        if self.fitArrangeDict.has_key(Uid):
            return self.fitArrangeDict[Uid].get_model()
        else:
            return None
    
    def remove_Fit_Problem(self,Uid):
        """remove   fitarrange in Uid"""
        if self.fitArrangeDict.has_key(Uid):
            del self.fitArrangeDict[Uid]
            
    def select_problem_for_fit(self,Uid,value):
        """
            select a couple of model and data at the Uid position in dictionary
            and set in self.selected value to value
            @param value: the value to allow fitting. can only have the value one or zero
        """
        if self.fitArrangeDict.has_key(Uid):
             self.fitArrangeDict[Uid].set_to_fit( value)
             
             
    def get_problem_to_fit(self,Uid):
        """
            return the self.selected value of the fit problem of Uid
           @param Uid: the Uid of the problem
        """
        if self.fitArrangeDict.has_key(Uid):
             self.fitArrangeDict[Uid].get_to_fit()
    
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
        self.pars=[]
        #self.selected  is zero when this fit problem is not schedule to fit 
        #self.selected is 1 when schedule to fit 
        self.selected = 0
        
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
        #return self.dList 
        return self.dList[0] 
      
    def remove_data(self,data):
        """
            Remove one element from the list
            @param data: Data to remove from dList
        """
        if data in self.dList:
            self.dList.remove(data)
    def set_to_fit (self, value=0):
        """
           set self.selected to 0 or 1  for other values raise an exception
           @param value: integer between 0 or 1
        """
        self.selected= value
        
    def get_to_fit(self):
        """
            @return self.selected value
        """
        return self.selected
    


    