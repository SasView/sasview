"""
Unit tests for the sas_gen
"""

import os.path
import warnings
warnings.simplefilter("ignore")

import unittest
import numpy as np

from sas.sascalc.calculator import sas_gen


def find(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)


class sas_gen_test(unittest.TestCase):

    def setUp(self):
        self.sldloader = sas_gen.SLDReader()
        self.pdbloader = sas_gen.PDBReader()
        self.omfloader = sas_gen.OMFReader()

    def test_sldreader(self):
        """
        Test .sld file loaded
        """
        f = self.sldloader.read(find("sld_file.sld"))
        self.assertEqual(f.pos_x[0], -40.5)
        self.assertEqual(f.pos_y[0], -13.5)
        self.assertEqual(f.pos_z[0], -13.5)
    
    def test_sldwriter(self):
        """
        Test .sld file is written correctly
        """
        # load in a sample sld file then resave it
        f = self.sldloader.read(find("sld_file.sld"))
        self.sldloader.write(find("write_test.sld"), f)
        # load in the saved file to confirm that Sasview does not reject it within its
        # own loading function
        g = self.sldloader.read(find("write_test.sld"))
        # confirm that the first row of data is as expected
        self.assertEqual(f.pos_x[0], g.pos_x[0])
        self.assertEqual(f.pos_y[0], g.pos_y[0])
        self.assertEqual(f.pos_z[0], g.pos_z[0])
        self.assertEqual(f.sld_n[0], g.sld_n[0])
        self.assertEqual(f.sld_mx[0], g.sld_mx[0])
        self.assertEqual(f.sld_my[0], g.sld_my[0])
        self.assertEqual(f.sld_mz[0], g.sld_mz[0])
        self.assertEqual(f.vol_pix[0], g.vol_pix[0])


    def test_pdbreader(self):
        """
        Test .pdb file loaded
        """
        f = self.pdbloader.read(find("c60.pdb"))
        self.assertEqual(f.pos_x[0], -0.733)
        self.assertEqual(f.pos_y[0], -1.008)
        self.assertEqual(f.pos_z[0], 3.326)

    def test_omfreader(self):
        """
        Test .omf file loaded
        """
        f = self.omfloader.read(find("A_Raw_Example-1.omf"))
        output = sas_gen.OMF2SLD()
        output.set_data(f)
        self.assertEqual(f.mx[0], 0)
        self.assertEqual(f.my[0], 0)
        self.assertEqual(f.mz[0], 0)
        self.assertEqual(output.pos_x[0], 0.0)
        self.assertEqual(output.pos_y[0], 0.0)
        self.assertEqual(output.pos_z[0], 0.0)

    def test_calculator(self):
        """
        Test that the calculator calculates.
        """
        f = self.omfloader.read(find("A_Raw_Example-1.omf"))
        omf2sld = sas_gen.OMF2SLD()
        omf2sld.set_data(f)
        model = sas_gen.GenSAS()
        model.set_sld_data(omf2sld.output)
        q = np.linspace(0, 0.1, 11)[1:]
        model.runXY([q, q])


if __name__ == '__main__':
    unittest.main()

