#!/usr/bin/env python
""" Provide functionality for a C extension model


    @author: Mathieu Doucet / UTK
    @contact: mathieu.doucet@nist.gov
"""

from sans.models.CylinderModel import CylinderModel
from sans_extension.c_models import Disperser
from sans.models.DisperseModel import DisperseModel
import copy    
    
class DisperseCylinderModel(CylinderModel):
    """ Class that evaluates a SmearCylinderModel model. 
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        CylinderModel.__init__(self)
        self.params['sigma_phi'] = 0.0
        self.params['sigma_theta'] = 0.0
        self.params['n_pts'] = 20
        
        
        ## Name of the model
        self.name = "DisperseCylinderModel"
   
    def clone(self):
        """ Return a identical copy of self """
        obj = DisperseCylinderModel()
        obj.params = copy.deepcopy(self.params)
        return obj   
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q, or [q,phi]
            @return: scattering function P(q)
        """
        model = CylinderModel()
        model.params = copy.deepcopy(self.params)
        #d = Disperser(model, ["cyl_phi", "cyl_theta"], 
		#				  [self.params['sigma_phi'], self.params['sigma_theta']])
        d = DisperseModel(model, ["cyl_phi", "cyl_theta"], 
					  [self.params['sigma_phi'], self.params['sigma_theta']])
        d.params['n_pts'] = self.params['n_pts']
        return d.run(x)
   
# End of file
