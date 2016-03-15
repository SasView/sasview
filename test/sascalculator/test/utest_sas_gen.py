"""
Unit tests for the sas_gen
"""
import warnings
warnings.simplefilter("ignore")

import unittest
from sas.sascalc.calculator import sas_gen
from sas.models.SphereModel import SphereModel

import numpy
 
import os.path

class sas_gen_test(unittest.TestCase):
    
    def setUp(self):
        self.sldloader = sas_gen.SLDReader()
        self.pdbloader = sas_gen.PDBReader()
        self.omfloader = sas_gen.OMFReader() 
        self.comp = SphereModel()
        
    def test_sldreader(self):
        """
        Test .sld file loaded 
        """
        f = self.sldloader.read("sld_file.sld")
        self.assertEqual(f.pos_x[0], -40.5)
        self.assertEqual(f.pos_y[0], -13.5)
        self.assertEqual(f.pos_z[0], -13.5)
        
    def test_pdbreader(self):
        """
        Test .pdb file loaded 
        """
        f = self.pdbloader.read("c60.pdb")
        self.assertEqual(f.pos_x[0], -0.733)
        self.assertEqual(f.pos_y[0], -1.008)
        self.assertEqual(f.pos_z[0], 3.326)
        
    def test_omfreader(self):
        """
        Test .omf file loaded 
        """
        f = self.omfloader.read("A_Raw_Example-1.omf")
        output = sas_gen.OMF2SLD()
        output.set_data(f)
        self.assertEqual(f.mx[0], 0)
        self.assertEqual(f.my[0], 0)
        self.assertEqual(f.mz[0], 0)
        self.assertEqual(output.pos_x[0], 0.0)
        self.assertEqual(output.pos_y[0], 0.0)
        self.assertEqual(output.pos_z[0], 0.0)

"""      
    def test_slda_and_run(self): # Works when sld reader uses loadtxt
        sld_data = self.sldloader.read("sphere697_r30.sld")
        # Generic computation  
        model = sas_gen.GenSAS()
        model.setParam('background', 0.0)
        model.setParam('scale', 1.0)
        model.setParam('Up_frac_in', 0.5)
        model.setParam('Up_frac_out', 0.5)
        model.setParam('Up_theta', 0.0)
        x = numpy.array([0.01])
        y = numpy.array([0.01])
        model.set_sld_data(sld_data)
        out_gen = model.runXY([x, y])
        # Analytic computation
        analy_model = self.comp
        analy_model.setParam('background', 0.0)
        analy_model.setParam('scale', 1.0)
        analy_model.setParam('radius', 30.0)
        analy_model.setParam('sldSolv', 0.0)
        analy_model.setParam('sldSph', 6.97e-06) 
        out_analy = analy_model.runXY([0.01, 0.01])
        # Comparison
        self.assertAlmostEqual(out_gen[0], out_analy, 1)
"""   
if __name__ == '__main__':
    unittest.main()
   
