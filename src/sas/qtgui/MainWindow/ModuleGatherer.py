import sys, logging, subprocess, pkg_resources


class ModuleGatherer:

    def get_imported_modules(self):

        module_versions_dict = {'python': sys.version}

        for mod in sys.modules.keys():

            # Not a built in python module, which has no version, only the python version
            if mod not in sys.builtin_module_names:

                # if starts with, it's a local file so skip
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
                                pass

                                # Modules without a formatted version, and that cannot be found by pkg_resources

                                # TODO possibly save log or list of modules with no version number

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

        return self.remove_duplicate_modules(module_versions_dict)


    def remove_duplicate_modules(self, modules_dict):

        output_dict = dict()

        for mod in modules_dict.keys():
            parent_module = mod.split('.')[0]

            # Save one instance of each module
            if parent_module not in output_dict.keys():
                output_dict[parent_module] = modules_dict[mod]
            else:
                # Modules versions are not the same
                if output_dict[parent_module] != modules_dict[mod]:
                    output_dict[f"{parent_module}_form_{mod}"] = modules_dict[mod]
                pass

        return output_dict

