#!/usr/bin/env python
""" 
    Provide Line function (y= A + Bx) as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
import math
import numpy


class LineModel(BaseComponent):
    """ 
        Class that evaluates a linear model.
        
        f(x) = A + Bx
         
        List of default parameters:
          A = 1.0
          B = 1.0 
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "LineModel"

        ## Define parameters
        self.params = {}
        self.params['A'] = 1.0
        self.params['B'] = 1.0
        self.description='f(x) = A + Bx'
        ## Parameter details [units, min, max]
        self.details = {}
        self.details['A'] = ['', None, None]
        self.details['B'] = ['', None, None]
        # fixed paramaters
        self.fixed=[]
    def _line(self, x):
        """
            Evaluate the function
            @param x: x-value
            @return: function value
        """
        return  self.params['A'] + x *self.params['B']
    
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: (Line value)
        """
        if x.__class__.__name__ == 'list':
            return self._line(x[0]*math.cos(x[1]))*self._line(x[0]*math.sin(x[1]))
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._line(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: Line value
        """
        if x.__class__.__name__ == 'list':
            return self._line(x[1])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._line(x)
        
    def evalDistribution(self, qdist):
        """
        Evaluate a distribution of q-values.
        
        * For 1D, a numpy array is expected as input:
        
            evalDistribution(q)
            
        where q is a numpy array.
        
        
        * For 2D, a list of numpy arrays are expected: [qx_prime,qy_prime],
          where 1D arrays,
                
        :param qdist: ndarray of scalar q-values or list [qx,qy] 
                    where qx,qy are 1D ndarrays 
        
        """
        if qdist.__class__.__name__ == 'list':
            # Check whether we have a list of ndarrays [qx,qy]
            if len(qdist)!=2 or \
                qdist[0].__class__.__name__ != 'ndarray' or \
                qdist[1].__class__.__name__ != 'ndarray':
                    raise RuntimeError, "evalDistribution expects a list of 2 ndarrays"
                
            # Extract qx and qy for code clarity
            qx = qdist[0]
            qy = qdist[1]
            #For 2D, Z = A + B * Y, 
            # so that it keeps its linearity in y-direction.
            # calculate q_r component for 2D isotropic
            q =  qy
            # vectorize the model function runXY
            v_model = numpy.vectorize(self.runXY,otypes=[float])
            # calculate the scattering
            iq_array = v_model(q)

            return iq_array
                
        elif qdist.__class__.__name__ == 'ndarray':
                # We have a simple 1D distribution of q-values
                v_model = numpy.vectorize(self.runXY,otypes=[float])
                iq_array = v_model(qdist)

                return iq_array
            
        else:
            mesg = "evalDistribution is expecting an ndarray of scalar q-values"
            mesg += " or a list [qx,qy] where qx,qy are 2D ndarrays."
            raise RuntimeError, mesg
        
    
   

if __name__ == "__main__": 
    l = Line()
    print "hello"
       
# End of file
