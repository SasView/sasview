#class Fitting
from sans.guitools.plottables import Data1D
from Loader import Load
from scipy import optimize
#from Fitting import Fit

class FitArrange:
    def __init__(self):
        """
            Store a set of data for a given model to perform the Fit
            @param model: the model selected by the user
            @param Ldata: a list of data what the user want to fit
        """
        self.model = None
        self.dList =[]
        
    def set_model(self,model):
        """ set the model """
        self.model = model
        
    def add_data(self,data):
        """ 
            @param data: Data to add in the list
            fill a self.dataList with data to fit
        """
        if not data in self.dList:
            self.dList.append(data)
            
    def get_model(self):
        """ Return the model"""
        return self.model   
     
    def get_data(self):
        """ Return list of data"""
        return self.dList 
      
    def remove_data(self,data):
        """
            Remove one element from the list
            @param data: Data to remove from the the lsit of data
        """
        if data in self.dList:
            self.dList.remove(data)
            
class ScipyFit:
    """ 
        Performs the Fit.he user determine what kind of data 
    """
    def __init__(self,data=[]):
        #this is a dictionary of FitArrange elements
        self.fitArrangeList={}
        #the constraint of the Fit
        self.constraint =None
        #Specify the use of scipy or park fit
        self.fitType =None
        
  
    
    def fit(self,pars, qmin=None, qmax=None):
        """
             Do the fit 
        """
        #for item in self.fitArrangeList.:
        
        fitproblem=self.fitArrangeList.values()[0]
        listdata=[]
        model = fitproblem.get_model()
        listdata = fitproblem.get_data()
        
        parameters = self.set_param(model,pars)
       
        # Do the fit with  data set (contains one or more data) and one model 
        xtemp,ytemp,dytemp=self._concatenateData( listdata)
        if qmin==None:
            qmin= min(xtemp)
        if qmax==None:
            qmax= max(xtemp)  
        chisqr, out, cov = fitHelper(model,parameters, xtemp,ytemp, dytemp ,qmin,qmax)
        return chisqr, out, cov
    
    def _concatenateData(self, listdata=[]):
        """ concatenate each fields of all data contains ins listdata"""
        if listdata==[]:
            raise ValueError, " data list missing"
        else:
            xtemp=[]
            ytemp=[]
            dytemp=[]
               
            for data in listdata:
                for i in range(len(data.x)):
                    if not data.x[i] in xtemp:
                        xtemp.append(data.x[i])
                       
                    if not data.y[i] in ytemp:
                        ytemp.append(data.y[i])
                        
                    if not data.dy[i] in dytemp:
                        dytemp.append(data.dy[i])
            return xtemp, ytemp,dytemp
        
    def set_model(self,model,Uid):
        """ Set model """
        if self.fitArrangeList.has_key(Uid):
            self.fitArrangeList[Uid].set_model(model)
        else:
            fitproblem= FitArrange()
            fitproblem.set_model(model)
            self.fitArrangeList[Uid]=fitproblem
        
    def set_data(self,data,Uid):
        """ Receive plottable and create a list of data to fit"""
        
        if self.fitArrangeList.has_key(Uid):
            self.fitArrangeList[Uid].add_data(data)
        else:
            fitproblem= FitArrange()
            fitproblem.add_data(data)
            self.fitArrangeList[Uid]=fitproblem
            
    def get_model(self,Uid):
        """ return list of data"""
        return self.fitArrangeList[Uid]
    
    def set_param(self,model, pars):
        """ Recieve a dictionary of parameter and save it """
        parameters=[]
        if model==None:
            raise ValueError, "Cannot set parameters for empty model"
        else:
            #for key ,value in pars:
            for key, value in pars.iteritems():
                param = Parameter(model, key, value)
                parameters.append(param)
        return parameters
    
    def add_constraint(self, constraint):
        """ User specify contraint to fit """
        self.constraint = str(constraint)
        
    def get_constraint(self):
        """ return the contraint value """
        return self.constraint
   
    def set_constraint(self,constraint):
        """ 
            receive a string as a constraint
            @param constraint: a string used to constraint some parameters to get a 
                specific value
        """
        self.constraint= constraint
    
    def createProblem(self):
        """
            Check the contraint value and specify what kind of fit to use
        """
        mylist=[]
        for k,value in self.fitArrangeList.iteritems():
            couple=()
            model=value.get_model()
            data=value.get_data()
            couple=(model,data)
            mylist.append(couple)
        #print mylist
        return mylist
    
                

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
    
def fitHelper(model, pars, x, y, err_y ,qmin=None, qmax=None):
    """
        Fit function
        @param model: sans model object
        @param pars: list of parameters
        @param x: vector of x data
        @param y: vector of y data
        @param err_y: vector of y errors 
    """
    def f(params):
        """
            Calculates the vector of residuals for each point 
            in y for a given set of input parameters.
            @param params: list of parameter values
            @return: vector of residuals
        """
        i = 0
        for p in pars:
            p.set(params[i])
            i += 1
        
        residuals = []
        for j in range(len(x)):
            if x[j]>qmin and x[j]<qmax:
                residuals.append( ( y[j] - model.runXY(x[j]) ) / err_y[j] )
       
        return residuals
        
    def chi2(params):
        """
            Calculates chi^2
            @param params: list of parameter values
            @return: chi^2
        """
        sum = 0
        res = f(params)
        for item in res:
            sum += item*item
        return sum
        
    p = [param() for param in pars]
    out, cov_x, info, mesg, success = optimize.leastsq(f, p, full_output=1, warning=True)
    print info, mesg, success
    # Calculate chi squared
    if len(pars)>1:
        chisqr = chi2(out)
    elif len(pars)==1:
        chisqr = chi2([out])
        
    return chisqr, out, cov_x    

      
if __name__ == "__main__": 
    load= Load()
    
    # test fit one data set one model
    load.set_filename("testdata_line.txt")
    load.set_values()
    data1 = Data1D(x=[], y=[], dx=None,dy=None)
    data1.name = "data1"
    load.load_data(data1)
    fitter =ScipyFit()
    from sans.guitools.LineModel import LineModel
    model  = LineModel()
    fitter.set_model(model,1)
    fitter.set_data(data1,1)
    
    chisqr, out, cov=fitter.fit({'A':2,'B':1},None,None)
    print "my list of param",fitter.createProblem()
    print"fit only one data",chisqr, out, cov 
    print "this model list of param",model.getParamList()
    # test fit with 2 data and one model
    fitter =ScipyFit()
   
    fitter.set_model(model,2 )
    load.set_filename("testdata1.txt")
    load.set_values()
    data2 = Data1D(x=[], y=[], dx=None,dy=None)
    data2.name = "data2"
    
    load.load_data(data2)
    fitter.set_data(data2,2)
    
    load.set_filename("testdata2.txt")
    load.set_values()
    data3 = Data1D(x=[], y=[], dx=None,dy=None)
    data3.name = "data2"
    load.load_data(data3)
    fitter.set_data(data3,2)
    chisqr, out, cov=fitter.fit({'A':2,'B':1},None,None)
    print"fit two data",chisqr, out, cov 
    