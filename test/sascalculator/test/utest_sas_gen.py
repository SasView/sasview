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
    return os.path.join(os.path.dirname(__file__), filename)


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
        x = np.linspace(0, 0.1, 11)[1:]
        model.runXY([x, x])


if __name__ == '__main__':
    unittest.main()

