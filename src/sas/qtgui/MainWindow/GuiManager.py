import sys
import os
import subprocess
import logging
import json
import webbrowser
import traceback

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QLocale, QUrl

import matplotlib as mpl
mpl.use("Qt5Agg")

from sas.sasview import __version__ as SASVIEW_VERSION
from sas.sasview import __release_date__ as SASVIEW_RELEASE_DATE

from twisted.internet import reactor
# General SAS imports
from sas import get_local_config, get_custom_config
from sas.qtgui.Utilities.ConnectionProxy import ConnectionProxy
from sas.qtgui.Utilities.SasviewLogger import setup_qt_logging

import sas.qtgui.Utilities.LocalConfig as LocalConfig
import sas.qtgui.Utilities.GuiUtils as GuiUtils

import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary
from sas.qtgui.Utilities.TabbedModelEditor import TabbedModelEditor
from sas.qtgui.Utilities.PluginManager import PluginManager
from sas.qtgui.Utilities.GridPanel import BatchOutputPanel
from sas.qtgui.Utilities.ResultPanel import ResultPanel

from sas.qtgui.Utilities.ReportDialog import ReportDialog
from sas.qtgui.MainWindow.Acknowledgements import Acknowledgements
from sas.qtgui.MainWindow.AboutBox import AboutBox
from sas.qtgui.MainWindow.WelcomePanel import WelcomePanel
from sas.qtgui.MainWindow.CategoryManager import CategoryManager
from sas.qtgui.MainWindow.PackageGatherer import PackageGatherer

from sas.qtgui.MainWindow.DataManager import DataManager

from sas.qtgui.Calculators.SldPanel import SldPanel
from sas.qtgui.Calculators.DensityPanel import DensityPanel
from sas.qtgui.Calculators.KiessigPanel import KiessigPanel
from sas.qtgui.Calculators.SlitSizeCalculator import SlitSizeCalculator
from sas.qtgui.Calculators.GenericScatteringCalculator import GenericScatteringCalculator
from sas.qtgui.Calculators.ResolutionCalculatorPanel import ResolutionCalculatorPanel
from sas.qtgui.Calculators.DataOperationUtilityPanel import DataOperationUtilityPanel

import sas.qtgui.Plotting.PlotHelper as PlotHelper

# Perspectives
import sas.qtgui.Perspectives as Perspectives
from sas.qtgui.Perspectives.Fitting.FittingPerspective import FittingWindow
from sas.qtgui.MainWindow.DataExplorer import DataExplorerWindow, DEFAULT_PERSPECTIVE

from sas.qtgui.Utilities.AddMultEditor import AddMultEditor
from sas.qtgui.Utilities.ImageViewer import ImageViewer
from sas.qtgui.Utilities.FileConverter import FileConverterWidget

logger = logging.getLogger(__name__)


class GuiManager(object):
    """
    Main SasView window functionality
    """
    def __init__(self, parent=None):
        """
        Initialize the manager as a child of MainWindow.
        """
        self._workspace = parent
        self._parent = parent

        # Decide on a locale
        QLocale.setDefault(QLocale('en_US'))

        # Redefine exception hook to not explicitly crash the app.
        sys.excepthook = self.info

        # Add signal callbacks
        self.addCallbacks()

        # Assure model categories are available
        self.addCategories()

        # Create the data manager
        # TODO: pull out all required methods from DataManager and reimplement
        self._data_manager = DataManager()

        # Create action triggers
        self.addTriggers()

        # Currently displayed perspective
        self._current_perspective = None
        self.loadedPerspectives = {}

        # Populate the main window with stuff
        self.addWidgets()

        # Fork off logging messages to the Log Window
        handler = setup_qt_logging()
        handler.messageWritten.connect(self.appendLog)

        # Log the start of the session
        logging.info(f" --- SasView session started, version {SASVIEW_VERSION}, {SASVIEW_RELEASE_DATE} ---")
        # Log the python version
        logging.info("Python: %s" % sys.version)

        # Set up the status bar
        self.statusBarSetup()

        # Current tutorial location
        self._tutorialLocation = os.path.abspath(os.path.join(GuiUtils.HELP_DIRECTORY_LOCATION,
                                              "_downloads",
                                              "Tutorial.pdf"))

    def info(self, type, value, tb):
        logger.error("".join(traceback.format_exception(type, value, tb)))

    def addWidgets(self):
        """
        Populate the main window with widgets
        """
        # Add the console window as another docked widget
        self.logDockWidget = QDockWidget("Log Explorer", self._workspace)
        self.logDockWidget.setObjectName("LogDockWidget")
        self.logDockWidget.visibilityChanged.connect(self.updateLogContextMenus)


        self.listWidget = QTextBrowser()
        self.logDockWidget.setWidget(self.listWidget)
        self._workspace.addDockWidget(Qt.BottomDockWidgetArea, self.logDockWidget)

        # Preload all perspectives
        self.loadAllPerspectives()
        # Add FileDialog widget as docked
        self.filesWidget = DataExplorerWindow(self._parent, self, manager=self._data_manager)
        ObjectLibrary.addObject('DataExplorer', self.filesWidget)

        self.dockedFilesWidget = QDockWidget("Data Explorer", self._workspace)
        self.dockedFilesWidget.setFloating(False)
        self.dockedFilesWidget.setWidget(self.filesWidget)
        # Modify menu items on widget visibility change
        self.dockedFilesWidget.visibilityChanged.connect(self.updateContextMenus)

        self._workspace.addDockWidget(Qt.LeftDockWidgetArea, self.dockedFilesWidget)
        self._workspace.resizeDocks([self.dockedFilesWidget], [305], Qt.Horizontal)

        # Add other, minor widgets
        self.ackWidget = Acknowledgements()
        self.aboutWidget = AboutBox()
        self.categoryManagerWidget = CategoryManager(self._parent, manager=self)

        self.grid_window = None
        self.grid_window = BatchOutputPanel(parent=self)
        if sys.platform == "darwin":
            self.grid_window.menubar.setNativeMenuBar(False)
        self.grid_subwindow = self._workspace.workspace.addSubWindow(self.grid_window)
        self.grid_subwindow.setVisible(False)
        self.grid_window.windowClosedSignal.connect(lambda: self.grid_subwindow.setVisible(False))

        self.results_panel = ResultPanel(parent=self._parent, manager=self)
        self.results_frame = self._workspace.workspace.addSubWindow(self.results_panel)
        self.results_frame.setVisible(False)
        self.results_panel.windowClosedSignal.connect(lambda: self.results_frame.setVisible(False))

        custom_config = get_custom_config()
        self._workspace.toolBar.setVisible(custom_config.TOOLBAR_SHOW)

        # Add calculators - floating for usability
        self.SLDCalculator = SldPanel(self)
        self.DVCalculator = DensityPanel(self)
        self.KIESSIGCalculator = KiessigPanel(self)
        self.SlitSizeCalculator = SlitSizeCalculator(self)
        self.GENSASCalculator = GenericScatteringCalculator(self)
        self.ResolutionCalculator = ResolutionCalculatorPanel(self)
        self.DataOperation = DataOperationUtilityPanel(self)
        self.FileConverter = FileConverterWidget(self)

    def loadAllPerspectives(self):
        # Close any existing perspectives to prevent multiple open instances
        self.closeAllPerspectives()
        # Load all perspectives
        loaded_dict = {}
        for name, perspective in Perspectives.PERSPECTIVES.items():
            try:
                loaded_perspective = perspective(parent=self)
                loaded_dict[name] = loaded_perspective
            except Exception as e:
                logger.warning(f"Unable to load {name} perspective.\n{e}")
        self.loadedPerspectives = loaded_dict

    def closeAllPerspectives(self):
        # Close all perspectives if they are open
        if isinstance(self.loadedPerspectives, dict):
            for name, perspective in self.loadedPerspectives.items():
                try:
                    perspective.setClosable(True)
                    if self.subwindow in self._workspace.workspace.subWindowList():
                        self._workspace.workspace.removeSubWindow(self.subwindow)
                    perspective.close()
                except Exception as e:
                    logger.warning(f"Unable to close {name} perspective\n{e}")
        self.loadedPerspectives = {}
        self._current_perspective = None

    def addCategories(self):
        """
        Make sure categories.json exists and if not compile it and install in ~/.sasview
        """
        try:
            from sas.sascalc.fit.models import ModelManager
            from sas.qtgui.Utilities.CategoryInstaller import CategoryInstaller
            model_list = ModelManager().cat_model_list()
            CategoryInstaller.check_install(model_list=model_list)
        except Exception:
            import traceback
            logger.error("%s: could not load SasView models")
            logger.error(traceback.format_exc())

    def updatePlotItems(self, graphs):
        """
        Wrapper for adding/removing actions in the windows menu
        """
        plot, delete = graphs
        if not plot.data:
            return
        if delete:
            self.removePlotItemsInWindowsMenu(plot)
        else:
            self.addPlotItemsInWindowsMenu(plot)


    def addPlotItemsInWindowsMenu(self, plot):
        """
        Dynamically update the QMenu content and assign signals
        """
        if not plot:
            return
        name = plot[1].name
        for action in self._workspace.menuWindow.actions():
            if action.text() == name:
                # action with this name already exists
                return

        # create action for this plot
        action = self._workspace.menuWindow.addAction(name)
        # connect action to slot
        action.triggered.connect(lambda chk, item=name: self.plotSelectedSlot(name))
        # add action to windows menu
        self._workspace.menuWindow.addAction(action)

    def plotSelectedSlot(self, plot_name):
        """
        Set focus on the selected plot
        """
        # loop over all visible plots and find the requested plot
        for plot in PlotHelper.currentPlots():
            # take last plot
            if PlotHelper.plotById(plot).data[-1].name == plot_name:
                # set focus on the plot
                # Note: none of the StackOverflow recommended solutions work here!
                # neither raise_(), nor showNormal() nor setWindowState(Qt.WindowActive)
                PlotHelper.plotById(plot).showNormal()
                PlotHelper.plotById(plot).setFocus()
                return
        pass

    def removePlotItemsInWindowsMenu(self, plot):
        """
        Dynamically update the QMenu content and disconnect signals
        """
        if not plot: # watch out for quick plots
            return
        name = plot.data[-1].name
        # loop over actions
        for action in self._workspace.menuWindow.actions():
            if action.text() == name:
                # disconnect action to slot
                action.triggered.disconnect()
                self._workspace.menuWindow.removeAction(action)
                return
        pass

    def updateLogContextMenus(self, visible=False):
        """
        Modify the View/Data Explorer menu item text on widget visibility
        """
        if visible:
            self._workspace.actionHide_LogExplorer.setText("Hide Log Explorer")
        else:
            self._workspace.actionHide_LogExplorer.setText("Show Log Explorer")

    def updateContextMenus(self, visible=False):
        """
        Modify the View/Data Explorer menu item text on widget visibility
        """
        if visible:
            self._workspace.actionHide_DataExplorer.setText("Hide Data Explorer")
        else:
            self._workspace.actionHide_DataExplorer.setText("Show Data Explorer")

    def statusBarSetup(self):
        """
        Define the status bar.
        | <message label> .... | Progress Bar |

        Progress bar invisible until explicitly shown
        """
        self.progress = QProgressBar()
        self._workspace.statusbar.setSizeGripEnabled(False)

        self.statusLabel = QLabel()
        self.statusLabel.setText("Welcome to SasView")
        self._workspace.statusbar.addPermanentWidget(self.statusLabel, 1)
        self._workspace.statusbar.addPermanentWidget(self.progress, stretch=0)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setVisible(False)

    def fileWasRead(self, data):
        """
        Callback for fileDataReceivedSignal
        """
        pass

    def showHelp(self, url):
        """
        Open a local url in the default browser
        """
        GuiUtils.showHelp(url)

    def workspace(self):
        """
        Accessor for the main window workspace
        """
        return self._workspace.workspace

    def perspectiveChanged(self, perspective_name):
        """
        Respond to change of the perspective signal
        """
        # Remove the previous perspective from the window
        self.clearPerspectiveMenubarOptions(self._current_perspective)
        if self._current_perspective:
            # Remove perspective and store in Perspective dictionary
            self.loadedPerspectives[
                self._current_perspective.name] = self._current_perspective
            self._workspace.workspace.removeSubWindow(self._current_perspective)
            self._workspace.workspace.removeSubWindow(self.subwindow)
        # Get new perspective
        self._current_perspective = self.loadedPerspectives[str(perspective_name)]

        self.setupPerspectiveMenubarOptions(self._current_perspective)

        self.subwindow = self._workspace.workspace.addSubWindow(
            self._current_perspective)

        # Resize to the workspace height
        workspace_height = self._workspace.workspace.sizeHint().height()
        perspective_size = self._current_perspective.sizeHint()
        perspective_width = perspective_size.width()
        self._current_perspective.resize(perspective_width, workspace_height-10)

        self._current_perspective.show()

    def updatePerspective(self, data):
        """
        Update perspective with data sent.
        """
        assert isinstance(data, list)
        if self._current_perspective is not None:
            self._current_perspective.setData(list(data.values()))
        else:
            msg = "No perspective is currently active."
            logging.info(msg)

    def communicator(self):
        """ Accessor for the communicator """
        return self.communicate

    def perspective(self):
        """ Accessor for the perspective """
        return self._current_perspective

    def updateProgressBar(self, value):
        """
        Update progress bar with the required value (0-100)
        """
        assert -1 <= value <= 100
        if value == -1:
            self.progress.setVisible(False)
            return
        if not self.progress.isVisible():
            self.progress.setTextVisible(True)
            self.progress.setVisible(True)

        self.progress.setValue(value)

    def updateStatusBar(self, text):
        """
        Set the status bar text
        """
        self.statusLabel.setText(text)

    def appendLog(self, msg):
        """Appends a message to the list widget in the Log Explorer. Use this
        instead of listWidget.insertPlainText() to facilitate auto-scrolling"""
        self.listWidget.append(msg.strip())

    def createGuiData(self, item, p_file=None):
        """
        Access the Data1D -> plottable Data1D conversion
        """
        return self._data_manager.create_gui_data(item, p_file)

    def setData(self, data):
        """
        Sends data to current perspective
        """
        if self._current_perspective is not None:
            self._current_perspective.setData(list(data.values()))
        else:
            msg = "Guiframe does not have a current perspective"
            logging.info(msg)

    def findItemFromFilename(self, filename):
        """
        Queries the data explorer for the index corresponding to the filename within
        """
        return self.filesWidget.itemFromFilename(filename)

    def quitApplication(self):
        """
        Close the reactor and exit nicely.
        """
        # Display confirmation messagebox
        quit_msg = "Are you sure you want to exit the application?"
        reply = QMessageBox.question(
            self._parent,
            'Information',
            quit_msg,
            QMessageBox.Yes,
            QMessageBox.No)

        # Exit if yes
        if reply == QMessageBox.Yes:

            # save the paths etc.
            self.saveCustomConfig()
            reactor.callFromThread(reactor.stop)
            return True

        return False

    def checkUpdate(self):
        """
        Check with the deployment server whether a new version
        of the application is available.
        A thread is started for the connecting with the server. The thread calls
        a call-back method when the current version number has been obtained.
        """
        version_info = {"version": "0.0.0"}
        c = ConnectionProxy(LocalConfig.__update_URL__, LocalConfig.UPDATE_TIMEOUT)
        response = c.connect()
        if response is None:
            return
        try:
            content = response.read().strip()
            logging.info("Connected to www.sasview.org. Latest version: %s"
                            % (content))
            version_info = json.loads(content)
            self.processVersion(version_info)
        except ValueError as ex:
            logging.info("Failed to connect to www.sasview.org:", ex)

    def log_installed_packages(self):
        """
        Log version number of locally installed python packages
        """
        PackageGatherer().log_installed_modules()

    def log_imported_packages(self):
        """
        Log version number of python packages imported in this instance of SasView.
        """
        PackageGatherer().log_imported_packages()

    def processVersion(self, version_info):
        """
        Call-back method for the process of checking for updates.
        This methods is called by a VersionThread object once the current
        version number has been obtained. If the check is being done in the
        background, the user will not be notified unless there's an update.

        :param version: version string
        """
        try:
            version = version_info["version"]
            if version == "0.0.0":
                msg = "Could not connect to the application server."
                msg += " Please try again later."
                self.communicate.statusBarUpdateSignal.emit(msg)

            elif version.__gt__(LocalConfig.__version__):
                msg = "Version %s is available! " % str(version)
                if "download_url" in version_info:
                    webbrowser.open(version_info["download_url"])
                else:
                    webbrowser.open(LocalConfig.__download_page__)
                self.communicate.statusBarUpdateSignal.emit(msg)
            else:
                msg = "You have the latest version"
                msg += " of %s" % str(LocalConfig.__appname__)
                self.communicate.statusBarUpdateSignal.emit(msg)
        except:
            msg = "guiframe: could not get latest application"
            msg += " version number\n  %s" % sys.exc_info()[1]
            logging.error(msg)
            msg = "Could not connect to the application server."
            msg += " Please try again later."
            self.communicate.statusBarUpdateSignal.emit(msg)

    def actionWelcome(self):
        """ Show the Welcome panel """
        self.welcomePanel = WelcomePanel()
        self._workspace.workspace.addSubWindow(self.welcomePanel)
        self.welcomePanel.show()

    def showWelcomeMessage(self):
        """ Show the Welcome panel, when required """
        # Assure the welcome screen is requested
        show_welcome_widget = True
        custom_config = get_custom_config()
        if hasattr(custom_config, "WELCOME_PANEL_SHOW"):
            if isinstance(custom_config.WELCOME_PANEL_SHOW, bool):
                show_welcome_widget = custom_config.WELCOME_PANEL_SHOW
            else:
                logging.warning("WELCOME_PANEL_SHOW has invalid value in custom_config.py")
        if show_welcome_widget:
            self.actionWelcome()

    def addCallbacks(self):
        """
        Method defining all signal connections for the gui manager
        """
        self.communicate = GuiUtils.Communicate()
        self.communicate.fileDataReceivedSignal.connect(self.fileWasRead)
        self.communicate.statusBarUpdateSignal.connect(self.updateStatusBar)
        self.communicate.updatePerspectiveWithDataSignal.connect(self.updatePerspective)
        self.communicate.progressBarUpdateSignal.connect(self.updateProgressBar)
        self.communicate.perspectiveChangedSignal.connect(self.perspectiveChanged)
        self.communicate.updateTheoryFromPerspectiveSignal.connect(self.updateTheoryFromPerspective)
        self.communicate.deleteIntermediateTheoryPlotsSignal.connect(self.deleteIntermediateTheoryPlotsByModelID)
        self.communicate.plotRequestedSignal.connect(self.showPlot)
        self.communicate.plotFromNameSignal.connect(self.showPlotFromName)
        self.communicate.updateModelFromDataOperationPanelSignal.connect(self.updateModelFromDataOperationPanel)
        self.communicate.activeGraphsSignal.connect(self.updatePlotItems)


    def addTriggers(self):
        """
        Trigger definitions for all menu/toolbar actions.
        """
        # disable not yet fully implemented actions
        self._workspace.actionUndo.setVisible(False)
        self._workspace.actionRedo.setVisible(False)
        self._workspace.actionReset.setVisible(False)
        self._workspace.actionStartup_Settings.setVisible(False)
        #self._workspace.actionImage_Viewer.setVisible(False)
        self._workspace.actionCombine_Batch_Fit.setVisible(False)
        # orientation viewer set to invisible SASVIEW-1132
        self._workspace.actionOrientation_Viewer.setVisible(False)

        # File
        self._workspace.actionLoadData.triggered.connect(self.actionLoadData)
        self._workspace.actionLoad_Data_Folder.triggered.connect(self.actionLoad_Data_Folder)
        self._workspace.actionOpen_Project.triggered.connect(self.actionOpen_Project)
        self._workspace.actionOpen_Analysis.triggered.connect(self.actionOpen_Analysis)
        self._workspace.actionSave.triggered.connect(self.actionSave_Project)
        self._workspace.actionSave_Analysis.triggered.connect(self.actionSave_Analysis)
        self._workspace.actionQuit.triggered.connect(self.actionQuit)
        # Edit
        self._workspace.actionUndo.triggered.connect(self.actionUndo)
        self._workspace.actionRedo.triggered.connect(self.actionRedo)
        self._workspace.actionCopy.triggered.connect(self.actionCopy)
        self._workspace.actionPaste.triggered.connect(self.actionPaste)
        self._workspace.actionReport.triggered.connect(self.actionReport)
        self._workspace.actionReset.triggered.connect(self.actionReset)
        self._workspace.actionExcel.triggered.connect(self.actionExcel)
        self._workspace.actionLatex.triggered.connect(self.actionLatex)
        self._workspace.actionSaveParamsAs.triggered.connect(self.actionSaveParamsAs)

        # View
        self._workspace.actionShow_Grid_Window.triggered.connect(self.actionShow_Grid_Window)
        self._workspace.actionHide_Toolbar.triggered.connect(self.actionHide_Toolbar)
        self._workspace.actionStartup_Settings.triggered.connect(self.actionStartup_Settings)
        self._workspace.actionCategory_Manager.triggered.connect(self.actionCategory_Manager)
        self._workspace.actionHide_DataExplorer.triggered.connect(self.actionHide_DataExplorer)
        self._workspace.actionHide_LogExplorer.triggered.connect(self.actionHide_LogExplorer)
        # Tools
        self._workspace.actionData_Operation.triggered.connect(self.actionData_Operation)
        self._workspace.actionSLD_Calculator.triggered.connect(self.actionSLD_Calculator)
        self._workspace.actionDensity_Volume_Calculator.triggered.connect(self.actionDensity_Volume_Calculator)
        self._workspace.actionKeissig_Calculator.triggered.connect(self.actionKiessig_Calculator)
        #self._workspace.actionKIESSING_Calculator.triggered.connect(self.actionKIESSING_Calculator)
        self._workspace.actionSlit_Size_Calculator.triggered.connect(self.actionSlit_Size_Calculator)
        self._workspace.actionSAS_Resolution_Estimator.triggered.connect(self.actionSAS_Resolution_Estimator)
        self._workspace.actionGeneric_Scattering_Calculator.triggered.connect(self.actionGeneric_Scattering_Calculator)
        self._workspace.actionPython_Shell_Editor.triggered.connect(self.actionPython_Shell_Editor)
        self._workspace.actionImage_Viewer.triggered.connect(self.actionImage_Viewer)
        self._workspace.actionFile_Converter.triggered.connect(self.actionFile_Converter)
        self._workspace.actionOrientation_Viewer.triggered.connect(self.actionOrientation_Viewer)
        self._workspace.actionFreeze_Theory.triggered.connect(self.actionFreeze_Theory)
        # Fitting
        self._workspace.actionNew_Fit_Page.triggered.connect(self.actionNew_Fit_Page)
        self._workspace.actionConstrained_Fit.triggered.connect(self.actionConstrained_Fit)
        self._workspace.actionCombine_Batch_Fit.triggered.connect(self.actionCombine_Batch_Fit)
        self._workspace.actionFit_Options.triggered.connect(self.actionFit_Options)
        self._workspace.actionGPU_Options.triggered.connect(self.actionGPU_Options)
        self._workspace.actionFit_Results.triggered.connect(self.actionFit_Results)
        self._workspace.actionAdd_Custom_Model.triggered.connect(self.actionAdd_Custom_Model)
        self._workspace.actionEdit_Custom_Model.triggered.connect(self.actionEdit_Custom_Model)
        self._workspace.actionManage_Custom_Models.triggered.connect(self.actionManage_Custom_Models)
        self._workspace.actionAddMult_Models.triggered.connect(self.actionAddMult_Models)
        self._workspace.actionEditMask.triggered.connect(self.actionEditMask)

        # Window
        self._workspace.actionCascade.triggered.connect(self.actionCascade)
        self._workspace.actionTile.triggered.connect(self.actionTile)
        self._workspace.actionArrange_Icons.triggered.connect(self.actionArrange_Icons)
        self._workspace.actionNext.triggered.connect(self.actionNext)
        self._workspace.actionPrevious.triggered.connect(self.actionPrevious)
        self._workspace.actionMinimizePlots.triggered.connect(self.actionMinimizePlots)
        self._workspace.actionClosePlots.triggered.connect(self.actionClosePlots)
        # Analysis
        self._workspace.actionFitting.triggered.connect(self.actionFitting)
        self._workspace.actionInversion.triggered.connect(self.actionInversion)
        self._workspace.actionInvariant.triggered.connect(self.actionInvariant)
        self._workspace.actionCorfunc.triggered.connect(self.actionCorfunc)
        # Help
        self._workspace.actionDocumentation.triggered.connect(self.actionDocumentation)
        self._workspace.actionTutorial.triggered.connect(self.actionTutorial)
        self._workspace.actionModel_Marketplace.triggered.connect(self.actionMarketplace)
        self._workspace.actionAcknowledge.triggered.connect(self.actionAcknowledge)
        self._workspace.actionAbout.triggered.connect(self.actionAbout)
        self._workspace.actionWelcomeWidget.triggered.connect(self.actionWelcome)
        self._workspace.actionCheck_for_update.triggered.connect(self.actionCheck_for_update)
        
        self.communicate.sendDataToGridSignal.connect(self.showBatchOutput)
        self.communicate.resultPlotUpdateSignal.connect(self.showFitResults)

    #============ FILE =================
    def actionLoadData(self):
        """
        Menu File/Load Data File(s)
        """
        self.filesWidget.loadFile()

    def actionLoad_Data_Folder(self):
        """
        Menu File/Load Data Folder
        """
        self.filesWidget.loadFolder()

    def actionOpen_Project(self):
        """
        Menu Open Project
        """
        self.filesWidget.loadProject()

    def actionOpen_Analysis(self):
        """
        """
        self.filesWidget.loadAnalysis()
        pass

    def actionSave_Project(self):
        """
        Menu Save Project
        """
        filename = self.filesWidget.saveProject()
        if not filename:
            return

        # datasets
        all_data = self.filesWidget.getSerializedData()
        final_data = {}
        for id, data in all_data.items():
            final_data[id] = {'fit_data': data}

        # Save from all serializable perspectives
        # Analysis should return {data-id: serialized-state}
        for name, per in self.loadedPerspectives.items():
            if hasattr(per, 'isSerializable') and per.isSerializable():
                analysis = per.serializeAll()
                for key, value in analysis.items():
                    if key in final_data:
                        final_data[key].update(value)
                    elif 'cs_tab' in key:
                        final_data[key] = value

        final_data['is_batch'] = analysis.get('is_batch', 'False')
        final_data['batch_grid'] = self.grid_window.data_dict
        final_data['visible_perspective'] = self._current_perspective.name

        with open(filename, 'w') as outfile:
            GuiUtils.saveData(outfile, final_data)

    def actionSave_Analysis(self):
        """
        Menu File/Save Analysis
        """
        per = self.perspective()
        if not hasattr(per, 'isSerializable') or not per.isSerializable:
            return
        # get fit page serialization
        all_data = self.filesWidget.getSerializedData()
        analysis = {}
        state = per.serializeCurrentPage()
        for id, params in state.items():
            if id in all_data:
                analysis[id] = {'fit_data': all_data[id]}
                analysis[id].update(params)
        if len(analysis) > 0:
            tab_id = 1 if not hasattr(per,
                                      'currentTab') else per.currentTab.tab_id
            self.filesWidget.saveAnalysis(analysis, tab_id, per.ext)
        else:
            logger.warning('No analysis was available to be saved.')

    def actionQuit(self):
        """
        Close the reactor, exit the application.
        """
        self.quitApplication()

    #============ EDIT =================
    def actionUndo(self):
        """
        """
        print("actionUndo TRIGGERED")
        pass

    def actionRedo(self):
        """
        """
        print("actionRedo TRIGGERED")
        pass

    def actionCopy(self):
        """
        Send a signal to the fitting perspective so parameters
        can be saved to the clipboard
        """
        self.communicate.copyFitParamsSignal.emit("")
        #self._workspace.actionPaste.setEnabled(True)
        pass

    def actionPaste(self):
        """
        Send a signal to the fitting perspective so parameters
        from the clipboard can be used to modify the fit state
        """
        self.communicate.pasteFitParamsSignal.emit()

    def actionReport(self):
        """
        Show the Fit Report dialog.
        """
        report_list = None
        if getattr(self._current_perspective, "currentTab"):
            try:
                report_list = self._current_perspective.currentTab.getReport()
            except Exception as ex:
                logging.error("Report generation failed with: " + str(ex))

        if report_list is not None:
            self.report_dialog = ReportDialog(parent=self, report_list=report_list)
            self.report_dialog.show()

    def actionReset(self):
        """
        """
        logging.warning(" *** actionOpen_Analysis logging *******")
        print("actionReset print TRIGGERED")
        sys.stderr.write("STDERR - TRIGGERED")
        pass

    def actionExcel(self):
        """
        Send a signal to the fitting perspective so parameters
        can be saved to the clipboard
        """
        self.communicate.copyExcelFitParamsSignal.emit("Excel")

    def actionLatex(self):
        """
        Send a signal to the fitting perspective so parameters
        can be saved to the clipboard
        """
        self.communicate.copyLatexFitParamsSignal.emit("Latex")

    def actionSaveParamsAs(self):
        """
        Menu Save Params
        """
        self.communicate.SaveFitParamsSignal.emit("Save")

    #============ VIEW =================
    def actionShow_Grid_Window(self):
        """
        """
        self.showBatchOutput(None)

    def showBatchOutput(self, output_data):
        """
        Display/redisplay the batch fit viewer
        """
        self.grid_subwindow.setVisible(True)
        self.grid_subwindow.raise_()
        if output_data:
            self.grid_window.addFitResults(output_data)

    def actionHide_Toolbar(self):
        """
        Toggle toolbar vsibility
        """
        if self._workspace.toolBar.isVisible():
            self._workspace.actionHide_Toolbar.setText("Show Toolbar")
            self._workspace.toolBar.setVisible(False)
        else:
            self._workspace.actionHide_Toolbar.setText("Hide Toolbar")
            self._workspace.toolBar.setVisible(True)
        pass

    def actionHide_DataExplorer(self):
        """
        Toggle Data Explorer vsibility
        """
        if self.dockedFilesWidget.isVisible():
            self.dockedFilesWidget.setVisible(False)
        else:
            self.dockedFilesWidget.setVisible(True)
        pass

    def actionHide_LogExplorer(self):
        """
        Toggle Data Explorer vsibility
        """
        if self.logDockWidget.isVisible():
            self.logDockWidget.setVisible(False)
        else:
            self.logDockWidget.setVisible(True)
        pass

    def actionStartup_Settings(self):
        """
        """
        print("actionStartup_Settings TRIGGERED")
        pass

    def actionCategory_Manager(self):
        """
        """
        self.categoryManagerWidget.show()

    #============ TOOLS =================
    def actionData_Operation(self):
        """
        """
        data, theory = self.filesWidget.getAllFlatData()
        self.communicate.sendDataToPanelSignal.emit(dict(data, **theory))

        self.DataOperation.show()

    def actionSLD_Calculator(self):
        """
        """
        self.SLDCalculator.show()

    def actionDensity_Volume_Calculator(self):
        """
        """
        self.DVCalculator.show()

    def actionKiessig_Calculator(self):
        """
        """
        self.KIESSIGCalculator.show()

    def actionSlit_Size_Calculator(self):
        """
        """
        self.SlitSizeCalculator.show()

    def actionSAS_Resolution_Estimator(self):
        """
        """
        try:
            self.ResolutionCalculator.show()
        except Exception as ex:
            logging.error(str(ex))
            return

    def actionGeneric_Scattering_Calculator(self):
        """
        """
        try:
            self.GENSASCalculator.show()
        except Exception as ex:
            logging.error(str(ex))
            return

    def actionPython_Shell_Editor(self):
        """
        Display the Jupyter console as a docked widget.
        """
        # Import moved here for startup performance reasons
        from sas.qtgui.Utilities.IPythonWidget import IPythonWidget
        terminal = IPythonWidget()

        # Add the console window as another docked widget
        self.ipDockWidget = QDockWidget("IPython", self._workspace)
        self.ipDockWidget.setObjectName("IPythonDockWidget")
        self.ipDockWidget.setWidget(terminal)
        self._workspace.addDockWidget(Qt.RightDockWidgetArea, self.ipDockWidget)

    def actionFreeze_Theory(self):
        """
        Convert a child index with data into a separate top level dataset
        """
        self.filesWidget.freezeCheckedData()

    def actionOrientation_Viewer(self):
        """
        Make sasmodels orientation & jitter viewer available
        """
        from sasmodels.jitter import run as orientation_run
        try:
            orientation_run()
        except Exception as ex:
            logging.error(str(ex))

    def actionImage_Viewer(self):
        """
        """
        try:
            self.image_viewer = ImageViewer(self)
            if sys.platform == "darwin":
                self.image_viewer.menubar.setNativeMenuBar(False)
            self.image_viewer.show()
        except Exception as ex:
            logging.error(str(ex))
            return

    def actionFile_Converter(self):
        """
        Shows the File Converter widget.
        """
        try:
            self.FileConverter.show()
        except Exception as ex:
            logging.error(str(ex))
            return

    #============ FITTING =================
    def actionNew_Fit_Page(self):
        """
        Add a new, empty Fit page in the fitting perspective.
        """
        # Make sure the perspective is correct
        per = self.perspective()
        if not isinstance(per, FittingWindow):
            return
        per.addFit(None)

    def actionConstrained_Fit(self):
        """
        Add a new Constrained and Simult. Fit page in the fitting perspective.
        """
        per = self.perspective()
        if not isinstance(per, FittingWindow):
            return
        per.addConstraintTab()

    def actionCombine_Batch_Fit(self):
        """
        """
        print("actionCombine_Batch_Fit TRIGGERED")
        pass

    def actionFit_Options(self):
        """
        """
        if getattr(self._current_perspective, "fit_options_widget"):
            self._current_perspective.fit_options_widget.show()
        pass

    def actionGPU_Options(self):
        """
        Load the OpenCL selection dialog if the fitting perspective is active
        """
        if hasattr(self._current_perspective, "gpu_options_widget"):
            self._current_perspective.gpu_options_widget.show()
        pass

    def actionFit_Results(self):
        """
        """
        self.showFitResults(None)

    def showFitResults(self, output_data):
        """
        Show bumps convergence plots
        """
        self.results_frame.setVisible(True)
        if output_data:
            self.results_panel.onPlotResults(output_data, optimizer=self.perspective().optimizer)

    def actionAdd_Custom_Model(self):
        """
        """
        self.model_editor = TabbedModelEditor(self)
        self.model_editor.show()

    def actionEdit_Custom_Model(self):
        """
        """
        self.model_editor = TabbedModelEditor(self, edit_only=True)
        self.model_editor.show()

    def actionManage_Custom_Models(self):
        """
        """
        self.model_manager = PluginManager(self)
        self.model_manager.show()

    def actionAddMult_Models(self):
        """
        """
        # Add Simple Add/Multiply Editor
        self.add_mult_editor = AddMultEditor(self)
        self.add_mult_editor.show()

    def actionEditMask(self):

        self.communicate.extMaskEditorSignal.emit()

    #============ ANALYSIS =================
    def actionFitting(self):
        """
        Change to the Fitting perspective
        """
        self.perspectiveChanged("Fitting")
        # Notify other widgets
        self.filesWidget.onAnalysisUpdate("Fitting")

    def actionInversion(self):
        """
        Change to the Inversion perspective
        """
        self.perspectiveChanged("Inversion")
        self.filesWidget.onAnalysisUpdate("Inversion")

    def actionInvariant(self):
        """
        Change to the Invariant perspective
        """
        self.perspectiveChanged("Invariant")
        self.filesWidget.onAnalysisUpdate("Invariant")

    def actionCorfunc(self):
        """
        Change to the Corfunc perspective
        """
        self.perspectiveChanged("Corfunc")
        self.filesWidget.onAnalysisUpdate("Corfunc")

    #============ WINDOW =================
    def actionCascade(self):
        """
        Arranges all the child windows in a cascade pattern.
        """
        self._workspace.workspace.cascadeSubWindows()

    def actionTile(self):
        """
        Tile workspace windows
        """
        self._workspace.workspace.tileSubWindows()

    def actionArrange_Icons(self):
        """
        Arranges all iconified windows at the bottom of the workspace
        """
        self._workspace.workspace.arrangeIcons()

    def actionNext(self):
        """
        Gives the input focus to the next window in the list of child windows.
        """
        self._workspace.workspace.activateNextSubWindow()

    def actionPrevious(self):
        """
        Gives the input focus to the previous window in the list of child windows.
        """
        self._workspace.workspace.activatePreviousSubWindow()

    def actionClosePlots(self):
        """
        Closes all Plotters and Plotter2Ds.
        """
        self.filesWidget.closeAllPlots()
        pass

    def actionMinimizePlots(self):
        """
        Minimizes all Plotters and Plotter2Ds.
        """
        self.filesWidget.minimizeAllPlots()
        pass

    #============ HELP =================
    def actionDocumentation(self):
        """
        Display the documentation

        TODO: use QNetworkAccessManager to assure _helpLocation is valid
        """
        helpfile = "/index.html"
        self.showHelp(helpfile)

    def actionTutorial(self):
        """
        Open the page with tutorial PDF links
        """
        helpfile = "/user/tutorial.html"
        self.showHelp(helpfile)

    def actionAcknowledge(self):
        """
        Open the Acknowledgements widget
        """
        self.ackWidget.show()

    def actionMarketplace(self):
        """
        Open the marketplace link in default browser
        """
        url = LocalConfig.MARKETPLACE_URL
        webbrowser.open_new(url)

    def actionAbout(self):
        """
        Open the About box
        """
        # Update the about box with current version and stuff

        # TODO: proper sizing
        self.aboutWidget.show()

    def actionCheck_for_update(self):
        """
        Menu Help/Check for Update
        """
        self.checkUpdate()

    def updateTheoryFromPerspective(self, index):
        """
        Catch the theory update signal from a perspective
        Send the request to the DataExplorer for updating the theory model.
        """
        item = self.filesWidget.updateTheoryFromPerspective(index)
        # Now notify the perspective that the item was/wasn't replaced
        per = self.perspective()
        if not isinstance(per, FittingWindow):
            # currently only fitting supports generation of theories.
            return
        per.currentTab.setTheoryItem(item)

    def deleteIntermediateTheoryPlotsByModelID(self, model_id):
        """
        Catch the signal to delete items in the Theory item model which correspond to a model ID.
        Send the request to the DataExplorer for updating the theory model.
        """
        self.filesWidget.deleteIntermediateTheoryPlotsByModelID(model_id)

    def updateModelFromDataOperationPanel(self, new_item, new_datalist_item):
        """
        :param new_item: item to be added to list of loaded files
        :param new_datalist_item:
        """
        if not isinstance(new_item, QStandardItem) or \
                not isinstance(new_datalist_item, dict):
            msg = "Wrong data type returned from calculations."
            raise AttributeError(msg)

        self.filesWidget.model.appendRow(new_item)
        self._data_manager.add_data(new_datalist_item)

    def showPlotFromName(self, name):
        """
        Pass the show plot request to the data explorer
        """
        if hasattr(self, "filesWidget"):
            self.filesWidget.displayDataByName(name=name, is_data=True)

    def showPlot(self, plot, id):
        """
        Pass the show plot request to the data explorer
        """
        if hasattr(self, "filesWidget"):
            self.filesWidget.displayData(plot, id)
            # update windows menu
            self.addPlotItemsInWindowsMenu(plot)

    def uncheckAllMenuItems(self, menuObject):
        """
        Uncheck all options in a given menu
        """
        menuObjects = menuObject.actions()

        for menuItem in menuObjects:
            menuItem.setChecked(False)

    def checkAnalysisOption(self, analysisMenuOption):
        """
        Unchecks all the items in the analysis menu and checks the item passed
        """
        self.uncheckAllMenuItems(self._workspace.menuAnalysis)
        analysisMenuOption.setChecked(True)

    def clearPerspectiveMenubarOptions(self, perspective):
        """
        When closing a perspective, clears the menu bar
        """
        for menuItem in self._workspace.menuAnalysis.actions():
            menuItem.setChecked(False)

        if isinstance(self._current_perspective, Perspectives.PERSPECTIVES["Fitting"]):
            self._workspace.menubar.removeAction(self._workspace.menuFitting.menuAction())

    def setupPerspectiveMenubarOptions(self, perspective):
        """
        When setting a perspective, sets up the menu bar
        """
        self._workspace.actionReport.setEnabled(False)
        self._workspace.actionOpen_Analysis.setEnabled(False)
        self._workspace.actionSave_Analysis.setEnabled(False)
        if hasattr(perspective, 'isSerializable') and perspective.isSerializable():
            self._workspace.actionOpen_Analysis.setEnabled(True)
            self._workspace.actionSave_Analysis.setEnabled(True)

        if isinstance(perspective, Perspectives.PERSPECTIVES["Fitting"]):
            self.checkAnalysisOption(self._workspace.actionFitting)
            # Put the fitting menu back in
            # This is a bit involved but it is needed to preserve the menu ordering
            self._workspace.menubar.removeAction(self._workspace.menuWindow.menuAction())
            self._workspace.menubar.removeAction(self._workspace.menuHelp.menuAction())
            self._workspace.menubar.addAction(self._workspace.menuFitting.menuAction())
            self._workspace.menubar.addAction(self._workspace.menuWindow.menuAction())
            self._workspace.menubar.addAction(self._workspace.menuHelp.menuAction())
            self._workspace.actionReport.setEnabled(True)

        elif isinstance(perspective, Perspectives.PERSPECTIVES["Invariant"]):
            self.checkAnalysisOption(self._workspace.actionInvariant)
        elif isinstance(perspective, Perspectives.PERSPECTIVES["Inversion"]):
            self.checkAnalysisOption(self._workspace.actionInversion)
        elif isinstance(perspective, Perspectives.PERSPECTIVES["Corfunc"]):
            self.checkAnalysisOption(self._workspace.actionCorfunc)

    def saveCustomConfig(self):
        """
        Save the config file based on current session values
        """
        # Load the current file
        config_content = GuiUtils.custom_config

        changed = self.customSavePaths(config_content)
        changed = changed or self.customSaveOpenCL(config_content)

        if changed:
            self.writeCustomConfig(config_content)

    def customSavePaths(self, config_content):
        """
        Update the config module with current session paths
        Returns True if update was done, False, otherwise
        """
        changed = False
        # Find load path
        open_path = GuiUtils.DEFAULT_OPEN_FOLDER
        defined_path = self.filesWidget.default_load_location
        if open_path != defined_path:
            # Replace the load path
            config_content.DEFAULT_OPEN_FOLDER = defined_path
            changed = True
        return changed

    def customSaveOpenCL(self, config_content):
        """
        Update the config module with current session OpenCL choice
        Returns True if update was done, False, otherwise
        """
        changed = False
        # Find load path
        file_value = GuiUtils.SAS_OPENCL
        session_value = os.environ.get("SAS_OPENCL", "")
        if file_value != session_value:
            # Replace the load path
            config_content.SAS_OPENCL = session_value
            changed = True
        return changed

    def writeCustomConfig(self, config):
        """
        Write custom configuration
        """
        from sas import make_custom_config_path
        path = make_custom_config_path()
        # Just clobber the file - we already have its content read in
        with open(path, 'w') as out_f:
            out_f.write("#Application appearance custom configuration\n")
            for key, item in config.__dict__.items():
                if key[:2] == "__":
                    continue
                if isinstance(item, str):
                    item = '"' + item + '"'
                out_f.write("%s = %s\n" % (key, str(item)))
        pass # debugger anchor
