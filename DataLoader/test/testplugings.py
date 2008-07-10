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
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='test_log.txt',
                    filemode='w')
class testLoader(unittest.TestCase):
    
    try:L=Loader()
    except AttributeError,msg:
        logging.warning(msg)
    def testplugin(self):
        """ test loading with readers"""
        
        self.assertEqual(self.L.__contains__('.tiff'),True)
        self.assertEqual(self.L.__contains__('.png'),True)
        self.assertEqual(self.L.__contains__('.txt'),True)
         #tested corrupted file.asc
        try:self.L.load('MAR07232_rest.ASC')
        except AttributeError,msg:
           #logging.log(10,str(msg))
           logging.warning(str(msg))
    def testplugin1(self):
        """ test loading with plugging"""
        self.L.__setitem__(dir='plugins')
        read3=IgorReader.Reader()
        self.L.__setitem__('plugins','.ASC',read3)
        self.assertEqual(self.L.__contains__('.ASC'),True)
        #Testing loading a txt file of 2 columns, the only reader should be read1 
        xload,yload,dyload=self.L.load('test_2_columns.txt') 
        x=[2.83954,0.204082,0.408163,0.612245,0.816327,1.02041,1.22449,1.42857,1.63265]
        y=[0.6,3.44938, 5.82026,5.27591,5.2781,5.22531,7.47487,7.85852,10.2278]
        dx=[]
        dy=[]
        self.assertEqual(len(xload),len(x))
        self.assertEqual(len(yload),len(y))
        self.assertEqual(len(dyload),0)
        for i in range(len(x)):
            self.assertEqual(xload[i],x[i])
            self.assertEqual(yload[i],y[i])