"""
    Unit tests for the red2d (3-7-column) reader
"""
import warnings

import unittest

import os.path

from sas.sascalc.dataloader.loader import Loader

warnings.simplefilter("ignore")


def find(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)


BASE_POINTS = 36864
BASE_LENGTH = 192


class DatReaderTests(unittest.TestCase):

    def setUp(self):
        self.loader = Loader()
        self.data_list = self.loader.load(find("detector_square.dat"))
        # Same data file, but first 15 rows of data removed
        self.data_list_rectangle = self.loader.load(
            find("detector_rectangular.DAT"))

    def _check_common_data(self, f, removed):
        self.assertEqual(len(f.qx_data),
                         BASE_POINTS - removed * BASE_LENGTH)
        self.assertEqual(len(f.x_bins) + removed, len(f.y_bins))
        self.assertEqual(len(f.x_bins), 192 - removed)
        self.assertEqual(f.qx_data[len(f.qx_data) - 1], 0.2908819)
        self.assertEqual(f.Q_unit, 'A^{-1}')
        self.assertEqual(f.I_unit, 'cm^{-1}')
        self.assertEqual(f.meta_data['loader'], "IGOR/DAT 2D Q_map")

    def test_check_square_data(self):
        """
            Test square detector data loaded by the .DAT reader
        """
        f = self.data_list[0]
        # The length of the data is 10
        self.assertEqual(len(self.data_list), 1)
        self.assertEqual(f.qx_data[0],-0.03573497)
        self._check_common_data(f, 0)

    def test_check_rectangular_data(self):
        """
            Test rectangular detector data loaded by the .DAT reader
        """
        f = self.data_list_rectangle[0]
        self.assertEqual(len(self.data_list_rectangle), 1)
        self.assertEqual(f.qx_data[0], -0.009160664)
        self._check_common_data(f, 15)


if __name__ == '__main__':
    unittest.main()
