# This program is public domain
"""
    @organization: Module loader contains class Loader which uses 
    some readers to return values contained in a file readed.
    
"""
import imp,os,sys
import logging
import os.path
logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='loader_log.txt',
                    filemode='w')

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
                    (file, path, info) = imp.find_module(name, path)
                    module = imp.load_module( name, file, item, info )
                    if hasattr(module, "Reader"):
                        try:
                            plugins.append(module.Reader())
                        except:
                            logging.error("Error accessing Reader in %s\n  %s" % (name, sys.exc_value))
                except :
                    logging.error("Error importing %s\n  %s" % (name, sys.exc_value))
                finally:
                    if not file==None:
                        file.close()
    except:
        # Should raise and catch at a higher level and display error on status bar
        pass   
    return plugins


class Loader(object):
    """
        Loader class extracts data from a given file.
        This provides routines for opening files based on extension,
        and readers built-in file extensions.
        It uses functionalities for class Load
        @note: For loader to operate properly each readers used should 
        contain a class name "Reader" that contains a field call ext.
        Can be used as follow:
        L=Loader()
        self.assertEqual(l.__contains__('.tiff'),True)
        #Recieves data 
        data=L.load(path)
    """
    #Store instance of class Load
    __load = None
    
    
    class Load(object):
    
        def __init__(self):
            #Dictionary containing readers and extension as keys
            self.readers = {}
            #Load all readers in plugins
            self.__setitem__()
            
            
        def __setitem__(self,dir=None, ext=None, reader=None):
            """
                __setitem__  sets in a dictionary(self.readers) a given reader
                with a file extension that it can read.
                @param ext: extension given of type string
                @param reader:instance Reader class
                @param dir: directory name where plugins readers will be saved
                @raise : ValueError will be raise if a "plugins" directory is not found
                and the user didn't add a reader as parameter or if the user didn't 
                add a reader as a parameter and plugins directory doesn't contain
                plugin reader.
                if an extension is not specified and a reader does not contain a field
                ext , a ValueError "missing extension" is raised.
                @note: when called without parameters __setitem__ will try to load
                readers inside a "readers" directory 
                if call with a directory name will try find readers 
                from that directory "dir"
            """
            if dir==None:
                dir='readers'
            
            if (reader==None and  ext==None) or dir:#1st load
                plugReader=None
                if os.path.isdir(dir):
                    plugReader=_findReaders(dir)# import all module in plugins
                if os.path.isdir('../'+dir):
                    plugReader=_findReaders('../'+dir)
                else:
                    if os.path.isdir('../DataLoader/'+dir):
                        os.chdir(os.path.abspath('../DataLoader/'+dir))# change the current 
                        plugReader=_findReaders(dir)
                       
                if plugReader !=None:
                    for preader in plugReader:# for each modules takes list of extensions
                        try:
                            list=preader.ext
                        except:
                            raise AttributeError," %s instance has no attribute 'ext'"\
                            %(preader.__class__)
                        for item in list:
                            ext=item
                            if ext not in self.readers:#assign extension with its reader
                                self.readers[ext] = []
                            self.readers[ext].insert(0,preader)
            #Reader and extension are given
            elif reader !=None and  ext !=None:
                if ext not in self.readers:
                    self.readers[ext] = []
                self.readers[ext].insert(0,reader)
            elif reader!=None:
                #only reader is receive try to find a field ext
                try:
                    list=preader.ext
                except:
                    raise AttributeError," Reader instance has no attribute 'ext'"
                for item in list:
                
                    ext=item
                    if ext not in self.readers:#assign extension with its reader
                        self.readers[ext] = []
                    self.readers[ext].insert(0,reader)

            else:
                raise ValueError,"missing reader"
                
            
        def __getitem__(self, ext):
            """
                __getitem__ get a list of readers that can read a file with that extension
                @param ext: file extension
                @return self.readers[ext]:list of readers that can read a file 
                with that extension
            """
            return self.readers[ext]
            
        def __contains__(self, ext):
            """
                @param ext:file extension
                @return: True or False whether there is a reader file with that extension
            """
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
                
                raise RuntimeError, "Unknown file type '%s'"%ext
                
       
        
        def load(self, path, format=None):
            """
                Call reader for the file type of path.
                @param path: path to file to load
                @param format: extension of file to load
                @return Data if sucessful
                  or None is not reader was able to read that file
                Raises ValueError if no reader is available.
                May raise a loader-defined exception if loader fails.
            """
            try:
                os.path.isfile( os.path.abspath(path)) 
            except:
                raise ValueError," file  path unknown"
            
            if format is None:
                try:
                    readers = self.lookup(path)
                except ValueError,msg:
                    raise ValueError,str(msg)
            else:
                readers = self.readers[format]
            if readers!=None:
                for fn in readers:
                    try:
                        value=fn.read(path)
                        return value
                    except ValueError,msg:
                        logging.error(str(msg))
            else:
                raise ValueError,"Loader contains no reader"
                        
                         
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
