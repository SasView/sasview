"""
    Unit tests for the ascii (n-column) reader
"""

import os.path
import warnings
import math
warnings.simplefilter("ignore")

import unittest
from sas.sascalc.dataloader.loader import Loader
from sas.sascalc.dataloader.data_info import Data2D


def find(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)


class ABSReaderTests(unittest.TestCase):
    
    def setUp(self):
        self.loader = Loader()
        self.f1_list = self.loader.load(find("ascii_test_1.txt"))
        self.f1 = self.f1_list[0]
        self.f2_list = self.loader.load(find("ascii_test_2.txt"))
        self.f2 = self.f2_list[0]
        self.f3_list = self.loader.load(find("ascii_test_3.txt"))
        self.f3 = self.f3_list[0]
        self.f4_list = self.loader.load(find("ascii_test_4.abs"))
        self.f4 = self.f4_list[0]
        self.f5_list = self.loader.load(find("ascii_test_5.txt"))
        self.f5 = self.f5_list[0]

    def test_checkdata(self):
        """
            Test .ABS file loaded as ascii
        """
        # The length of the data is 10
        self.assertEqual(len(self.f1_list), 1)
        self.assertEqual(len(self.f2_list), 1)
        self.assertEqual(len(self.f3_list), 1)
        self.assertEqual(len(self.f4_list), 1)
        self.assertEqual(len(self.f5_list), 1)
        self.assertEqual(len(self.f1.x), 10)
        self.assertEqual(self.f1.x[0],0.002618)
        self.assertEqual(self.f1.x[9],0.0497)
        self.assertTrue(self.f1.x_unit == 'A^{-1}')
        self.assertTrue(self.f1.y_unit == 'cm^{-1}')
        
        self.assertEqual(self.f1.meta_data['loader'],"ASCII")

    def test_truncated_1(self):
        """
            Test an ascii file with header and a 
            comment line in the middle of the data section.
            The business rule says that we should stop
            reading at the first comment once the data
            section has started (and treat the comment
            as though it were the start of a footer).
        """
        # The length of the data is 5
        self.assertEqual(len(self.f2.x), 5)
        self.assertEqual(self.f2.x[0],0.002618)
        self.assertEqual(self.f2.x[4],0.02356)

    def test_truncated_2(self):
        """
            Test a 6-col ascii file with header and a 
            line with only 2 columns in the middle of the data section.
            The business rule says that we should stop
            reading at the first inconsitent line.
        """
        # The length of the data is 5
        self.assertEqual(len(self.f3.x), 5)
        self.assertEqual(self.f3.x[0],0.002618)
        self.assertEqual(self.f3.x[4],0.02356)

    def test_truncated_3(self):
        """
            Test a 6-col ascii file with complex header and 
            many lines with 2 or 2 columns in the middle of the data section.
            The business rule says that we should stop
            reading at the last line of header.
        """
        # The length of the data is 5
        self.assertEqual(len(self.f4.x), 5)
        self.assertEqual(self.f4.x[0],0.012654)
        self.assertEqual(self.f4.x[4],0.02654)

    def test_truncated_4(self):
        """
            Test mix of 6-col and 2-col.
            Only the last 5 2-col lines should be read.
        """
        # The length of the data is 5
        self.assertEqual(len(self.f5.x), 5)
        self.assertEqual(self.f5.x[0],0.02879)
        self.assertEqual(self.f5.x[4],0.0497)

    def test_truncated_5(self):
        """
            Test a 6-col ascii file with complex header where one of them has a
            letter and many lines with 2 or 2 columns in the middle of the data
            section. Will be rejected because fewer than 5 lines.
        """
        # Test .ABS file loaded as ascii
        f = None
        try:
            f = self.loader.load(find("ascii_test_6.txt"))
        # The length of the data is 5
        except:
            self.assertEqual(f, None)

    def test_nan_values(self):
        """
        Test loading an ascii data file with nan values saved in x, y, or dy.
        """
        f_1d = self.loader.load(find("nans_in_1d_data.dat"))[0]
        f_2d = self.loader.load(find("nans_in_2d_data.DAT"))[0]
        for i in range(0, len(f_1d.x) - 1):
            self.assertFalse(math.isnan(f_1d.x[i]))
            self.assertFalse(math.isnan(f_1d.y[i]))
            self.assertFalse(math.isnan(f_1d.dy[i]))
        self.assertTrue(isinstance(f_2d, Data2D))
        f_2d.data = f_2d.data.flatten()
        f_2d.qx_data = f_2d.qx_data.flatten()
        f_2d.qy_data = f_2d.qy_data.flatten()
        for i in range(0, len(f_2d.data) - 1):
            self.assertFalse(math.isnan(f_2d.data[i]))
            self.assertFalse(math.isnan(f_2d.qx_data[i]))
            self.assertFalse(math.isnan(f_2d.qy_data[i]))

    def test_encoding(self):
        # Compare loading of utf-8 versus ansi/windows-1252
        ansi = self.loader.load(find("encoding_ANSI.txt"))
        utf8 = self.loader.load(find("encoding_UTF_8.txt"))
        self._check_cl_data(ansi)
        self._check_cl_data(utf8)

    def _check_cl_data(self, data):
        self.assertEqual(len(data), 1)
        data_set = data[0]
        self.assertEqual(len(data_set.x), 969)
        self.assertEqual(len(data_set.x), len(data_set.y))
        self.assertEqual(data_set.x[0], 0.000201634)
        self.assertEqual(data_set.y[0], 208487062.3)
        self.assertEqual(data_set.x_unit, 'A^{-1}')
        self.assertEqual(data_set.y_unit, 'cm^{-1}')

    def test_save_ascii(self):
        f_name = "test_f1_output.txt"
        f_name_csv = "test_f1_output.csv"
        # Save and load text file
        self.loader.save(f_name, self.f1, None)
        self.assertTrue(os.path.isfile(f_name))
        reload = self.loader.load(f_name)
        f1_reload = reload[0]
        # Compare data from saved text file to previously loaded data
        self.assertEqual(len(self.f1.x), len(f1_reload.x))
        self.assertEqual(len(self.f1.y), len(f1_reload.y))
        self.assertEqual(self.f1.y[0], f1_reload.y[0])
        # Save and load csv file
        self.loader.save(f_name_csv, self.f1, None)
        self.assertTrue(os.path.isfile(f_name_csv))
        reload_csv = self.loader.load(f_name_csv)
        f1_reload_csv = reload_csv[0]
        # Compare data from saved csv file to previously loaded data
        self.assertEqual(len(self.f1.x), len(f1_reload_csv.x))
        self.assertEqual(len(self.f1.y), len(f1_reload_csv.y))
        self.assertEqual(self.f1.y[0], f1_reload_csv.y[0])
        # Destroy generated files
        os.remove(f_name)
        self.assertFalse(os.path.isfile(f_name))
        os.remove(f_name_csv)
        self.assertFalse(os.path.isfile(f_name_csv))


if __name__ == '__main__':
    unittest.main()
   
