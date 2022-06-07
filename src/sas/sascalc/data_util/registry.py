"""
File extension registry.

This provides routines for opening files based on extension,
and registers the built-in file extensions.
"""

from typing import Optional
from collections import defaultdict

from sas.sascalc.dataloader.loader_exceptions import NoKnownLoaderException



class ExtensionRegistry:
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
    def __init__(self):
        self.readers = defaultdict(list)

    def __setitem__(self, ext, loader):
        self.readers[ext].insert(0, loader) # TODO: Why insert at zero, not just append?

    def __getitem__(self, ext):
        return self.readers[ext]

    def __contains__(self, ext: str):
        return ext in self.readers

    def formats(self):
        """
        Return a sorted list of the registered formats.
        """
        names = [a for a in self.readers.keys() if not a.startswith('.')] # What is this doing?
        names.sort()
        return names

    def extensions(self):
        """
        Return a sorted list of registered extensions.
        """
        exts = [a for a in self.readers.keys() if a.startswith('.')]
        exts.sort()
        return exts

    def lookup(self, path: str):
        """
        Return the loader associated with the file type of path.

        :param path: Data file path
        :return: List of available readers for the file extension (maybe empty)
        """

        # Find matching lower-case extensions
        path_lower = path.lower()
        extensions = [ext for ext in self.extensions() if path_lower.endswith(ext)]

        # Sort matching extensions by decreasing order of length # TODO: Again, why???
        extensions.sort(key=len)

        # Combine loaders for matching extensions into one big list
        loaders = [loader for ext in extensions for loader in self.readers[ext]]

        # Remove duplicates and return
        return list(set(loaders))

    def load(self, path, format: Optional[str]=None):
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
            loaders = self.readers.get(format.lower(), [])
            if not loaders:
                raise NoKnownLoaderException("No loaders match format %r"
                                             % format)
        last_exc = None
        for load_function in loaders:
            try:
                return load_function(path)
            except Exception as e:
                last_exc = e
                pass  # give other loaders a chance to succeed
        # If we get here it is because all loaders failed
        raise last_exc
