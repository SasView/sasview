"""
    Utilities to manage models
"""


import traceback
import os
import sys
import os.path
# Time is needed by the log method
import time
import datetime
import logging
import py_compile
import shutil

# Explicitly import from the pluginmodel module so that py2exe
# places it in the distribution. The Model1DPlugin class is used
# as the base class of plug-in models.
#from sas.sascalc.fit.pluginmodel import Model1DPlugin
from sas.qtgui.Utilities.CategoryInstaller import CategoryInstaller
from sasmodels.sasview_model import load_custom_model, load_standard_models

PLUGIN_DIR = 'plugin_models'
PLUGIN_LOG = os.path.join(os.path.expanduser("~"), '.sasview', PLUGIN_DIR,
                          "plugins.log")
PLUGIN_NAME_BASE = '[plug-in] '

def get_model_python_path():
    """
    Returns the python path for a model
    """
    return os.path.dirname(__file__)


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
    #if not issubclass(model, Model1DPlugin):
    #    msg = "Plugin %s must be of type Model1DPlugin \n" % str(name)
    #    plugin_log(msg)
    #    return None
    if model.__name__ != "Model":
        msg = "Plugin %s class name must be Model \n" % str(name)
        plugin_log(msg)
        return None
    try:
        new_instance = model()
    except:
        msg = "Plugin %s error in __init__ \n\t: %s %s\n" % (str(name),
                                                             str(sys.exc_info()[0]),
                                                             sys.exc_info()[1])
        plugin_log(msg)
        return None

    if hasattr(new_instance, "function"):
        try:
            value = new_instance.function()
        except:
            msg = "Plugin %s: error writing function \n\t :%s %s\n " % \
                    (str(name), str(sys.exc_info()[0]), sys.exc_info()[1])
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
    dir = os.path.join(os.path.expanduser("~"), '.sasview', PLUGIN_DIR)

    # If the plugin directory doesn't exist, create it
    if not os.path.isdir(dir):
        os.makedirs(dir)

    # Find paths needed
    try:
        # For source
        if os.path.isdir(os.path.dirname(__file__)):
            p_dir = os.path.join(os.path.dirname(__file__), PLUGIN_DIR)
        else:
            raise
    except:
        # Check for data path next to exe/zip file.
        #Look for maximum n_dir up of the current dir to find plugins dir
        n_dir = 12
        p_dir = None
        f_dir = os.path.join(os.path.dirname(__file__))
        for i in range(n_dir):
            if i > 1:
                f_dir, _ = os.path.split(f_dir)
            plugin_path = os.path.join(f_dir, PLUGIN_DIR)
            if os.path.isdir(plugin_path):
                p_dir = plugin_path
                break
        if not p_dir:
            raise
    # Place example user models as needed
    if os.path.isdir(p_dir):
        for file in os.listdir(p_dir):
            file_path = os.path.join(p_dir, file)
            if os.path.isfile(file_path):
                if file.split(".")[-1] == 'py' and\
                    file.split(".")[0] != '__init__':
                    if not os.path.isfile(os.path.join(dir, file)):
                        shutil.copy(file_path, dir)

    return dir


class ReportProblem:
    """
    Class to check for problems with specific values
    """
    def __bool__(self):
        type, value, tb = sys.exc_info()
        if type is not None and issubclass(type, py_compile.PyCompileError):
            print("Problem with", repr(value))
            raise type(value).with_traceback(tb)
        return 1

report_problem = ReportProblem()


def compile_file(dir):
    """
    Compile a py file
    """
    try:
        import compileall
        compileall.compile_dir(dir=dir, ddir=dir, force=1,
                               quiet=report_problem)
    except:
        return sys.exc_info()[1]
    return None


def _find_models():
    """
    Find custom models
    """
    # List of plugin objects
    directory = find_plugins_dir()
    # Go through files in plug-in directory
    if not os.path.isdir(directory):
        msg = "SasView couldn't locate Model plugin folder %r." % directory
        logging.warning(msg)
        return {}

    plugin_log("looking for models in: %s" % str(directory))
    # compile_file(directory)  #always recompile the folder plugin
    logging.info("plugin model dir: %s" % str(directory))

    plugins = {}
    for filename in os.listdir(directory):
        name, ext = os.path.splitext(filename)
        if ext == '.py' and not name == '__init__':
            path = os.path.abspath(os.path.join(directory, filename))
            try:
                model = load_custom_model(path)
                model.name = PLUGIN_NAME_BASE + model.name
                plugins[model.name] = model
            except Exception:
                msg = traceback.format_exc()
                msg += "\nwhile accessing model in %r" % path
                plugin_log(msg)
                logging.warning("Failed to load plugin %r. See %s for details"
                               % (path, PLUGIN_LOG))

    return plugins


class ModelList(object):
    """
    Contains dictionary of model and their type
    """
    def __init__(self):
        """
        """
        self.mydict = {}

    def set_list(self, name, mylist):
        """
        :param name: the type of the list
        :param mylist: the list to add

        """
        if name not in list(self.mydict.keys()):
            self.reset_list(name, mylist)

    def reset_list(self, name, mylist):
        """
        :param name: the type of the list
        :param mylist: the list to add
        """
        self.mydict[name] = mylist

    def get_list(self):
        """
        return all the list stored in a dictionary object
        """
        return self.mydict


class ModelManagerBase:
    """
    Base class for the model manager
    """
    ## external dict for models
    model_combobox = ModelList()
    ## Dictionary of form factor models
    form_factor_dict = {}
    ## dictionary of structure factor models
    struct_factor_dict = {}
    ##list of structure factors
    struct_list = []
    ##list of model allowing multiplication by a structure factor
    multiplication_factor = []
    ##list of multifunctional shapes (i.e. that have user defined number of levels
    multi_func_list = []
    ## list of added models -- currently python models found in the plugin dir.
    plugins = []
    ## Event owner (guiframe)
    event_owner = None
    last_time_dir_modified = 0

    def __init__(self):
        self.model_dictionary = {}
        self.stored_plugins = {}
        self._getModelList()

    def findModels(self):
        """
        find  plugin model in directory of plugin .recompile all file
        in the directory if file were modified
        """
        temp = {}
        if self.is_changed():
            return  _find_models()
        logging.info("plugin model : %s" % str(temp))
        return temp

    def _getModelList(self):
        """
        List of models we want to make available by default
        for this application

        :return: the next free event ID following the new menu events

        """

        # regular model names only
        self.model_name_list = []

        #Build list automagically from sasmodels package
        for model in load_standard_models():
            self.model_dictionary[model.name] = model
            if model.is_structure_factor:
                self.struct_list.append(model)
            if model.is_form_factor:
                self.multiplication_factor.append(model)
            if model.is_multiplicity_model:
                self.multi_func_list.append(model)
            else:
                self.model_name_list.append(model.name)

        #Looking for plugins
        self.stored_plugins = self.findModels()
        self.plugins = list(self.stored_plugins.values())
        for name, plug in self.stored_plugins.items():
            self.model_dictionary[name] = plug
        
        self._get_multifunc_models()

        return 0

    def is_changed(self):
        """
        check the last time the plugin dir has changed and return true
        is the directory was modified else return false
        """
        is_modified = False
        plugin_dir = find_plugins_dir()
        if os.path.isdir(plugin_dir):
            temp = os.path.getmtime(plugin_dir)
            if  self.last_time_dir_modified != temp:
                is_modified = True
                self.last_time_dir_modified = temp

        return is_modified

    def update(self):
        """
        return a dictionary of model if
        new models were added else return empty dictionary
        """
        new_plugins = self.findModels()
        if len(new_plugins) > 0:
            for name, plug in  new_plugins.items():
                if name not in list(self.stored_plugins.keys()):
                    self.stored_plugins[name] = plug
                    self.plugins.append(plug)
                    self.model_dictionary[name] = plug
            self.model_combobox.set_list("Plugin Models", self.plugins)
            return self.model_combobox.get_list()
        else:
            return {}

    def plugins_reset(self):
        """
        return a dictionary of model
        """
        self.plugins = []
        new_plugins = _find_models()
        for name, plug in  new_plugins.items():
            for stored_name, stored_plug in self.stored_plugins.items():
                if name == stored_name:
                    del self.stored_plugins[name]
                    del self.model_dictionary[name]
                    break
            self.stored_plugins[name] = plug
            self.plugins.append(plug)
            self.model_dictionary[name] = plug

        self.model_combobox.reset_list("Plugin Models", self.plugins)
        return self.model_combobox.get_list()

    def _on_model(self, evt):
        """
        React to a model menu event

        :param event: wx menu event

        """
        if int(evt.GetId()) in list(self.form_factor_dict.keys()):
            from sasmodels.sasview_model import MultiplicationModel
            self.model_dictionary[MultiplicationModel.__name__] = MultiplicationModel
            model1, model2 = self.form_factor_dict[int(evt.GetId())]
            model = MultiplicationModel(model1, model2)
        else:
            model = self.struct_factor_dict[str(evt.GetId())]()


    def _get_multifunc_models(self):
        """
        Get the multifunctional models
        """
        items = [item for item in self.plugins if item.is_multiplicity_model]
        self.multi_func_list = items

    def get_model_list(self):
        """
        return dictionary of models for fitpanel use

        """
        ## Model_list now only contains attribute lists not category list.
        ## Eventually this should be in one master list -- read in category
        ## list then pull those models that exist and get attributes then add
        ## to list ..and if model does not exist remove from list as now
        ## and update json file.
        ##
        ## -PDB   April 26, 2014

#        self.model_combobox.set_list("Shapes", self.shape_list)
#        self.model_combobox.set_list("Shape-Independent",
#                                     self.shape_indep_list)
        self.model_combobox.set_list("Structure Factors", self.struct_list)
        self.model_combobox.set_list("Plugin Models", self.plugins)
        self.model_combobox.set_list("P(Q)*S(Q)", self.multiplication_factor)
        self.model_combobox.set_list("multiplication",
                                     self.multiplication_factor)
        self.model_combobox.set_list("Multi-Functions", self.multi_func_list)
        return self.model_combobox.get_list()

    def get_model_name_list(self):
        """
        return regular model name list
        """
        return self.model_name_list

    def get_model_dictionary(self):
        """
        return dictionary linking model names to objects
        """
        return self.model_dictionary


class ModelManager(object):
    """
    implement model
    """
    __modelmanager = ModelManagerBase()
    cat_model_list = [__modelmanager.model_dictionary[model_name] for model_name \
                      in list(__modelmanager.model_dictionary.keys()) \
                      if model_name not in list(__modelmanager.stored_plugins.keys())]

    CategoryInstaller.check_install(model_list=cat_model_list)
    def findModels(self):
        return self.__modelmanager.findModels()

    def _getModelList(self):
        return self.__modelmanager._getModelList()

    def is_changed(self):
        return self.__modelmanager.is_changed()

    def update(self):
        return self.__modelmanager.update()

    def plugins_reset(self):
        return self.__modelmanager.plugins_reset()

    def populate_menu(self, modelmenu, event_owner):
        return self.__modelmanager.populate_menu(modelmenu, event_owner)

    def _on_model(self, evt):
        return self.__modelmanager._on_model(evt)

    def _get_multifunc_models(self):
        return self.__modelmanager._get_multifunc_models()

    def get_model_list(self):
        return self.__modelmanager.get_model_list()

    def get_model_name_list(self):
        return self.__modelmanager.get_model_name_list()

    def get_model_dictionary(self):
        return self.__modelmanager.get_model_dictionary()

