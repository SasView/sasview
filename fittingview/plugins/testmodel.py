"""
Test plug-in model
These are links of available functions:

http://docs.python.org/library/math.html
http://www.scipy.org/Numpy_Functions_by_Category
"""
from sans.models.pluginmodel import Model1DPlugin  ##DO NOT CHANGE THIS LINE!!!
from math import *                    ##DO NOT CHANGE THIS LINE!!!
from numpy import *                ##DO NOT CHANGE THIS LINE!!!

##PLEASE READ COMMENTS CAREFULLY !!! COMMENT ARE IN CAPITAL LETTERS AND AFTER ##
## THESE COMMENTS ARE THERE TO GUIDE YOU. YOU CAN REMOVE THEM ONLY WHEN YOU ARE
## CONFORTABLE ENOUGH WITH OUR MODEL PLUGIN OPTION


## <-----  SIGN DEFINES WHERE YOU CAN MODIFY THE CODE

class Model(Model1DPlugin):##DO NOT CHANGE THIS LINE!!!
    """
    ##YOU CAN BE MODIFY ANYTHING BETWEEN """ """
    ##DESCRIPTION OF MODEL PLUG-IN GOES HERE
    
    ##EXAMPLE:Class that evaluates a cos(x) model. 
    """
    
    ## YOU CAN MODIFY THE LINE BELLOW. CHANGE ONLY WORDS BETWEEN " " 
    ## TO RENAME YOUR MODEL
    name = "A+Bcos(2x)+Csin(2x)"      ## <----- NAME OF THE MODEL   
    
    def __init__(self):
        """
        Initialization
        """
        Model1DPlugin.__init__(self, name= self.name)##DO NOT CHANGE THIS LINE!!!
        
        ## EDIT PARAMETERS' NAMES AND VALUE
        ## DELETE MODIFIABLE LINE HERE WILL REDUCE THE NUMBER OF PARAMETERS
        self.params = {}                        ##DO NOT CHANGE THIS LINE!!!
        ## YOU CAN MODIFY THE LINE BELLOW.CHANGE WORD BETWEEN ' ' AND NUMBER 
        ## YOU CAN ALSO DELETE THIS LINE
        self.params['A'] = 1.0       ## <-----  
        ## YOU CAN MODIFY THE LINE BELLOW.CHANGE WORD BETWEEN ' ' AND NUMBER 
        ## YOU CAN ALSO DELETE THIS LINE   
        self.params['B'] = 1.0       ## <----- 
        ## YOU CAN MODIFY THE LINE BELLOW.CHANGE WORD BETWEEN ' ' AND NUMBER 
        ## YOU CAN ALSO DELETE THIS LINE    
        self.params['C'] = 10.0      ## <-----  

        ## STORING PARAMETERS  [UNIT, MINIMUM VALUE, MAXIMUM VALUE]
        self.details = {}       ##DO NOT CHANGE THIS LINE!!!
        ## YOU CAN MODIFY THE LINE BELLOW.CHANGE WORD BETWEEN ' ',WORD BETWEEN
        ## ' ', TWO OTHER NUMBERS TO NEW VALUE OR YOU CAN ALSO DELETE TH LINE    
        self.details['A'] = ['', -1e16, 1e16]        ## <----- 
        ## YOU CAN MODIFY THE LINE BELLOW.CHANGE WORD BETWEEN ' ',WORD BETWEEN
        ## ' ', TWO OTHER NUMBERS TO NEW VALUE OR YOU CAN ALSO DELETE TH LINE    
        self.details['B'] = ['', -1e16, 1e16]         ## <----- 
        ## YOU CAN MODIFY THE LINE BELLOW.CHANGE WORD BETWEEN ' ',WORD BETWEEN
        ## ' ', TWO OTHER NUMBERS TO NEW VALUE OR YOU CAN ALSO DELETE TH LINE    
        self.details['C'] = ['', -1e16, 1e16]         ## <----- 
        ## YOU CAN MODIFY THE LINE BELLOW.MODIFY WORDS BETWEEN """   """  ONLY!!!!
        self.description = "F(x)=A+Bcos(2x)+Csin(2x) " ## <----- 
   
    def function(self, x = 0.0):  ##DO NOT CHANGE THIS LINE!!!
        """
        Evaluate the model
        
        :param x: input x
        
        :return: function value
        
        """
        ## ADD YOUR FUNCTION HERE.
        ## REUSE THE PARAMETERS DEFINED PREVIOUSLY TO WRITE YOUR FUNCTION.
        
        ## IN THIS EXAMPLE THE FUNTION IS:
        ## A+Bcos(2x)+Csin(2x)
        ## YOU CAN USE math.sin or sin directly
        ## NOTE: sin, cos ARE FUNCTIONS  IMPORTED FROM PYTHON MATH LIBRARY
        ## FOR MORE INFORMATION CHECK http://docs.python.org/library/math.html      
        ## OTHER FUNCTIONS ARE ALSO 
        ##  AVAILABLE http://www.scipy.org/Numpy_Functions_by_Category
        ## numpy FUNCTIONS ARE FOR EXPERT USER
        
        return self.params['A']+self.params['B']*cos(2.0*x)+self.params['C']*math.sin(2.0*x)
   