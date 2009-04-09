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
        # Test .ABS file loaded as ascii
        f = self.loader.load("ascii_test_1.txt")
        # The length of the data is 10
        self.assertEqual(len(f.x), 10)
        
        
if __name__ == '__main__':
    unittest.main()
   