"""
Unit tests for the sans_gen
"""
import warnings
warnings.simplefilter("ignore")

import unittest
from sans.calculator import sans_gen
 
import os.path

class sans_gen_test(unittest.TestCase):
    
    def setUp(self):
        self.model = sans_gen.GenSAS()
        self.sldloader = sans_gen.SLDReader()
        self.pdbloader = sans_gen.PDBReader()
        self.omfloader = sans_gen.OMFReader()
        
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
        self.assertEqual(f.mx[0], 0)
        self.assertEqual(f.my[0], 0)
        self.assertEqual(f.mz[0], 0)
        
if __name__ == '__main__':
    unittest.main()
   