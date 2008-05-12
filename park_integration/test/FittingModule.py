#class Fitting
from sans.guitools.fittings import Parameter
import sans.guitools.fittings
class Fitting:
    """ 
        Performs the Fit.he user determine what kind of data 
    """
    def __init__(self,data1,data2=None):
        self.model = ""
        self.data1 = data1
        self.data2= data2
        self.contraint =None
        
    def fit_engine(self):
        """
            Check the contraint value and specify what kind of fit to use
        """
        return True
    def fit(self):
        """
             Do the fit 
        """
          
        #Display the fittings values
        self.default_A = self.model.getParam('A') 
        self.default_B = self.model.getParam('B') 
        self.cstA = Parameter(self.model, 'A', self.default_A)
        self.cstB  = Parameter(self.model, 'B', self.default_B)
        xmin= min(self.data1.x)
        xmax= max(self.data1.x)
        
        chisqr, out, cov = sans.guitools.fittings.sansfit(self.model, 
        [self.cstA, self.cstB],self.data1.x, self.data1.y,self.data1.dy,xmin,xmax)
        
        return chisqr, out, cov
    
    def set_model(self,model):
        """ Set model """
        self.model = model
        
    
    def set_data(self,x,y,dx,dy):
        """ Receive values from Loader class and set plottable variables"""
        self.data1.x = x
        self.data1.y = y
        self.data1.dx= dx
        self.data1.dy= dy
    def get_data(self):
        """ return data"""
        return self.data1
    
    def add_contraint(self, contraint):
        """ User specify contraint to fit """
        self.contraint = str(contraint)
    def get_contraint(self):
        """ return the contraint value """
        return self.contraint
        
    