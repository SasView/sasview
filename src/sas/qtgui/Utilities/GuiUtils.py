# -*- coding: utf-8 -*-
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
import json
import types
from io import BytesIO

import numpy as np

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
from sas.qtgui.Plotting.Plottables import Plottable
from sas.sascalc.dataloader.data_info import Sample, Source, Vector
from sas.sascalc.dataloader.data_info import Detector, Process, TransmissionSpectrum
from sas.sascalc.dataloader.data_info import Aperture, Collimation
from sas.qtgui.Plotting.Plottables import View
from sas.qtgui.Plotting.Plottables import PlottableTheory1D
from sas.qtgui.Plotting.Plottables import PlottableFit1D
from sas.qtgui.Plotting.Plottables import Text
from sas.qtgui.Plotting.Plottables import Chisq
from sas.qtgui.MainWindow.DataState import DataState

from sas.sascalc.fit.AbstractFitEngine import FResult
from sas.sascalc.fit.AbstractFitEngine import FitData1D, FitData2D
from sasmodels.sasview_model import SasviewModel

from sas.sascalc.dataloader.loader import Loader
from sas.sascalc.file_converter.nxcansas_writer import NXcanSASWriter

from sas.qtgui.Utilities import CustomDir

if os.path.splitext(sys.argv[0])[1].lower() != ".py":
        HELP_DIRECTORY_LOCATION = "doc"
else:
        HELP_DIRECTORY_LOCATION = "docs/sphinx-docs/build/html"
IMAGES_DIRECTORY_LOCATION = HELP_DIRECTORY_LOCATION + "/_images"

# This matches the ID of a plot created using FittingLogic._create1DPlot, e.g.
# "5 [P(Q)] modelname"
# or
# "4 modelname".
# Useful for determining whether the plot in question is for an intermediate result, such as P(Q) or S(Q) in the
# case of a product model; the identifier for this is held in square brackets, as in the example above.
theory_plot_ID_pattern = re.compile(r"^([0-9]+)\s+(\[(.*)\]\s+)?(.*)$")

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
    except ValueError:
        print("Value error")
        pass
    finally:
        if fObj is not None:
            fObj.close()
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
logging.info("Custom config path: %s", custom_config)

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
    SAS_OPENCL = custom_config.SAS_OPENCL
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
    SAS_OPENCL = config.SAS_OPENCL

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

    # Request to delete plots (in the theory view) related to a given model ID
    deleteIntermediateTheoryPlotsSignal = QtCore.pyqtSignal(str)

    # New plot requested from the GUI manager
    # Old "NewPlotEvent"
    plotRequestedSignal = QtCore.pyqtSignal(list, int)

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

    # Notify the gui manager about new data to be added to the grid view
    sendDataToGridSignal = QtCore.pyqtSignal(list)

    # Mask Editor requested
    maskEditorSignal = QtCore.pyqtSignal(Data2D)

    #second Mask Editor for external
    extMaskEditorSignal = QtCore.pyqtSignal()

    # Fitting parameter copy to clipboard
    copyFitParamsSignal = QtCore.pyqtSignal(str)

    # Fitting parameter copy to clipboard for Excel
    copyExcelFitParamsSignal = QtCore.pyqtSignal(str)

    # Fitting parameter copy to clipboard for Latex
    copyLatexFitParamsSignal = QtCore.pyqtSignal(str)

    # Fitting parameter copy to clipboard for Latex
    SaveFitParamsSignal = QtCore.pyqtSignal(str)

    # Fitting parameter paste from clipboard
    pasteFitParamsSignal = QtCore.pyqtSignal()

    # Notify about new categories/models from category manager
    updateModelCategoriesSignal = QtCore.pyqtSignal()

    # Tell the data explorer to switch tabs
    changeDataExplorerTabSignal = QtCore.pyqtSignal(int)

    # Plot fitting results (FittingWidget->GuiManager)
    resultPlotUpdateSignal = QtCore.pyqtSignal(list)

    # show the plot as a regular in-workspace object
    forcePlotDisplaySignal = QtCore.pyqtSignal(list)

    # Update the masked ranges in fitting
    updateMaskedDataSignal = QtCore.pyqtSignal()

def updateModelItemWithPlot(item, update_data, name="", checkbox_state=None):
    """
    Adds a checkboxed row named "name" to QStandardItem
    Adds 'update_data' to that row.
    """
    assert isinstance(item, QtGui.QStandardItem)

    # Check if data with the same ID is already present
    for index in range(item.rowCount()):
        plot_item = item.child(index)
        if not plot_item.isCheckable():
            continue
        plot_data = plot_item.child(0).data()
        if plot_data.id is not None and \
                plot_data.name == update_data.name:
                #(plot_data.name == update_data.name or plot_data.id == update_data.id):
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

    if checkbox_state is not None:
        checkbox_item.setCheckState(checkbox_state)
    # Append the new row to the main item
    item.appendRow(checkbox_item)

def deleteRedundantPlots(item, new_plots):
    """
    Checks all plots that are children of the given item; if any have an ID or name not included in new_plots,
    it is deleted. Useful for e.g. switching from P(Q)S(Q) to P(Q); this would remove the old S(Q) plot.

    Ensure that new_plots contains ALL the relevant plots(!!!)
    """
    assert isinstance(item, QtGui.QStandardItem)

    # lists of plots names/ids for all deletable plots on item
    names = [p.name for p in new_plots if p.name is not None]
    ids = [p.id for p in new_plots if p.id is not None]

    items_to_delete = []

    for index in range(item.rowCount()):
        plot_item = item.child(index)
        if not plot_item.isCheckable():
            continue
        plot_data = plot_item.child(0).data()
        if (plot_data.id is not None) and \
            (plot_data.id not in ids) and \
            (plot_data.name not in names) and \
            (plot_data.plot_role == Data1D.ROLE_DELETABLE):
            items_to_delete.append(plot_item)

    for plot_item in items_to_delete:
        item.removeRow(plot_item.row())

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

def getMonospaceFont():
    """Convenience function; returns a monospace font to be used in any shells, code editors, etc."""

    # Note: Consolas is only available on Windows; the style hint is used on other operating systems
    font = QtGui.QFont("Consolas", 10)
    font.setStyleHint(QtGui.QFont.Monospace, QtGui.QFont.PreferQuality)
    return font

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

def plotsFromModel(model_name, model_item):
    """
    Returns the list of plots for the item with model name in the model
    """
    assert isinstance(model_item, QtGui.QStandardItem)
    assert isinstance(model_name, str)

    plot_data = []
    # Iterate over model looking for named items
    for index in range(model_item.rowCount()):
        item = model_item.child(index)
        if isinstance(item.data(), (Data1D, Data2D)):
            plot_data.append(item.data())
        if model_name in str(item.text()):
            #plot_data.append(item.child(0).data())
            # Going 1 level deeper only
            for index_2 in range(item.rowCount()):
                item_2 = item.child(index_2)
                if item_2 and isinstance(item_2.data(), (Data1D, Data2D)):
                    plot_data.append(item_2.data())

    return plot_data

def plotsFromFilename(filename, model_item):
    """
    Returns the list of plots for the item with text=filename in the model
    """
    assert isinstance(model_item, QtGui.QStandardItemModel)
    assert isinstance(filename, str)

    plot_data = {}
    # Iterate over model looking for named items
    for index in range(model_item.rowCount()):
        item = model_item.item(index)
        if filename in str(item.text()):
            # TODO: assure item type is correct (either data1/2D or Plotter)
            plot_data[item] = item.child(0).data()
            # Going 1 level deeper only
            for index_2 in range(item.rowCount()):
                item_2 = item.child(index_2)
                if item_2 and item_2.isCheckable():
                    # TODO: assure item type is correct (either data1/2D or Plotter)
                    plot_data[item_2] = item_2.child(0).data()

    return plot_data

def getChildrenFromItem(root):
    """
    Recursively go down the model item looking for all children
    """
    def recurse(parent):
        for row in range(parent.rowCount()):
            for column in range(parent.columnCount()):
                child = parent.child(row, column)
                yield child
                if child.hasChildren():
                    yield from recurse(child)
    if root is not None:
        yield from recurse(root)

def plotsFromCheckedItems(model_item):
    """
    Returns the list of plots for items in the model which are checked
    """
    assert isinstance(model_item, QtGui.QStandardItemModel)

    plot_data = []

    # Iterate over model looking for items with checkboxes
    for index in range(model_item.rowCount()):
        item = model_item.item(index)
        if item and item.isCheckable() and item.checkState() == QtCore.Qt.Checked:
            data = item.child(0).data()
            plot_data.append((item, data))

        items = list(getChildrenFromItem(item))

        for it in items:
            if it.isCheckable() and it.checkState() == QtCore.Qt.Checked:
                data = it.child(0).data()
                plot_data.append((it, data))

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
            if process is None:
                continue
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

def dataFromItem(item):
    """
    Retrieve Data1D/2D component from QStandardItem.
    The assumption - data stored in SasView standard, in child 0
    """
    try:
        data = item.child(0).data()
    except AttributeError:
        data = None
    return data

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

def showHelp(url):
    """
    Open a local url in the default browser
    """
    location = HELP_DIRECTORY_LOCATION + url
    #WP: Added to handle OSX bundle docs
    if os.path.isdir(location) == False:
        sas_path = os.path.abspath(os.path.dirname(sys.argv[0]))
        location = sas_path+"/"+location
    try:
        webbrowser.open('file://' + os.path.realpath(location))
    except webbrowser.Error as ex:
        logging.warning("Cannot display help. %s" % ex)

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
                out.write("<X>"+" "*20+ "<Y>"+" "*20+"<dY>"+" "*20+"<dX>\n")
                #out.write("<X>   <Y>   <dY>   <dX>\n")
            else:
                out.write("<X>"+" "*20+ "<Y>"+" "*20+"<dY>\n")
        else:
            out.write("<X>"+" "*20+ "<Y>\n")

        for i in range(len(data.x)):
            if has_errors:
                if data.dx is not None and data.dx.any():
                    if  data.dx[i] is not None:
                        out.write("%.15e  %.15e  %.15e  %.15e\n" % (data.x[i],
                                                        data.y[i],
                                                        data.dy[i],
                                                        data.dx[i]))
                    else:
                        out.write("%.15e  %.15e  %.15e\n" % (data.x[i],
                                                    data.y[i],
                                                    data.dy[i]))
                else:
                    out.write("%.15e  %.15e  %.15e\n" % (data.x[i],
                                                data.y[i],
                                                data.dy[i]))
            else:
                out.write("%.15e  %.15e\n" % (data.x[i],
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
                "CanSAS 1D files(*.xml);;"\
                "NXcanSAS files (*.h5)"
    kwargs = {
        'caption'   : 'Save As',
        #'directory' : default_name,
        'filter'    : wildcard,
        'parent'    : None,
        'options'   : QtWidgets.QFileDialog.DontUseNativeDialog
    }
    # Query user for filename.
    filename_tuple = QtWidgets.QFileDialog.getSaveFileName(**kwargs)
    filename = filename_tuple[0]

    # User cancelled.
    if not filename:
        return

    # Check/add extension
    if not os.path.splitext(filename)[1]:
        ext = filename_tuple[1]
        if 'Text files' in ext:
            filename += '.txt'
        elif 'CanSAS' in ext:
            filename += '.xml'
        elif 'NXcanSAS' in ext:
            filename += '.h5'
        else:
            pass

    #Instantiate a loader
    loader = Loader()
    if os.path.splitext(filename)[1].lower() == ".txt":
        onTXTSave(data, filename)
    elif os.path.splitext(filename)[1].lower() == ".xml":
        loader.save(filename, data, ".xml")
    elif os.path.splitext(filename)[1].lower() == ".h5":
        nxcansaswriter = NXcanSASWriter()
        nxcansaswriter.write([data], filename)

def saveData2D(data):
    """
    Save data2d dialog
    """
    default_name = os.path.basename(data.filename)
    default_name, _ = os.path.splitext(default_name)
    ext_format = ".dat"
    default_name += "_out" + ext_format

    wildcard = "IGOR/DAT 2D file in Q_map (*.dat);;"\
                "NXcanSAS files (*.h5)"
    kwargs = {
        'caption'   : 'Save As',
        'filter'    : wildcard,
        'parent'    : None,
        'options'   : QtWidgets.QFileDialog.DontUseNativeDialog
    }
    # Query user for filename.
    filename_tuple = QtWidgets.QFileDialog.getSaveFileName(**kwargs)
    filename = filename_tuple[0]

    # User cancelled.
    if not filename:
        return

    # Check/add extension
    if not os.path.splitext(filename)[1]:
        ext = filename_tuple[1]
        if 'IGOR' in ext:
            filename += '.dat'
        elif 'NXcanSAS' in ext:
            filename += '.h5'
        else:
            pass

    #Instantiate a loader
    loader = Loader()

    if os.path.splitext(filename)[1].lower() == ext_format:
        loader.save(filename, data, ext_format)
    elif os.path.splitext(filename)[1].lower() == ".h5":
        nxcansaswriter = NXcanSASWriter()
        nxcansaswriter.write([data], filename)


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

    # make sure we have some function to operate on
    if xLabel is None:
        xLabel = 'log10(x)'
    if yLabel is None:
        yLabel = 'log10(y)'

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

def replaceHTMLwithUTF8(html):
    """
    Replace some important HTML-encoded characters
    with their UTF-8 equivalents
    """
    # Angstrom
    html_out = html.replace("&#x212B;", "Å")
    # infinity
    html_out = html_out.replace("&#x221e;", "∞")
    # +/-
    html_out = html_out.replace("&#177;", "±")

    return html_out

def replaceHTMLwithASCII(html):
    """
    Replace some important HTML-encoded characters
    with their ASCII equivalents
    """
    # Angstrom
    html_out = html.replace("&#x212B;", "Ang")
    # infinity
    html_out = html_out.replace("&#x221e;", "inf")
    # +/-
    html_out = html_out.replace("&#177;", "+/-")

    return html_out

def convertUnitToUTF8(unit):
    """
    Convert ASCII unit display into UTF-8 symbol
    """
    if unit == "1/A":
        return "Å<sup>-1</sup>"
    elif unit == "1/cm":
        return "cm<sup>-1</sup>"
    elif unit == "Ang":
        return "Å"
    elif unit == "1e-6/Ang^2":
        return "10<sup>-6</sup>/Å<sup>2</sup>"
    elif unit == "inf":
        return "∞"
    elif unit == "-inf":
        return "-∞"
    else:
        return unit

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

def checkModel(path):
    """
    Check that the model save in file 'path' can run.
    """
    # The following return needs to be removed once
    # the unittest related changes in Sasmodels are commited
    # return True
    # try running the model
    from sasmodels.sasview_model import load_custom_model
    Model = load_custom_model(path)
    model = Model()
    q =  np.array([0.01, 0.1])
    _ = model.evalDistribution(q)
    qx, qy =  np.array([0.01, 0.01]), np.array([0.1, 0.1])
    _ = model.evalDistribution([qx, qy])

    # check the model's unit tests run
    from sasmodels.model_test import run_one
    # TestSuite module in Qt5 now deletes tests in the suite after running,
    # so suite[0] in run_one() in sasmodels/model_test.py will contain [None] and
    # test.info.tests will raise.
    # Not sure how to change the behaviour here, most likely sasmodels will have to
    # be modified
    result = run_one(path)

    return result

def saveData(fp, data):
    """
    save content of data to fp (a .write()-supporting file-like object)
    """

    def add_type(dict, type):
        dict['__type__'] = type.__name__
        return dict

    def jdefault(o):
        """
        objects that can't otherwise be serialized need to be converted
        """
        # tuples and sets (TODO: default JSONEncoder converts tuples to lists, create custom Encoder that preserves tuples)
        if isinstance(o, (tuple, set)):
            content = { 'data': list(o) }
            return add_type(content, type(o))

        # "simple" types
        if isinstance(o, (Sample, Source, Vector, FResult)):
            return add_type(o.__dict__, type(o))
        # detector
        if isinstance(o, (Detector, Process, TransmissionSpectrum, Aperture, Collimation)):
            return add_type(o.__dict__, type(o))

        if isinstance(o, (Plottable, View)):
            return add_type(o.__dict__, type(o))

        # SasviewModel - unique
        if isinstance(o, SasviewModel):
            # don't store parent
            content = o.__dict__.copy()
            return add_type(content, SasviewModel)

        # DataState
        if isinstance(o, (Data1D, Data2D, FitData1D, FitData2D)):
            # don't store parent
            content = o.__dict__.copy()
            return add_type(content, type(o))

        # ndarray
        if isinstance(o, np.ndarray):
            content = {'data':o.tolist()}
            return add_type(content, type(o))

        if isinstance(o, types.FunctionType):
            # we have a pure function
            content = o.__dict__.copy()
            return add_type(content, type(o))

        # not supported
        logging.info("data cannot be serialized to json: %s" % type(o))
        return None

    json.dump(data, fp, indent=2, sort_keys=True, default=jdefault)

def readDataFromFile(fp):
    '''
    Reads in Data1D/Data2 datasets from the file.
    Datasets are stored in the JSON format.
    '''
    supported = [
        tuple, set, types.FunctionType,
        Sample, Source, Vector,
        Plottable, Data1D, Data2D, PlottableTheory1D, PlottableFit1D, Text, Chisq, View,
        Detector, Process, TransmissionSpectrum, Collimation, Aperture,
        DataState, np.ndarray, FResult, FitData1D, FitData2D, SasviewModel]

    lookup = dict((cls.__name__, cls) for cls in supported)

    class TooComplexException(Exception):
        pass

    def simple_type(cls, data, level):
        class Empty(object):
            def __init__(self):
                for key, value in data.items():
                    setattr(self, key, generate(value, level))

        # create target object
        o = Empty()
        o.__class__ = cls

        return o

    def construct(type, data, level):
        try:
            cls = lookup[type]
        except KeyError:
            logging.info('unknown type: %s' % type)
            return None

        # tuples and sets
        if cls in (tuple, set):
            # convert list to tuple/set
            return cls(generate(data['data'], level))

        # "simple" types
        if cls in (Sample, Source, Vector, FResult, FitData1D, FitData2D,
                   SasviewModel, Detector, Process, TransmissionSpectrum,
                   Collimation, Aperture):
            return simple_type(cls, data, level)
        if issubclass(cls, Plottable) or (cls == View):
            return simple_type(cls, data, level)

        # DataState
        if cls == DataState:
            o = simple_type(cls, data, level)
            o.parent = None # TODO: set to ???
            return o

        # ndarray
        if cls == np.ndarray:
            o = data['data']
            if isinstance(o, list):
                # new format - ndarray as ascii list
                return np.array(o)
            else:
                # pre-5.0-release format - binary ndarray
                buffer = BytesIO()
                buffer.write(data['data'].encode('latin-1'))
                buffer.seek(0)
                return np.load(buffer)

        # function
        if cls == types.FunctionType:
            return cls

        logging.info('not implemented: %s, %s' % (type, cls))
        return None

    def generate(data, level):
        if level > 16: # recursion limit (arbitrary number)
            raise TooComplexException()
        else:
            level += 1

        if isinstance(data, dict):
            try:
                type = data['__type__']
            except KeyError:
                # if dictionary doesn't have __type__ then it is assumed to be just an ordinary dictionary
                o = {}
                for key, value in data.items():
                    o[key] = generate(value, level)
                return o

            return construct(type, data, level)

        if isinstance(data, list):
            return [generate(item, level) for item in data]

        return data

    new_stored_data = {}
    for id, data in json.load(fp).items():
        try:
            new_stored_data[id] = generate(data, 0)
        except TooComplexException:
            logging.info('unable to load %s' % id)

    return new_stored_data

def readProjectFromSVS(filepath):
    """
    Read old SVS file and convert to the project dictionary
    """
    from sas.sascalc.dataloader.readers.cansas_reader import Reader as CansasReader
    from sas.sascalc.fit.pagestate import Reader

    loader = Loader()
    loader.associate_file_reader('.svs', Reader)
    temp = loader.load(filepath)

    # CRUFT: SasView 4.x uses a callback interface to register bits of state
    state_svs = []
    def collector(state=None, datainfo=None, format=None):
        if state is not None:
            state_svs.append(state)
    state_reader = Reader(call_back=collector)
    data_svs = state_reader.read(filepath)

    if isinstance(temp, list) and isinstance(state_svs, list):
        output = list(zip(temp, state_svs))
    else:
        output = [(temp, state_svs)]
    return output

def convertFromSVS(datasets):
    """
    Read in properties from SVS and convert into a simple dict
    """
    content = {}
    for dataset in datasets:
        # we already have data - interested only in properties
        #[[item_1, state_1], [item_2, state_2],...]
        data = dataset[0]
        params = dataset[1]
        content[params.data_id] = {}
        content[params.data_id]['fit_data'] = [data, {'checked': 2}, []]
        param_dict = {}
        param_dict['fitpage_category'] = [params.categorycombobox]
        param_dict['fitpage_model'] = [params.formfactorcombobox]
        param_dict['fitpage_structure'] = [params.structurecombobox]
        param_dict['2D_params'] = [str(params.is_2D)]
        param_dict['chainfit_params'] = ["False"]
        param_dict['data_id'] = [params.data_id]
        param_dict['data_name'] = [params.data_name]
        param_dict['is_data'] = [str(params.is_data)]
        param_dict['magnetic_params'] = [str(params.magnetic_on)]
        param_dict['model_name'] = [params.formfactorcombobox]
        param_dict['polydisperse_params'] = [str(params.enable_disp)]
        param_dict['q_range_max'] = [str(params.qmax)]
        param_dict['q_range_min'] = [str(params.qmin)]
        # Smearing is a bit trickier. 4.x has multiple keywords,
        # one for each combobox option
        if params.enable_smearer:
            if params.slit_smearer:
                w = 1
            elif params.pinhole_smearer:
                w = 2
            else:
                w = 0
            param_dict['smearing'] = [str(w)]
        # weighting is also tricky. 4.x has multiple keywords,
        # one for each radio box.
        if params.dI_noweight:
            w = 2
        elif params.dI_didata:
            w = 3
        elif params.dI_sqrdata:
            w = 4
        elif params.dI_idata:
            w = 5
        else:
            w = 2
        param_dict['weighting'] = [str(w)]

        # 4.x multi_factor is really the multiplicity
        if params.multi_factor is not None:
            param_dict['multiplicity'] = [str(int(params.multi_factor))]

        # playing with titles
        data.filename = params.file
        data.title = params.data_name
        data.name = params.data_name

        # main parameters
        for p in params.parameters:
            p_name = p[1]
            param_dict[p_name] = [str(p[0]), str(p[2]), None, str(p[5][1]), str(p[6][1]), []]
        # orientation parameters
        if params.is_2D:
            for p in params.orientation_params:
                p_name = p[1]
                p_min = "-360.0"
                p_max = "360.0"
                if p[5][1] != "":
                    p_min = p[5][1]
                if p[6][1] != "":
                    p_max = p[6][1]
                param_dict[p_name] = [str(p[0]), str(p[2]), None, p_min, p_max, []]

        # disperse parameters
        if params.enable_disp:
            for p in params.fittable_param:
                p_name = p[1]
                p_opt = str(p[0])
                p_err = "0"
                p_width = str(p[2])
                p_min = str(0)
                p_max = "inf"
                param_npts = p_name.replace('.width','.npts')
                param_nsigmas = p_name.replace('.width', '.nsigmas')
                if params.is_2D and p_name in params.disp_obj_dict:
                    lookup = params.orientation_params_disp
                    p_min = "-360.0"
                    p_max = "360.0"
                else:
                    lookup = params.fixed_param
                p_npts = [s[2] for s in lookup if s[1] == param_npts][0]
                p_nsigmas = [s[2] for s in lookup if s[1] == param_nsigmas][0]
                if p_name in params.disp_obj_dict:
                    p_disp = params.disp_obj_dict[p_name]
                else:
                    p_disp = "gaussian"
                param_dict[p_name] = [p_opt, p_width, p_min, p_max, p_npts, p_nsigmas, p_disp]

        param_dict['is_batch_fitting'] = ['False']
        content[params.data_id]['fit_params'] = param_dict

    return content

def enum(*sequential, **named):
    """Create an enumeration object from a list of strings"""
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)
