"""
    Unit tests for data manipulations
"""
from __future__ import print_function

import unittest
import numpy as np
from sas.sascalc.dataloader.loader import Loader
from sas.sascalc.dataloader.readers.abs_reader import Reader as AbsReader
from sas.sascalc.dataloader.readers.danse_reader import Reader as DANSEReader

from sas.sascalc.dataloader.data_info import Data1D

import os.path


def find(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)


class abs_reader(unittest.TestCase):

    def setUp(self):
        reader = AbsReader()
        self.data_list = reader.read(find("jan08002.ABS"))
        self.data = self.data_list[0]

    def test_abs_checkdata(self):
        """
            Check the data content to see whether
            it matches the specific file we loaded.
            Check the units too to see whether the
            Data1D defaults changed. Otherwise the
            tests won't pass
        """
        self.assertEqual(os.path.basename(self.data.filename), "jan08002.ABS")
        self.assertEqual(self.data.meta_data['loader'], "IGOR 1D")

        self.assertEqual(self.data.source.wavelength_unit, 'A')
        self.assertEqual(self.data.source.wavelength, 6.0)

        self.assertEqual(self.data.detector[0].distance_unit, 'mm')
        self.assertEqual(self.data.detector[0].distance, 1000.0)

        self.assertEqual(self.data.sample.transmission, 0.5667)

        self.assertEqual(self.data.detector[0].beam_center_unit, 'mm')
        center_x = 114.58*5.08
        center_y = 64.22*5.08
        self.assertEqual(self.data.detector[0].beam_center.x, center_x)
        self.assertEqual(self.data.detector[0].beam_center.y, center_y)

        self.assertEqual(self.data.y_unit, 'cm^{-1}')
        self.assertEqual(self.data.x[0], 0.008082)
        self.assertEqual(self.data.x[1], 0.0275)
        self.assertEqual(self.data.x[2], 0.02762)
        self.assertEqual(self.data.x[126], 0.5828)

        self.assertEqual(self.data.y[0], 0.02198)
        self.assertEqual(self.data.y[1], 0.02201)
        self.assertEqual(self.data.y[2], 0.02695)
        self.assertEqual(self.data.y[126], 0.2958)

        self.assertEqual(self.data.dy[0], 0.002704)
        self.assertEqual(self.data.dy[1], 0.001643)
        self.assertEqual(self.data.dy[2], 0.002452)
        self.assertEqual(self.data.dy[126], 1)

    def test_checkdata2(self):
        self.assertEqual(self.data.dy[126], 1)

    def test_generic_loader(self):
        # the generic loader should work as well
        data = Loader().load(find("jan08002.ABS"))
        self.assertEqual(data[0].meta_data['loader'], "IGOR 1D")

    def test_usans_negative_dxl(self):
        data_abs = Loader().load(find("sam14_cor.ABS"))[0]
        data_cor = Loader().load(find("sam14_cor.txt"))[0]
        for i in range(0, len(data_abs.x) - 1):
            self.assertEqual(data_abs.x[i], data_cor.x[i])
            self.assertEqual(data_abs.y[i], data_cor.y[i])
            self.assertEqual(data_abs.dxl[i], -data_cor.dx[i])
            self.assertTrue(data_abs.dxl[i] > 0)


class DanseReaderTests(unittest.TestCase):

    def setUp(self):
        reader = DANSEReader()
        self.data_list = reader.read(find("MP_New.sans"))
        self.data = self.data_list[0]

    def test_checkdata(self):
        """
            Check the data content to see whether
            it matches the specific file we loaded.
            Check the units too to see whether the
            Data1D defaults changed. Otherwise the
            tests won't pass
        """
        self.assertEqual(len(self.data_list), 1)
        self.assertEqual(os.path.basename(self.data.filename), "MP_New.sans")
        self.assertEqual(self.data.meta_data['loader'], "DANSE")

        self.assertEqual(self.data.source.wavelength_unit, 'A')
        self.assertEqual(self.data.source.wavelength, 7.5)

        self.assertEqual(self.data.detector[0].distance_unit, 'mm')
        self.assertAlmostEqual(self.data.detector[0].distance, 5414.99, 3)

        self.assertEqual(self.data.detector[0].beam_center_unit, 'mm')
        center_x = 68.74*5.0
        center_y = 64.77*5.0
        self.assertEqual(self.data.detector[0].beam_center.x, center_x)
        self.assertEqual(self.data.detector[0].beam_center.y, center_y)

        self.assertEqual(self.data.I_unit, 'cm^{-1}')
        self.assertEqual(self.data.data[0], 1.57831)
        self.assertEqual(self.data.data[1], 2.70983)
        self.assertEqual(self.data.data[2], 3.83422)

        self.assertEqual(self.data.err_data[0], 1.37607)
        self.assertEqual(self.data.err_data[1], 1.77569)
        self.assertEqual(self.data.err_data[2], 2.06313)

    def test_generic_loader(self):
        # the generic loader should work as well
        data = Loader().load(find("MP_New.sans"))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0].meta_data['loader'], "DANSE")


if __name__ == '__main__':
    unittest.main()
