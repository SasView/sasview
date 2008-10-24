"""
    File handler to support different file extensions.
    Uses reflectometry's registry utility.
    
    The default readers are found in the 'readers' sub-module
    and registered by default at initialization time.
    
    To add a new default reader, one must register it in
    the register_readers method found in readers/__init__.py. 
    
    A utility method (find_plugins) is available to inspect 
    a directory (for instance, a user plug-in directory) and
    look for new readers/writers.
"""

"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2008, University of Tennessee
"""

from data_util.registry import ExtensionRegistry
import os 
import sys
import logging
import time
from zipfile import ZipFile

# Default readers are defined in the readers sub-module
import readers

class Registry(ExtensionRegistry):
    """
        Registry class for file format extensions.
        Readers and writers are supported.
    """
    
    def __init__(self):
        super(Registry, self).__init__()
        
        ## Writers
        self.writers = {}
        
        ## List of wildcards
        self.wildcards = ['All (*.*)|*.*']
        
        ## Creation time, for testing
        self._created = time.time()
        
        # Register default readers
        readers.register_readers(self._identify_plugin)
        
    def find_plugins(self, dir):
        """
            Find readers in a given directory. This method
            can be used to inspect user plug-in directories to
            find new readers/writers.
            
            @param dir: directory to search into
            @return: number of readers found
        """
        readers_found = 0
        
        # Check whether the directory exists
        if not os.path.isdir(dir): 
            logging.warning("DataLoader couldn't load from %s" % dir)
            return readers_found
        
        for item in os.listdir(dir):
            full_path = os.path.join(dir, item)
            if os.path.isfile(full_path):
                
                # Process python files
                if item.endswith('.py'):
                    toks = os.path.splitext(os.path.basename(item))
                    try:
                        sys.path.insert(0, os.path.abspath(dir))
                        module = __import__(toks[0], globals(), locals())
                        if self._identify_plugin(module):
                            readers_found += 1
                    except :
                        logging.error("Loader: Error importing %s\n  %s" % (item, sys.exc_value))
                            
                # Process zip files
                elif item.endswith('.zip'):
                    try:
                        # Find the modules in the zip file
                        zfile = ZipFile(item)
                        nlist = zfile.namelist()
                        
                        sys.path.insert(0, item)
                        for mfile in nlist:
                            try:
                                # Change OS path to python path
                                fullname = mfile.replace('/', '.')
                                fullname = os.path.splitext(fullname)[0]
                                module = __import__(fullname, globals(), locals(), [""])
                                if self._identify_plugin(module):
                                    readers_found += 1
                            except:
                                logging.error("Loader: Error importing %s\n  %s" % (mfile, sys.exc_value))
                            
                    except:
                        logging.error("Loader: Error importing %s\n  %s" % (item, sys.exc_value))
                     
        return readers_found 
    
    def _identify_plugin(self, module):
        """
            Look into a module to find whether it contains a 
            Reader class. If so, add it to readers and (potentially)
            to the list of writers.
            @param module: module object
        """
        reader_found = False
        
        if hasattr(module, "Reader"):
            try:
                # Find supported extensions
                loader = module.Reader()
                for ext in loader.ext:
                    if ext not in self.loaders:
                        self.loaders[ext] = []
                    self.loaders[ext].insert(0,loader.read)
                    reader_found = True
                        
                    # Keep track of wildcards
                    for wcard in loader.type:
                        if wcard not in self.wildcards:
                            self.wildcards.append(wcard)
                            
                # Check whether writing is supported
                if hasattr(loader, 'write'):
                    for ext in loader.ext:
                        if ext not in self.writers:
                            self.writers[ext] = []
                        self.writers[ext].insert(0,loader.write)
            except:
                logging.error("Loader: Error accessing Reader in %s\n  %s" % (name, sys.exc_value))
        return reader_found

    def lookup_writers(self, path):
        """
        Return the loader associated with the file type of path.
        
        Raises ValueError if file type is not known.
        """        
        # Find matching extensions
        extlist = [ext for ext in self.extensions() if path.endswith(ext)]
        # Sort matching extensions by decreasing order of length
        extlist.sort(lambda a,b: len(a)<len(b))
        # Combine loaders for matching extensions into one big list
        writers = []
        for L in [self.writers[ext] for ext in extlist]:
            writers.extend(L)
        # Remove duplicates if they exist
        if len(writers) != len(set(writers)):
            result = []
            for L in writers:
                if L not in result: result.append(L)
            writers = L
        # Raise an error if there are no matching extensions
        if len(writers) == 0:
            raise ValueError, "Unknown file type for "+path
        # All done
        return writers

    def save(self, path, data, format=None):
        """
        Call the writer for the file type of path.

        Raises ValueError if no writer is available.
        Raises KeyError if format is not available.
        May raise a writer-defined exception if writer fails.        
        """
        if format is None:
            writers = self.lookup_writers(path)
        else:
            writers = self.writers[format]
        for fn in writers:
            try:
                return fn(path, data)
            except:
                pass # give other loaders a chance to succeed
        # If we get here it is because all loaders failed
        raise # reraises last exception

        
class Loader(object):
    """
        Utility class to use the Registry as a singleton.
    """
    ## Registry instance
    __registry = Registry()
    
    def load(self, file, format=None):
        """
            Load a file
            
            @param file: file name (path)
            @param format: specified format to use (optional)
            @return: DataInfo object
        """
        return self.__registry.load(file, format)
    
    def save(self, file, data, format):
        """
            Save a DataInfo object to file
            @param file: file name (path)
            @param data: DataInfo object
            @param format: format to write the data in 
        """
        return self.__registry.save(file, data, format)
        
    def _get_registry_creation_time(self):
        """
            Internal method used to test the uniqueness
            of the registry object
        """
        return self.__registry._created
    
    def find_plugins(self, dir):
        """
            Find plugins in a given directory
            @param dir: directory to look into to find new readers/writers
        """
        return self.__registry.find_plugins(dir)
    
    def get_wildcards(self):
        return self.__registry.wildcards
        
if __name__ == "__main__": 
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='loader.log',
                        filemode='w')
    l = Loader()
    data = l.load('test/cansas1d.xml')
    l.save('test_file.xml', data, '.xml')
    
    print l.get_wildcards()
        
        
    