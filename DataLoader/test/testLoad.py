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
class testLoader(unittest.TestCase):
   
        
    """ test fitting """
    #Creating a loader
    L=Loader()
    
    #creating readers
    read1=TXT2_Reader.Reader()
    read2=TXT3_Reader.Reader()
    read3=IgorReader.Reader()
    read4=danse_reader.Reader()
    read5=tiff_reader.Reader()
    #for each readers set an extensions inside the loader
    L.__setitem__('.txt',read2)
    L.__setitem__('.txt',read1)
    L.__setitem__('.dat',read1)
    
    L.__setitem__('.dat',read2)
    L.__setitem__('.ASC',read3)
    L.__setitem__('.sans',read4)
    L.__setitem__('.tif',read5)
    L.__setitem__('.jpg',read5)
    L.__setitem__('.png',read5)
    L.__setitem__('.jpeg',read5)
    L.__setitem__('.gif',read5)
    L.__setitem__('.bmp',read5)
       
    def testLoad1(self):
        """test reading empty file, no file can read it"""
        self.assertEqual(self.L.load('empty.txt'),None)
        self.assertEqual( self.L.getAcTReader('empty.txt'),None)
         
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
        self.assertEqual( self.L.getAcTReader('test_2_columns.txt'),self.read1.__class__)
    
    def testLoad2(self):
        """Testing loading a txt file of 3 columns, the only reader should be read2"""
        xload,yload,dyload= self.L.load('test_3_columns.txt') 
        x=[0,0.204082,0.408163,0.612245,0.816327,1.02041,1.22449]    
        y=[2.83954,3.44938,5.82026,5.27591,5.2781,5.22531,7.47487]
        dx=[]
        dy=[0.6,0.676531,0.753061,0.829592,0.906122,0.982653,1.05918]
        self.assertEqual(len(xload),len(x))
        self.assertEqual(len(yload),len(y))
        self.assertEqual(len(dyload),len(dy))
        for i in range(len(x)):
            self.assertEqual(xload[i],x[i])
            self.assertEqual(yload[i],y[i])
            self.assertEqual(dyload[i],dy[i])
        self.assertEqual(self.L.getAcTReader('test_3_columns.txt'),self.read2.__class__)
    
    def testload3(self):
        """ Testing loading Igor data"""
        #tested good file.asc
        Z,xmin, xmax, ymin, ymax= self.L.load('MAR07232_rest.ASC') 
        self.assertEqual(xmin,-0.018558945804750416)
        self.assertEqual(xmax, 0.016234058202440633,)
        self.assertEqual(ymin,-0.01684257151702391)
        self.assertEqual(ymax,0.017950440578015116)
        self.assertEqual(self.L.getAcTReader('MAR07232_rest.ASC'),self.read3.__class__)
        #tested corrupted file.asc
        self.assertEqual(self.L.load('AR07232_rest.ASC') ,None)
    
    def testload4(self):
        """ Testing loading danse file"""
        #tested good file.sans
        data=self.L.load('MP_New.sans')
        
        self.assertEqual(data.__class__,danse_reader.ReaderInfo)
        self.assertEqual(self.L.getAcTReader('MP_New.sans'),self.read4.__class__)
        #tested corrupted file.sans
        self.assertEqual(self.L.load('P_New.sans'),None)
    
    def testload5(self):
        """ Testing loading image file"""
        data=self.L.load('angles_flat.png')
        self.assertEqual(data.__class__,tiff_reader.ReaderInfo)
        self.assertEqual(self.L.getAcTReader('angles_flat.png'),self.read5.__class__)
   
   