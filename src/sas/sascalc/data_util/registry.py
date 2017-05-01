# This program is public domain
"""
File extension registry.

This provides routines for opening files based on extension,
and registers the built-in file extensions.
"""
from __future__ import print_function

import os.path

class ExtensionRegistry(object):
    """
    Associate a file loader with an extension.

    Note that there may be multiple loaders for the same extension.

    Example: ::

        registry = ExtensionRegistry()

        # Add an association by setting an element
        registry['.zip'] = unzip
        
        # Multiple extensions for one loader
        registry['.tgz'] = untar
        registry['.tar.gz'] = untar

        # Generic extensions to use after trying more specific extensions; 
        # these will be checked after the more specific extensions fail.
        registry['.gz'] = gunzip

        # Multiple loaders for one extension
        registry['.cx'] = cx1
        registry['.cx'] = cx2
        registry['.cx'] = cx3

        # Show registered extensions
        print registry.extensions()
        
        # Can also register a format name for explicit control from caller
        registry['cx3'] = cx3
        print registry.formats()

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
    def __init__(self, **kw):
        self.loaders = {}
    def __setitem__(self, ext, loader):
        if ext not in self.loaders:
            self.loaders[ext] = []
        self.loaders[ext].insert(0,loader)
    def __getitem__(self, ext):
        return self.loaders[ext]
    def __contains__(self, ext):
        return ext in self.loaders
    def formats(self):
        """
        Return a sorted list of the registered formats.
        """
        names = [a for a in self.loaders.keys() if not a.startswith('.')]
        names.sort()
        return names
    def extensions(self):
        """
        Return a sorted list of registered extensions.
        """
        exts = [a for a in self.loaders.keys() if a.startswith('.')]
        exts.sort()
        return exts
    def lookup(self, path):
        """
        Return the loader associated with the file type of path.
        
        Raises ValueError if file type is not known.
        """        
        # Find matching extensions
        extlist = [ext for ext in self.extensions() if path.endswith(ext)]
        # Sort matching extensions by decreasing order of length
        extlist.sort(lambda a,b: len(a)<len(b))
        # Combine loaders for matching extensions into one big list
        loaders = []
        for L in [self.loaders[ext] for ext in extlist]:
            loaders.extend(L)
        # Remove duplicates if they exist
        if len(loaders) != len(set(loaders)):
            result = []
            for L in loaders:
                if L not in result: result.append(L)
            loaders = L
        # Raise an error if there are no matching extensions
        if len(loaders) == 0:
            raise ValueError("Unknown file type for "+path)
        # All done
        return loaders
    def load(self, path, format=None):
        """
        Call the loader for the file type of path.

        Raises ValueError if no loader is available.
        Raises KeyError if format is not available.
        May raise a loader-defined exception if loader fails.        
        """
        if format is None:
            loaders = self.lookup(path)
        else:
            loaders = self.loaders[format]
        for fn in loaders:
            try:
                return fn(path)
            except:
                pass # give other loaders a chance to succeed
        # If we get here it is because all loaders failed
        raise # reraises last exception

def test():
    reg = ExtensionRegistry()
    class CxError(Exception): pass
    def cx(file): return 'cx'
    def new_cx(file): return 'new_cx'
    def fail_cx(file): raise CxError
    def cat(file): return 'cat'
    def gunzip(file): return 'gunzip'
    reg['.cx'] = cx
    reg['.cx1'] = cx
    reg['.cx'] = new_cx
    reg['.gz'] = gunzip
    reg['.cx.gz'] = new_cx
    reg['.cx1.gz'] = fail_cx
    reg['.cx1'] = fail_cx
    reg['.cx2'] = fail_cx
    reg['new_cx'] = new_cx

    # Two loaders associated with .cx
    assert reg.lookup('hello.cx') == [new_cx,cx]
    # Make sure the last loader applies first
    assert reg.load('hello.cx') == 'new_cx'
    # Make sure the next loader applies if the first fails
    assert reg.load('hello.cx1') == 'cx'
    # Make sure the format override works
    assert reg.load('hello.cx1',format='.cx.gz') == 'new_cx'
    # Make sure the format override works
    assert reg.load('hello.cx1',format='new_cx') == 'new_cx'
    # Make sure the case of all loaders failing is correct
    try:  reg.load('hello.cx2')
    except CxError: pass # correct failure
    else: raise AssertError("Incorrect error on load failure")
    # Make sure the case of no loaders fails correctly
    try: reg.load('hello.missing')
    except ValueError,msg:
        assert str(msg)=="Unknown file type for hello.missing",'Message: <%s>'%(msg)
    else: raise AssertError("No error raised for missing extension")
    assert reg.formats() == ['new_cx']
    assert reg.extensions() == ['.cx','.cx.gz','.cx1','.cx1.gz','.cx2','.gz']
    # make sure that it supports multiple '.' in filename
    assert reg.load('hello.extra.cx1') == 'cx'
    assert reg.load('hello.gz') == 'gunzip'
    assert reg.load('hello.cx1.gz') == 'gunzip' # Since .cx1.gz fails

if __name__ == "__main__": test()
