"""
    Global defaults and various utility functions usable by the general GUI
"""

import os
import sys
import imp
import warnings
import webbrowser
import urlparse

warnings.simplefilter("ignore")
import logging

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

from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.guiframe.dataFitting import Data2D


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

def _find_local_config(confg_file, path):
    """
        Find configuration file for the current application
    """
    config_module = None
    fObj = None
    try:
        fObj, path_config, descr = imp.find_module(confg_file, [path])
        config_module = imp.load_module(confg_file, fObj, path_config, descr)
    except ImportError:
        logging.error("Error loading %s/%s: %s" % (path, confg_file, sys.exc_value))
    finally:
        if fObj is not None:
            fObj.close()
    logging.info("GuiManager loaded %s/%s" % (path, confg_file))
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
        logging.info("found local_config in %s", os.getcwd())
else:
    logging.info("found local_config in %s", PATH_APP)


from sas.sasgui.guiframe.customdir  import SetupCustom
c_conf_dir = SetupCustom().setup_dir(PATH_APP)
custom_config = _find_local_config('custom_config', c_conf_dir)
if custom_config is None:
    custom_config = _find_local_config('custom_config', os.getcwd())
    if custom_config is None:
        msgConfig = "Custom_config file was not imported"
        logging.info(msgConfig)
    else:
        logging.info("using custom_config in %s", os.getcwd())
else:
    logging.info("using custom_config from %s", c_conf_dir)

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
except AttributeError:
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
except AttributeError:
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
    # Old "StatusEvent"
    statusBarUpdateSignal = QtCore.pyqtSignal(str)

    # Send data to the current perspective
    updatePerspectiveWithDataSignal = QtCore.pyqtSignal(list)

    # New data in current perspective
    updateModelFromPerspectiveSignal = QtCore.pyqtSignal(QtGui.QStandardItem)

    # New plot requested from the GUI manager
    # Old "NewPlotEvent"
    plotRequestedSignal = QtCore.pyqtSignal(str)

    # Progress bar update value
    progressBarUpdateSignal = QtCore.pyqtSignal(int)

    # Workspace charts added/removed
    activeGraphsSignal = QtCore.pyqtSignal(list)


def updateModelItem(item, update_data, name=""):
    """
    Adds a checkboxed row named "name" to QStandardItem
    Adds QVariant 'update_data' to that row.
    """
    assert isinstance(item, QtGui.QStandardItem)
    assert isinstance(update_data, QtCore.QVariant)

    checkbox_item = QtGui.QStandardItem(True)
    checkbox_item.setCheckable(True)
    checkbox_item.setCheckState(QtCore.Qt.Checked)
    checkbox_item.setText(name)

    # Add "Info" item
    py_update_data = update_data.toPyObject()
    if isinstance(py_update_data, (Data1D or Data2D)):
        # If Data1/2D added - extract Info from it
        info_item = infoFromData(py_update_data)
    else:
        # otherwise just add a naked item
        info_item = QtGui.QStandardItem("Info")

    # Add the actual Data1D/Data2D object
    object_item = QtGui.QStandardItem()
    object_item.setData(update_data)

    # Set the data object as the first child
    checkbox_item.setChild(0, object_item)

    # Set info_item as the second child
    checkbox_item.setChild(1, info_item)

    # Append the new row to the main item
    item.appendRow(checkbox_item)

def plotsFromCheckedItems(model_item):
    """
    Returns the list of plots for items in the model which are checked
    """
    assert isinstance(model_item, QtGui.QStandardItemModel)

    plot_data = []
    # Iterate over model looking for items with checkboxes
    for index in range(model_item.rowCount()):
        item = model_item.item(index)
        if item.isCheckable() and item.checkState() == QtCore.Qt.Checked:
            # TODO: assure item type is correct (either data1/2D or Plotter)
            plot_data.append(item.child(0).data().toPyObject())
        # Going 1 level deeper only
        for index_2 in range(item.rowCount()):
            item_2 = item.child(index_2)
            if item_2 and item_2.isCheckable() and item_2.checkState() == QtCore.Qt.Checked:
                # TODO: assure item type is correct (either data1/2D or Plotter)
                plot_data.append(item_2.child(0).data().toPyObject())

    return plot_data

def infoFromData(data):
    """
    Given Data1D/Data2D object, extract relevant Info elements
    and add them to a model item
    """
    assert isinstance(data, (Data1D, Data2D))

    info_item = QtGui.QStandardItem("Info")

    title_item = QtGui.QStandardItem("Title: " + data.title)
    info_item.appendRow(title_item)
    run_item = QtGui.QStandardItem("Run: " + str(data.run))
    info_item.appendRow(run_item)
    type_item = QtGui.QStandardItem("Type: " + str(data.__class__.__name__))
    info_item.appendRow(type_item)

    if data.path:
        path_item = QtGui.QStandardItem("Path: " + data.path)
        info_item.appendRow(path_item)

    if data.instrument:
        instr_item = QtGui.QStandardItem("Instrument: " + data.instrument)
        info_item.appendRow(instr_item)

    process_item = QtGui.QStandardItem("Process")
    if isinstance(data.process, list) and data.process:
        for process in data.process:
            process_date = process.date
            process_date_item = QtGui.QStandardItem("Date: " + process_date)
            process_item.appendRow(process_date_item)

            process_descr = process.description
            process_descr_item = QtGui.QStandardItem("Description: " + process_descr)
            process_item.appendRow(process_descr_item)

            process_name = process.name
            process_name_item = QtGui.QStandardItem("Name: " + process_name)
            process_item.appendRow(process_name_item)

    info_item.appendRow(process_item)

    return info_item

def openLink(url):
    """
    Open a URL in an external browser.
    Check the URL first, though.
    """
    parsed_url = urlparse.urlparse(url)
    if parsed_url.scheme:
        webbrowser.open(url)
    else:
        msg = "Attempt at opening an invalid URL"
        raise AttributeError, msg

def retrieveData1d(data):
    """
    Retrieve 1D data from file and construct its text
    representation
    """
    try:
        xmin = min(data.x)
        ymin = min(data.y)
    except:
        msg = "Unable to find min/max of \n data named %s" % \
                    data.filename
        logging.error(msg)
        raise ValueError, msg

    text = data.__str__()
    text += 'Data Min Max:\n'
    text += 'X_min = %s:  X_max = %s\n' % (xmin, max(data.x))
    text += 'Y_min = %s:  Y_max = %s\n' % (ymin, max(data.y))
    if data.dy != None:
        text += 'dY_min = %s:  dY_max = %s\n' % (min(data.dy), max(data.dy))
    text += '\nData Points:\n'
    x_st = "X"
    for index in range(len(data.x)):
        if data.dy != None and len(data.dy) > index:
            dy_val = data.dy[index]
        else:
            dy_val = 0.0
        if data.dx != None and len(data.dx) > index:
            dx_val = data.dx[index]
        else:
            dx_val = 0.0
        if data.dxl != None and len(data.dxl) > index:
            if index == 0:
                x_st = "Xl"
            dx_val = data.dxl[index]
        elif data.dxw != None and len(data.dxw) > index:
            if index == 0:
                x_st = "Xw"
            dx_val = data.dxw[index]

        if index == 0:
            text += "<index> \t<X> \t<Y> \t<dY> \t<d%s>\n" % x_st
        text += "%s \t%s \t%s \t%s \t%s\n" % (index,
                                                data.x[index],
                                                data.y[index],
                                                dy_val,
                                                dx_val)
    return text

def retrieveData2d(data):
    """
    Retrieve 1D data from file and construct its text
    representation
    """
    text = data.__str__()
    text += 'Data Min Max:\n'
    text += 'I_min = %s\n' % min(data.data)
    text += 'I_max = %s\n\n' % max(data.data)
    text += 'Data (First 2501) Points:\n'
    text += 'Data columns include err(I).\n'
    text += 'ASCII data starts here.\n'
    text += "<index> \t<Qx> \t<Qy> \t<I> \t<dI> \t<dQparal> \t<dQperp>\n"
    di_val = 0.0
    dx_val = 0.0
    dy_val = 0.0
    len_data = len(data.qx_data)
    for index in xrange(0, len_data):
        x_val = data.qx_data[index]
        y_val = data.qy_data[index]
        i_val = data.data[index]
        if data.err_data != None:
            di_val = data.err_data[index]
        if data.dqx_data != None:
            dx_val = data.dqx_data[index]
        if data.dqy_data != None:
            dy_val = data.dqy_data[index]

        text += "%s \t%s \t%s \t%s \t%s \t%s \t%s\n" % (index,
                                                        x_val,
                                                        y_val,
                                                        i_val,
                                                        di_val,
                                                        dx_val,
                                                        dy_val)
        # Takes too long time for typical data2d: Break here
        if index >= 2500:
            text += ".............\n"
            break

    return text
