from register import ExtensionRegistry

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
    def getActiveReader(self,path):
        return self.reg.getAcTReader(path)
    def getextension(self,name=False,ext=True):
        """ return list of readers"""
        return self.reg.formats(name,ext) 
