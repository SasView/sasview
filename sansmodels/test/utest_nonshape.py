"""
    Unit tests for non shape based model (Task 8.2.1)
    These tests are part of the requirements
"""

import unittest, time, math
from scipy.special import erf,gammaln

# Disable "missing docstring" complaint
# pylint: disable-msg=C0111
# Disable "too many methods" complaint 
# pylint: disable-msg=R0904 
# Disable "could be a function" complaint 
# pylint: disable-msg=R0201

import scipy 
class TestGuinier(unittest.TestCase):
    """
        Unit tests for Guinier function
        
        F(x) = exp[ [A] + [B]*Q**2 ]
        
        The model has two parameters: A and B
    """
    def _func(self, a, b, x):
        return a*math.exp(-(b*x)**2/3.0)
    
    def setUp(self):
        from sans.models.GuinierModel import GuinierModel
        self.model= GuinierModel()
        
    def test1D(self):
        self.model.setParam('scale', 2.0)
        self.model.setParam('rg', 1.0)
        
        self.assertEqual(self.model.run(0.0), 2.0)
        self.assertEqual(self.model.run(2.0), 2.0*math.exp(-(1.0*2.0)**2/3.0))
        self.assertEqual(self.model.runXY(2.0), 2.0*math.exp(-(1.0*2.0)**2/3.0))
        
    def test2D(self):
        self.model.setParam('scale', 2.0)
        self.model.setParam('rg', 1.0)
        
        #value = self._func(2.0, 1.0, 1.0)*self._func(2.0, 1.0, 2.0)
        value = self._func(2.0, 1.0, math.sqrt(5.0))
        #self.assertEqual(self.model.runXY([0.0,0.0]), 2.0*2.0)
        self.assertEqual(self.model.runXY([0.0,0.0]), 2.0)
        self.assertEqual(self.model.runXY([1.0,2.0]), value)
        
    def test2Dphi(self):
        self.model.setParam('scale', 2.0)
        self.model.setParam('rg', 1.0)
        
        x = 1.0
        y = 2.0
        r = math.sqrt(x**2 + y**2)
        phi = math.atan2(y, x)
        
        #value = self._func(2.0, 1.0, x)*self._func(2.0, 1.0, y)
        value = self._func(2.0, 1.0, r)
        
        #self.assertEqual(self.model.run([r, phi]), value)
        self.assertAlmostEquals(self.model.run([r, phi]), value,1)
        
        
class TestPorod(unittest.TestCase):
    """
        Unit tests for Porod function
        
        F(x) = C/Q**4 
        
        The model has one parameter: C
    """
    def _func(self, c, x):
        return c/(x**4)
    
    def setUp(self):
        from sans.models.PorodModel import PorodModel
        self.model= PorodModel()
        self.model.setParam('scale', 2.0)        
        
    def test1D(self):
        value = self._func(2.0, 3.0)
        self.assertEqual(self.model.run(3.0), value)
        self.assertEqual(self.model.runXY(3.0), value)
        
    def test2D(self):
        #value = self._func(2.0, 1.0)*self._func(2.0, 2.0)
        value = self._func(2.0, math.sqrt(5.0))
        self.assertEqual(self.model.runXY([1.0,2.0]), value)
        
    def test2Dphi(self):
        x = 1.0
        y = 2.0
        r = math.sqrt(x**2 + y**2)
        phi = math.atan2(y, x)
        
        #value = self._func(2.0, 1.0)*self._func(2.0, 2.0)
        value = self._func(2.0, r)
        self.assertAlmostEquals(self.model.run([r, phi]), value,1)
        
class TestDebye(unittest.TestCase):
    """
        Unit tests for Debye function
        
        F(x) = 2( exp(-x)+x -1 )/x**2
        
        The model has three parameters: 
            Rg     =  radius of gyration
            scale  =  scale factor
            bkd    =  Constant background
    """
    def _func(self, Rg, scale, bkg, x):
        y = (Rg * x)**2
        return scale * (2*(math.exp(-y) + y -1)/y**2) + bkg
    
    def setUp(self):
        from sans.models.DebyeModel import DebyeModel
        self.model= DebyeModel()
        self.model.setParam('rg', 50.0)    
        self.model.setParam('scale',1.0) 
        self.model.setParam('background',0.001)   
        
    def test1D(self):
        value = self._func(50.0, 1.0, 0.001, 2.0)
        self.assertEqual(self.model.run(2.0), value)
        self.assertEqual(self.model.runXY(2.0), value)

        # User enter zero as a value of x, y= 1
        self.assertAlmostEqual(self.model.run(0.0), 1.00, 2)
        
    def test1D_clone(self):
        value = self._func(50.0, 1.0, 10.0, 2.0)
        self.model.setParam('background', 10.0)
        clone = self.model.clone()
        self.assertEqual(clone.run(2.0), value)
        self.assertEqual(clone.runXY(2.0), value)
        
        # User enter zero as a value of x
        # An exceptio is raised: No more exception
        #self.assertRaises(ZeroDivisionError, clone.run, 0.0)
        
    def test2D(self):
        #value = self._func(50.0, 1.0, 0.001, 1.0)*self._func(50.0, 1.0, 0.001, 2.0)
        value = self._func(50.0, 1.0, 0.001, math.sqrt(5.0))
        self.assertEqual(self.model.runXY([1.0,2.0]), value)
        
    def test2Dphi(self):
        x = 1.0
        y = 2.0
        r = math.sqrt(x**2 + y**2)
        phi = math.atan2(y, x)
        
        value = self._func(50.0, 1.0, 0.001, 1.0)*self._func(50.0, 1.0, 0.001, 2.0)
        self.assertAlmostEquals(self.model.run([r, phi]), value,1)
        
        
class TestLorentz(unittest.TestCase):
    """
        Unit tests for Lorentz function
        
         F(x) = scale/( 1 + (x*L)^2 ) + bkd
        
        The model has three parameters: 
            L     =  screen Length
            scale  =  scale factor
            bkd    =  incoherent background
    """
    def _func(self, I0 , L, bgd, qval):
        return I0/(1.0 + (qval*L)*(qval*L)) + bgd
    
    def setUp(self):
        from sans.models.LorentzModel import LorentzModel
        self.model= LorentzModel()
        
    def test1D(self):
        self.model.setParam('scale', 100.0)
        self.model.setParam('Length', 50.0)
        self.model.setParam('background', 1.0)
        
        self.assertEqual(self.model.run(0.0), 101.0)
        self.assertEqual(self.model.run(2.0), self._func(100.0, 50.0, 1.0, 2.0))
        self.assertEqual(self.model.runXY(2.0), self._func(100.0, 50.0, 1.0, 2.0))
        
    def test2D(self):
        self.model.setParam('scale', 100.0)
        self.model.setParam('Length', 50.0)
        self.model.setParam('background', 1.0)
        
        #value = self._func(100.0, 50.0, 1.0, 1.0)*self._func(100.0, 50.0, 1.0, 2.0)    
        value = self._func(100.0, 50.0, 1.0, math.sqrt(5.0))  
        self.assertEqual(self.model.runXY([1.0,2.0]), value)
        
    def test2Dphi(self):
        self.model.setParam('scale', 100.0)
        self.model.setParam('Length', 50.0)
        self.model.setParam('background', 1.0)
        
        x = 1.0
        y = 2.0
        r = math.sqrt(x**2 + y**2)
        phi = math.atan2(y, x)
        
        value = self._func(100.0, 50.0, 1.0, x)*self._func(100.0, 50.0, 1.0, y)
        self.assertAlmostEquals(self.model.run([r, phi]), value,1)
        
class TestDAB(unittest.TestCase):
    """
        Unit tests for DAB function
        
         F(x) = scale/( 1 + (x*L)^2 )^(2) + bkd
        
        The model has three parameters: 
            L      =  Correlation Length
            scale  =  scale factor
            bkd    =  incoherent background
    """
    def _func(self, Izero, range, incoh, qval):
        return Izero* pow(range,3)/pow((1.0 + (qval*range)*(qval*range)),2) + incoh
    
    def setUp(self):
        from sans.models.DABModel import DABModel
        self.model= DABModel()
        self.scale = 10.0
        self.length = 40.0
        self.back = 1.0
        
        self.model.setParam('scale', self.scale)
        self.model.setParam('length', self.length)
        self.model.setParam('background', self.back)
        
    def test1D(self):

        self.assertEqual(self.model.run(2.0), self._func(self.scale, self.length, self.back, 2.0))
        self.assertEqual(self.model.runXY(2.0), self._func(self.scale, self.length, self.back, 2.0))
        
    def test2D(self):
        #value = self._func(self.scale, self.length, self.back, 1.0)*self._func(self.scale, self.length, self.back, 2.0)    
        value = self._func(self.scale, self.length, self.back, math.sqrt(5.0))
        self.assertEqual(self.model.runXY([1.0,2.0]), value)
        
    def test2Dphi(self):
        x = 1.0
        y = 2.0
        r = math.sqrt(x**2 + y**2)
        phi = math.atan2(y, x)
        
        value = self._func(self.scale, self.length, self.back, x)*self._func(self.scale, self.length, self.back, y)
        self.assertAlmostEquals(self.model.run([x, y]), value,1)


class TestPowerLaw(unittest.TestCase):
    """
        Unit tests for PowerLaw function

        F(x) = scale* (x)^(m) + bkd
        
        The model has three parameters: 
            m     =  power
            scale  =  scale factor
            bkd    =  incoherent background
    """
    def _func(self, a, m, bgd, qval):
        return a*math.pow(qval,-m) + bgd
    
    
    def setUp(self):
        from sans.models.PowerLawModel import PowerLawModel
        self.model= PowerLawModel()
        
    def test1D(self):
        self.model.setParam('scale', math.exp(-6))
        self.model.setParam('m', 4.0)
        self.model.setParam('background', 1.0)
        
        #self.assertEqual(self.model.run(0.0), 1.0)
        self.assertEqual(self.model.run(2.0), self._func(math.exp(-6), 4.0, 1.0, 2.0))
        self.assertEqual(self.model.runXY(2.0), self._func(math.exp(-6), 4.0, 1.0, 2.0))
    
    def testlimit(self):
        self.model.setParam('scale', math.exp(-6))
        self.model.setParam('m', -4.0)
        self.model.setParam('background', 1.0)
        
        self.assertEqual(self.model.run(0.0), 1.0)
        
    def test2D(self):
        self.model.setParam('scale', math.exp(-6))
        self.model.setParam('m', 4.0)
        self.model.setParam('background', 1.0)
        
        #value = self._func(math.exp(-6), 4.0, 1.0, 1.0)\
        #*self._func(math.exp(-6), 4.0, 1.0, 2.0)    
        value = self._func(math.exp(-6), 4.0, 1.0, math.sqrt(5.0))
        
        self.assertEqual(self.model.runXY([1.0,2.0]), value)
        
    def test2Dphi(self):
        self.model.setParam('scale', math.exp(-6))
        self.model.setParam('m', 4.0)
        self.model.setParam('background', 1.0)
        
        x = 1.0
        y = 2.0
        r = math.sqrt(x**2 + y**2)
        phi = math.atan2(y, x)
        
        value = self._func(math.exp(-6), 4.0, 1.0, x)\
        *self._func(math.exp(-6), 4.0, 1.0, y)
        self.assertAlmostEquals(self.model.run([r, phi]), value,1)
                
class TestTeubnerStrey(unittest.TestCase):
    """
        Unit tests for PowerLaw function

        F(x) = 1/( scale + c1*(x)^(2)+  c2*(x)^(4)) + bkd
        
        The model has Four parameters: 
            scale  =  scale factor
            c1     =  constant
            c2     =  constant
            bkd    =  incoherent background
    """
    def _func(self, scale, c1, c2, bck, q):
        
        q2 = q*q;
        q4 = q2*q2;
    
        return 1.0/(scale + c1*q2+c2*q4) + bck
    
    def setUp(self):
        from sans.models.TeubnerStreyModel import TeubnerStreyModel
        self.model= TeubnerStreyModel()
        
    def test1D(self):
        
        self.model.setParam('c1', -30.0) 
        self.model.setParam('c2', 5000.0) 
        self.model.setParam('scale', 0.1)
        self.model.setParam('background', 0.1)
        #self.assertEqual(1/(math.sqrt(4)), math.pow(4,-1/2))
        #self.assertEqual(self.model.TeubnerStreyLengths(),False )
        
        self.assertEqual(self.model.run(0.0), 10.1)
        self.assertEqual(self.model.run(2.0), self._func(0.1,-30.0,5000.0,0.1,2.0))
        self.assertEqual(self.model.runXY(2.0), self._func(0.1,-30.0,5000.0,0.1,2.0))
        
    def test2D(self):
        self.model.setParam('c1', -30.0) 
        self.model.setParam('c2', 5000.0) 
        self.model.setParam('scale', 0.1)
        self.model.setParam('background', 0.1)
        #value = self._func(0.1,-30.0,5000.0,0.1, 1.0)\
        #*self._func(0.1,-30.0,5000.0,0.1, 2.0)    
        value = self._func(0.1,-30.0,5000.0,0.1, math.sqrt(5.0))
        
        self.assertEqual(self.model.runXY([1.0,2.0]), value)
        
    def test2Dphi(self):
        self.model.setParam('c1', -30.0) 
        self.model.setParam('c2', 5000.0) 
        self.model.setParam('scale', 0.1)
        self.model.setParam('background', 0.1)
        
        x = 1.0
        y = 2.0
        r = math.sqrt(x**2 + y**2)
        phi = math.atan2(y, x)
        
        #value = self._func(0.1,-30.0,5000.0,0.1, x)\
        #*self._func(0.1,-30.0,5000.0,0.1, y)
        value = self._func(0.1,-30.0,5000.0,0.1, r)
        self.assertAlmostEquals(self.model.run([r, phi]), value,1)
        
class TestBEPolyelectrolyte(unittest.TestCase):
    """
        Unit tests for  BEPolyelectrolyte function
        
        F(x) = K*1/(4*pi()*Lb*(alpha)^(2)*(q^(2)+k2)/(1+(r02)^(2))*(q^(2)+k2)\
                       *(q^(2)-(12*h*C/b^(2)))
        
        The model has Eight parameters: 
            K        =  Constrast factor of the polymer
            Lb       =  Bjerrum length
            H        =  virial parameter
            B        =  monomer length
            Cs       =  Concentration of monovalent salt 
            alpha    =  ionazation degree 
            C        = polymer molar concentration
            bkd      = background
    """
    def _func(self, K, Lb, H, B, Cs, alpha, C, bkd, r02, k2,  x):
        return (K /( (4*math.pi *Lb*(alpha**2)*(x**2 +k2)) *( (1 +(r02**2))  \
                    *((x**2) + k2)*((x**2) -(12 * H * C/(B**2))) )))+ bkd
    
    def setUp(self):
        from sans.models.BEPolyelectrolyte import BEPolyelectrolyte
        self.model= BEPolyelectrolyte()
        
        self.K = 10.0
        self.Lb = 6.5
        self.h = 11
        self.b = 13
        self.Cs = 0.1
        self.alpha = 0.05
        self.C  = .7
        self.Bkd =0.01
       
        self.model.setParam('K', self.K) 
        self.model.setParam('Lb', self.Lb) 
        self.model.setParam('H', self.h)
        self.model.setParam('B', self.b)
        self.model.setParam('Cs',self.Cs) 
        self.model.setParam('alpha', self.alpha) 
        self.model.setParam('C', self.C)
        self.model.setParam('background', self.Bkd)
        
    def _func(self, q):
        
        Ca = self.C *6.022136e-4          
        Csa = self.Cs * 6.022136e-4        
        k2= 4*math.pi*self.Lb*(2*self.Cs+self.alpha*Ca)   

        r02 = 1./self.alpha / Ca**0.5*( self.b / (48*math.pi*self.Lb)**0.5 )
        q2 = q**2    
        Sq = self.K*1./(4*math.pi*self.Lb*self.alpha**2) * (q2 + k2)  /  (1+(r02**2) * (q2+k2) * (q2- (12*self.h*Ca/self.b**2)) ) + self.Bkd
        return Sq
       
    def test1D(self):
        
       
        q = 0.001
   
        self.assertEqual(self.model.run(q), self._func(q))
        self.assertEqual(self.model.runXY(q), self._func(q))
         
    def test2D(self):
        #self.assertAlmostEquals(self.model.runXY([1.0,2.0]), self._func(1.0)*self._func(2.0), 8)
        self.assertAlmostEquals(self.model.runXY([1.0,2.0]), self._func(math.sqrt(1.0+2.0**2)), 8)
        
    def test2Dphi(self):

        x = 1.0
        y = 2.0
        r = math.sqrt(x**2 + y**2)
        phi = math.atan2(y, x)
        
        self.assertAlmostEquals(self.model.run([r, phi]), self._func(r), 8)
        
class TestFractalModel(unittest.TestCase):
    """
        Unit tests for  Number Density Fractal function   
        F(x)= P(x)*S(x) + bkd
        The model has Seven parameters: 
            scale   =  Volume fraction
            Radius  =  Block radius
            Fdim    =  Fractal dimension
            L       =  correlation Length
            SDLB    =  SDL block
            SDLS    =  SDL solvent
            bkd     =  background
    """
    def setUp(self):
        from sans.models.FractalModel import FractalModel
        self.model= FractalModel()
        self.r0 = 5.0
        self.sldp = 2.0e-6
        self.sldm = 6.35e-6
        self.phi = 0.05
        self.Df = 2
        self.corr = 100.0
        self.bck = 1.0
        
        self.model.setParam('scale', self.phi) 
        self.model.setParam('radius', self.r0) 
        self.model.setParam('fractal_dim',self.Df)
        self.model.setParam('cor_length', self.corr)
        self.model.setParam('sldBlock', self.sldp) 
        self.model.setParam('sldSolv', self.sldm) 
        self.model.setParam('background', self.bck)
        
    def _func(self, x):
        r0 = self.r0
        sldp = self.sldp
        sldm = self.sldm
        phi = self.phi
        Df = self.Df
        corr = self.corr
        bck = self.bck
        
        pq = 1.0e8*phi*4.0/3.0*math.pi*r0*r0*r0*(sldp-sldm)*(sldp-sldm)*math.pow((3*(math.sin(x*r0) - x*r0*math.cos(x*r0))/math.pow((x*r0),3)),2);
        
        sq = Df*math.exp(gammaln(Df-1.0))*math.sin((Df-1.0)*math.atan(x*corr));
        sq /= math.pow((x*r0),Df) * math.pow((1.0 + 1.0/(x*corr)/(x*corr)),((Df-1.0)/2.0));
        sq += 1.0;
        
        #self.assertAlmostEqual(self.model._scatterRanDom(x), pq, 8 )
        #self.assertEqual(self.model._Block(x),sq )
        
        return sq*pq+bck
    
    def test1D(self):        
        x = 0.001
        
        iq = self._func(x)
        self.assertEqual(self.model.run(x), iq)
        self.assertEqual(self.model.runXY(x), iq)
    
    def test2D(self):
        x = 1.0
        y = 2.0
        r = math.sqrt(x**2 + y**2)
        phi = math.atan2(y, x)
        iq_x = self._func(x)
        iq_y = self._func(y)
        
        #self.assertEqual(self.model.run([r, phi]), iq_x*iq_y)
        self.assertEqual(self.model.run([r, phi]), self.model.run(r))
        #self.assertEqual(self.model.runXY([x,y]), iq_x*iq_y)
        self.assertEqual(self.model.runXY([x,y]), self.model.run(r))
        
if __name__ == '__main__':
    unittest.main()

