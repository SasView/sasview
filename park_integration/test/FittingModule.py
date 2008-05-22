#class Fitting
from sans.guitools.plottables import Data1D
from Loader import Load
from scipy import optimize


class FitArrange:
    def __init__(self):
        """
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
            
class Fitting:
    """ 
        Performs the Fit.he user determine what kind of data 
    """
    def __init__(self,data=[]):
        #self.model is a list of all models to fit
        #self.model={}
        self.fitArrangeList={}
        #the list of all data to fit 
        self.data = data
        #list of models parameters
        self.parameters=[]
        
        self.constraint =None
        self.fitType =None
        
    def fit_engine(self,word):
        """
            Check the contraint value and specify what kind of fit to use
        """
        self.fitType = word
        return True
    
    def fit(self,pars, qmin=None, qmax=None):
        """
             Do the fit 
        """
        #for item in self.fitArrangeList.:
        
        fitproblem=self.fitArrangeList.values()[0]
        listdata=[]
        model =fitproblem.get_model()
        listdata= fitproblem.get_data()
        self.set_param(model, pars)
        if listdata==[]:
            raise ValueError, " data list missing"
        else:
            # Do the fit with more than one data set and one model 
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
            if qmin==None:
                qmin= min(xtemp)
            if qmax==None:
                qmax= max(xtemp)  
            chisqr, out, cov = fitHelper(model,self.parameters, xtemp,ytemp, dytemp ,qmin,qmax)
            return chisqr, out, cov
    
    def set_model(self,model,Uid):
        """ Set model """
        #self.model[Uid] = model
        fitproblem= FitArrange()
        fitproblem.set_model(model)
        self.fitArrangeList[Uid]=fitproblem
        
    def set_data(self,data,Uid):
        """ Receive plottable and create a list of data to fit"""
        #self.data.append(data)
        if self.fitArrangeList.has_key(Uid):
            self.fitArrangeList[Uid].add_data(data)
        else:
            fitproblem= FitArrange()
            fitproblem.add_data(data)
            self.fitArrangeList[Uid]=fitproblem
            
    def get_data(self):
        """ return list of data"""
        return self.data
    
    def set_param(self,model, pars):
        """ Recieve a dictionary of parameter and save it """
        self.parameters=[]
        if model==None:
            raise ValueError, "Cannot set parameters for empty model"
        else:
            #for key ,value in pars:
            for key, value in pars.iteritems():
                print "this is the key",key
                print "this is the value",value
                param = Parameter(model, key, value)
                self.parameters.append(param)
            
    def add_contraint(self, contraint):
        """ User specify contraint to fit """
        self.contraint = str(contraint)
        
    def get_contraint(self):
        """ return the contraint value """
        return self.contraint



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
    Fit =Fitting()
    
    from sans.guitools.LineModel import LineModel
    model  = LineModel()
    Fit.set_model(model,1)
    Fit.set_data(data1,1)
    #default_A = model.getParam('A') 
    #default_B = model.getParam('B') 
    #cstA = Parameter(model, 'A', default_A)
    #cstB  = Parameter(model, 'B', default_B)
    
    #chisqr, out, cov=Fit.fit([cstA,cstB],None,None)
    chisqr, out, cov=Fit.fit({'A':2,'B':1},None,None)
    print"fit only one data",chisqr, out, cov 
    
    # test fit with 2 data and one model
    Fit =Fitting()
    Fit.set_model(model,2 )
    load.set_filename("testdata1.txt")
    load.set_values()
    data2 = Data1D(x=[], y=[], dx=None,dy=None)
    data2.name = "data2"
    
    load.load_data(data2)
    Fit.set_data(data2,2)
    
    load.set_filename("testdata2.txt")
    load.set_values()
    data3 = Data1D(x=[], y=[], dx=None,dy=None)
    data3.name = "data2"
    load.load_data(data3)
    Fit.set_data(data3,2)
    chisqr, out, cov=Fit.fit({'A':2,'B':1},None,None)
    print"fit two data",chisqr, out, cov 
    