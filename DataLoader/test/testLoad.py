"""
    Unit tests for DataLoader module 
"""

import unittest
import math
import DataLoader
from DataLoader.loader import  Loader
from DataLoader.readers import TXT3_Reader,TXT2_Reader
from DataLoader.readers import DataReader,danse_reader,tiff_reader

class testLoader(unittest.TestCase):
    """ test fitting """
    def testLoad(self):
        """ 
            test module Load
        """
        #Creating a loader
        L=Loader()
        
        #creating readers
        read1=TXT2_Reader.Reader()
        read2=TXT3_Reader.Reader()
        read3=DataReader.Reader()
        read4=danse_reader.Reader()
        read5=tiff_reader.Reader()
        #for each readers set an extensions inside the loader
        L.__setitem__('.txt',read1)
        L.__setitem__('.dat',read1)
        L.__setitem__('.txt',read2)
        L.__setitem__('.dat',read2)
        L.__setitem__('.ASC',read3)
        L.__setitem__('.sans',read4)
        L.__setitem__('.tif',read5)
        L.__setitem__('.jpg',read5)
        L.__setitem__('.png',read5)
        L.__setitem__('.jpeg',read5)
        L.__setitem__('.gif',read5)
        L.__setitem__('.bmp',read5)
        
        #test reading empty file
        self.assertEqual(L.load('empty.txt'),None)
         
        #print L.loadData('test_2_columns.txt') 
        xload,yload,dyload=L.load('test_2_columns.txt') 
        x=[.83954,0.204082,0.408163,0.612245,0.816327,1.02041,1.22449,1.42857,1.63265]
        y=[0.6,3.44938, 5.82026,5.27591,5.2781,5.22531,7.47487,7.85852,10.2278]
        dx=[]
        dy=[]
        self.assertEqual(len(xload),len(x))
        self.assertEqual(len(yload),len(y))
        self.assertEqual( L.getAcTReader('test_2_columns.txt'),DataLoader.readers.TXT2_Reader.Reader)
        
        
        
        
        