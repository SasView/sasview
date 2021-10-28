import sys, logging, subprocess, pkg_resources, json


class PackageGatherer:
    """
    A class used to gather packages/modules  used by SasView and their current installed version

    Methods
    -------
    log_installed_modules
        Log version number of locally installed python packages

    log_imported_modules
        Log version number of python packages imported in this instance of SasView.

    get_imported_modules
        Get a dictionary of imported module version numbers

    remove_duplicate_modules
        Strip duplicate instances of each module

    format_unattainable_modules_list
        Format module names in the unattainable_modules list
    """


    def log_installed_modules(self):
        """ Log version number of locally installed python packages

        Use pip list to create a dictionary of installed modules as the keys, with their respective version numbers
        as the values. Only packages available through pip will be included.

        Returns
        -------
        None
        """
        installed_modules = {'python': sys.version}

        # Get python modules installed locally
        installed_modules_json = json.loads(subprocess.check_output("pip list -l --format=json"))
        for mod in installed_modules_json:
            installed_modules[mod['name']] = mod['version']

        logging.info(f"Installed modules\n"
                     f"{installed_modules}")


    def log_imported_modules(self):
        """ Log version number of python packages imported in this instance of SasView.

        Use the get_imported_modules method to to create a dictionary of installed modules as the keys, with their
        respective version numbers as the values. There may be some packages whose version number is unattainable.

        Returns
        -------
        None
        """
        imported_modules = self.get_imported_modules()

        logging.info(f"Imported modules\n"
                     f"{imported_modules}")


    def get_imported_modules(self):
        """ Get a dictionary of imported module version numbers

        Use a variaty of method, for example a module.version call, to attempt to get the module version of each
        module that has been imported in this instance of running SasView. The sys.modules command lists the
        imported modules. A list of modules who's version number cannot be found is also included.

        Returns
        -------
        module_versions_dict : dict
            A dictionary with the module names as the key, with their respective version numbers as the value.
        """

        module_versions_dict = {'python': sys.version}
        unattainable_modules = []

        for mod in sys.modules.keys():

            # Not a built in python module, which has no version, only the python version
            if mod not in sys.builtin_module_names:

                # if starts with sas, it's a local file so skip
                if mod.split('.')[0] != 'sas':

                    # Different attempts of retrieving the modules version
                    try:
                        module_versions_dict[mod] = __import__(mod).__version__
                    except AttributeError:

                        try:
                            module_versions_dict[mod] = __import__(mod).version
                        except AttributeError:

                            # Unreliable, so last option
                            try:
                                module_versions_dict[mod] = pkg_resources.get_distribution(mod).version
                            except:
                                # Modules without a formatted version, and that cannot be found by pkg_resources
                                unattainable_modules.append(mod)
                                pass

                                # Below is code that calculates the version of each module using pip, however it is
                                # very time consuming, and only is useful for a handful of modules, like PyQt5

                                # try:
                                #     pip_module_show = str(subprocess.check_output(f"pip show {mod}"), 'utf-8')
                                #     show_list = pip_module_show.replace("\r\n", ",").split(",")
                                #     for sec in show_list:
                                #         if sec.startswith("Version"):
                                #             module_versions_dict[mod] = sec.split(":")[1].strip()
                                #         else:
                                #             # Unalbe to get  version for this specific module
                                #             pass
                                # except Exception as x:
                                #     # Module not available through pip
                                #     logging.error(f"{x} when attempting to get the version of {mod} through pip")
                                #     pass

                        except Exception as x:
                            # Unable to access module
                            logging.error(f"{x} when attempting to access {mod} version using .version")
                            pass

                    except Exception as x:
                        # Unable to access module
                        logging.error(f"{x} when attempting to access {mod} version using .__version__")
                        pass

                    # Modules that require specific methods to get the version number
                    if "PyQt5" in mod:
                        try:
                            from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
                            module_versions_dict["Qt"] = QT_VERSION_STR
                            module_versions_dict["PyQt"] = PYQT_VERSION_STR
                        except:
                            unattainable_modules.append(["Qt", "PyQt"])
                            pass

        # Clean up
        module_versions_dict = self.remove_duplicate_modules(module_versions_dict)
        unattainable_modules = self.format_unattainable_modules_list(module_versions_dict, unattainable_modules)

        # Modules who's version number could not be found
        module_versions_dict["Can't get version number for following modules"] = unattainable_modules

        return module_versions_dict



    def remove_duplicate_modules(self, modules_dict):
        """ Strip duplicate instances of each module

        Multiple instances of one module can be keys  of the dictionary of module version numbers generated by the
        method get_imported_modules. This is because if an individual class is imported from a module, then each class
        would be listed in sys.modules. For example the command from PyQt5.QtWidgets import QMainWindow,  QMdiArea
        lead to both QMainWindow and QMdiArea being keys, when in reality they are both part of PyQt5. This method
        save the first instance of each module, unless the version numbers are different.

        Parameters
        ----------
        modules_dict : dict
            A dictionary with the module names as the key, with their respective version numbers as the value.

        Returns
        -------
        output_dict : dict
            A reduced / cleaneddictionary with the module names as the key, with their respective version numbers
            as the value.
        """

        output_dict = dict()

        for mod in modules_dict.keys():
            parent_module = mod.split('.')[0]

            # Save one instance of each module
            if parent_module not in output_dict.keys():
                output_dict[parent_module] = modules_dict[mod]
            else:
                # Modules versions are not the same
                if output_dict[parent_module] != modules_dict[mod]:
                    output_dict[f"{parent_module}_from_{mod}"] = modules_dict[mod]
                pass

        return output_dict


    def format_unattainable_modules_list(self, modules_dict, unattainable_modules):
        """Format module names in the unattainable_modules list

        The unattainable_modules is a list of modules who's version number could not be found. This method rename each
        module in the unattainable_modules to it's parent modules name, remove modules that already have a version
        number and remove duplicate modules from the unattainable_modules list. Entries may appear in the
        unattainable_modules if they are a class in a module, and the version number could not be ascertained from
        the class.

        Parameters
        ----------
        modules_dict : dict
            A dictionary with the module names as the key, with their respective version numbers as the value.
        unattainable_modules : list
            A list of modules who's version number could not be found.

        Returns
        -------
        output_list : list
            A reduced / clean list of modules who's version number could not be found

        """

        output_list = list()

        for mod in unattainable_modules:
            parent_module = mod.split('.')[0]
            # Version number exists for this module
            if parent_module in modules_dict.keys():
                pass
            # Module is already in output_list
            elif parent_module in output_list:
                pass
            # Append module to output_list
            else:
                output_list.append(mod)

        return output_list
