"""
    Unit tests for specific models
    @author: JHJ Cho / UTK
"""
#This test replaces the older utests for multiplicationModel. Aug. 31, 2009. JC
import unittest, numpy,math
### P*S with sphere model    
class TestsphereSuareW(unittest.TestCase):
    """ 
        Unit tests for SphereModel(Q) * SquareWellStructure(Q)
    """
    def setUp(self):
        from sas.models.SphereModel import SphereModel
        from sas.models.SquareWellStructure import SquareWellStructure
        from sas.models.DiamCylFunc import DiamCylFunc
        from sas.models.MultiplicationModel import MultiplicationModel

        self.model = SphereModel()
        self.model2 = SquareWellStructure()
        self.model3 = MultiplicationModel(self.model, self.model2)  
        self.modelD = DiamCylFunc() 

    #Radius of model1.calculate_ER should be equal to the output/2 of DiamFunctions
    def test_multplication_radius(self):
        """
            test multiplication model (check the effective radius & the output
             of the multiplication)
        """
        self.model.setParam("radius", 60)
        modelDrun = 60
        self.model2.setParam("volfraction", 0.2)
        self.model2.setParam("effect_radius", modelDrun )
        
        #Compare new method with old method         
        self.assertEqual(self.model3.run(0.1), self.model.run(0.1)*self.model2.run(0.1))
        
        #Compare radius from two different calculations. Note: modelD.run(0.0) is DIAMETER
        self.assertEqual(self.model.calculate_ER(), modelDrun)
        
        
    def testMultiplicationParam(self):
        """ Test Multiplication  (check the setparameters and the run & runXY w/ array dispersion)"""
        ## test details dictionary

        ## test parameters list
        list3= self.model3.getParamList()

        for item in self.model.getParamList():
            if not 'scale' in item: 
                self.assert_(item in list3)
        for item in self.model2.getParamList():
            #model3 parameters should not include effect_radius*
            if not 'effect_radius' in item:  
                self.assert_(item in list3)
            
        ## test set value for parameters and get paramaters
        self.model3.setParam("scale_factor", 15)
        self.assertEqual(self.model3.getParam("scale_factor"), 15)
        self.model3.setParam("radius", 20)
        self.assertEqual(self.model3.getParam("radius"), 20)
        self.model3.setParam("radius.width", 15)
        self.assertEqual(self.model3.getParam("radius.width"), 15)
        self.model3.setParam("scale_factor", 15)
        self.assertEqual(self.model3.getParam("scale_factor"), 15)
        self.assertEqual(self.model3.getParam("volfraction"), self.model.getParam("scale"))
        
        ## Dispersity 
        list3= self.model3.getDispParamList()
        self.assertEqual(list3, ['radius.npts', 'radius.nsigmas', 'radius.width'])
        
        from sas.models.dispersion_models import ArrayDispersion
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
      
class TestsphereHardS(unittest.TestCase):
    """ 
        Unit tests for SphereModel(Q) * HardsphereStructure(Q)
    """
    def setUp(self):
        from sas.models.SphereModel import SphereModel
        from sas.models.HardsphereStructure import HardsphereStructure
        from sas.models.DiamCylFunc import DiamCylFunc
        from sas.models.MultiplicationModel import MultiplicationModel

        self.model = SphereModel()
        self.model2 = HardsphereStructure()
        self.model3 = MultiplicationModel(self.model, self.model2)  
        self.modelD = DiamCylFunc() 

    #Radius of model1.calculate_ER should be equal to the output/2 of DiamFunctions
    def test_multplication_radius(self):
        """
            test multiplication model (check the effective radius & the output
             of the multiplication)
        """
        self.model.setParam("radius", 60)
        modelDrun = 60
        self.model2.setParam("volfraction", 0.2)
        self.model2.setParam("effect_radius", modelDrun )
        
        #Compare new method with old method         
        self.assertEqual(self.model3.run(0.1), self.model.run(0.1)*self.model2.run(0.1))
        
        #Compare radius from two different calculations. Note: modelD.run(0.0) is DIAMETER
        self.assertEqual(self.model.calculate_ER(), modelDrun)
        
        
    def testMultiplicationParam(self):
        """ Test Multiplication  (check the parameters)"""
        ## test details dictionary

        ## test parameters list
        list3= self.model3.getParamList()

        for item in self.model.getParamList():
            if not 'scale' in item: 
                self.assert_(item in list3)
        for item in self.model2.getParamList():
            #model3 parameters should not include effect_radius*
            if not 'effect_radius' in item:  
                self.assert_(item in list3)
            
        ## test set value for parameters and get paramaters
        self.model3.setParam("scale_factor", 15)
        self.assertEqual(self.model3.getParam("scale_factor"), 15)
        self.model3.setParam("radius", 20)
        self.assertEqual(self.model3.getParam("radius"), 20)
        self.model3.setParam("radius.width", 15)
        self.assertEqual(self.model3.getParam("radius.width"), 15)
        self.model3.setParam("scale_factor", 15)
        self.assertEqual(self.model3.getParam("scale_factor"), 15)
        self.assertEqual(self.model3.getParam("volfraction"), self.model.getParam("scale"))
        
        ## Dispersity 
        list3= self.model3.getDispParamList()
        self.assertEqual(list3, ['radius.npts', 'radius.nsigmas', 'radius.width'])
        
        from sas.models.dispersion_models import ArrayDispersion
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
class TestsphereSHS(unittest.TestCase):
    """ 
        Unit tests for SphereModel(Q) * StickyHSStructure(Q)
    """
    def setUp(self):
        from sas.models.SphereModel import SphereModel
        from sas.models.StickyHSStructure import StickyHSStructure
        from sas.models.DiamCylFunc import DiamCylFunc
        from sas.models.MultiplicationModel import MultiplicationModel

        self.model = SphereModel()
        self.model2 = StickyHSStructure()
        self.model3 = MultiplicationModel(self.model, self.model2)  
        self.modelD = DiamCylFunc() 

    #Radius of model1.calculate_ER should be equal to the output/2 of DiamFunctions
    def test_multplication_radius(self):
        """
            test multiplication model (check the effective radius & the output
             of the multiplication)
        """
        self.model.setParam("radius", 60)
        modelDrun = 60
        self.model2.setParam("volfraction", 0.2)
        self.model2.setParam("effect_radius", modelDrun )
        
        #Compare new method with old method         
        self.assertEqual(self.model3.run(0.1), self.model.run(0.1)*self.model2.run(0.1))
        
        #Compare radius from two different calculations. Note: modelD.run(0.0) is DIAMETER
        self.assertEqual(self.model.calculate_ER(), modelDrun)
        
        
    def testMultiplicationParam(self):
        """ Test Multiplication  (check the parameters)"""
        ## test details dictionary

        ## test parameters list
        list3= self.model3.getParamList()

        for item in self.model.getParamList():
            if not 'scale' in item: 
                self.assert_(item in list3)
        for item in self.model2.getParamList():
            #model3 parameters should not include effect_radius*
            if not 'effect_radius' in item:  
                self.assert_(item in list3)
            
        ## test set value for parameters and get paramaters
        self.model3.setParam("scale_factor", 15)
        self.assertEqual(self.model3.getParam("scale_factor"), 15)
        self.model3.setParam("radius", 20)
        self.assertEqual(self.model3.getParam("radius"), 20)
        self.model3.setParam("radius.width", 15)
        self.assertEqual(self.model3.getParam("radius.width"), 15)
        self.model3.setParam("scale_factor", 15)
        self.assertEqual(self.model3.getParam("scale_factor"), 15)
        self.assertEqual(self.model3.getParam("volfraction"), self.model.getParam("scale"))
        
        ## Dispersity 
        list3= self.model3.getDispParamList()
        self.assertEqual(list3, ['radius.npts', 'radius.nsigmas', 'radius.width'])
        
        from sas.models.dispersion_models import ArrayDispersion
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
        
class TestsphereHayterM(unittest.TestCase):
    """ 
        Unit tests for SphereModel(Q) * HayterMSAStructure(Q)
    """
    def setUp(self):
        from sas.models.SphereModel import SphereModel
        from sas.models.HayterMSAStructure import HayterMSAStructure
        from sas.models.DiamCylFunc import DiamCylFunc
        from sas.models.MultiplicationModel import MultiplicationModel

        self.model = SphereModel()
        self.model2 = HayterMSAStructure()
        self.model3 = MultiplicationModel(self.model, self.model2)  
        self.modelD = DiamCylFunc() 

    #Radius of model1.calculate_ER should be equal to the output/2 of DiamFunctions
    def test_multplication_radius(self):
        """
            test multiplication model (check the effective radius & the output
             of the multiplication)
        """
        self.model.setParam("radius", 60)
        modelDrun = 60
        self.model2.setParam("volfraction", 0.2)
        self.model2.setParam("effect_radius", modelDrun )
        
        #Compare new method with old method         
        self.assertEqual(self.model3.run(0.1), self.model.run(0.1)*self.model2.run(0.1))
        
        #Compare radius from two different calculations. Note: modelD.run(0.0) is DIAMETER
        self.assertEqual(self.model.calculate_ER(), modelDrun)
        
        
    def testMultiplicationParam(self):
        """ Test Multiplication  (check the parameters)"""
        ## test details dictionary

        ## test parameters list
        list3= self.model3.getParamList()

        for item in self.model.getParamList():
            if not 'scale' in item: 
                self.assert_(item in list3)
        for item in self.model2.getParamList():
            #model3 parameters should not include effect_radius*
            if not 'effect_radius' in item:  
                self.assert_(item in list3)
            
        ## test set value for parameters and get paramaters
        self.model3.setParam("scale_factor", 15)
        self.assertEqual(self.model3.getParam("scale_factor"), 15)
        self.model3.setParam("radius", 20)
        self.assertEqual(self.model3.getParam("radius"), 20)
        self.model3.setParam("radius.width", 15)
        self.assertEqual(self.model3.getParam("radius.width"), 15)
        self.model3.setParam("scale_factor", 15)
        self.assertEqual(self.model3.getParam("scale_factor"), 15)
        self.assertEqual(self.model3.getParam("volfraction"), self.model.getParam("scale"))
        
        ## Dispersity 
        list3= self.model3.getDispParamList()
        self.assertEqual(list3, ['radius.npts', 'radius.nsigmas', 'radius.width'])
        
        from sas.models.dispersion_models import ArrayDispersion
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
          
### P*S with cylinder model
class TestcylinderSuareW(unittest.TestCase):
    """ 
        Unit tests for CylinderModel(Q) * SquareWellStructure(Q)
    """
    def setUp(self):
        from sas.models.CylinderModel import CylinderModel
        from sas.models.SquareWellStructure import SquareWellStructure
        from sas.models.DiamCylFunc import DiamCylFunc
        from sas.models.MultiplicationModel import MultiplicationModel

        self.model = CylinderModel()
        self.model2 = SquareWellStructure()
        self.model3 = MultiplicationModel(self.model, self.model2)  
        self.modelD = DiamCylFunc() 

    #Radius of model1.calculate_ER should be equal to the output/2 of DiamFunctions
    def test_multplication_radius(self):
        """
            test multiplication model (check the effective radius & the output
             of the multiplication)
        """
        self.model.setParam("radius", 60)
        self.modelD.setParam("radius", 60)
        modelDrun = self.modelD.run(0.1)/2
        self.model2.setParam("volfraction", 0.2)
        self.model2.setParam("effect_radius", modelDrun)
        
        #Compare new method with old method         
        self.assertEqual(self.model3.run(0.1), self.model.run(0.1)*self.model2.run(0.1))
        
        #Compare radius from two different calculations. Note: modelD.run(0.0) is DIAMETER
        self.assertEqual(self.model.calculate_ER(), modelDrun)
        
        
    def testMultiplicationParam(self):
        """ Test Multiplication  (check the setparameters and the run & runXY w/ array dispersion)"""
        ## test details dictionary

        ## test parameters list
        list3= self.model3.getParamList()

        for item in self.model.getParamList():
            if not 'scale' in item: 
                self.assert_(item in list3)
        for item in self.model2.getParamList():
            #model3 parameters should not include effect_radius*
            if not 'effect_radius' in item:  
                self.assert_(item in list3)
            
        ## test set value for parameters and get paramaters
        self.model3.setParam("scale_factor", 15)
        self.assertEqual(self.model3.getParam("scale_factor"), 15)
        self.model3.setParam("radius", 20)
        self.assertEqual(self.model3.getParam("radius"), 20)
        self.model3.setParam("radius.width", 15)
        self.assertEqual(self.model3.getParam("radius.width"), 15)
        self.model3.setParam("scale_factor", 15)
        self.assertEqual(self.model3.getParam("scale_factor"), 15)
        self.assertEqual(self.model3.getParam("volfraction"), self.model.getParam("scale"))
        
        ## Dispersity 
        list3= self.model3.getDispParamList()
        self.assertEqual(list3, ['radius.npts', 'radius.nsigmas', 'radius.width', 'length.npts', \
         'length.nsigmas', 'length.width', 'cyl_theta.npts', 'cyl_theta.nsigmas', 'cyl_theta.width',\
          'cyl_phi.npts', 'cyl_phi.nsigmas', 'cyl_phi.width'])
        
        from sas.models.dispersion_models import ArrayDispersion
        disp_th = ArrayDispersion()
        
        values_th = numpy.zeros(100)
        weights   = numpy.zeros(100)
        for i in range(100):
            values_th[i]=(math.pi/99.0*i)
            weights[i]=(1.0)
    
        disp_th.set_weights(values_th, weights)
        
        self.model3.set_dispersion('radius', disp_th)
        
        model4= self.model3.clone()
        self.assertEqual(model4.getParam("radius"), 20)
      
class TestcylinderHardS(unittest.TestCase):
    """ 
        Unit tests for CylinderModel(Q) * HardsphereStructure(Q)
    """
    def setUp(self):
        from sas.models.CylinderModel import CylinderModel
        from sas.models.HardsphereStructure import HardsphereStructure
        from sas.models.DiamCylFunc import DiamCylFunc
        from sas.models.MultiplicationModel import MultiplicationModel

        self.model = CylinderModel()
        self.model2 = HardsphereStructure()
        self.model3 = MultiplicationModel(self.model, self.model2)  
        self.modelD = DiamCylFunc() 

    #Radius of model1.calculate_ER should be equal to the output/2 of DiamFunctions
    def test_multplication_radius(self):
        """
            test multiplication model (check the effective radius & the output
             of the multiplication)
        """
        self.model.setParam("radius", 60)
        self.modelD.setParam("radius", 60)
        modelDrun = self.modelD.run(0.1)/2
        self.model2.setParam("volfraction", 0.2)
        self.model2.setParam("effect_radius", modelDrun )
        
        #Compare new method with old method         
        self.assertEqual(self.model3.run(0.1), self.model.run(0.1)*self.model2.run(0.1))
        
        #Compare radius from two different calculations. Note: modelD.run(0.0) is DIAMETER
        self.assertEqual(self.model.calculate_ER(), modelDrun)
        
        
    def testMultiplicationParam(self):
        """ Test Multiplication """
        ## test details dictionary

        ## test parameters list
        list3= self.model3.getParamList()

        for item in self.model.getParamList():
            #model3 parameters should not include scale*
            if not 'scale' in item: 
                self.assert_(item in list3)
        for item in self.model2.getParamList():
            #model3 parameters should not include effect_radius*
            if not 'effect_radius' in item:  
                self.assert_(item in list3)
            
        ## test set value for parameters and get paramaters
        #self.model3.setParam("scale", 15)
        #self.assertEqual(self.model3.getParam("scale"), 15)
        self.model3.setParam("scale_factor", 0.1)
        self.assertEqual(self.model3.getParam("scale_factor"), 0.1)
        self.model3.setParam("radius", 20)
        self.assertEqual(self.model3.getParam("radius"), 20)
        self.model3.setParam("radius.width", 15)
        self.assertEqual(self.model3.getParam("radius.width"), 15)
        self.model3.setParam("scale_factor", 15)
        self.assertEqual(self.model3.getParam("scale_factor"), 15)
        self.assertEqual(self.model3.getParam("volfraction"), self.model.getParam("scale"))
        
        ## Dispersity 
        list3= self.model3.getDispParamList()
        self.assertEqual(list3, ['radius.npts', 'radius.nsigmas', 'radius.width', 'length.npts', \
         'length.nsigmas', 'length.width', 'cyl_theta.npts', 'cyl_theta.nsigmas', 'cyl_theta.width',\
          'cyl_phi.npts', 'cyl_phi.nsigmas', 'cyl_phi.width'])
        
        from sas.models.dispersion_models import ArrayDispersion
        disp_th = ArrayDispersion()
        
        values_th = numpy.zeros(100)
        weights   = numpy.zeros(100)
        for i in range(100):
            values_th[i]=(math.pi/99.0*i)
            weights[i]=(1.0)
    
        disp_th.set_weights(values_th, weights)
        
        self.model3.set_dispersion('radius', disp_th)
        

        model4= self.model3.clone()
        self.assertEqual(model4.getParam("radius"), 20)
class TestcylinderSHS(unittest.TestCase):
    """ 
        Unit tests for SphereModel(Q) * StickyHSStructure(Q)
    """
    def setUp(self):
        from sas.models.CylinderModel import CylinderModel
        from sas.models.StickyHSStructure import StickyHSStructure
        from sas.models.DiamCylFunc import DiamCylFunc
        from sas.models.MultiplicationModel import MultiplicationModel

        self.model = CylinderModel()
        self.model2 = StickyHSStructure()
        self.model3 = MultiplicationModel(self.model, self.model2)  
        self.modelD = DiamCylFunc()

    #Radius of model1.calculate_ER should be equal to the output/2 of DiamFunctions
    def test_multplication_radius(self):
        """
            test multiplication model (check the effective radius & the output
             of the multiplication)
        """
        self.model.setParam("radius", 60)
        self.modelD.setParam("radius", 60)
        modelDrun = self.modelD.run(0.1)/2
        self.model2.setParam("volfraction", 0.2)
        self.model2.setParam("effect_radius", modelDrun )
        
        #Compare new method with old method         
        self.assertEqual(self.model3.run(0.1), self.model.run(0.1)*self.model2.run(0.1))
        
        #Compare radius from two different calculations. Note: modelD.run(0.0) is DIAMETER
        self.assertEqual(self.model.calculate_ER(), modelDrun)
        
        
    def testMultiplicationParam(self):
        """ Test Multiplication  (check the parameters)"""
        ## test details dictionary

        ## test parameters list
        list3= self.model3.getParamList()

        for item in self.model.getParamList():
            if not 'scale' in item: 
                self.assert_(item in list3)
        for item in self.model2.getParamList():
            #model3 parameters should not include effect_radius*
            if not 'effect_radius' in item:  
                self.assert_(item in list3)
            
        ## test set value for parameters and get paramaters
        self.model3.setParam("scale_factor", 15)
        self.assertEqual(self.model3.getParam("scale_factor"), 15)
        self.model3.setParam("radius", 20)
        self.assertEqual(self.model3.getParam("radius"), 20)
        self.model3.setParam("radius.width", 15)
        self.assertEqual(self.model3.getParam("radius.width"), 15)
        self.model3.setParam("scale_factor", 15)
        self.assertEqual(self.model3.getParam("scale_factor"), 15)
        self.assertEqual(self.model3.getParam("volfraction"), self.model.getParam("scale"))
        
        ## Dispersity 
        list3= self.model3.getDispParamList()
        self.assertEqual(list3, ['radius.npts', 'radius.nsigmas', 'radius.width', 'length.npts', \
         'length.nsigmas', 'length.width', 'cyl_theta.npts', 'cyl_theta.nsigmas', 'cyl_theta.width',\
          'cyl_phi.npts', 'cyl_phi.nsigmas', 'cyl_phi.width'])
        
        from sas.models.dispersion_models import ArrayDispersion
        disp_th = ArrayDispersion()
        
        values_th = numpy.zeros(100)
        weights   = numpy.zeros(100)
        for i in range(100):
            values_th[i]=(math.pi/99.0*i)
            weights[i]=(1.0)
    
        disp_th.set_weights(values_th, weights)
        
        self.model3.set_dispersion('radius', disp_th)
        
        model4= self.model3.clone()
        self.assertEqual(model4.getParam("radius"), 20)
        
class TestcylinderHayterM(unittest.TestCase):
    """ 
        Unit tests for CylinderModel(Q) * HayterMSAStructure(Q)
    """
    def setUp(self):
        from sas.models.CylinderModel import CylinderModel
        from sas.models.HayterMSAStructure import HayterMSAStructure
        from sas.models.DiamCylFunc import DiamCylFunc
        from sas.models.MultiplicationModel import MultiplicationModel

        self.model = CylinderModel()
        self.model2 = HayterMSAStructure()
        self.model3 = MultiplicationModel(self.model, self.model2)  
        self.modelD = DiamCylFunc()

    #Radius of model1.calculate_ER should be equal to the output/2 of DiamFunctions
    def test_multplication_radius(self):
        """
            test multiplication model (check the effective radius & the output
             of the multiplication)
        """
        self.model.setParam("radius", 60)
        self.modelD.setParam("radius", 60)
        modelDrun = self.modelD.run(0.1)/2
        self.model2.setParam("volfraction", 0.2)
        self.model2.setParam("effect_radius", modelDrun )
        
        #Compare new method with old method         
        self.assertEqual(self.model3.run(0.1), self.model.run(0.1)*self.model2.run(0.1))
        
        #Compare radius from two different calculations. Note: modelD.run(0.0) is DIAMETER
        self.assertEqual(self.model.calculate_ER(), modelDrun)
        
        
    def testMultiplicationParam(self):
        """ Test Multiplication  (check the parameters)"""
        ## test details dictionary

        ## test parameters list
        list3= self.model3.getParamList()

        for item in self.model.getParamList():
            if not 'scale' in item:  
                self.assert_(item in list3)
        for item in self.model2.getParamList():
            #model3 parameters should not include effect_radius*
            if not 'effect_radius' in item:  
                self.assert_(item in list3)
            
        ## test set value for parameters and get paramaters
        #self.model3.setParam("scale", 15)
        #self.assertEqual(self.model3.getParam("scale"), 15)
        self.model3.setParam("scale_factor", 15)
        self.assertEqual(self.model3.getParam("scale_factor"), 15)
        self.model3.setParam("radius", 20)
        self.assertEqual(self.model3.getParam("radius"), 20)
        self.model3.setParam("radius.width", 15)
        self.assertEqual(self.model3.getParam("radius.width"), 15)
        self.model3.setParam("scale_factor", 15)
        self.assertEqual(self.model3.getParam("scale_factor"), 15)
        self.assertEqual(self.model3.getParam("volfraction"), self.model.getParam("scale"))
        
        ## Dispersity 
        list3= self.model3.getDispParamList()
        self.assertEqual(list3, ['radius.npts', 'radius.nsigmas', 'radius.width', 'length.npts', \
         'length.nsigmas', 'length.width', 'cyl_theta.npts', 'cyl_theta.nsigmas', 'cyl_theta.width',\
          'cyl_phi.npts', 'cyl_phi.nsigmas', 'cyl_phi.width'])
        
        from sas.models.dispersion_models import ArrayDispersion
        disp_th = ArrayDispersion()
        
        values_th = numpy.zeros(100)
        weights   = numpy.zeros(100)
        for i in range(100):
            values_th[i]=(math.pi/99.0*i)
            weights[i]=(1.0)
    
        disp_th.set_weights(values_th, weights)
        
        self.model3.set_dispersion('radius', disp_th)        

        model4= self.model3.clone()
        self.assertEqual(model4.getParam("radius"), 20)        
        
class TestGuinierHayterM(unittest.TestCase):
    """ 
        Unit tests for GuinierModel(Q) * HayterMSAStructure(Q)
    """
    def setUp(self):
        from sas.models.GuinierModel import GuinierModel
        from sas.models.HayterMSAStructure import HayterMSAStructure
        from sas.models.MultiplicationModel import MultiplicationModel

        self.model = GuinierModel()
        self.model2 = HayterMSAStructure()
        self.model3 = MultiplicationModel(self.model, self.model2)  

    #Radius of model1.calculate_ER should be equal to the output/2 of DiamFunctions
    def test_multplication_radius(self):
        """
            test multiplication model (check the effective radius & the output
             of the multiplication)
        """
        self.model.setParam("rg", 60)
        self.model.setParam("scale", 1)
        #Compare new method with old method         
        self.assertEqual(self.model3.run(0.1), self.model.run(0.1)*self.model2.run(0.1))
        
        #effective radius calculation is not implemented for this model. 
        self.assertEqual(self.model3.calculate_ER(), NotImplemented)       
        
class TestLamellarHayterM(unittest.TestCase):
    """ 
        Unit tests for LamellarModel(Q) * HayterMSAStructure(Q)
    """
    def setUp(self):
        from sas.models.LamellarModel import LamellarModel
        from sas.models.HayterMSAStructure import HayterMSAStructure
        from sas.models.MultiplicationModel import MultiplicationModel

        self.model = LamellarModel()
        self.model2 = HayterMSAStructure()
        self.model3 = MultiplicationModel(self.model, self.model2)  

    #Radius of model1.calculate_ER should Not be finite.
    def test_multplication_radius(self):
        """
            test multiplication model (check the effective radius & the output
             of the multiplication)
        """
        #Check run       
        self.assertFalse(numpy.isfinite(self.model3.run(0.1)))
        #check effective radius . 
        self.assertTrue(numpy.isfinite(self.model.calculate_ER()))      
                
if __name__ == '__main__':
    unittest.main()
