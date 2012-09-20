"""
Class for making sure all category stuff is installed
and works fine.

Copyright (c) Institut Laue-Langevin 2012

@author kieranrcampbell@gmail.com
@modified by NIST/MD sanview team
"""

import os
import sys
import shutil
import cPickle as pickle
from collections import defaultdict

USER_FILE = 'serialized_cat.p'

class CategoryInstaller:
    """
    Class for making sure all category stuff is installed

    Note - class is entirely static!
    """


    def __init__(self):
        """ initialization """

    @staticmethod
    def _get_installed_model_dir():
        """
        returns the dir where installed_models.txt should be
        """
        import sans.dataloader.readers
        return sans.dataloader.readers.get_data_path()

    @staticmethod
    def _get_models_py_dir():
        """
        returns the dir where models.py should be
        """
        import sans.perspectives.fitting.models
        return sans.perspectives.fitting.models.get_model_python_path()
    @staticmethod
    def _get_default_cat_p_dir():
        """
        returns the dir where default_cat.p should be
        """
        app_path = sys.path[0]
        return app_path

    @staticmethod
    def _get_home_dir():
        """
        returns the users sansview config dir
        """
        return os.path.join(os.path.expanduser("~"), ".sasview")

    @staticmethod
    def _regenerate_model_dict(master_category_dict):
        """
        regenerates self.by_model_dict which has each model name as the key
        and the list of categories belonging to that model
        along with the enabled mapping
        returns tuplet (by_model_dict, model_enabled_dict)
        """
        by_model_dict = defaultdict(list)
        model_enabled_dict = defaultdict(bool)
        
        for category in master_category_dict:
            for (model, enabled) in master_category_dict[category]:
                by_model_dict[model].append(category)
                model_enabled_dict[model] = enabled
    
        return (by_model_dict, model_enabled_dict)


    @staticmethod
    def _regenerate_master_dict(by_model_dict, model_enabled_dict):
        """
        regenerates master_category_dict from by_model_dict 
        and model_enabled_dict
        returns the master category dictionary
        """
        master_category_dict = defaultdict(list)
        for model in by_model_dict:
            for category in by_model_dict[model]:
                master_category_dict[category].append(\
                    (model, model_enabled_dict[model]))
        
        return master_category_dict

    @staticmethod
    def get_user_file():
        """
        returns the user data file, eg .sasview/serialized_cat.p
        """
        return os.path.join(CategoryInstaller._get_home_dir(),
                            USER_FILE)

    @staticmethod
    def get_default_file():
        """
        returns the path of the default file
        e.g. blahblah/default_categories.p
        """
        return os.path.join(\
            CategoryInstaller._get_default_cat_p_dir(), "default_categories.p")
        
    @staticmethod
    def check_install(homedir = None, defaultfile = None,
                      modelsdir = None, installed_models_dir = None):
        """
        the main method of this class
        makes sure serialized_cat.p exists and if not
        compile it and install
        :param homefile: Override the default home directory
        :param defaultfile: Override the default file location
        :param modelsfile: The file where models.py lives. This
        MUST be overwritten in setup.py
        :param installed_models_dir: Where installed_models.txt is to go:
        """
        model_list = []
        serialized_file = None
        if homedir == None:
            serialized_file = CategoryInstaller.get_user_file()
        else:
            serialized_file = os.path.join(homedir, USER_FILE)

        if os.path.exists(serialized_file):
            return

        if installed_models_dir == None:
            installed_models_dir = \
                CategoryInstaller._get_installed_model_dir() 
        
        installed_model_file = open(
            os.path.join(installed_models_dir,
                         "installed_models.txt"), 'w')

        if modelsdir == None:
            modelsdir = CategoryInstaller._get_models_py_dir()
        python_model_file = open(os.path.join(modelsdir, 
                                              "models.py"),
                                 'r')

        python_models = python_model_file.read()
        
        # we remove models that appear in the installed
        # model folder but not in models.py . the excess
        # hard coded ones on the end come from them being
        # present in models.py but not actual models, eg
        # TwoLorenzianModel contains the string 'Lorenzian'
        # but we don't actually want to include Lorenzian
        model_list = [mod for mod in model_list if \
                          mod in python_models and \
                          not 'init' in mod and \
                          not 'BaseComponent' in mod \
                          and not 'MultiplicationModel' in mod \
                          and not 'pluginmodel' in mod \
                          and mod != 'PowerLawModel' \
                          and mod != 'Lorentzian']

        
        for mod in model_list:
            installed_model_file.write(mod + '\n')
        
        installed_model_file.close()

        # start sorting category stuff
        default_file = None
        if defaultfile == None:
            default_file = CategoryInstaller.get_default_file()
        else:
            default_file = defaultfile

        master_category_dict = pickle.load(open(default_file, 'rb'))
        
        (by_model_dict, model_enabled_dict) = \
            CategoryInstaller._regenerate_model_dict(master_category_dict)
            
            
        for found_model in model_list:
            if not found_model in by_model_dict:
                print found_model + ' : ' + str(by_model_dict[found_model]) 
                by_model_dict[found_model].append("Uncategorized")
                model_enabled_dict[found_model] = True

                # remove any stray models from categorization 
                # that aren't stored anymore

        models_to_delete = []
        for model in by_model_dict:
            if not model in model_list:
                models_to_delete.append(model)

        for model in models_to_delete:
            by_model_dict.pop(model)

        master_category_dict = \
            CategoryInstaller._regenerate_master_dict(by_model_dict,
                                                      model_enabled_dict)
        
        pickle.dump( master_category_dict,
                     open(default_file, 'wb') )

        #shutil.copyfile(default_file, serialized_file)
