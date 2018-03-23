"""
Global defaults and various utility functions usable by the general GUI
"""

import os
import re
import sys
import imp
import warnings
import webbrowser
import urllib.parse

warnings.simplefilter("ignore")
import logging

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from periodictable import formula as Formula
from sas.qtgui.Plotting import DataTransform
from sas.qtgui.Plotting.ConvertUnits import convertUnit
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D
from sas.sascalc.dataloader.loader import Loader
from sas.qtgui.Utilities import CustomDir

## TODO: CHANGE FOR SHIPPED PATH IN RELEASE
if os.path.splitext(sys.argv[0])[1].lower() != ".py":
        HELP_DIRECTORY_LOCATION = "doc"
else:
        HELP_DIRECTORY_LOCATION = "docs/sphinx-docs/build/html"
IMAGES_DIRECTORY_LOCATION = HELP_DIRECTORY_LOCATION + "/_images"

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
        #logging.info("Using application path: %s", app_path)
        return app_path

    # Next, try the current working directory
    if os.path.isfile(os.path.join(os.getcwd(), "custom_config.py")):
        #logging.info("Using application path: %s", os.getcwd())
        return os.path.abspath(os.getcwd())

    # Finally, try the directory of the sasview module
    # TODO: gui_manager will have to know about sasview until we
    # clean all these module variables and put them into a config class
    # that can be passed by sasview.py.
    # logging.info(sys.executable)
    # logging.info(str(sys.argv))
    from sas import sasview as sasview
    app_path = os.path.dirname(sasview.__file__)
    # logging.info("Using application path: %s", app_path)
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
        pass
        #logging.error("Error loading %s/%s: %s" % (path, confg_file, sys.exc_value))
    except ValueError:
        print("Value error")
        pass
    finally:
        if fObj is not None:
            fObj.close()
    #logging.info("GuiManager loaded %s/%s" % (path, confg_file))
    return config_module


# Get APP folder
PATH_APP = get_app_dir()
DATAPATH = PATH_APP

# Read in the local config, which can either be with the main
# application or in the installation directory
config = _find_local_config('local_config', PATH_APP)

if config is None:
    config = _find_local_config('local_config', os.getcwd())
else:
    pass

c_conf_dir = CustomDir.setup_conf_dir(PATH_APP)

custom_config = _find_local_config('custom_config', c_conf_dir)
if custom_config is None:
    custom_config = _find_local_config('custom_config', os.getcwd())
    if custom_config is None:
        msgConfig = "Custom_config file was not imported"

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
    if open_folder is not None and os.path.isdir(open_folder):
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

#DEFAULT_STYLE = config.DEFAULT_STYLE

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

    # New theory data in current perspective
    updateTheoryFromPerspectiveSignal = QtCore.pyqtSignal(QtGui.QStandardItem)

    # New plot requested from the GUI manager
    # Old "NewPlotEvent"
    plotRequestedSignal = QtCore.pyqtSignal(list)

    # Plot from file names
    plotFromFilenameSignal = QtCore.pyqtSignal(str)

    # Plot update requested from a perspective
    plotUpdateSignal = QtCore.pyqtSignal(list)

    # Progress bar update value
    progressBarUpdateSignal = QtCore.pyqtSignal(int)

    # Workspace charts added/removed
    activeGraphsSignal = QtCore.pyqtSignal(list)

    # Current workspace chart's name changed
    activeGraphName = QtCore.pyqtSignal(tuple)

    # Current perspective changed
    perspectiveChangedSignal = QtCore.pyqtSignal(str)

    # File/dataset got deleted
    dataDeletedSignal = QtCore.pyqtSignal(list)

    # Send data to Data Operation Utility panel
    sendDataToPanelSignal = QtCore.pyqtSignal(dict)

    # Send result of Data Operation Utility panel to Data Explorer
    updateModelFromDataOperationPanelSignal = QtCore.pyqtSignal(QtGui.QStandardItem, dict)

    # Notify about a new custom plugin being written/deleted/modified
    customModelDirectoryChanged = QtCore.pyqtSignal()

def updateModelItemWithPlot(item, update_data, name=""):
    """
    Adds a checkboxed row named "name" to QStandardItem
    Adds 'update_data' to that row.
    """
    assert isinstance(item, QtGui.QStandardItem)

    # Check if data with the same ID is already present
    for index in range(item.rowCount()):
        plot_item = item.child(index)
        if plot_item.isCheckable():
            plot_data = plot_item.child(0).data()
            if plot_data.id is not None and \
                   (plot_data.name == update_data.name or plot_data.id == update_data.id):
            # if plot_data.id is not None and plot_data.id == update_data.id:
                # replace data section in item
                plot_item.child(0).setData(update_data)
                plot_item.setText(name)
                # Plot title if any
                if plot_item.child(1).hasChildren():
                    plot_item.child(1).child(0).setText("Title: %s"%name)
                # Force redisplay
                return

    # Create the new item
    checkbox_item = createModelItemWithPlot(update_data, name)

    # Append the new row to the main item
    item.appendRow(checkbox_item)

class HashableStandardItem(QtGui.QStandardItem):
    """
    Subclassed standard item with reimplemented __hash__
    to allow for use as an index.
    """
    def __init__(self, parent=None):
        super(HashableStandardItem, self).__init__()

    def __hash__(self):
        ''' just a random hash value '''
        #return hash(self.__init__)
        return 0

    def clone(self):
        ''' Assure __hash__ is cloned as well'''
        clone = super(HashableStandardItem, self).clone()
        clone.__hash__ = self.__hash__
        return clone


def createModelItemWithPlot(update_data, name=""):
    """
    Creates a checkboxed QStandardItem named "name"
    Adds 'update_data' to that row.
    """
    py_update_data = update_data

    checkbox_item = HashableStandardItem()
    checkbox_item.setCheckable(True)
    checkbox_item.setCheckState(QtCore.Qt.Checked)
    checkbox_item.setText(name)

    # Add "Info" item
    if isinstance(py_update_data, (Data1D, Data2D)):
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

    # And return the newly created item
    return checkbox_item

def updateModelItem(item, update_data, name=""):
    """
    Adds a simple named child to QStandardItem
    """
    assert isinstance(item, QtGui.QStandardItem)
    #assert isinstance(update_data, list)

    # Add the actual Data1D/Data2D object
    object_item = QtGui.QStandardItem()
    object_item.setText(name)
    object_item.setData(update_data)

    # Append the new row to the main item
    item.appendRow(object_item)

def updateModelItemStatus(model_item, filename="", name="", status=2):
    """
    Update status of checkbox related to high- and low-Q extrapolation
    choice in Invariant Panel
    """
    assert isinstance(model_item, QtGui.QStandardItemModel)

    # Iterate over model looking for items with checkboxes
    for index in range(model_item.rowCount()):
        item = model_item.item(index)
        if item.text() == filename and item.isCheckable() \
                and item.checkState() == QtCore.Qt.Checked:
            # Going 1 level deeper only
            for index_2 in range(item.rowCount()):
                item_2 = item.child(index_2)
                if item_2 and item_2.isCheckable() and item_2.text() == name:
                    item_2.setCheckState(status)

    return

def itemFromFilename(filename, model_item):
    """
    Returns the model item text=filename in the model
    """
    assert isinstance(model_item, QtGui.QStandardItemModel)
    assert isinstance(filename, str)

    # Iterate over model looking for named items
    item = list([i for i in [model_item.item(index)
                             for index in range(model_item.rowCount())]
                 if str(i.text()) == filename])
    return item[0] if len(item)>0 else None

def plotsFromFilename(filename, model_item):
    """
    Returns the list of plots for the item with text=filename in the model
    """
    assert isinstance(model_item, QtGui.QStandardItemModel)
    assert isinstance(filename, str)

    plot_data = []
    # Iterate over model looking for named items
    for index in range(model_item.rowCount()):
        item = model_item.item(index)
        if str(item.text()) == filename:
            # TODO: assure item type is correct (either data1/2D or Plotter)
            plot_data.append(item.child(0).data())
            # Going 1 level deeper only
            for index_2 in range(item.rowCount()):
                item_2 = item.child(index_2)
                if item_2 and item_2.isCheckable():
                    # TODO: assure item type is correct (either data1/2D or Plotter)
                    plot_data.append(item_2.child(0).data())

    return plot_data

def plotsFromCheckedItems(model_item):
    """
    Returns the list of plots for items in the model which are checked
    """
    assert isinstance(model_item, QtGui.QStandardItemModel)

    plot_data = []
    # Iterate over model looking for items with checkboxes
    for index in range(model_item.rowCount()):
        item = model_item.item(index)

        # Going 1 level deeper only
        for index_2 in range(item.rowCount()):
            item_2 = item.child(index_2)
            if item_2 and item_2.isCheckable() and item_2.checkState() == QtCore.Qt.Checked:
                # TODO: assure item type is correct (either data1/2D or Plotter)
                plot_data.append((item_2, item_2.child(0).data()))

        if item.isCheckable() and item.checkState() == QtCore.Qt.Checked:
            # TODO: assure item type is correct (either data1/2D or Plotter)
            plot_data.append((item, item.child(0).data()))

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
    parsed_url = urllib.parse.urlparse(url)
    if parsed_url.scheme:
        webbrowser.open(url)
    else:
        msg = "Attempt at opening an invalid URL"
        raise AttributeError(msg)

def retrieveData1d(data):
    """
    Retrieve 1D data from file and construct its text
    representation
    """
    if not isinstance(data, Data1D):
        msg = "Incorrect type passed to retrieveData1d"
        raise AttributeError(msg)
    try:
        xmin = min(data.x)
        ymin = min(data.y)
    except:
        msg = "Unable to find min/max of \n data named %s" % \
                    data.filename
        #logging.error(msg)
        raise ValueError(msg)

    text = data.__str__()
    text += 'Data Min Max:\n'
    text += 'X_min = %s:  X_max = %s\n' % (xmin, max(data.x))
    text += 'Y_min = %s:  Y_max = %s\n' % (ymin, max(data.y))
    if data.dy is not None:
        text += 'dY_min = %s:  dY_max = %s\n' % (min(data.dy), max(data.dy))
    text += '\nData Points:\n'
    x_st = "X"
    for index in range(len(data.x)):
        if data.dy is not None and len(data.dy) > index:
            dy_val = data.dy[index]
        else:
            dy_val = 0.0
        if data.dx is not None and len(data.dx) > index:
            dx_val = data.dx[index]
        else:
            dx_val = 0.0
        if data.dxl is not None and len(data.dxl) > index:
            if index == 0:
                x_st = "Xl"
            dx_val = data.dxl[index]
        elif data.dxw is not None and len(data.dxw) > index:
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
    Retrieve 2D data from file and construct its text
    representation
    """
    if not isinstance(data, Data2D):
        msg = "Incorrect type passed to retrieveData2d"
        raise AttributeError(msg)

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
    for index in range(0, len_data):
        x_val = data.qx_data[index]
        y_val = data.qy_data[index]
        i_val = data.data[index]
        if data.err_data is not None:
            di_val = data.err_data[index]
        if data.dqx_data is not None:
            dx_val = data.dqx_data[index]
        if data.dqy_data is not None:
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

def onTXTSave(data, path):
    """
    Save file as formatted txt
    """
    with open(path,'w') as out:
        has_errors = True
        if data.dy is None or not data.dy.any():
            has_errors = False
        # Sanity check
        if has_errors:
            try:
                if len(data.y) != len(data.dy):
                    has_errors = False
            except:
                has_errors = False
        if has_errors:
            if data.dx is not None and data.dx.any():
                out.write("<X>   <Y>   <dY>   <dX>\n")
            else:
                out.write("<X>   <Y>   <dY>\n")
        else:
            out.write("<X>   <Y>\n")

        for i in range(len(data.x)):
            if has_errors:
                if data.dx is not None and data.dx.any():
                    if  data.dx[i] is not None:
                        out.write("%g  %g  %g  %g\n" % (data.x[i],
                                                        data.y[i],
                                                        data.dy[i],
                                                        data.dx[i]))
                    else:
                        out.write("%g  %g  %g\n" % (data.x[i],
                                                    data.y[i],
                                                    data.dy[i]))
                else:
                    out.write("%g  %g  %g\n" % (data.x[i],
                                                data.y[i],
                                                data.dy[i]))
            else:
                out.write("%g  %g\n" % (data.x[i],
                                        data.y[i]))

def saveData1D(data):
    """
    Save 1D data points
    """
    default_name = os.path.basename(data.filename)
    default_name, extension = os.path.splitext(default_name)
    if not extension:
        extension = ".txt"
    default_name += "_out" + extension

    wildcard = "Text files (*.txt);;"\
                "CanSAS 1D files(*.xml)"
    kwargs = {
        'caption'   : 'Save As',
        'directory' : default_name,
        'filter'    : wildcard,
        'parent'    : None,
    }
    # Query user for filename.
    filename_tuple = QtWidgets.QFileDialog.getSaveFileName(**kwargs)
    filename = filename_tuple[0]

    # User cancelled.
    if not filename:
        return

    #Instantiate a loader
    loader = Loader()
    if os.path.splitext(filename)[1].lower() == ".txt":
        onTXTSave(data, filename)
    if os.path.splitext(filename)[1].lower() == ".xml":
        loader.save(filename, data, ".xml")

def saveData2D(data):
    """
    Save data2d dialog
    """
    default_name = os.path.basename(data.filename)
    default_name, _ = os.path.splitext(default_name)
    ext_format = ".dat"
    default_name += "_out" + ext_format

    wildcard = "IGOR/DAT 2D file in Q_map (*.dat)"
    kwargs = {
        'caption'   : 'Save As',
        'directory' : default_name,
        'filter'    : wildcard,
        'parent'    : None,
    }
    # Query user for filename.
    filename_tuple = QtWidgets.QFileDialog.getSaveFileName(**kwargs)
    filename = filename_tuple[0]

    # User cancelled.
    if not filename:
        return

    #Instantiate a loader
    loader = Loader()

    if os.path.splitext(filename)[1].lower() == ext_format:
        loader.save(filename, data, ext_format)

class FormulaValidator(QtGui.QValidator):
    def __init__(self, parent=None):
        super(FormulaValidator, self).__init__(parent)
  
    def validate(self, input, pos):

        self._setStyleSheet("")
        return QtGui.QValidator.Acceptable, pos

        #try:
        #    Formula(str(input))
        #    self._setStyleSheet("")
        #    return QtGui.QValidator.Acceptable, pos

        #except Exception as e:
        #    self._setStyleSheet("background-color:pink;")
        #    return QtGui.QValidator.Intermediate, pos

    def _setStyleSheet(self, value):
        try:
            if self.parent():
                self.parent().setStyleSheet(value)
        except:
            pass

def xyTransform(data, xLabel="", yLabel=""):
    """
    Transforms x and y in View and set the scale
    """
    # Changing the scale might be incompatible with
    # currently displayed data (for instance, going
    # from ln to log when all plotted values have
    # negative natural logs).
    # Go linear and only change the scale at the end.
    xscale = 'linear'
    yscale = 'linear'
    # Local data is either 1D or 2D
    if data.id == 'fit':
        return

    # control axis labels from the panel itself
    yname, yunits = data.get_yaxis()
    xname, xunits = data.get_xaxis()

    # Goes through all possible scales
    # self.x_label is already wrapped with Latex "$", so using the argument

    # X
    if xLabel == "x":
        data.transformX(DataTransform.toX, DataTransform.errToX)
        xLabel = "%s(%s)" % (xname, xunits)
    if xLabel == "x^(2)":
        data.transformX(DataTransform.toX2, DataTransform.errToX2)
        xunits = convertUnit(2, xunits)
        xLabel = "%s^{2}(%s)" % (xname, xunits)
    if xLabel == "x^(4)":
        data.transformX(DataTransform.toX4, DataTransform.errToX4)
        xunits = convertUnit(4, xunits)
        xLabel = "%s^{4}(%s)" % (xname, xunits)
    if xLabel == "ln(x)":
        data.transformX(DataTransform.toLogX, DataTransform.errToLogX)
        xLabel = "\ln{(%s)}(%s)" % (xname, xunits)
    if xLabel == "log10(x)":
        data.transformX(DataTransform.toX_pos, DataTransform.errToX_pos)
        xscale = 'log'
        xLabel = "%s(%s)" % (xname, xunits)
    if xLabel == "log10(x^(4))":
        data.transformX(DataTransform.toX4, DataTransform.errToX4)
        xunits = convertUnit(4, xunits)
        xLabel = "%s^{4}(%s)" % (xname, xunits)
        xscale = 'log'

    # Y
    if yLabel == "ln(y)":
        data.transformY(DataTransform.toLogX, DataTransform.errToLogX)
        yLabel = "\ln{(%s)}(%s)" % (yname, yunits)
    if yLabel == "y":
        data.transformY(DataTransform.toX, DataTransform.errToX)
        yLabel = "%s(%s)" % (yname, yunits)
    if yLabel == "log10(y)":
        data.transformY(DataTransform.toX_pos, DataTransform.errToX_pos)
        yscale = 'log'
        yLabel = "%s(%s)" % (yname, yunits)
    if yLabel == "y^(2)":
        data.transformY(DataTransform.toX2, DataTransform.errToX2)
        yunits = convertUnit(2, yunits)
        yLabel = "%s^{2}(%s)" % (yname, yunits)
    if yLabel == "1/y":
        data.transformY(DataTransform.toOneOverX, DataTransform.errOneOverX)
        yunits = convertUnit(-1, yunits)
        yLabel = "1/%s(%s)" % (yname, yunits)
    if yLabel == "y*x^(2)":
        data.transformY(DataTransform.toYX2, DataTransform.errToYX2)
        xunits = convertUnit(2, xunits)
        yLabel = "%s \ \ %s^{2}(%s%s)" % (yname, xname, yunits, xunits)
    if yLabel == "y*x^(4)":
        data.transformY(DataTransform.toYX4, DataTransform.errToYX4)
        xunits = convertUnit(4, xunits)
        yLabel = "%s \ \ %s^{4}(%s%s)" % (yname, xname, yunits, xunits)
    if yLabel == "1/sqrt(y)":
        data.transformY(DataTransform.toOneOverSqrtX, DataTransform.errOneOverSqrtX)
        yunits = convertUnit(-0.5, yunits)
        yLabel = "1/\sqrt{%s}(%s)" % (yname, yunits)
    if yLabel == "ln(y*x)":
        data.transformY(DataTransform.toLogXY, DataTransform.errToLogXY)
        yLabel = "\ln{(%s \ \ %s)}(%s%s)" % (yname, xname, yunits, xunits)
    if yLabel == "ln(y*x^(2))":
        data.transformY(DataTransform.toLogYX2, DataTransform.errToLogYX2)
        xunits = convertUnit(2, xunits)
        yLabel = "\ln (%s \ \ %s^{2})(%s%s)" % (yname, xname, yunits, xunits)
    if yLabel == "ln(y*x^(4))":
        data.transformY(DataTransform.toLogYX4, DataTransform.errToLogYX4)
        xunits = convertUnit(4, xunits)
        yLabel = "\ln (%s \ \ %s^{4})(%s%s)" % (yname, xname, yunits, xunits)
    if yLabel == "log10(y*x^(4))":
        data.transformY(DataTransform.toYX4, DataTransform.errToYX4)
        xunits = convertUnit(4, xunits)
        yscale = 'log'
        yLabel = "%s \ \ %s^{4}(%s%s)" % (yname, xname, yunits, xunits)

    # Perform the transformation of data in data1d->View
    data.transformView()

    return (xLabel, yLabel, xscale, yscale)

def dataFromItem(item):
    """
    Retrieve Data1D/2D component from QStandardItem.
    The assumption - data stored in SasView standard, in child 0
    """
    return item.child(0).data()

def formatNumber(value, high=False):
    """
    Return a float in a standardized, human-readable formatted string.
    This is used to output readable (e.g. x.xxxe-y) values to the panel.
    """
    try:
        value = float(value)
    except:
        output = "NaN"
        return output.lstrip().rstrip()

    if high:
        output = "%-7.5g" % value

    else:
        output = "%-5.3g" % value
    return output.lstrip().rstrip()

def convertUnitToHTML(unit):
    """
    Convert ASCII unit display into well rendering HTML
    """
    if unit == "1/A":
        return "&#x212B;<sup>-1</sup>"
    elif unit == "1/cm":
        return "cm<sup>-1</sup>"
    elif unit == "Ang":
        return "&#x212B;"
    elif unit == "1e-6/Ang^2":
        return "10<sup>-6</sup>/&#x212B;<sup>2</sup>"
    elif unit == "inf":
        return "&#x221e;"
    elif unit == "-inf":
        return "-&#x221e;"
    else:
        return unit

def parseName(name, expression):
    """
    remove "_" in front of a name
    """
    if re.match(expression, name) is not None:
        word = re.split(expression, name, 1)
        for item in word:           
            if item.lstrip().rstrip() != '':
                return item
    else:
        return name

def toDouble(value_string):
    """
    toFloat conversion which cares deeply about user's locale
    """
    # Holy shit this escalated quickly in Qt5.
    # No more float() cast on general locales.
    value = QtCore.QLocale().toFloat(value_string)
    if value[1]:
        return value[0]

    # Try generic locale
    value = QtCore.QLocale(QtCore.QLocale('en_US')).toFloat(value_string)
    if value[1]:
        return value[0]
    else:
        raise TypeError

def findNextFilename(filename, directory):
    """
    Finds the next available (non-existing) name for 'filename' in 'directory'.
    plugin.py -> plugin (n).py  - for first 'n' for which the file doesn't exist
    """
    basename, ext = os.path.splitext(filename)
    # limit the number of copies
    MAX_FILENAMES = 1000
    # Start with (1)
    number_ext = 1
    proposed_filename = ""
    found_filename = False
    # Find the next available filename or exit if too many copies
    while not found_filename or number_ext > MAX_FILENAMES:
        proposed_filename = basename + " ("+str(number_ext)+")" + ext
        if os.path.exists(os.path.join(directory, proposed_filename)):
            number_ext += 1
        else:
            found_filename = True

    return proposed_filename


class DoubleValidator(QtGui.QDoubleValidator):
    """
    Allow only dots as decimal separator
    """
    def validate(self, input, pos):
        """
        Return invalid for commas
        """
        if input is not None and ',' in input:
            return (QtGui.QValidator.Invalid, input, pos)
        return super(DoubleValidator, self).validate(input, pos)

    def fixup(self, input):
        """
        Correct (remove) potential preexisting content
        """
        super(DoubleValidator, self).fixup(input)
        input = input.replace(",", "")


def enum(*sequential, **named):
    """Create an enumeration object from a list of strings"""
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)
