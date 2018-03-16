"""
    Utilities to manage models
"""
from __future__ import print_function

import os
import sys
import time
import datetime
import logging
import traceback
import py_compile
import shutil

from sasmodels.sasview_model import load_custom_model, load_standard_models

from sas import get_user_dir

# Explicitly import from the pluginmodel module so that py2exe
# places it in the distribution. The Model1DPlugin class is used
# as the base class of plug-in models.
from .pluginmodel import Model1DPlugin

logger = logging.getLogger(__name__)


PLUGIN_DIR = 'plugin_models'
PLUGIN_LOG = os.path.join(get_user_dir(), PLUGIN_DIR, "plugins.log")
PLUGIN_NAME_BASE = '[plug-in] '


def plugin_log(message):
    """
    Log a message in a file located in the user's home directory
    """
    out = open(PLUGIN_LOG, 'a')
    now = time.time()
    stamp = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')
    out.write("%s: %s\n" % (stamp, message))
    out.close()


def _check_plugin(model, name):
    """
    Do some checking before model adding plugins in the list

    :param model: class model to add into the plugin list
    :param name:name of the module plugin

    :return model: model if valid model or None if not valid

    """
    #Check if the plugin is of type Model1DPlugin
    if not issubclass(model, Model1DPlugin):
        msg = "Plugin %s must be of type Model1DPlugin \n" % str(name)
        plugin_log(msg)
        return None
    if model.__name__ != "Model":
        msg = "Plugin %s class name must be Model \n" % str(name)
        plugin_log(msg)
        return None
    try:
        new_instance = model()
    except Exception:
        msg = "Plugin %s error in __init__ \n\t: %s %s\n" % (str(name),
                                                             str(sys.exc_type),
                                                             sys.exc_info()[1])
        plugin_log(msg)
        return None

    if hasattr(new_instance, "function"):
        try:
            value = new_instance.function()
        except Exception:
            msg = "Plugin %s: error writing function \n\t :%s %s\n " % \
                    (str(name), str(sys.exc_type), sys.exc_info()[1])
            plugin_log(msg)
            return None
    else:
        msg = "Plugin  %s needs a method called function \n" % str(name)
        plugin_log(msg)
        return None
    return model


def find_plugins_dir():
    """
    Find path of the plugins directory.
    The plugin directory is located in the user's home directory.
    """
    path = os.path.join(os.path.expanduser("~"), '.sasview', PLUGIN_DIR)

    # TODO: trigger initialization of plugins dir from installer or startup
    # If the plugin directory doesn't exist, create it
    if not os.path.isdir(path):
        os.makedirs(path)
    # TODO: should we be checking for new default models every time?
    # TODO: restore support for default plugins
    #initialize_plugins_dir(path)
    return path


def initialize_plugins_dir(path):
    # TODO: There are no default plugins
    # TODO: Default plugins directory is in sasgui, but models.py is in sascalc
    # TODO: Move default plugins beside sample data files
    # TODO: Should not look for defaults above the root of the sasview install

    # Walk up the tree looking for default plugin_models directory
    base = os.path.abspath(os.path.dirname(__file__))
    for _ in range(12):
        default_plugins_path = os.path.join(base, PLUGIN_DIR)
        if os.path.isdir(default_plugins_path):
            break
        base, _ = os.path.split(base)
    else:
        logger.error("default plugins directory not found")
        return

    # Copy files from default plugins to the .sasview directory
    # This may include c files, depending on the example.
    # Note: files are never replaced, even if the default plugins are updated
    for filename in os.listdir(default_plugins_path):
        # skip __init__.py and all pyc files
        if filename == "__init__.py" or filename.endswith('.pyc'):
            continue
        source = os.path.join(default_plugins_path, filename)
        target = os.path.join(path, filename)
        if os.path.isfile(source) and not os.path.isfile(target):
            shutil.copy(source, target)


class ReportProblem(object):
    """
    Class to check for problems with specific values
    """
    def __nonzero__(self):
        type, value, tb = sys.exc_info()
        if type is not None and issubclass(type, py_compile.PyCompileError):
            print("Problem with", repr(value))
            raise (type, value, tb)
        return 1

report_problem = ReportProblem()


def compile_file(dir):
    """
    Compile a py file
    """
    try:
        import compileall
        compileall.compile_dir(dir=dir, ddir=dir, force=0,
                               quiet=report_problem)
    except Exception:
        return sys.exc_info()[1]
    return None


def find_plugin_models():
    """
    Find custom models
    """
    # List of plugin objects
    plugins_dir = find_plugins_dir()
    # Go through files in plug-in directory
    if not os.path.isdir(plugins_dir):
        msg = "SasView couldn't locate Model plugin folder %r." % plugins_dir
        logger.warning(msg)
        return {}

    plugin_log("looking for models in: %s" % plugins_dir)
    # compile_file(plugins_dir)  #always recompile the folder plugin
    logger.info("plugin model dir: %s", plugins_dir)

    plugins = {}
    for filename in os.listdir(plugins_dir):
        name, ext = os.path.splitext(filename)
        if ext == '.py' and not name == '__init__':
            path = os.path.abspath(os.path.join(plugins_dir, filename))
            try:
                model = load_custom_model(path)
                # TODO: add [plug-in] tag to model name in sasview_model
                if not model.name.startswith(PLUGIN_NAME_BASE):
                    model.name = PLUGIN_NAME_BASE + model.name
                plugins[model.name] = model
            except Exception:
                msg = traceback.format_exc()
                msg += "\nwhile accessing model in %r" % path
                plugin_log(msg)
                logger.warning("Failed to load plugin %r. See %s for details",
                               path, PLUGIN_LOG)

    return plugins


class ModelManagerBase(object):
    """
    Base class for the model manager
    """
    #: mutable dictionary of models, continually updated to reflect the
    #: current set of plugins
    model_dictionary = None  # type: Dict[str, Model]
    #: constant list of standard models
    standard_models = None  # type: Dict[str, Model]
    #: list of plugin models reset each time the plugin directory is queried
    plugin_models = None  # type: Dict[str, Model]
    #: timestamp on the plugin directory at the last plugin update
    last_time_dir_modified = 0  # type: int

    def __init__(self):
        # the model dictionary is allocated at the start and updated to
        # reflect the current list of models.  Be sure to clear it rather
        # than reassign to it.
        self.model_dictionary = {}

        #Build list automagically from sasmodels package
        self.standard_models = {model.name: model
                                for model in load_standard_models()}
        # Look for plugins
        self.plugins_reset()

    def _is_plugin_dir_changed(self):
        """
        check the last time the plugin dir has changed and return true
        is the directory was modified else return false
        """
        is_modified = False
        plugin_dir = find_plugins_dir()
        if os.path.isdir(plugin_dir):
            mod_time = os.path.getmtime(plugin_dir)
            if  self.last_time_dir_modified != mod_time:
                is_modified = True
                self.last_time_dir_modified = mod_time

        return is_modified

    def composable_models(self):
        """
        return list of standard models that can be used in sum/multiply
        """
        # TODO: should scan plugin models in addition to standard models
        # and update model_editor so that it doesn't add plugins to the list
        return [model.name for model in self.standard_models.values()
                if not model.is_multiplicity_model]

    def plugins_update(self):
        """
        return a dictionary of model if
        new models were added else return empty dictionary
        """
        return self.plugins_reset()
        #if self._is_plugin_dir_changed():
        #    return self.plugins_reset()
        #else:
        #    return {}

    def plugins_reset(self):
        """
        return a dictionary of model
        """
        self.plugin_models = find_plugin_models()
        self.model_dictionary.clear()
        self.model_dictionary.update(self.standard_models)
        self.model_dictionary.update(self.plugin_models)
        return self.get_model_list()

    def get_model_list(self):
        """
        return dictionary of classified models

        *Structure Factors* are the structure factor models
        *Multi-Functions* are the multiplicity models
        *Plugin Models* are the plugin models

        Note that a model can be both a plugin and a structure factor or
        multiplicity model.
        """
        ## Model_list now only contains attribute lists not category list.
        ## Eventually this should be in one master list -- read in category
        ## list then pull those models that exist and get attributes then add
        ## to list ..and if model does not exist remove from list as now
        ## and update json file.
        ##
        ## -PDB   April 26, 2014


        # Classify models
        structure_factors = []
        form_factors = []
        multiplicity_models = []
        for model in self.model_dictionary.values():
            # Old style models don't have is_structure_factor attribute
            if getattr(model, 'is_structure_factor', False):
                structure_factors.append(model)
            if getattr(model, 'is_form_factor', False):
                form_factors.append(model)
            if model.is_multiplicity_model:
                multiplicity_models.append(model)
        plugin_models = list(self.plugin_models.values())

        return {
            "Structure Factors": structure_factors,
            "Form Factors": form_factors,
            "Plugin Models": plugin_models,
            "Multi-Functions": multiplicity_models,
        }


class ModelManager(object):
    """
    manage the list of available models
    """
    base = None  # type: ModelManagerBase()

    def __init__(self):
        if ModelManager.base is None:
            ModelManager.base = ModelManagerBase()

    def cat_model_list(self):
        return list(self.base.standard_models.values())

    def update(self):
        return self.base.plugins_update()

    def plugins_reset(self):
        return self.base.plugins_reset()

    def get_model_list(self):
        return self.base.get_model_list()

    def composable_models(self):
        return self.base.composable_models()

    def get_model_dictionary(self):
        return self.base.model_dictionary
