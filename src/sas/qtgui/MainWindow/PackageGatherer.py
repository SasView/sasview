import logging
import pathlib
import sys

import pkg_resources

import sas
import sas.system.version

logger = logging.getLogger(__name__)

class PackageGatherer:
    """ A class used to gather packages/modules  used by SasView and their current installed version

    :method log_installed_packages: Log version number of locally installed python packages
    :method log_imported_packages: Log version number of python packages imported in this instance of SasView.
    :method get_imported_packages: Get a dictionary of imported module version numbers
    :method remove_duplicate_modules: Strip duplicate instances of each module
    :method format_unattainable_packages_list: Format module names in the unattainable_modules list
    """

    def log_installed_modules(self):
        """ Log version number of locally installed python packages

        Use pip list to create a dictionary of installed modules as the keys, with their respective version numbers
        as the values. Only packages available through pip will be included.

        :returns:Nothing
        :rtype: None
        """

        # Get python modules installed locally

        installed_packages = pkg_resources.working_set

        python_str = f'python:{sys.version}\n'
        print_str = "\n".join(f"{package.key}: {package.version}" for package in installed_packages)
        msg = f"Installed packages:\n{python_str+print_str}"
        logger.info(msg)


    def log_imported_packages(self):
        """ Log version number of python packages imported in this instance of SasView.

        Use the get_imported_packages method to to create a dictionary of installed modules as the keys, with their
        respective version numbers as the values. There may be some packages whose version number is unattainable.

        :returns: Nothing
        :rtype: None
        """
        imported_packages_dict = self.get_imported_packages()

        res_str = "\n".join(f"{module}: {version_num}" for module, version_num
                            in imported_packages_dict["results"].items())
        no_res_str = "\n".join(f"{module}: {version_num}" for module, version_num
                               in imported_packages_dict["no_results"].items())
        errs_res_str = "\n".join(f"{module}: {version_num}" for module, version_num
                                 in imported_packages_dict["errors"].items())

        msg = f"Imported modules:\n {res_str}\n {no_res_str}\n {errs_res_str}"
        logger.info(msg)


    def get_imported_packages(self):
        """ Get a dictionary of imported package version numbers

        Use a variety of method, for example a module.version call, to attempt to get the module version of each
        module that has been imported in this instance of running SasView. The sys.modules command lists the
        imported modules. A list of modules whose version number cannot be found is also included.

        :returns: A dictionary with the package names as the key, with their respective version numbers as the value.
        :rtype: dict
        """
        package_versions_dict = {'python': sys.version, 'SasView': sas.system.version.__version__}
        err_version_dict = {}
        no_version_list = []
        # Generate a list of standard modules by looking at the local python library
        try:
            standard_lib = [path.stem.split('.')[0] for path in pathlib.Path(pathlib.__file__)
                            .parent.absolute().glob('*')]
        except Exception:
            standard_lib = ['abc', 'aifc', 'antigravity', 'argparse', 'ast', 'asynchat', 'asyncio', 'asyncore',
                            'base64', 'bdb', 'binhex', 'bisect', 'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmd',
                            'code', 'codecs', 'codeop', 'collections', 'colorsys', 'compileall', 'concurrent',
                            'configparser', 'contextlib', 'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt',
                            'csv', 'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib',
                            'dis', 'distutils', 'doctest', 'email', 'encodings', 'ensurepip', 'enum', 'filecmp',
                            'fileinput', 'fnmatch', 'formatter', 'fractions', 'ftplib', 'functools', 'genericpath',
                            'getopt', 'getpass', 'gettext', 'glob', 'graphlib', 'gzip', 'hashlib', 'heapq', 'hmac',
                            'html', 'http', 'idlelib', 'imaplib', 'imghdr', 'importlib', 'inspect', 'io',
                            'ipaddress', 'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging', 'lzma',
                            'mailbox', 'mailcap', 'mimetypes', 'modulefinder', 'msilib', 'multiprocessing', 'netrc',
                            'nntplib', 'ntpath', 'nturl2path', 'numbers', 'opcode', 'operator', 'optparse', 'os',
                            'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil', 'platform', 'plistlib',
                            'poplib', 'posixpath', 'pprint', 'profile', 'pstats', 'pty', 'pyclbr', 'pydoc',
                            'pydoc_data', 'py_compile', 'queue', 'quopri', 'random', 're', 'reprlib', 'rlcompleter',
                            'runpy', 'sched', 'secrets', 'selectors', 'shelve', 'shlex', 'shutil', 'signal',
                            'site-packages', 'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'sqlite3',
                            'sre_compile', 'sre_constants', 'sre_parse', 'ssl', 'stat', 'statistics', 'string',
                            'stringprep', 'struct', 'subprocess', 'sunau', 'symbol', 'symtable', 'sysconfig',
                            'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'test', 'textwrap', 'this', 'threading',
                            'timeit', 'tkinter', 'token', 'tokenize', 'trace', 'traceback', 'tracemalloc', 'tty',
                            'turtle', 'turtledemo', 'types', 'typing', 'unittest', 'urllib', 'uu', 'uuid', 'venv',
                            'warnings', 'wave', 'weakref', 'webbrowser', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc',
                            'zipapp', 'zipfile', 'zipimport', 'zoneinfo', '_aix_support', '_bootlocale',
                            '_bootsubprocess', '_collections_abc', '_compat_pickle', '_compression', '_markupbase',
                            '_osx_support', '_pydecimal', '_pyio', '_py_abc', '_sitebuiltins', '_strptime',
                            '_threading_local', '_weakrefset', '__future__', '__phello__', '__pycache__']
        standard_lib.extend(sys.builtin_module_names)
        standard_lib.append("sas")

        for module_name in sys.modules.keys():

            package_name = module_name.split('.')[0]

            # A built in python module or a local file, which have no version, only the python/SasView version
            if package_name in standard_lib or package_name in package_versions_dict:
                continue

            # Import module
            try:
                package = __import__(package_name)
            except Exception as e:
                err_version_dict[package_name] = f"Unknown: {e} when attempting to import module"
                continue

            # Retrieving the modules version using the __version__ attribute
            if hasattr(package, '__version__'):
                # Module has __version__ attribute
                try:
                    package_versions_dict[package_name] = package.__version__
                    continue
                except Exception as e:
                    # Unable to access module
                    err_version_dict[package_name] = f"Unknown: {e} when attempting to access {package_name} " \
                                                     f"version using .__version__"
                    pass

            # Retrieving the modules version using the pkg_resources package
            # Unreliable, so second option
            try:
                package_versions_dict[package_name] = pkg_resources.get_distribution(package_name).version
            except Exception:
                # Modules that cannot be found by pkg_resources
                pass
            else:
                continue

            # Modules version number could not be attained by any of the previous methods

            no_version_list.append(package_name)

            # Currently not required for any packages used by SasView
            # Retrieving the modules version using the version attribute
            # if hasattr(package, 'version'):
            #     # Module has version attribute
            #     try:
            #         if isinstance(package.version, str):
            #             print(package)
            #             package_versions_dict[package_name] = package.version
            #             continue
            #     except Exception as e:
            #         # Unable to access module
            #         err_version_dict[package_name] = f"Unknown: {e} when attempting to access {package_name} " \
            #                                          f"version using .version"
            #         pass

        # Clean up
        package_versions_dict = self.remove_duplicate_modules(package_versions_dict)
        no_version_dict = self.format_no_version_list(package_versions_dict, no_version_list)

        return {"results": package_versions_dict, "no_results": no_version_dict, "errors": err_version_dict}


    def remove_duplicate_modules(self, modules_dict):
        """ Strip duplicate instances of each module

        Multiple instances of one module can be keys  of the dictionary of module version numbers generated by the
        method get_imported_packages. This is because if an individual class is imported from a module, then each class
        would be listed in sys.modules. For example the command from PySide6.QtWidgets import QMainWindow,  QMdiArea
        lead to both QMainWindow and QMdiArea being keys, when in reality they are both part of PySide6. This method
        save the first instance of each module, unless the version numbers are different.

        :param modules_dict: A dictionary with the module names as the key, with their respective version numbers as
            the value.
        :type modules_dict: dict

        :return: A reduced / cleaned dictionary with the module names as the key, with their respective version
            numbers as the value.
        :rtype: dict
        """
        output_dict = dict()

        for module_name in modules_dict.keys():
            parent_module = module_name.split('.')[0]
            # Save one instance of each module
            if parent_module not in output_dict:
                output_dict[parent_module] = modules_dict[module_name]
            else:
                # Modules versions are not the same
                if output_dict[parent_module] != modules_dict[module_name]:
                    output_dict[f"{parent_module}_from_{module_name}"] = modules_dict[module_name]
                pass

        return output_dict


    def format_no_version_list(self, modules_dict, no_version_list):
        """ Format module names in the no_version_list list

        The unattainable_modules is a list of modules whose version number could not be found. This method rename each
        module in the unattainable_modules to it's parent modules name, remove modules that already have a version
        number and remove duplicate modules from the no_version_list list. Entries may appear in the
        no_version_list if they are a class in a module, and the version number could not be ascertained from
        the class.

        :param modules_dict: A dictionary with the module names as the key, with their respective version numbers as
            the value.
        :type modules_dict: dict
        :param no_version_list: A list of modules whose version number could not be found.
        :type no_version_list: list

        :return: A reduced / clean list of modules whose version number could not be found
        :rtype: dict
        """

        output_dict = {}

        for module_name in no_version_list:
            parent_module = module_name.split('.')[0]
            # Version number exists for this module
            if parent_module in modules_dict.keys():
                pass
            # Module is already in output_list
            elif parent_module in output_dict:
                pass
            # Append module to output_list
            else:
                output_dict[module_name] = "Unknown: Version number could not be found"

        return output_dict
