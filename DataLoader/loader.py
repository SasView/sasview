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
                #print "in findplugings",path
                try:
                    (file, path, info) = imp.find_module(name, path)
                    module = imp.load_module( name, file, item, info )
                    if hasattr(module, "Reader"):
                        try:
                            plugins.append(module.Reader())
                        except:
                            log("Error accessing Reader in %s\n  %s" % (name, sys.exc_value))
                except :
                    log("Error importing %s\n  %s" % (name, sys.exc_value))
                finally:
                    if not file==None:
                        file.close()
    except:
        # Should raise and catch at a higher level and display error on status bar
        pass   
    return plugins
class Loader(object):
    
    __load = None
    class Load(object):
    
        def __init__(self):
            self.readers = {}
            self.reading=None
            self.__setitem__()
            #print "in loader",self.readers
            
        def __setitem__(self, ext=None, reader=None):
            import os
            if reader==None and  ext==None:#1st load
                plugReader=None
                if os.path.isdir('plugins'):
                    #print "plugreader in pluging",plugReader 
                    plugReader=_findReaders('plugins')# import all module in plugins
                if os.path.isdir('../plugins'):
                    #print "plugreader in Dataloader pluging",plugReader 
                    plugReader=_findReaders('../plugins')
                else:
                    if os.path.isdir('..\DataLoader\plugins'):
                        os.chdir(os.path.abspath('..\DataLoader\plugins'))# change the current 
                        #directory to dataLoader\plugins
                        plugReader=_findReaders('plugins')
                       
                if plugReader !=None:
                    for preader in plugReader:# for each modules takes list of extensions
                        print preader,preader.ext
                        for item in preader.ext:
                            ext=item
                            if ext not in self.readers:#assign extension with its reader
                                self.readers[ext] = []
                            self.readers[ext].insert(0,preader)
                            
                #print "plugreader",plugReader 
                #print "In setitem",self.readers
            elif reader !=None and  ext !=None:
                if ext not in self.readers:
                    self.readers[ext] = []
                self.readers[ext].insert(0,reader)
            elif reader!=None:
                for item in reader.ext:
                    ext=item
                    if ext not in self.readers:#assign extension with its reader
                        self.readers[ext] = []
                    self.readers[ext].insert(0,reader)
            else:
                raise ValueError,"missing reader"
            
            
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
            #print "exten",ext
            #print self.readers
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
            try:
                #print "in load",os.path.abspath(path)
                os.path.isfile( os.path.abspath(path)) 
                #print "went here in load check path"
            except:
                raise ValueError," file doesn't exist"
            if format is None:
                readers = self.lookup(path)
            else:
                readers = self.readers[format]
            if readers!=None:
            
                for fn in readers:
                    try:
                        #print "path",os.getcwd( )
                        value=fn.read(path)
                        self.reading= fn.__class__
                        return value
                    except ValueError,msg:
                        print str(msg)
    def __init__(self):
        """ Create singleton instance """
        # Check whether we already have an instance
        if Loader.__load is None:
            # Create and remember instance
            Loader.__load = Loader.Load()
            Loader.__load.__setitem__()
        # Store instance reference as the only member in the handle
        self.__dict__['_Loader__load'] = Loader.__load

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__load, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__load, attr, value)
