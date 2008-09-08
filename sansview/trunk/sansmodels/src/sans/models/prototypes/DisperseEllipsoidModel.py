#!/usr/bin/env python
""" Provide functionality for a C extension model


    @author: Mathieu Doucet / UTK
    @contact: mathieu.doucet@nist.gov
"""

from sans.models.EllipsoidModel import EllipsoidModel
from sans.models.DisperseModel import DisperseModel
import copy    
    
class DisperseEllipsoidModel(EllipsoidModel):
    """ Class that evaluates a DisperseEllipsoidModel model. 
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        EllipsoidModel.__init__(self)
        self.params['sigma_phi'] = 0.0
        self.params['sigma_theta'] = 0.0
        self.params['n_pts'] = 20
        
        
        ## Name of the model
        self.name = "DisperseEllipsoidModel"
   
    def clone(self):
        """ Return a identical copy of self """
        obj = DisperseEllipsoidModel()
        obj.params = copy.deepcopy(self.params)
        return obj   
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q, or [q,phi]
            @return: scattering function P(q)
        """
        model = EllipsoidModel()
        model.params = copy.deepcopy(self.params)
        #d = Disperser(model, ["cyl_phi", "cyl_theta"], 
		#				  [self.params['sigma_phi'], self.params['sigma_theta']])
        d = DisperseModel(model, ["axis_phi", "axis_theta"], 
					  [self.params['sigma_phi'], self.params['sigma_theta']])
        d.params['n_pts'] = self.params['n_pts']
        return d.run(x)
   
# End of file
