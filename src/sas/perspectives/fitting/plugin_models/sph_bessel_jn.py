"""
Test plug-in model
These are links of available functions:

http://docs.python.org/library/math.html
http://www.scipy.org/Numpy_Functions_by_Category
"""

"""
## *****************************************************************************
Please select the 'Compile' from the menubar after the modification and saving.
Note that we recommend to save the file as a different file name.
Otherwise, it could be removed in the future on re-installation of the SasView.
## *****************************************************************************
"""

from sas.models.pluginmodel import Model1DPlugin  ##DO NOT CHANGE THIS LINE!!!
import math                  ##DO NOT CHANGE THIS LINE!!!
import numpy                 ##DO NOT CHANGE THIS LINE!!!
import scipy.special            ##CHANGE THIS LINE WITH CAUTION!!!
import os
import sys
##PLEASE READ COMMENTS CAREFULLY !!! COMMENT ARE IN CAPITAL LETTERS AND AFTER ##
## THESE COMMENTS ARE THERE TO GUIDE YOU. YOU CAN REMOVE THEM ONLY WHEN YOU ARE
## CONFORTABLE ENOUGH WITH OUR MODEL PLUGIN OPTION


## <-----  SIGN DEFINES WHERE YOU CAN MODIFY THE CODE

class Model(Model1DPlugin): ##DO NOT CHANGE THIS LINE!!!
    """
    ##YOU CAN BE MODIFY ANYTHING BETWEEN """ """
    ##DESCRIPTION OF MODEL PLUG-IN GOES HERE
    
    ##EXAMPLE: Class that evaluates a polynomial model. 
    """
    name = "" 
                                
    def __init__(self):      ##DO NOT CHANGE THIS LINE!!!
        """
        Initialization
        """
        Model1DPlugin.__init__(self, name=self.name) ##DO NOT CHANGE THIS LINE!!!
        
        ## EDIT PARAMETERS' NAMES AND VALUE
        ## DELETE MODIFIABLE LINE HERE WILL REDUCE THE NUMBER OF PARAMETERS
        self.params = {}                ##DO NOT CHANGE THIS LINE!!!
        # Set the name same as the file name
        self.name = self.get_fname()     ##DO NOT CHANGE THIS LINE!!!
        ## YOU CAN MODIFY THE LINE BELLOW.CHANGE WORD BETWEEN ' ' AND NUMBER 
        ## YOU CAN ALSO DELETE THIS LINE
        self.params['C'] = 1.0   ## <-----   
        ## YOU CAN MODIFY THE LINE BELLOW.CHANGE WORD BETWEEN ' ' AND NUMBER 
        ## YOU CAN ALSO DELETE THIS LINE                                                      
        self.params['A'] = 1.0       ## <-----   
        ## YOU CAN MODIFY THE LINE BELLOW.CHANGE WORD BETWEEN ' ' AND NUMBER 
        ## YOU CAN ALSO DELETE THIS LINE                 
        self.params['B'] = 0.0      ## <-----   
        ## YOU CAN MODIFY THE LINE BELLOW.CHANGE WORD BETWEEN ' ' AND NUMBER 
        ## YOU CAN ALSO DELETE THIS LINE                 
        self.params['D'] = 0.0      ## <-----   
        ## YOU CAN ALSO DELETE THIS LINE                 
        self.params['n'] = 1      ## <----- 
 
        ## DEFINE DEFAULT DETAILS
        self.set_details()      ##DO NOT DELETE OR CHANGE THIS LINE!!!
        
        ## YOU CAN MODIFY THE LINE BELLOW.MODIFY WORDS BETWEEN """   """  ONLY!!!!
        self.description = """
            Spherical Bessel Function: C*sph_jn(n, Ax+B)+D
                 """                        ## <-----   
   
    def function(self, x = 0.0): ##DO NOT CHANGE THIS LINE!!!
        """ 
        Evaluate the model
        
        :param x: input x
        
        :return: function value
        
        """
        ## ADD YOUR FUNCTION HERE.
        ## REUSE THE PARAMETERS DEFINED PREVIOUSLY TO WRITE YOUR FUNCTION.
        
        ## IN THIS EXAMPLE THE FUNTION IS:
        ## C*sph_jn(Ax+B)+D
         
        ## NOTE: pow IS A FUNCTION IMPORTED FROM PYTHON MATH LIBRARY
        ## FOR MORE INFORMATION CHECK http://docs.python.org/library/math.html      
        ## OTHER FUNCTIONS ARE ALSO 
        ###  AVAILABLE http://www.scipy.org/Numpy_Functions_by_Category
        ## numpy FUNCTIONS ARE FOR EXPERT USER
        
        ## YOU CAN ERASE EVERYTHING BELLOW FOR YOUR OWN FUNCTION
        #Redefine parameters as local parameters
        a = self.params['A']       ## <-----   
        b = self.params['B']       ## <-----   
        c = self.params['C']       ## <-----   
        d = self.params['D']       ## <-----   
        # Take integer value only
        n = int(self.params['n'])      ## <-----   

        ##THIS OUR FUNCTION TEMPLATE
        #Remove a singular point (lim poly --> 0) for sin(poly)/poly
        #(Just note: In Python, indentation defines the belongings of 'if', 'for', and so on..)
        input = a * x + b
        # sph_out and _ are in array types from scipy upto n'th order
        # where _ is not used for this function.
        sph_out, _ = scipy.special.sph_jn(n, input)
        # Take only n'th value
        result = c * sph_out[n] + d      ## <-----                

        return result ## MODIFY ONLY RESULT. DON'T DELETE RETURN!!!!
    
    ## DO NOT MODIFY THE FOLLOWING LINES!!!!!!!!!!!!!!!!      
    def get_fname(self):
        """
        Get the model name same as the file name
        """
        path = sys._getframe().f_code.co_filename
        basename  = os.path.basename(path)
        name, _ = os.path.splitext(basename)
        return name
            
###############################################################################   
## DO NOT MODIFY THE FOLLOWING LINES!!!!!!!!!!!!!!!!       
if __name__ == "__main__": 
    m= Model() 
    out1 = m.runXY(0.0)
    out2 = m.runXY(0.01)
    isfine1 = numpy.isfinite(out1)
    isfine2 = numpy.isfinite(out2)
    print "Testing the value at Q = 0.0:"
    print out1, " : finite? ", isfine1
    print "Testing the value at Q = 0.01:"
    print out2, " : finite? ", isfine2
    if isfine1 and isfine2:
        print "===> Simple Test: Passed!"
    else:
        print "===> Simple Test: Failed!"
