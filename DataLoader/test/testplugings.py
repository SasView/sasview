"""
    Unit tests for DataLoader module 
"""

import unittest
import math
import DataLoader
from DataLoader.loader import  Loader
from DataLoader.readers import TXT3_Reader,TXT2_Reader
from DataLoader.readers import IgorReader,danse_reader,tiff_reader
import os.path
import os 
class testLoader(unittest.TestCase):
   
    def testplugin(self):
        """ test loading with plugging"""
        l=Loader()
        self.assertEqual(l.__contains__('.tiff'),True)
        self.assertEqual(l.__contains__('.png'),True)
        self.assertEqual(l.__contains__('.txt'),True)
       