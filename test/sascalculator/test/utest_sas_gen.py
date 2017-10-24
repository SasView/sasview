"""
Unit tests for the sas_gen
"""
import warnings
warnings.simplefilter("ignore")

import unittest
from sas.sascalc.calculator import sas_gen


class sas_gen_test(unittest.TestCase):

    def setUp(self):
        self.sldloader = sas_gen.SLDReader()
        self.pdbloader = sas_gen.PDBReader()
        self.omfloader = sas_gen.OMFReader()

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


if __name__ == '__main__':
    unittest.main()

