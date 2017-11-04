"""
    Unit tests for the red2d (3-7-column) reader
"""
import warnings
warnings.simplefilter("ignore")

import unittest
from sas.sascalc.dataloader.loader import  Loader

import os.path


def find(filename):
    return os.path.join(os.path.dirname(__file__), filename)


class abs_reader(unittest.TestCase):

    def setUp(self):
        self.loader = Loader()
        self.data_list = self.loader.load(find("exp18_14_igor_2dqxqy.dat"))

    def test_checkdata(self):
        """
            Test .DAT file loaded as IGOR/DAT 2D Q_map
        """
        f = self.data_list[0]
        # The length of the data is 10
        self.assertEqual(len(self.data_list), 1)
        self.assertEqual(len(f.qx_data),  36864)
        self.assertEqual(f.qx_data[0],-0.03573497)
        self.assertEqual(f.qx_data[36863],0.2908819)
        self.assertEqual(f.Q_unit, '1/A')
        self.assertEqual(f.I_unit, '1/cm')

        self.assertEqual(f.meta_data['loader'],"IGOR/DAT 2D Q_map")


if __name__ == '__main__':
    unittest.main()
