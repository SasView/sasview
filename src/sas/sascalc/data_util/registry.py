"""
File extension registry.

This provides routines for opening files based on extension,
and registers the built-in file extensions.
"""
from __future__ import print_function

from sas.sascalc.dataloader.loader_exceptions import NoKnownLoaderException


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
        self.loaders[ext].insert(0, loader)

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

        :param path: Data file path
        :return: List of available readers for the file extension (maybe empty)
        """
        # Find matching lower-case extensions
        path_lower = path.lower()
        extlist = [ext for ext in self.extensions() if path_lower.endswith(ext)]
        # Sort matching extensions by decreasing order of length
        extlist.sort(key=len)
        # Combine loaders for matching extensions into one big list
        loaders = []
        for L in [self.loaders[ext] for ext in extlist]:
            loaders.extend(L)
        # Remove duplicates if they exist
        if len(loaders) != len(set(loaders)):
            result = []
            for L in loaders:
                if L not in result:
                    result.append(L)
            loaders = result
        return loaders

    def load(self, path, format=None):
        """
        Call the loader for the file type of path.

        Raises an exception if the loader fails or if no loaders are defined
        for the given path or format.
        """
        if format is None:
            loaders = self.lookup(path)
            if not loaders:
                raise NoKnownLoaderException("No loaders match extension in %r"
                                             % path)
        else:
            loaders = self.loaders.get(format.lower(), [])
            if not loaders:
                raise NoKnownLoaderException("No loaders match format %r"
                                             % format)
        last_exc = None
        for fn in loaders:
            try:
                return fn(path)
            except Exception as e:
                last_exc = e
                pass  # give other loaders a chance to succeed
        # If we get here it is because all loaders failed
        raise last_exc
