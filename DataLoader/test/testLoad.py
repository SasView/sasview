"""
    Unit tests for DataLoader module 
    log file "test_log.txt" contains all errors when running loader
    It is create in the folder where test is runned
"""
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='test_log.txt',
                    filemode='w')


#logger.info('oops I did it again')

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
       
    def testLoad0(self):
        """test reading empty file"""
        self.assertEqual(self.L.load('empty.txt'),None)
        
    def testLoad1(self):
        """test reading 2 columns"""
        
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
       
    
    def testLoad2(self):
        """Testing loading a txt file of 3 columns"""
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
       
    
    def testload3(self):
        """ Testing loading Igor data"""
        #tested good file.asc
        Z,xmin, xmax, ymin, ymax= self.L.load('MAR07232_rest.ASC') 
        self.assertEqual(xmin,-0.018558945804750416)
        self.assertEqual(xmax, 0.016234058202440633,)
        self.assertEqual(ymin,-0.01684257151702391)
        self.assertEqual(ymax,0.017950440578015116)
       
        #tested corrupted file.asc
        try:self.L.load('AR07232_rest.ASC')
        except ValueError,msg:
           #logging.log(10,str(msg))
           logging.error(str(msg))
    def testload4(self):
        """ Testing loading danse file"""
        #tested good file.sans
        data=self.L.load('MP_New.sans')
        
        self.assertEqual(data.__class__,danse_reader.ReaderInfo)
        
        #tested corrupted file.sans
        try: self.L.load('P_New.sans')
        except ValueError,msg:
           #logging.log(40,str(msg))
           logging.error(str(msg))
        #else: raise ValueError,"No error raised for missing extension"
    def testload5(self):
        """ Testing loading image file"""
        data=self.L.load('angles_flat.png')
        self.assertEqual(data.__class__,tiff_reader.ReaderInfo)
        
    def testload6(self):
        """test file with unknown extension"""
        try:self.L.load('hello.missing')
        except ValueError,msg:
           self.assertEqual( str(msg),"Unknown file type '.missing'")
        else: raise ValueError,"No error raised for missing extension"
        
        #self.L.lookup('hello.missing')
        try: self.L.lookup('hello.missing')
        except ValueError,msg:
           self.assertEqual( str(msg),"Unknown file type '.missing'")
        else: raise ValueError,"No error raised for missing extension"
        
    def testload7(self):
        """ test file containing an image but as extension .txt"""
        self.assertEqual(self.L.load('angles_flat.txt'),None)
   