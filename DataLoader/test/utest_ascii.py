"""
    Unit tests for the ascii (n-column) reader
"""
import warnings
warnings.simplefilter("ignore")

import unittest
from DataLoader.loader import  Loader
 
import os.path

class abs_reader(unittest.TestCase):
    
    def setUp(self):
        self.loader = Loader()
        
    def test_checkdata(self):
        """
            Test .ABS file loaded as ascii
        """
        f = self.loader.load("ascii_test_1.txt")
        # The length of the data is 10
        self.assertEqual(len(f.x), 10)
        
    def test_truncated_1(self):
        """
            Test an ascii file with header and a 
            comment line in the middle of the data section.
            The business rule says that we should stop
            reading at the first comment once the data
            section has started (and treat the comment
            as though it were the start of a footer).
        """
        # Test .ABS file loaded as ascii
        f = self.loader.load("ascii_test_2.txt")
        # The length of the data is 10
        self.assertEqual(len(f.x), 5)
        
    def test_truncated_2(self):
        """
            Test a 6-col ascii file with header and a 
            line with only 2 columns in the middle of the data section.
            The business rule says that we should stop
            reading at the first inconsitent line.
        """
        # Test .ABS file loaded as ascii
        f = self.loader.load("ascii_test_3.txt")
        # The length of the data is 5
        self.assertEqual(len(f.x), 5)
        
    def test_truncated_3(self):
        """
            Test a 6-col ascii file with complex header and 
            many lines with 2 or 2 columns in the middle of the data section.
            The business rule says that we should stop
            reading at the last line of header.
        """
        # Test .ABS file loaded as ascii
        f = self.loader.load("ascii_test_4.abs")
        # The length of the data is 5
        self.assertEqual(len(f.x), 5)
        
    def test_truncated_4(self):
        """
            Test mix of 6-col and 2-col.
            Only the last 5 2-col lines should be read.
        """
        # Test .ABS file loaded as ascii
        f = self.loader.load("ascii_test_5.txt")
        # The length of the data is 5
        self.assertEqual(len(f.x), 5)
        self.assertEqual(f.x[0],0.02879)
        self.assertEqual(f.x[4],0.0497)
        
        
if __name__ == '__main__':
    unittest.main()
   