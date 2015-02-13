
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#
#If you use DANSE applications to do scientific research that leads to
#publication, we ask that you acknowledge the use of the software with the
#following sentence:
#
#"This work benefited from DANSE software developed under NSF award DMR-0520547."
#
#copyright 2008, University of Tennessee
################################################################################

"""
Class definitions for python dispersion model for 
model parameters. These classes are bridges to the C++
dispersion object.

The ArrayDispersion class takes in numpy arrays only.

Usage:
These classes can be used to set the dispersion model of a SAS model
parameter:

    cyl = CylinderModel()
    cyl.set_dispersion('radius', GaussianDispersion())


After the dispersion model is set, you can access it's
parameter through the dispersion dictionary:

    cyl.dispersion['radius']['width'] = 5.0

:TODO: For backward compatibility, the model parameters are still kept in
    a dictionary. The next iteration of refactoring work should involve moving
    away from value-based parameters to object-based parameter. We want to
    store parameters as objects so that we can unify the 'params' and 'dispersion'
    dictionaries into a single dictionary of parameter objects that hold the
    complete information about the parameter (units, limits, dispersion model, etc...).  

    
"""
import sas_extension.c_models as c_models 



class DispersionModel:
    """
    Python bridge class for a basic dispersion model 
    class with a constant parameter value distribution
    """
    def __init__(self):
        self.cdisp = c_models.new_dispersion_model()
        
    def set_weights(self, values, weights):
        """
        Set the weights of an array dispersion
        """
        message = "set_weights is not available for DispersionModel.\n"
        message += "  Solution: Use an ArrayDispersion object"
        raise "RuntimeError", message
        
class GaussianDispersion(DispersionModel):
    """
    Python bridge class for a dispersion model based 
    on a Gaussian distribution.
    """
    def __init__(self):
        self.cdisp = c_models.new_gaussian_model()
        
    def set_weights(self, values, weights):
        """
            Set the weights of an array dispersion
        """
        message = "set_weights is not available for GaussianDispersion.\n"
        message += "  Solution: Use an ArrayDispersion object"
        raise "RuntimeError", message
        
class RectangleDispersion(DispersionModel):
    """
    Python bridge class for a dispersion model based 
    on a Gaussian distribution.
    """
    def __init__(self):
        self.cdisp = c_models.new_rectangle_model()
        
    def set_weights(self, values, weights):
        """
            Set the weights of an array dispersion
        """
        message = "set_weights is not available for GaussianDispersion.\n"
        message += "  Solution: Use an ArrayDispersion object"
        raise "RuntimeError", message 
    
class SchulzDispersion(DispersionModel):
    """
        Python bridge class for a dispersion model based 
        on a Schulz distribution.
    """
    def __init__(self):
        """
        """
        self.cdisp = c_models.new_schulz_model()
        
    def set_weights(self, values, weights):
        """
        Set the weights of an array dispersion
        """
        message = "set_weights is not available for SchulzDispersion.\n"
        message += "  Solution: Use an ArrayDispersion object"
        raise "RuntimeError", message
    
class LogNormalDispersion(DispersionModel):
    """
    Python bridge class for a dispersion model based 
    on a Log Normal distribution.
    """
    def __init__(self):
        self.cdisp = c_models.new_lognormal_model()
        
    def set_weights(self, values, weights):
        """
        Set the weights of an array dispersion
        """
        message = "set_weights is not available for LogNormalDispersion.\n"
        message += "  Solution: Use an ArrayDispersion object"
        raise "RuntimeError", message
        
class ArrayDispersion(DispersionModel):
    """
    Python bridge class for a dispersion model based on arrays.
    The user has to set a weight distribution that
    will be used in the averaging the model parameter
    it is applied to. 
    """
    def __init__(self):
        self.cdisp = c_models.new_array_model()
        
    def set_weights(self, values, weights):
        """
        Set the weights of an array dispersion
        Only accept numpy arrays.
        
        :param values: numpy array of values
        :param weights: numpy array of weights for each value entry
        
        """
        if len(values) != len(weights):
            raise ValueError, "ArrayDispersion.set_weights: \
            given arrays are of different lengths"
        
        c_models.set_dispersion_weights(self.cdisp, values, weights)
        
models = {"gaussian":GaussianDispersion,  "rectangula":RectangleDispersion,
          "array":ArrayDispersion, "schulz":SchulzDispersion, 
          "lognormal":LogNormalDispersion}       
        