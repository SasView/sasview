"""
    Unit tests for specific models
    @author: Gervaise Alina / UTK
"""

import unittest, numpy,math

from sans.models.MultiplicationModel import MultiplicationModel
from sans.models.SphereModel import SphereModel
from sans.models.SquareWellStructure import SquareWellStructure
      
class TestDisperser(unittest.TestCase):
    """ Unit tests for sphere model * SquareWellStructure"""
    model1= SphereModel()
    model2= SquareWellStructure()
    model3= MultiplicationModel(model1, model2)
    details={}
    details['scale'] = ['', None, None]
    details['radius'] = ['A', None, None]
    details['contrast'] = ['A-2', None, None]
    details['background'] = ['cm-1', None, None]
    details['volfraction'] = ['', None, None]
    details['welldepth'] = ['kT', None, None]
    details['wellwidth'] = ['', None, None]
    
    ## fittable parameters
    fixed=[]
    fixed=['radius.width']
    def testMultiplicationModel(self):
        """ Test Multiplication  sphere with SquareWellStructure"""
        ## test details dictionary
        self.assertEqual(self.model3.details, self.details)
        
        ## test parameters list
        list3= self.model3.getParamList()
        for item in self.model1.getParamList():
            self.assert_(item in list3)
        for item in self.model2.getParamList():
            self.assert_(item in list3)
            
        ## test set value for parameters and get paramaters
        self.model3.setParam("scale", 15)
        self.assertEqual(self.model3.getParam("scale"), 15)
        self.model3.setParam("radius", 20)
        self.assertEqual(self.model3.getParam("radius"), 20)
        self.model3.setParam("radius.width", 15)
        self.assertEqual(self.model3.getParam("radius.width"), 15)
        
        ## Dispersity 
        list3= self.model3.getDispParamList()
        self.assertEqual(list3, ['radius.npts', 'radius.nsigmas', 'radius.width'])
        
        from sans.models.dispersion_models import ArrayDispersion
        disp_th = ArrayDispersion()
        
        values_th = numpy.zeros(100)
        weights   = numpy.zeros(100)
        for i in range(100):
            values_th[i]=(math.pi/99.0*i)
            weights[i]=(1.0)
    
        disp_th.set_weights(values_th, weights)
        
        self.model3.set_dispersion('radius', disp_th)
        
        val_1d = self.model3.run(math.sqrt(0.0002))
        val_2d = self.model3.runXY([0.01,0.01]) 
        
        self.assertTrue(math.fabs(val_1d-val_2d)/val_1d < 0.02)
        model4= self.model3.clone()
        self.assertEqual(model4.getParam("radius"), 20)
        
if __name__ == '__main__':
    unittest.main()