"""
    Unit tests for non shape based model (Task 8.2.1)
    These tests are part of the requirements
"""

import unittest, time, math
from scipy.special import erf,gamma

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
        return math.exp(a+b*x**2)
    
    def setUp(self):
        from GuinierModel import GuinierModel
        self.model= GuinierModel()
        
    def test1D(self):
        self.model.setParam('A', 2.0)
        self.model.setParam('B', 1.0)
        
        self.assertEqual(self.model.run(0.0), math.exp(2.0))
        self.assertEqual(self.model.run(2.0), math.exp(2.0+1.0*(2.0)**2))
        
    def test2D(self):
        self.model.setParam('A', 2.0)
        self.model.setParam('B', 1.0)
        
        value = self._func(2.0, 1.0, 1.0)*self._func(2.0, 1.0, 2.0)
        self.assertEqual(self.model.runXY([0.0,0.0]), math.exp(2.0)*math.exp(2.0))
        self.assertEqual(self.model.runXY([1.0,2.0]), value)
        
    def test2Dphi(self):
        self.model.setParam('A', 2.0)
        self.model.setParam('B', 1.0)
        
        x = 1.0
        y = 2.0
        r = math.sqrt(x**2 + y**2)
        phi = math.atan2(y, x)
        
        value = self._func(2.0, 1.0, x)*self._func(2.0, 1.0, y)
        
        #self.assertEqual(self.model.run([r, phi]), value)
        self.assertAlmostEquals(self.model.run([r, phi]), value,1)
        
        
class TestPorod(unittest.TestCase):
    """
        Unit tests for Porod function
        
        F(x) = exp[ [C]/Q**4 ]
        
        The model has one parameter: C
    """
    def _func(self, c, x):
        return math.exp(c/(x*x*x*x))
    
    def setUp(self):
        from PorodModel import PorodModel
        self.model= PorodModel()
        self.model.setParam('c', 2.0)        
        
    def test1D(self):
        value = self._func(2.0, 3.0)
        self.assertEqual(self.model.run(3.0), value)
        
    def test2D(self):
        value = self._func(2.0, 1.0)*self._func(2.0, 2.0)
        self.assertEqual(self.model.runXY([1.0,2.0]), value)
        
    def test2Dphi(self):
        x = 1.0
        y = 2.0
        r = math.sqrt(x**2 + y**2)
        phi = math.atan2(y, x)
        
        value = self._func(2.0, 1.0)*self._func(2.0, 2.0)
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
        from DebyeModel import DebyeModel
        self.model= DebyeModel()
        self.model.setParam('Rg', 50.0)    
        self.model.setParam('scale',1.0) 
        self.model.setParam('bkd',0.001)   
        
    def test1D(self):
        value = self._func(50.0, 1.0, 0.001, 2.0)
        self.assertEqual(self.model.run(2.0), value)
        
        #user enter zero as a value of x
        self.assertEqual(self.model.run(0.0),False)
       
        
    def test2D(self):
        value = self._func(50.0, 1.0, 0.001, 1.0)*self._func(50.0, 1.0, 0.001, 2.0)
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
    def _func(self,scale,L,bkd,x):
         return scale/( 1 + (x*L)**2 ) + bkd 
    def setUp(self):
        from LorentzModel import LorentzModel
        self.model= LorentzModel()
        
    def test1D(self):
        self.model.setParam('scale', 100.0)
        self.model.setParam('L', 50.0)
        self.model.setParam('bkd', 1.0)
        
        self.assertEqual(self.model.run(0.0), 101.0)
        self.assertEqual(self.model.run(2.0), self._func(100.0, 50.0, 1.0, 2.0))
        
    def test2D(self):
        self.model.setParam('scale', 100.0)
        self.model.setParam('L', 50.0)
        self.model.setParam('bkd', 1.0)
        
        value = self._func(100.0, 50.0, 1.0, 1.0)*self._func(100.0, 50.0, 1.0, 2.0)    
        self.assertEqual(self.model.runXY([1.0,2.0]), value)
        
    def test2Dphi(self):
        self.model.setParam('scale', 100.0)
        self.model.setParam('L', 50.0)
        self.model.setParam('bkd', 1.0)
        
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
    def _func(self, a, b,c, x):
        return a/(( 1 + ( x * b )**2 ))**2 + c
    
    def setUp(self):
        from DABModel import DABModel
        self.model= DABModel()
        
    def test1D(self):
        self.model.setParam('scale', 10.0)
        self.model.setParam('L', 40.0)
        self.model.setParam('bkd', 0.0)
        
        self.assertEqual(self.model.run(0.0), 10.0)
        self.assertEqual(self.model.run(2.0), self._func(10.0, 40.0, 0.0, 2.0))
        
    def test2D(self):
        self.model.setParam('scale', 10.0)
        self.model.setParam('L', 40.0)
        self.model.setParam('bkd', 0.0)
        
        value = self._func(10.0, 40.0, 0.0, 1.0)*self._func(10.0, 40.0, 0.0, 2.0)    
        self.assertEqual(self.model.runXY([1.0,2.0]), value)
        
    def test2Dphi(self):
        self.model.setParam('scale', 10.0)
        self.model.setParam('L', 40.0)
        self.model.setParam('bkd', 0.0)
        
        x = 1.0
        y = 2.0
        r = math.sqrt(x**2 + y**2)
        phi = math.atan2(y, x)
        
        value = self._func(10.0, 40.0, 0.0, x)*self._func(10.0, 40.0, 0.0, y)
        self.assertAlmostEquals(self.model.run([r, phi]), value,1)
        
class TestPowerLaw(unittest.TestCase):
    """
        Unit tests for PowerLaw function

        F(x) = scale* (x)^(m) + bkd
        
        The model has three parameters: 
            m     =  power
            scale  =  scale factor
            bkd    =  incoherent background
    """
    def _func(self, a, m,c, x):
        return a*(x )**m + c
    
    def setUp(self):
        from PowerLawModel import PowerLawModel
        self.model= PowerLawModel()
        
    def test1D(self):
        self.model.setParam('scale', math.exp(-6))
        self.model.setParam('m', 4.0)
        self.model.setParam('bkd', 1.0)
        
        self.assertEqual(self.model.run(0.0), 1.0)
        self.assertEqual(self.model.run(2.0), self._func(math.exp(-6), 4.0, 1.0, 2.0))
        
    def test2D(self):
        self.model.setParam('scale', math.exp(-6))
        self.model.setParam('m', 4.0)
        self.model.setParam('bkd', 1.0)
        
        value = self._func(math.exp(-6), 4.0, 1.0, 1.0)\
        *self._func(math.exp(-6), 4.0, 1.0, 2.0)    
        
        self.assertEqual(self.model.runXY([1.0,2.0]), value)
        
    def test2Dphi(self):
        self.model.setParam('scale', math.exp(-6))
        self.model.setParam('m', 4.0)
        self.model.setParam('bkd', 1.0)
        
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
    def _func(self, a,c1,c2,b, x):
        return 1/( a + c1*(x)**(2)+  c2*(x)**(4)) + b
    
    def setUp(self):
        from TeubnerStreyModel import TeubnerStreyModel
        self.model= TeubnerStreyModel()
        
    def test1D(self):
        
        self.model.setParam('c1', -30.0) 
        self.model.setParam('c2', 5000.0) 
        self.model.setParam('scale', 0.1)
        self.model.setParam('bkd', 0.1)
        #self.assertEqual(1/(math.sqrt(4)), math.pow(4,-1/2))
        self.assertEqual(self.model.TeubnerStreyLengths(),False )
        
        self.assertEqual(self.model.run(0.0), 10.1)
        self.assertEqual(self.model.run(2.0), self._func(0.1,-30.0,5000.0,0.1,2.0))
        
    def test2D(self):
        self.model.setParam('c1', -30.0) 
        self.model.setParam('c2', 5000.0) 
        self.model.setParam('scale', 0.1)
        self.model.setParam('bkd', 0.1)
        value = self._func(0.1,-30.0,5000.0,0.1, 1.0)\
        *self._func(0.1,-30.0,5000.0,0.1, 2.0)    
        
        self.assertEqual(self.model.runXY([1.0,2.0]), value)
        
    def test2Dphi(self):
        self.model.setParam('c1', -30.0) 
        self.model.setParam('c2', 5000.0) 
        self.model.setParam('scale', 0.1)
        self.model.setParam('bkd', 0.1)
        
        x = 1.0
        y = 2.0
        r = math.sqrt(x**2 + y**2)
        phi = math.atan2(y, x)
        
        value = self._func(0.1,-30.0,5000.0,0.1, x)\
        *self._func(0.1,-30.0,5000.0,0.1, y)
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
        from BEPolyelectrolyte import BEPolyelectrolyte
        self.model= BEPolyelectrolyte()
        
    def test1D(self):
        
        self.model.setParam('K', 10.0) 
        self.model.setParam('Lb', 7.1) 
        self.model.setParam('H', 12)
        self.model.setParam('B', 10)
        self.model.setParam('Cs',0.0) 
        self.model.setParam('alpha', 0.05) 
        self.model.setParam('C', 0.7)
        self.model.setParam('bkd', 0.001)
        K2 = 4 * math.pi * 7.1 * (2*0.0 + 0.05*0.7)
        Ca = 0.7 * 6.022136 * math.exp(-4)
        r02 =1/(0.05 * math.pow(Ca,0.5)*(10/math.pow((48* math.pi *7.1),0.5)))
 
        
        self.assertEqual(self.model.run(0.0), self._func( 10.0, 7.1, 12,\
                        10.0, 0.0,0.05,0.7,0.001, r02, K2,  0.0))
        self.assertEqual(self.model.run(2.0),  self._func( 10.0, 7.1, 12,\
                        10.0, 0.0,0.05,0.7,0.001, r02, K2,  2.0))
        
    def test2D(self):
        self.model.setParam('K', 10.0) 
        self.model.setParam('Lb', 7.1) 
        self.model.setParam('H', 12)
        self.model.setParam('B', 10)
        self.model.setParam('Cs',0.0) 
        self.model.setParam('alpha', 0.05) 
        self.model.setParam('C', 0.7)
        self.model.setParam('bkd', 0.001)
        K2 = 4 * math.pi * 7.1 * (2*0.0 + 0.05*0.7)
        Ca = 0.7 * 6.022136 * math.exp(-4)
        r02 =1/(0.05 * math.pow(Ca,0.5)*(10/math.pow((48* math.pi *7.1),0.5)))
 
        value = self._func(10.0, 7.1, 12, 10.0, 0.0,0.05,0.7,0.001, r02, K2,  1.0)\
        *self._func(10.0, 7.1, 12,10.0, 0.0,0.05,0.7,0.001, r02, K2, 2.0)    
        
        self.assertAlmostEquals(self.model.runXY([1.0,2.0]), value)
        
    def test2Dphi(self):
        self.model.setParam('K', 10.0) 
        self.model.setParam('Lb', 7.1) 
        self.model.setParam('H', 12)
        self.model.setParam('B', 10)
        self.model.setParam('Cs',0.0) 
        self.model.setParam('alpha', 0.05) 
        self.model.setParam('C', 0.7)
        self.model.setParam('bkd', 0.001)
        K2 = 4 * math.pi * 7.1 * (2*0.0 + 0.05*0.7)
        Ca = 0.7 * 6.022136 * math.exp(-4)
        r02 =1/(0.05 * math.pow(Ca,0.5)*(10/math.pow((48* math.pi *7.1),0.5)))
        
        x = 1.0
        y = 2.0
        r = math.sqrt(x**2 + y**2)
        phi = math.atan2(y, x)
        
        value = self._func(10.0, 7.1, 12, 10.0, 0.0,0.05,0.7,0.001, r02, K2,  x)\
        *self._func(10.0, 7.1, 12, 10.0, 0.0,0.05,0.7,0.001, r02, K2, y)
        self.assertAlmostEquals(self.model.run([r, phi]), value,1)
        
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
    def _func(self,p,s, bkd, x):
        return p*s + bkd
    
    def setUp(self):
        from FractalModel import FractalModel
        self.model= FractalModel()
        
    def test1D(self):
        
        self.model.setParam('scale', 0.05) 
        self.model.setParam('Radius',5) 
        self.model.setParam('Fdim',2)
        self.model.setParam('L', 100)
        self.model.setParam('SDLB',2*math.exp(-6)) 
        self.model.setParam('SDLS', 6.35*math.exp(-6)) 
        self.model.setParam('bkd', 0.0)
        
        s= 1 + (math.sin((2 - 1) * math.atan(2.0*100))* 2 * gamma(2-1))\
           /( math.pow( (2.0*5),2)*( 1 + 1/math.pow(((2.0**2)*(100**2)),(2-1)/2))) 
        v= (4/3)*math.pi *math.pow(5, 3)
        f= ( math.sin(2.0*5)-(2.0*5)*math.cos(2.0*5) )/(3*math.pow(2.0*5, 3))
        p= 0.05 *(v**2)*(((2*math.exp(-6))-(6.35*math.exp(-6)))**2)*(f**2)
       
        self.assertEqual(self.model._scatterRanDom(2.0),p )
        self.assertEqual(self.model._Block(2.0),s )
        self.assertEqual(self.model.run(2.0),self._func(p,s ,0.0,2.0))
        
class TestUnifiedPowerLaw(unittest.TestCase):
    """
        Unit tests for Unified PowerLaw function

        F(x) =  bkd + sum(G[i]*exp(-x**2 *Rg[i]**2 /3)) \
          + [B[i]( erf(x*Rg[i]/math.sqrt(6)))** (3*p[i])]/x**p[i] )
        
    """
  
    def setUp(self):
        from  UnifiedPowerLaw import  UnifiedPowerLawModel
        self.model=  UnifiedPowerLawModel()
        
    def _func(self,level,B,Rg,G,Pow,bkd, x):
        return bkd + (B * math.pow(erf(x *Rg/math.sqrt(6)),3 *Pow))/math.pow(x,Pow)
    
    def _Sum (self,level,x):
        self.sum = 0
        for i in xrange(level):
            self.sum =self.sum +self.model.getParam('G'+str(i+1))*math.exp(-(x**2)*\
                         (self.model.getParam('Rg'+str(i+1))**2)/3)
        return self.sum
    
    def test1D(self):
        

        self.model.setParam('bkd', 0.0)
        #setValueParam(self,level,Bvalue,Rgvalue,Gvalue,Pvalue)
        self.model.setValueParam(1,2,1,2,5)
        self.model.setValueParam(2,3,12,8,9)
        self.model.setValueParam(3,0,2,3,2)
        self.model.setValueParam(4,1,4,1,-1)
        self.model.setValueParam(5,1,4,1,-2)
        
        self.assertEqual(self.model.getValue('P',1),5)
        self.assertEqual(self.model.getValue('Rg',2),12)
   
        value1 = self._func(1,2,1,2,5,0.0,1.0)+self._Sum(5,1.0)
        value2 = self._func(2,3,12,8,9,0.0,1.0)+self._Sum(5,1.0)
        value3 = self._func(3,0,2,3,2,0.0,1.0)+self._Sum(5,1.0)
        value4 = self._func(4,1,4,1,-1,0.0,1.0)+self._Sum(5,1.0)
        value5 = self._func(5,1,4,1,-2,0.0,1.0)+self._Sum(5,1.0)
        self.assertEqual(self.model.run(1,1.0), value1)
        self.assertEqual(self.model.run(2,1.0), value2)
        self.assertEqual(self.model.run(3,1.0), value3)
        self.assertEqual(self.model.run(4,1.0), value4)
        self.assertEqual(self.model.run(5,1.0), value5)
        
 
        
        
if __name__ == '__main__':
    unittest.main()