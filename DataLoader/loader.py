# This program is public domain
"""
File extension registry.

This provides routines for opening files based on extension,
and registers the built-in file extensions.
"""
import imp,os,sys
import logging
import os.path
def _findReaders(dir):
    # List of plugin objects
    plugins = []
    # Go through files in plug-in directory
    try:
        
        list = os.listdir(dir)
        for item in list:
            
            toks = os.path.splitext(os.path.basename(item))
            if toks[1]=='.py' and not toks[0]=='__init__':
                name = toks[0]
                path = [os.path.abspath(dir)]
                file = None
        
                try:
                    print"name",name 
                    print "path",path
                    print imp.find_module(name, path)
                    (file, path, info) = imp.find_module(name, path)
                    print"file",file
                    print "path", path
                    print "info",info
                    print"hasattr",imp.load_module( name, file, item, info )
                    module = imp.load_module( name, file, item, info )
                    print"module", module
    
                    if hasattr(module, "Reader"):
                        print "went here"
                        try:
                            plugins.append(module.Reader())
                        except:
                            log("Error accessing Reader in %s\n  %s" % (name, sys.exc_value))
                except :
                    print"Error importing %s\n  %s" % (name,sys.exc_value)
                    log("Error importing %s\n  %s" % (name, sys.exc_value))
                finally:
                    if not file==None:
                        file.close()
    except:
        # Should raise and catch at a higher level and display error on status bar
        pass   
    return plugins
class Loader(object):
    """
    Associate a file loader with an extension.

    Note that there may be multiple readers for the same extension.

    Example:

    registry = Loader()

    # Add an association by setting an element
    registry['.zip'] = unzip

    # Multiple extensions for one loader
    registry['.tgz'] = untar
    registry['.tar.gz'] = untar

    # Multiple readers for one extension
    registry['.cx'] = cx1
    registry['.cx'] = cx2
    registry['.cx'] = cx3
    
    # Can also register a format name for explicit control from caller
    registry['cx3'] = cx3

    # Retrieve readers for a file name
    registry.lookup('hello.cx') -> [cx3,cx2,cx1]

    # Run loader on a filename
    registry.load('hello.cx') ->
        try:
            return cx3('hello.cx')
        except:
            try:
                return cx2('hello.cx')
            except:
                return cx1('hello.cx')

    # Load in a specific format ignoring extension
    registry.load('hello.cx',format='cx3') ->
        return cx3('hello.cx')
    """
    def __init__(self):
        self.readers = {}
        self.reading=None
        
        
    def __setitem__(self, ext=None, reader=None):
        if reader==None:
            print os.getcwd()
            print  os.path.isdir('plugins')
            print "absolute path : ",os.path.abspath('plugins')
            plugReader=None
            if os.path.isdir('plugins'):
                print "went here"
                plugReader=_findReaders('plugins')# import all module in plugins
            elif os.path.isdir('../plugins'):
                plugReader=_findReaders('../plugins')
            if plugReader !=None:
                print "this is plugreader",plugReader
                for preader in plugReader:# for each modules takes list of extensions
                    #print preader.ext
                    for item in preader.ext:
                        ext=item
                        if ext not in self.readers:#assign extension with its reader
                            self.readers[ext] = []
                        self.readers[ext].insert(0,preader)
                        print "extension",ext
                        print "readers",self.readers
        else:
            if ext not in self.readers:
                self.readers[ext] = []
            self.readers[ext].insert(0,reader)
        
        
    def __getitem__(self, ext):
        return self.readers[ext]
        
    
    
    def __contains__(self, ext):
        return ext in self.readers
    
    
    def formats(self, name=True, ext=False):
        """
        Return a list of the registered formats.  If name=True then
        named formats are returned.  If ext=True then extensions
        are returned.
        """
        names = [a for a in self.readers.keys() if not a.startswith('.')]
        exts = [a for a in self.readers.keys() if a.startswith('.')]
        names.sort()
        exts.sort()
        ret = []
        if name: ret += names
        if ext: ret += exts
        return ret
        
    def lookup(self, path):
        """
        Return the loader associated with the file type of path.
        """        
        file = os.path.basename(path)
        idx = file.find('.')
        ext = file[idx:] if idx >= 0 else ''
        try:
            return self.readers[ext]
        except:
            #raise ValueError, "Unknown file type '%s'"%ext
            print  "Unknown file type '%s'"%ext
 
                
    def getAcTReader(self,path):
        return self.reading
    
    def load(self, path, format=None):
        """
        Call the loader for the file type of path.

        Raises ValueError if no loader is available.
        May raise a loader-defined exception if loader fails.
        """
        if format is None:
            readers = self.lookup(path)
        else:
            readers = self.readers[format]
        if readers!=None:
            for fn in readers:
                try:
                    value=fn.read(path)
                    self.reading= fn.__class__
                    return value
                except ValueError,msg:
                    print str(msg)
if __name__=="__main__":
    l=Loader()
    l.__setitem__()
    print "look up",l.lookup('angles_flat.png')
    print l.__getitem__('.tiff')
    print l.__contains__('.tiff')
    