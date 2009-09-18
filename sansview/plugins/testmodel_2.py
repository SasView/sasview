"""
    Test plug-in model
"""
from sans.models.pluginmodel import Model1DPlugin   ##Do not change this line!!!
import math                                         ##Do not change this line!!!

# Modify ONLY lines with '## YOU CAN MODIFY THIS LINE'.
# Your model HAS to be called Model
class Model(Model1DPlugin):         ##Do not change this line!!!
    """ Class that evaluates a ploynomial model. 
    """
    
    ## Name of your model
    name = "sin(poly)/(poly)"    ## YOU CAN MODIFY THIS LINE.
    
    def __init__(self):      ##Do not change this line!!!
        """ Initialization """
        Model1DPlugin.__init__(self, name= self.name)  ##Do not change this line!!!
        
        ## Parameters definition and defaults
        self.params = {}                    ##Do not change this line!!!
        self.params['scale'] = 1.0          ## YOU CAN MODIFY THIS LINE
        self.params['A'] = 0.0              ## YOU CAN MODIFY THIS LINE
        self.params['B'] = 10.0             ## YOU CAN MODIFY THIS LINE
        self.params['C'] = 0.0             ## YOU CAN MODIFY THIS LINE
        self.params['D'] = 0.0              ## YOU CAN MODIFY THIS LINE
        self.params['E'] = 0.0              ## YOU CAN MODIFY THIS LINE
        self.params['F'] = 0.0              ## YOU CAN MODIFY THIS LINE

        ## Parameter details [units, min, max]
        self.details = {}                           ##Do not change this line!!!
        self.details['scale'] = ['',None, None]   ## YOU CAN MODIFY THIS LINE
        self.details['A'] = ['', None, None]       ## YOU CAN MODIFY THIS LINE
        self.details['B'] = ['', None, None]       ## YOU CAN MODIFY THIS LINE
        self.details['C'] = ['', None, None]       ## YOU CAN MODIFY THIS LINE
        self.details['D'] = ['', None, None]       ## YOU CAN MODIFY THIS LINE
        self.details['E'] = ['', None, None]       ## YOU CAN MODIFY THIS LINE
        self.details['F'] = ['', 0, 1e16]       ## YOU CAN MODIFY THIS LINE     
          
        self.description = "scale * sin(F(x)/F(x)) \n where F(x)=A+B*x+C*x^2+D*x^3+E*x^4+F*x^5"  ## YOU CAN MODIFY THIS LINE
   
    def function(self, x = 0.0): ##Do not change this line!!!
        """ Evaluate the model
            @param x: input x
            @return: function value
        """
        ##You can modify from HERE to the END of this function!!!
        
        #Redefine parameters as local parameters
        a = self.params['A']      
        b = self.params['B']       
        c = self.params['C']       
        d = self.params['D']       
        e = self.params['E']      
        f = self.params['F']       
        scl = self.params['scale']  
        
        #Polynomial
        poly = a + b*x + c*math.pow(x,2) + d*math.pow(x,3) \
             + e*math.pow(x,4) +f*math.pow(x,5)                  
        
        #Remove a singular point (lim poly --> 0) for sin(poly)/poly
        #(Just note: In Python, indentation defines the belongings of 'if', 'for', and so on..)
        if poly == 0:
            result = 1
        else:
            result = math.sin(poly)/poly
            
        #Re-scale
        result *=scl      

        return result
   