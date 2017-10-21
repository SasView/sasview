"""
Class for making sure all category stuff is installed
and works fine.

Copyright (c) Institut Laue-Langevin 2012

@author kieranrcampbell@gmail.com
@modified by NIST/MD sasview team
"""

import os
import sys
import json
import logging
from collections import defaultdict, OrderedDict

from sas import get_user_dir

USER_FILE = 'categories.json'

logger = logging.getLogger(__name__)

class CategoryInstaller(object):
    """
    Class for making sure all category stuff is installed

    Note - class is entirely static!
    """

    @staticmethod
    def _get_installed_model_dir():
        """
        returns the dir where installed_models.txt should be
        """
        from sas.sascalc.dataloader.readers import get_data_path
        return get_data_path()

    @staticmethod
    def _get_default_cat_file_dir():
        """
        returns the dir where default_cat.j should be
        """
        # The default categories file is usually found with the code, except
        # when deploying using py2app (it will be in Contents/Resources), or
        # py2exe (it will be in the exec dir).
        import sas.sasview
        cat_file = "default_categories.json"

        possible_cat_file_paths = [
            os.path.join(os.path.split(sas.sasview.__file__)[0], cat_file),           # Source
            os.path.join(os.path.dirname(sys.executable), '..', 'Resources', cat_file), # Mac
            os.path.join(os.path.dirname(sys.executable), cat_file)                     # Windows
        ]

        for path in possible_cat_file_paths:
            if os.path.isfile(path):
                return os.path.dirname(path)

        raise RuntimeError('CategoryInstaller: Could not find folder containing default categories')

    @staticmethod
    def _get_home_dir():
        """
        returns the users sasview config dir
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
        return OrderedDict(sorted(master_category_dict.items(), key=lambda t: t[0]))

    @staticmethod
    def get_user_file():
        """
        returns the user data file, eg .sasview/categories.json.json
        """
        return os.path.join(get_user_dir(), USER_FILE)

    @staticmethod
    def get_default_file():
        logger.warning("CategoryInstaller.get_default_file is deprecated.")

    @staticmethod
    def check_install(homedir = None, model_list=None):
        """
        Makes sure categories.json exists and if not compile it and install.

        This is the main method of this class.

        :param homefile: Override the default home directory
        :param model_list: List of model names except those in
            Plugin Models which are user supplied.
        """
        _model_dict = {model.name: model for model in model_list}
        _model_list = _model_dict.keys()

        serialized_file = None
        if homedir is None:
            serialized_file = CategoryInstaller.get_user_file()
        else:
            serialized_file = os.path.join(homedir, USER_FILE)
        if os.path.isfile(serialized_file):
            with open(serialized_file, 'rb') as f:
                master_category_dict = json.load(f)
        else:
            master_category_dict = defaultdict(list)

        (by_model_dict, model_enabled_dict) = \
                CategoryInstaller._regenerate_model_dict(master_category_dict)
        add_list = _model_list
        del_name = False
        for cat in master_category_dict.keys():
            for ind in range(len(master_category_dict[cat])):
                model_name, enabled = master_category_dict[cat][ind]
                if model_name not in _model_list:
                    del_name = True
                    try:
                        by_model_dict.pop(model_name)
                        model_enabled_dict.pop(model_name)
                    except Exception:
                        logger.error("CategoryInstaller: %s", sys.exc_value)
                else:
                    add_list.remove(model_name)
        if del_name or (len(add_list) > 0):
            for model in add_list:
                model_enabled_dict[model] = True
                # TODO: should be:  not _model_dict[model].category
                if (_model_dict[model].category is None
                        or len(str(_model_dict[model].category.capitalize())) == 0):
                    by_model_dict[model].append('Uncategorized')
                else:
                    category = _model_dict[model].category
                    toks = category.split(':')
                    category = toks[-1]
                    toks = category.split('-')
                    capitalized_words = [t.capitalize() for t in toks]
                    category = ' '.join(capitalized_words)

                    by_model_dict[model].append(category)

            master_category_dict = \
                CategoryInstaller._regenerate_master_dict(by_model_dict,
                                                          model_enabled_dict)

            json.dump(master_category_dict, open(serialized_file, 'wb'))
