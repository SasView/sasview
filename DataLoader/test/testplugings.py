"""
    Unit tests for DataLoader module 
"""

import unittest
import math
import DataLoader
from DataLoader.loader import  SingleLoader
from DataLoader.readers import TXT3_Reader,TXT2_Reader
from DataLoader.readers import IgorReader,danse_reader,tiff_reader
import os.path
import os 
class testLoader(unittest.TestCase):
   
    def testplugin(self):
        """ test loading with plugging"""
        l=SingleLoader()
        self.assertEqual(l.__contains__('.tiff'),True)
        self.assertEqual(l.__contains__('.png'),True)
        self.assertEqual(l.__contains__('.txt'),True)
        #self.assertEqual(l.getAcTReader('angles_flat.png'),tiff_reader.Reader)
        #self.assertEqual(l.load('angles_flat.png').__class__,tiff_reader.ReaderInfo)
        #print l.load('_THETA_weights.txt') 