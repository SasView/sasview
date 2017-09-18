"""
    Unit tests for the ascii (n-column) reader
"""
import warnings
warnings.simplefilter("ignore")

import unittest
from sas.sascalc.dataloader.loader import Loader


class ABSReaderTests(unittest.TestCase):
    
    def setUp(self):
        self.loader = Loader()
        self.f1_list = self.loader.load("ascii_test_1.txt")
        self.f1 = self.f1_list[0]
        self.f2_list = self.loader.load("ascii_test_2.txt")
        self.f2 = self.f2_list[0]
        self.f3_list = self.loader.load("ascii_test_3.txt")
        self.f3 = self.f3_list[0]
        self.f4_list = self.loader.load("ascii_test_4.abs")
        self.f4 = self.f4_list[0]
        self.f5_list = self.loader.load("ascii_test_5.txt")
        self.f5 = self.f5_list[0]

    def test_checkdata(self):
        """
            Test .ABS file loaded as ascii
        """
        # The length of the data is 10
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
            f = self.loader.load("ascii_test_6.txt")
        # The length of the data is 5
        except:
            self.assertEqual(f, None)

if __name__ == '__main__':
    unittest.main()
   
