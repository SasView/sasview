
from sas.models.BaseComponent import BaseComponent
import math

class Smear:
    
    def __init__(self, model, param, sigma):
        """
            @param model: model to smear
            @param param: parameter to smear
            @param sigma: std deviations for parameter
        """

        
        ## Model to smear
        self.model = model
        ## Standard deviation of the smearing
        self.sigmas = sigma
        ## Parameter to smear
        self.params = param
        ## Nominal value of the smeared parameter
        self.centers = []
        ## Error on last evaluation
        self.error = 0.0
        ## Error flag
        self.doErrors = False
        for par in self.params:
            self.centers.append(self.model.getParam(par))
        
    def smearParam(self, id, x):
        """
            @param x: input value
        """
        # from random import random
        # If we exhausted the parameter array, simply evaluate
        # the model
        if id < len(self.params):
            #print "smearing", self.params[id]
            
            # Average over Gaussian distribution (2 sigmas)
            value_sum = 0.0
            gauss_sum = 0.0
            
            min_value = self.centers[id] - 2*self.sigmas[id]
            max_value = self.centers[id] + 2*self.sigmas[id]
            n_pts = 25
            step = (max_value - min_value)/(n_pts-1)
            #print min_value, max_value, step, max_value-min_value
            if step == 0.0:
                return self.smearParam(id+1,x)
            
            # Gaussian function used to weigh points
            gaussian = Gaussian()
            gaussian.setParam('sigma', self.sigmas[id])
            gaussian.setParam('mean', self.centers[id])
                    
            # Compute average
            prev_value = None
            error_sys = 0.0
            for i in range(n_pts):
                # Set the parameter value           
                value = min_value + i*step
                # value = random()*4.0*self.sigmas[id] + min_value
                # print value
                self.model.setParam(self.params[id], value)
                gauss_value = gaussian.run(value)
                #gauss_value = 1.0
                #if id==0: print value, gauss_value
                func_value, error_1 = self.smearParam(id+1, x)
                if self.doErrors:
                    if not prev_value == None:
                        error_sys += (func_value-prev_value)*(func_value-prev_value)/4.0
                    prev_value = func_value

                value_sum += gauss_value * func_value
                gauss_sum += gauss_value
                
            #print "Error", math.sqrt(error)
            return value_sum/gauss_sum, math.sqrt(error_sys)
        
        else:
            return self.model.run(x), 0.0
        
    def run(self, x):
        """
            @param x: input
        """
        
        # Go through the list of parameters
        n_par = len(self.params)
        
        # Check array lengths
        if not len(self.centers) == n_par or\
            not len(self.sigmas) == n_par:
            raise ValueError, "Incompatible array lengths"
        
        # Smear first parameters
        if n_par > 0:
            value, error = self.smearParam(0, x)
            self.error = error
            
            # Put back original values
            for i in range(len(self.centers)):
                self.model.setParam(self.params[i], self.centers[i])
            
            
            return value
        
class Gaussian(BaseComponent):
    """ Gaussian function """
    
    def __init__(self):
        """ Initialization """
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "Gaussian"
        ## Scale factor
        self.params['scale']  = 1.0
        ## Mean value
        self.params['mean']   = 0.0
        ## Standard deviation
        self.params['sigma']  = 1.0
        ## Internal log
        self.log = {}
        return
    
    def run(self, x=0):
        """ Evaluate the function 
            @param x: input q or [q,phi]
            @return: scattering function
        """
        if(type(x)==type([])):
            # vector input
            if(len(x)==2):
                return self.analytical_2D(x)
            else:
                raise ValueError, "Gaussian takes a scalar or a 2D point"
        else:
            return self.analytical_1D(x)

    def analytical_2D(self, x):
        """ Evaluate 2D model 
            @param x: input [q,phi]
            @return: scattering function
        """
        
        # 2D sphere is the same as 1D sphere
        return self.analytical_1D(x[0])

    def analytical_1D(self, x):
        """ Evaluate 1D model
            @param x: input q
            @return: scattering function
        """
        vary = x-self.params['mean']
        expo_value = -vary*vary/(2*self.params['sigma']*self.params['sigma'])
        value = self.params['scale'] *  math.exp(expo_value)
        
        return value
