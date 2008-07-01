# This program is public domain
"""
File extension registry.

This provides routines for opening files based on extension,
and registers the built-in file extensions.
"""
import logging
import os.path

class ExtensionRegistry(object):
    """
    Associate a file loader with an extension.

    Note that there may be multiple loaders for the same extension.

    Example:

    registry = ExtensionRegistry()

    # Add an association by setting an element
    registry['.zip'] = unzip

    # Multiple extensions for one loader
    registry['.tgz'] = untar
    registry['.tar.gz'] = untar

    # Multiple loaders for one extension
    registry['.cx'] = cx1
    registry['.cx'] = cx2
    registry['.cx'] = cx3
    
    # Can also register a format name for explicit control from caller
    registry['cx3'] = cx3

    # Retrieve loaders for a file name
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
        self.loaders = {}
        self.reader=None
    def __setitem__(self, ext, loader):
        if ext not in self.loaders:
            self.loaders[ext] = []
        self.loaders[ext].insert(0,loader)
    def __getitem__(self, ext):
        return self.loaders[ext]
    def __contains__(self, ext):
        return ext in self.loaders
    def formats(self, name=True, ext=False):
        """
        Return a list of the registered formats.  If name=True then
        named formats are returned.  If ext=True then extensions
        are returned.
        """
        names = [a for a in self.loaders.keys() if not a.startswith('.')]
        exts = [a for a in self.loaders.keys() if a.startswith('.')]
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
            return self.loaders[ext]
        except:
            #raise ValueError, "Unknown file type '%s'"%ext
            print  "Unknown file type '%s'"%ext
        
    def loads(self, path, format=None):
        """
        Call the loader for the file type of path.

        Raises ValueError if no loader is available.
        May raise a loader-defined exception if loader fails.
        """
        if format is None:
            loaders = self.lookup(path)
        else:
            loaders = self.loaders[format]
        for fn in loaders:
            print fn
            try:
                value=fn.read(path)
                self.reader= fn
                return value 
            except ValueError,msg:
                #pass
                print str(msg)
    def getAcTReader(self,path):
        return self.reader
    def load(self, path, format=None):
        """
        Call the loader for the file type of path.

        Raises ValueError if no loader is available.
        May raise a loader-defined exception if loader fails.
        """
        if format is None:
            loaders = self.lookup(path)
        else:
            loaders = self.loaders[format]
        if loaders!=None:
            for fn in loaders:
                try:
                    value=fn.read(path)
                    self.reader= fn.__class__
                    return value
                    #value=fn.read(path)
                    #return value 
                except ValueError,msg:
                    #pass
                    print str(msg)
