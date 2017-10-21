"""
    File handler to support different file extensions.
    Uses reflectometer registry utility.

    The default readers are found in the 'readers' sub-module
    and registered by default at initialization time.

    To add a new default reader, one must register it in
    the register_readers method found in readers/__init__.py.

    A utility method (find_plugins) is available to inspect
    a directory (for instance, a user plug-in directory) and
    look for new readers/writers.
"""
#####################################################################
# This software was developed by the University of Tennessee as part of the
# Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
# project funded by the US National Science Foundation.
# See the license text in license.txt
# copyright 2008, University of Tennessee
######################################################################

import os
import sys
import logging
import time
from zipfile import ZipFile

from sas.sascalc.data_util.registry import ExtensionRegistry

# Default readers are defined in the readers sub-module
from . import readers
from .loader_exceptions import NoKnownLoaderException, FileContentsException,\
    DefaultReaderException
from .readers import ascii_reader
from .readers import cansas_reader
from .readers import cansas_reader_HDF5

logger = logging.getLogger(__name__)


class Registry(ExtensionRegistry):
    """
    Registry class for file format extensions.
    Readers and writers are supported.
    """
    def __init__(self):
        super(Registry, self).__init__()

        # Writers
        self.writers = {}

        # List of wildcards
        self.wildcards = ['All (*.*)|*.*']

        # Creation time, for testing
        self._created = time.time()

        # Register default readers
        readers.read_associations(self)

    def load(self, path, format=None):
        """
        Call the loader for the file type of path.

        :param path: file path
        :param format: explicit extension, to force the use
            of a particular reader

        Defaults to the ascii (multi-column), cansas XML, and cansas NeXuS
        readers if no reader was registered for the file's extension.
        """
        # Gets set to a string if the file has an associated reader that fails
        msg_from_reader = None
        try:
            return super(Registry, self).load(path, format=format)
        #except Exception: raise  # for debugging, don't use fallback loader
        except NoKnownLoaderException as nkl_e:
            pass  # Try the ASCII reader
        except FileContentsException as fc_exc:
            # File has an associated reader but it failed.
            # Save the error message to display later, but try the 3 default loaders
            msg_from_reader = fc_exc.message
        except Exception:
            pass

        # File has no associated reader, or the associated reader failed.
        # Try the ASCII reader
        try:
            ascii_loader = ascii_reader.Reader()
            return ascii_loader.read(path)
        except DefaultReaderException:
            pass  # Loader specific error to try the cansas XML reader
        except FileContentsException as e:
            if msg_from_reader is None:
                raise RuntimeError(e.message)

        # ASCII reader failed - try CanSAS xML reader
        try:
            cansas_loader = cansas_reader.Reader()
            return cansas_loader.read(path)
        except DefaultReaderException:
            pass  # Loader specific error to try the NXcanSAS reader
        except FileContentsException as e:
            if msg_from_reader is None:
                raise RuntimeError(e.message)
        except Exception:
            pass

        # CanSAS XML reader failed - try NXcanSAS reader
        try:
            cansas_nexus_loader = cansas_reader_HDF5.Reader()
            return cansas_nexus_loader.read(path)
        except DefaultReaderException as e:
            logging.error("No default loader can load the data")
            # No known reader available. Give up and throw an error
            if msg_from_reader is None:
                msg = "\nUnknown data format: {}.\nThe file is not a ".format(path)
                msg += "known format that can be loaded by SasView.\n"
                raise NoKnownLoaderException(msg)
            else:
                # Associated reader and default readers all failed.
                # Show error message from associated reader
                raise RuntimeError(msg_from_reader)
        except FileContentsException as e:
            err_msg = msg_from_reader if msg_from_reader is not None else e.message
            raise RuntimeError(err_msg)

    def find_plugins(self, dir):
        """
        Find readers in a given directory. This method
        can be used to inspect user plug-in directories to
        find new readers/writers.

        :param dir: directory to search into
        :return: number of readers found
        """
        readers_found = 0
        temp_path = os.path.abspath(dir)
        if not os.path.isdir(temp_path):
            temp_path = os.path.join(os.getcwd(), dir)
        if not os.path.isdir(temp_path):
            temp_path = os.path.join(os.path.dirname(__file__), dir)
        if not os.path.isdir(temp_path):
            temp_path = os.path.join(os.path.dirname(sys.path[0]), dir)

        dir = temp_path
        # Check whether the directory exists
        if not os.path.isdir(dir):
            msg = "DataLoader couldn't locate DataLoader plugin folder."
            msg += """ "%s" does not exist""" % dir
            logger.warning(msg)
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
                    except:
                        msg = "Loader: Error importing "
                        msg += "%s\n  %s" % (item, sys.exc_value)
                        logger.error(msg)

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
                                module = __import__(fullname, globals(),
                                                    locals(), [""])
                                if self._identify_plugin(module):
                                    readers_found += 1
                            except:
                                msg = "Loader: Error importing"
                                msg += " %s\n  %s" % (mfile, sys.exc_value)
                                logger.error(msg)

                    except:
                        msg = "Loader: Error importing "
                        msg += " %s\n  %s" % (item, sys.exc_value)
                        logger.error(msg)

        return readers_found

    def associate_file_type(self, ext, module):
        """
        Look into a module to find whether it contains a
        Reader class. If so, APPEND it to readers and (potentially)
        to the list of writers for the given extension

        :param ext: file extension [string]
        :param module: module object
        """
        reader_found = False

        if hasattr(module, "Reader"):
            try:
                # Find supported extensions
                loader = module.Reader()
                if ext not in self.loaders:
                    self.loaders[ext] = []
                # Append the new reader to the list
                self.loaders[ext].append(loader.read)

                reader_found = True

                # Keep track of wildcards
                type_name = module.__name__
                if hasattr(loader, 'type_name'):
                    type_name = loader.type_name

                wcard = "%s files (*%s)|*%s" % (type_name, ext.lower(),
                                                ext.lower())
                if wcard not in self.wildcards:
                    self.wildcards.append(wcard)

                # Check whether writing is supported
                if hasattr(loader, 'write'):
                    if ext not in self.writers:
                        self.writers[ext] = []
                    # Append the new writer to the list
                    self.writers[ext].append(loader.write)

            except:
                msg = "Loader: Error accessing"
                msg += " Reader in %s\n  %s" % (module.__name__, sys.exc_value)
                logger.error(msg)
        return reader_found

    def associate_file_reader(self, ext, loader):
        """
        Append a reader object to readers

        :param ext: file extension [string]
        :param module: reader object
        """
        reader_found = False

        try:
            # Find supported extensions
            if ext not in self.loaders:
                self.loaders[ext] = []
            # Append the new reader to the list
            self.loaders[ext].append(loader.read)

            reader_found = True

            # Keep track of wildcards
            if hasattr(loader, 'type_name'):
                type_name = loader.type_name

                wcard = "%s files (*%s)|*%s" % (type_name, ext.lower(),
                                                ext.lower())
                if wcard not in self.wildcards:
                    self.wildcards.append(wcard)

        except:
            msg = "Loader: Error accessing Reader "
            msg += "in %s\n  %s" % (loader.__name__, sys.exc_value)
            logger.error(msg)
        return reader_found

    def _identify_plugin(self, module):
        """
        Look into a module to find whether it contains a
        Reader class. If so, add it to readers and (potentially)
        to the list of writers.
        :param module: module object

        """
        reader_found = False

        if hasattr(module, "Reader"):
            try:
                # Find supported extensions
                loader = module.Reader()
                for ext in loader.ext:
                    if ext not in self.loaders:
                        self.loaders[ext] = []
                    # When finding a reader at run time,
                    # treat this reader as the new default
                    self.loaders[ext].insert(0, loader.read)

                    reader_found = True

                    # Keep track of wildcards
                    type_name = module.__name__
                    if hasattr(loader, 'type_name'):
                        type_name = loader.type_name
                    wcard = "%s files (*%s)|*%s" % (type_name, ext.lower(),
                                                    ext.lower())
                    if wcard not in self.wildcards:
                        self.wildcards.append(wcard)

                # Check whether writing is supported
                if hasattr(loader, 'write'):
                    for ext in loader.ext:
                        if ext not in self.writers:
                            self.writers[ext] = []
                        self.writers[ext].insert(0, loader.write)

            except:
                msg = "Loader: Error accessing Reader"
                msg += " in %s\n  %s" % (module.__name__, sys.exc_value)
                logger.error(msg)
        return reader_found

    def lookup_writers(self, path):
        """
        :return: the loader associated with the file type of path.
        :Raises ValueError: if file type is not known.
        """
        # Find matching extensions
        extlist = [ext for ext in self.extensions() if path.endswith(ext)]
        # Sort matching extensions by decreasing order of length
        extlist.sort(key=len)
        # Combine loaders for matching extensions into one big list
        writers = []
        for L in [self.writers[ext] for ext in extlist]:
            writers.extend(L)
        # Remove duplicates if they exist
        if len(writers) != len(set(writers)):
            result = []
            for L in writers:
                if L not in result:
                    result.append(L)
            writers = L
        # Raise an error if there are no matching extensions
        if len(writers) == 0:
            raise ValueError("Unknown file type for " + path)
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
            except Exception:
                pass  # give other loaders a chance to succeed
        # If we get here it is because all loaders failed
        raise  # reraises last exception


class Loader(object):
    """
    Utility class to use the Registry as a singleton.
    """
    ## Registry instance
    __registry = Registry()

    def associate_file_type(self, ext, module):
        """
        Look into a module to find whether it contains a
        Reader class. If so, append it to readers and (potentially)
        to the list of writers for the given extension

        :param ext: file extension [string]
        :param module: module object
        """
        return self.__registry.associate_file_type(ext, module)

    def associate_file_reader(self, ext, loader):
        """
        Append a reader object to readers

        :param ext: file extension [string]
        :param module: reader object
        """
        return self.__registry.associate_file_reader(ext, loader)

    def load(self, file, format=None):
        """
        Load a file

        :param file: file name (path)
        :param format: specified format to use (optional)
        :return: DataInfo object
        """
        return self.__registry.load(file, format)

    def save(self, file, data, format):
        """
        Save a DataInfo object to file
        :param file: file name (path)
        :param data: DataInfo object
        :param format: format to write the data in
        """
        return self.__registry.save(file, data, format)

    def _get_registry_creation_time(self):
        """
        Internal method used to test the uniqueness
        of the registry object
        """
        return self.__registry._created

    def find_plugins(self, directory):
        """
        Find plugins in a given directory

        :param dir: directory to look into to find new readers/writers
        """
        return self.__registry.find_plugins(directory)

    def get_wildcards(self):
        """
        Return the list of wildcards
        """
        return self.__registry.wildcards
