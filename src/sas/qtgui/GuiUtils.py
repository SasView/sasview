"""
    Global defaults and various utility functions usable by the general GUI
"""

import os
import sys
import time
import imp
import warnings
import re
warnings.simplefilter("ignore")
import logging
import traceback

from PyQt4 import QtCore
from PyQt4 import QtGui

# Translate event handlers
#from sas.sasgui.guiframe.events import EVT_CATEGORY
#from sas.sasgui.guiframe.events import EVT_STATUS
#from sas.sasgui.guiframe.events import EVT_APPEND_BOOKMARK
#from sas.sasgui.guiframe.events import EVT_PANEL_ON_FOCUS
#from sas.sasgui.guiframe.events import EVT_NEW_LOAD_DATA
#from sas.sasgui.guiframe.events import EVT_NEW_COLOR
#from sas.sasgui.guiframe.events import StatusEvent
#from sas.sasgui.guiframe.events import NewPlotEvent


def get_app_dir():
    """
        The application directory is the one where the default custom_config.py
        file resides.

        :returns: app_path - the path to the applicatin directory
    """
    # First, try the directory of the executable we are running
    app_path = sys.path[0]
    if os.path.isfile(app_path):
        app_path = os.path.dirname(app_path)
    if os.path.isfile(os.path.join(app_path, "custom_config.py")):
        app_path = os.path.abspath(app_path)
        logging.info("Using application path: %s", app_path)
        return app_path

    # Next, try the current working directory
    if os.path.isfile(os.path.join(os.getcwd(), "custom_config.py")):
        logging.info("Using application path: %s", os.getcwd())
        return os.path.abspath(os.getcwd())

    # Finally, try the directory of the sasview module
    # TODO: gui_manager will have to know about sasview until we
    # clean all these module variables and put them into a config class
    # that can be passed by sasview.py.
    logging.info(sys.executable)
    logging.info(str(sys.argv))
    from sas import sasview as sasview
    app_path = os.path.dirname(sasview.__file__)
    logging.info("Using application path: %s", app_path)
    return app_path

def get_user_directory():
    """
        Returns the user's home directory
    """
    userdir = os.path.join(os.path.expanduser("~"), ".sasview")
    if not os.path.isdir(userdir):
        os.makedirs(userdir)
    return userdir

def _find_local_config(file, path):
    """
        Find configuration file for the current application
    """
    config_module = None
    fObj = None
    try:
        fObj, path_config, descr = imp.find_module(file, [path])
        config_module = imp.load_module(file, fObj, path_config, descr)
    except:
        logging.error("Error loading %s/%s: %s" % (path, file, sys.exc_value))
    finally:
        if fObj is not None:
            fObj.close()
    logging.info("GuiManager loaded %s/%s" % (path, file))
    return config_module

# Get APP folder
PATH_APP = get_app_dir()
DATAPATH = PATH_APP

# GUI always starts from the App folder
#os.chdir(PATH_APP)
# Read in the local config, which can either be with the main
# application or in the installation directory
config = _find_local_config('local_config', PATH_APP)
if config is None:
    config = _find_local_config('local_config', os.getcwd())
    if config is None:
        # Didn't find local config, load the default
        import sas.sasgui.guiframe.config as config
        logging.info("using default local_config")
    else:
        logging.info("found local_config in %s" % os.getcwd())
else:
    logging.info("found local_config in %s" % PATH_APP)


from sas.sasgui.guiframe.customdir  import SetupCustom
c_conf_dir = SetupCustom().setup_dir(PATH_APP)
custom_config = _find_local_config('custom_config', c_conf_dir)
if custom_config is None:
    custom_config = _find_local_config('custom_config', os.getcwd())
    if custom_config is None:
        msgConfig = "Custom_config file was not imported"
        logging.info(msgConfig)
    else:
        logging.info("using custom_config in %s" % os.getcwd())
else:
    logging.info("using custom_config from %s" % c_conf_dir)

#read some constants from config
APPLICATION_STATE_EXTENSION = config.APPLICATION_STATE_EXTENSION
APPLICATION_NAME = config.__appname__
SPLASH_SCREEN_PATH = config.SPLASH_SCREEN_PATH
WELCOME_PANEL_ON = config.WELCOME_PANEL_ON
SPLASH_SCREEN_WIDTH = config.SPLASH_SCREEN_WIDTH
SPLASH_SCREEN_HEIGHT = config.SPLASH_SCREEN_HEIGHT
SS_MAX_DISPLAY_TIME = config.SS_MAX_DISPLAY_TIME
if not WELCOME_PANEL_ON:
    WELCOME_PANEL_SHOW = False
else:
    WELCOME_PANEL_SHOW = True
try:
    DATALOADER_SHOW = custom_config.DATALOADER_SHOW
    TOOLBAR_SHOW = custom_config.TOOLBAR_SHOW
    FIXED_PANEL = custom_config.FIXED_PANEL
    if WELCOME_PANEL_ON:
        WELCOME_PANEL_SHOW = custom_config.WELCOME_PANEL_SHOW
    PLOPANEL_WIDTH = custom_config.PLOPANEL_WIDTH
    DATAPANEL_WIDTH = custom_config.DATAPANEL_WIDTH
    GUIFRAME_WIDTH = custom_config.GUIFRAME_WIDTH
    GUIFRAME_HEIGHT = custom_config.GUIFRAME_HEIGHT
    CONTROL_WIDTH = custom_config.CONTROL_WIDTH
    CONTROL_HEIGHT = custom_config.CONTROL_HEIGHT
    DEFAULT_PERSPECTIVE = custom_config.DEFAULT_PERSPECTIVE
    CLEANUP_PLOT = custom_config.CLEANUP_PLOT
    # custom open_path
    open_folder = custom_config.DEFAULT_OPEN_FOLDER
    if open_folder != None and os.path.isdir(open_folder):
        DEFAULT_OPEN_FOLDER = os.path.abspath(open_folder)
    else:
        DEFAULT_OPEN_FOLDER = PATH_APP
except:
    DATALOADER_SHOW = True
    TOOLBAR_SHOW = True
    FIXED_PANEL = True
    WELCOME_PANEL_SHOW = False
    PLOPANEL_WIDTH = config.PLOPANEL_WIDTH
    DATAPANEL_WIDTH = config.DATAPANEL_WIDTH
    GUIFRAME_WIDTH = config.GUIFRAME_WIDTH
    GUIFRAME_HEIGHT = config.GUIFRAME_HEIGHT
    CONTROL_WIDTH = -1
    CONTROL_HEIGHT = -1
    DEFAULT_PERSPECTIVE = None
    CLEANUP_PLOT = False
    DEFAULT_OPEN_FOLDER = PATH_APP

DEFAULT_STYLE = config.DEFAULT_STYLE

PLUGIN_STATE_EXTENSIONS = config.PLUGIN_STATE_EXTENSIONS
OPEN_SAVE_MENU = config.OPEN_SAVE_PROJECT_MENU
VIEW_MENU = config.VIEW_MENU
EDIT_MENU = config.EDIT_MENU
extension_list = []
if APPLICATION_STATE_EXTENSION is not None:
    extension_list.append(APPLICATION_STATE_EXTENSION)
EXTENSIONS = PLUGIN_STATE_EXTENSIONS + extension_list
try:
    PLUGINS_WLIST = '|'.join(config.PLUGINS_WLIST)
except:
    PLUGINS_WLIST = ''
APPLICATION_WLIST = config.APPLICATION_WLIST
IS_WIN = True
IS_LINUX = False
CLOSE_SHOW = True
TIME_FACTOR = 2
NOT_SO_GRAPH_LIST = ["BoxSum"]

class Communicate(QtCore.QObject):
    """
    Utility class for tracking of the Qt signals
    """
    # File got successfully read
    fileReadSignal = QtCore.pyqtSignal(list)

    # Open File returns "list" of paths
    fileDataReceivedSignal = QtCore.pyqtSignal(dict)

    # Update Main window status bar with "str"
    statusBarUpdateSignal = QtCore.pyqtSignal(str)

    # Send data to the current perspective
    updatePerspectiveWithDataSignal = QtCore.pyqtSignal(list)
