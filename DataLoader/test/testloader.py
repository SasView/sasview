"""
    Unit tests for fitting module 
"""
import unittest
import math
import DataLoader
from DataLoader.loader import  Loader
from DataLoader.readers import TXT3_Reader,TXT2_Reader
from DataLoader.readers import DataReader,danse_reader,tiff_reader



class testFitModule(unittest.TestCase):
    """ test fitting """
    def testLoader(self):
        """ 
            test module Load
        """
        L=Loader()
        
        read1=TXT2_Reader.Reader()
        read2=TXT3_Reader.Reader()
        read3=DataReader.Reader()
        read4=danse_reader.Reader()
        read5=tiff_reader.Reader()
        
        L.setFormat('.txt',read1)
        L.setFormat('.txt',read2)
        
        L.setFormat('.dat',read2)
        L.setFormat('.dat',read1)
        
        L.setFormat('.ASC',read3)
        L.setFormat('.sans',read4)
        L.setFormat('.tif',read5)
        L.setFormat('.jpg',read5)
        L.setFormat('.png',read5)
        L.setFormat('.jpeg',read5)
        L.setFormat('.gif',read5)
        L.setFormat('.bmp',read5)
        
        
        self.assertEqual(L.loadData('empty.txt'),None) 
        print L.loadData('test_2_columns.txt') 
        self.assertEqual( L.getActiveReader('test_2_columns.txt'),DataLoader.readers.TXT2_Reader.Reader)
        print L.loadData('test_3_columns.txt') 
        self.assertEqual( L.getActiveReader('test_3_columns.txt'),DataLoader.readers.TXT3_Reader.Reader)
        print L.loadData('test_2_columns.date')
        self.assertEqual( L.getActiveReader('test_2_columns.date'),None) 
        print L.loadData('MAR07232_rest.ASC') 
        self.assertEqual( L.getActiveReader('MAR07232_rest.ASC'),DataLoader.readers.DataReader.Reader)
        #error test
        print L.loadData('AR07232_rest.ASC')
        self.assertEqual( L.getActiveReader('test_3_columns.txt'),None) 
        print L.loadData('MP_New.sans') 
        self.assertEqual( L.getActiveReader('MP_New.sans'),DataLoader.readers.read4.Reader)
        print L.loadData('P_New.sans') 
        self.assertEqual( L.getActiveReader('P_New.sans'),None)
        print L.loadData('angles_flat.png') 
        self.assertEqual(L.getActiveReader('angles_flat.png'),DataLoader.readers.tiff_reader.Reader)
        
    
    