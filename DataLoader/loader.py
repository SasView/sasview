from register import ExtensionRegistry
import TXT3_Reader, TXT2_Reader,DataReader
import danse_reader
import tiff_reader
#import tiff_reader
class Loader:
    def __init__(self):
        """ init method"""
        self.reg=ExtensionRegistry()
    def setFormat(self,ext,reader):
        """ 
            Load the available reader with file extensions
            @param ext:file extension
            @param reader: instance of a reader
        """
        #self.reg[ext]=reader
        self.reg.__setitem__(ext, reader)
    def getReader(self,ext):
        return self.reg.__getitem__( ext)
        
    
    def loadData(self,path,format=None):
        """ Read a file and save values"""
        self.reg.lookup(path)
        try:  
            return self.reg.load(path,format)
        except ValueError,msg:
            print msg
        
        
    def getextension(self,name=False,ext=True):
        """ return list of readers"""
        return self.reg.formats(name,ext) 
def test():
    L=Loader()
    
    read1=TXT2_Reader.Reader()
    read2=TXT3_Reader.Reader()
    read3=DataReader.DataReader()
    read4=danse_reader.DataReader()
    read5=tiff_reader.DataReader()
    
    L.setFormat('.txt',read1)
    L.setFormat('.txt',read2)
    
    L.setFormat('.dat',read2)
    L.setFormat('.dat',read1)
    
    L.setFormat('.ASC',read3)
    L.setFormat('.sans',read4)
    L.setFormat('.sans',read5)
    L.setFormat('.tif',read5)
    L.setFormat('.jpg',read5)
    L.setFormat('.png',read5)
    L.setFormat('.jpeg',read5)
    L.setFormat('.gif',read5)
    L.setFormat('.bmp',read5)
    
    
    
    print L.loadData('testdata_line.txt') 
    print L.loadData('test.dat') 
    print L.loadData('test.date') 
    print L.loadData('MAR07232_rest.ASC') 
    print L.loadData('AR07232_rest.ASC') 
    print L.loadData('MP_New.sans') 
    print L.loadData('P_New.sans') 
    print L.loadData('angles_flat.png') 
    
    
    


if __name__ == "__main__": test()
