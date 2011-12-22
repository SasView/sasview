"""
Test plug-in model
These are links of available functions:

http://docs.python.org/library/math.html
http://www.scipy.org/Numpy_Functions_by_Category
"""
## *****************************************************************************
## For safety of your model, saving as a different file name is recommended.
## Otherwise, it could be removed in the future re-installation of the SansView.
## *****************************************************************************
from sans.models.pluginmodel import Model1DPlugin  ##DO NOT CHANGE THIS LINE!!!

## FOR MORE INFORMATION CHECK http://docs.python.org/library/math.html      
## AND http://www.scipy.org/Numpy_Functions_by_Category
import math                    ##DO NOT CHANGE THIS LINE!!!
import numpy                   ##DO NOT CHANGE THIS LINE!!!

## <-----  SIGN DEFINES WHERE YOU CAN MODIFY THE CODE

class Model(Model1DPlugin): ##DO NOT CHANGE THIS LINE!!!
    """
    ##YOU CAN BE MODIFY ANYTHING BETWEEN """ """
    ##DESCRIPTION OF MODEL PLUG-IN GOES HERE
    
    ##EXAMPLE: Class that evaluates a polynomial model. 
    """
    ## YOU CAN MODIFY THE LINE BELLOW. CHANGE ONLY WORDS BETWEEN " " 
    ## TO RENAME YOUR MODEL: THIS NAME IS WHAT YOU SEE ON GUI.
    name = "polynomial5"        ## <----- NAME OF THE MODEL   
                                
    def __init__(self):      ##DO NOT CHANGE THIS LINE!!!
        """
        Initialization
        """
        Model1DPlugin.__init__(self, name=self.name) ##DO NOT CHANGE THIS LINE!!!
        
        ## HERE WE DEFINE THE PARAM NAME AND ITS INITIAL VALUE 
        ## YOU CAN MODIFY THE LINE BELLOW.CHANGE WORD BETWEEN ' ' AND NUMBER                                                      
        self.params['A'] = 0.1       ## <-----                
        self.params['B'] = 10.0      ## <-----                 
        self.params['C'] = 0.0       ## <-----                
        self.params['D'] = 0.0       ## <-----                    
        self.params['E'] = 0.0       ## <-----                  
        self.params['F'] = 0.0       ## <-----   
        
        ## DEFINE DEFAULT DETAILS
        self.set_details()      ##DO NOT DELETE OR CHANGE THIS LINE!!!
        
        ## IN THIS EXAMPLE THE FUNTION IS:
        ## F(x)=A+B*x+C*x^2+D*x^3+E*x^4+F*x^5             
   
    def function(self, x = 0.0): ##DO NOT CHANGE THIS LINE!!!
        """ 
        Evaluate the model
        :param x: input x
        :return: function value
        """
        ## DEFINE YOUR FUNCTION HERE.
        ## YOU CAN ERASE EVERYTHING BELLOW FOR YOUR OWN FUNCTION
        #Redefine parameters as local parameters, or skip and use long name
        a = self.params['A']       ## <-----   
        b = self.params['B']       ## <-----   
        c = self.params['C']       ## <-----   
        d = self.params['D']       ## <-----   
        e = self.params['E']       ## <-----   
        f = self.params['F']       ## <-----   
 
        ##THIS OUR FUNCTION TEMPLATE
        poly = a + b * x + c * math.pow(x,2) + d * math.pow(x,3) \
                + e * math.pow(x,4) + f * math.pow(x,5)              ## <-----                
        
        #(Just note: In Python, indentation defines the belongings 
        # of 'if', 'for', and so on..)
        #(lim x --> 0) 
        if x == 0:                          ## <-----   
            result = a                      ## <-----   
        else:                               ## <-----   
            result = poly                   ## <-----    

        return result       ## MODIFY ONLY RESULT. DON'T DELETE RETURN!!!!

###############################################################################
## THIS IS FOR TEST. DO NOT MODIFY THE FOLLOWING LINES!!!!!!!!!!!!!!!!       
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