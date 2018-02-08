import sys
import os
import subprocess
import logging
import json
import webbrowser

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QLocale, QUrl

from twisted.internet import reactor
# General SAS imports
from sas.qtgui.Utilities.ConnectionProxy import ConnectionProxy
from sas.qtgui.Utilities.SasviewLogger import XStream

import sas.qtgui.Utilities.LocalConfig as LocalConfig
import sas.qtgui.Utilities.GuiUtils as GuiUtils

import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary
from sas.qtgui.Utilities.TabbedModelEditor import TabbedModelEditor
from sas.qtgui.Utilities.PluginManager import PluginManager
from sas.qtgui.MainWindow.UI.AcknowledgementsUI import Ui_Acknowledgements
from sas.qtgui.MainWindow.AboutBox import AboutBox
from sas.qtgui.MainWindow.WelcomePanel import WelcomePanel

from sas.qtgui.MainWindow.DataManager import DataManager

from sas.qtgui.Calculators.SldPanel import SldPanel
from sas.qtgui.Calculators.DensityPanel import DensityPanel
from sas.qtgui.Calculators.KiessigPanel import KiessigPanel
from sas.qtgui.Calculators.SlitSizeCalculator import SlitSizeCalculator
from sas.qtgui.Calculators.GenericScatteringCalculator import GenericScatteringCalculator
from sas.qtgui.Calculators.ResolutionCalculatorPanel import ResolutionCalculatorPanel
from sas.qtgui.Calculators.DataOperationUtilityPanel import DataOperationUtilityPanel

# Perspectives
import sas.qtgui.Perspectives as Perspectives
from sas.qtgui.Perspectives.Fitting.FittingPerspective import FittingWindow
from sas.qtgui.MainWindow.DataExplorer import DataExplorerWindow, DEFAULT_PERSPECTIVE

class Acknowledgements(QDialog, Ui_Acknowledgements):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

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

        # Add signal callbacks
        self.addCallbacks()

        # Create the data manager
        # TODO: pull out all required methods from DataManager and reimplement
        self._data_manager = DataManager()

        # Create action triggers
        self.addTriggers()

        # Currently displayed perspective
        self._current_perspective = None

        # Populate the main window with stuff
        self.addWidgets()

        # Fork off logging messages to the Log Window
        XStream.stdout().messageWritten.connect(self.listWidget.insertPlainText)
        XStream.stderr().messageWritten.connect(self.listWidget.insertPlainText)

        # Log the start of the session
        logging.info(" --- SasView session started ---")
        # Log the python version
        logging.info("Python: %s" % sys.version)

        # Set up the status bar
        self.statusBarSetup()

        # Needs URL like path, so no path.join() here
        self._helpLocation = GuiUtils.HELP_DIRECTORY_LOCATION + "/index.html"

        # Current tutorial location
        self._tutorialLocation = os.path.abspath(os.path.join(GuiUtils.HELP_DIRECTORY_LOCATION,
                                              "_downloads",
                                              "Tutorial.pdf"))

    def addWidgets(self):
        """
        Populate the main window with widgets

        TODO: overwrite close() on Log and DR widgets so they can be hidden/shown
        on request
        """
        # Add FileDialog widget as docked
        self.filesWidget = DataExplorerWindow(self._parent, self, manager=self._data_manager)
        ObjectLibrary.addObject('DataExplorer', self.filesWidget)

        self.dockedFilesWidget = QDockWidget("Data Explorer", self._workspace)
        self.dockedFilesWidget.setFloating(False)
        self.dockedFilesWidget.setWidget(self.filesWidget)

        # Disable maximize/minimize and close buttons
        self.dockedFilesWidget.setFeatures(QDockWidget.NoDockWidgetFeatures)

        #self._workspace.workspace.addDockWidget(Qt.LeftDockWidgetArea, self.dockedFilesWidget)
        self._workspace.addDockWidget(Qt.LeftDockWidgetArea, self.dockedFilesWidget)

        # Add the console window as another docked widget
        self.logDockWidget = QDockWidget("Log Explorer", self._workspace)
        self.logDockWidget.setObjectName("LogDockWidget")

        self.listWidget = QTextBrowser()
        self.logDockWidget.setWidget(self.listWidget)
        self._workspace.addDockWidget(Qt.BottomDockWidgetArea, self.logDockWidget)

        # Add other, minor widgets
        self.ackWidget = Acknowledgements()
        self.aboutWidget = AboutBox()
        self.welcomePanel = WelcomePanel()

        # Add calculators - floating for usability
        self.SLDCalculator = SldPanel(self)
        self.DVCalculator = DensityPanel(self)
        self.KIESSIGCalculator = KiessigPanel(self)
        self.SlitSizeCalculator = SlitSizeCalculator(self)
        self.GENSASCalculator = GenericScatteringCalculator(self)
        self.ResolutionCalculator = ResolutionCalculatorPanel(self)
        self.DataOperation = DataOperationUtilityPanel(self)

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
        location = GuiUtils.HELP_DIRECTORY_LOCATION + url
        try:
            webbrowser.open('file://' + os.path.realpath(location))
        except webbrowser.Error as ex:
            logging.warning("Cannot display help. %s" % ex)

    def workspace(self):
        """
        Accessor for the main window workspace
        """
        return self._workspace.workspace

    def perspectiveChanged(self, perspective_name):
        """
        Respond to change of the perspective signal
        """

        # Save users from themselves...
        #if isinstance(self._current_perspective, Perspectives.PERSPECTIVES[str(perspective_name)]):
        self.setupPerspectiveMenubarOptions(self._current_perspective)
        #    return

        # Close the previous perspective
        self.clearPerspectiveMenubarOptions(self._current_perspective)
        if self._current_perspective:
            self._current_perspective.setClosable()
            #self._workspace.workspace.removeSubWindow(self._current_perspective)
            self._current_perspective.close()
            self._workspace.workspace.removeSubWindow(self._current_perspective)
        # Default perspective
        self._current_perspective = Perspectives.PERSPECTIVES[str(perspective_name)](parent=self)

        subwindow = self._workspace.workspace.addSubWindow(self._current_perspective)

        # Resize to the workspace height
        workspace_height = self._workspace.workspace.sizeHint().height()
        perspective_size = self._current_perspective.sizeHint()
        perspective_width = perspective_size.width()
        self._current_perspective.resize(perspective_width, workspace_height-10)
        # Resize the mdi area to match the widget within
        subwindow.resize(subwindow.minimumSizeHint())

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

    def showWelcomeMessage(self):
        """ Show the Welcome panel """
        self._workspace.workspace.addSubWindow(self.welcomePanel)
        self.welcomePanel.show()

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
        self.communicate.plotRequestedSignal.connect(self.showPlot)
        self.communicate.plotFromFilenameSignal.connect(self.showPlotFromFilename)
        self.communicate.updateModelFromDataOperationPanelSignal.connect(self.updateModelFromDataOperationPanel)

    def addTriggers(self):
        """
        Trigger definitions for all menu/toolbar actions.
        """
        # File
        self._workspace.actionLoadData.triggered.connect(self.actionLoadData)
        self._workspace.actionLoad_Data_Folder.triggered.connect(self.actionLoad_Data_Folder)
        self._workspace.actionOpen_Project.triggered.connect(self.actionOpen_Project)
        self._workspace.actionOpen_Analysis.triggered.connect(self.actionOpen_Analysis)
        self._workspace.actionSave.triggered.connect(self.actionSave)
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

        # View
        self._workspace.actionShow_Grid_Window.triggered.connect(self.actionShow_Grid_Window)
        self._workspace.actionHide_Toolbar.triggered.connect(self.actionHide_Toolbar)
        self._workspace.actionStartup_Settings.triggered.connect(self.actionStartup_Settings)
        self._workspace.actionCategry_Manager.triggered.connect(self.actionCategry_Manager)
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
        # Fitting
        self._workspace.actionNew_Fit_Page.triggered.connect(self.actionNew_Fit_Page)
        self._workspace.actionConstrained_Fit.triggered.connect(self.actionConstrained_Fit)
        self._workspace.actionCombine_Batch_Fit.triggered.connect(self.actionCombine_Batch_Fit)
        self._workspace.actionFit_Options.triggered.connect(self.actionFit_Options)
        self._workspace.actionGPU_Options.triggered.connect(self.actionGPU_Options)
        self._workspace.actionFit_Results.triggered.connect(self.actionFit_Results)
        self._workspace.actionChain_Fitting.triggered.connect(self.actionChain_Fitting)
        self._workspace.actionAdd_Custom_Model.triggered.connect(self.actionAdd_Custom_Model)
        self._workspace.actionEdit_Custom_Model.triggered.connect(self.actionEdit_Custom_Model)
        self._workspace.actionManage_Custom_Models.triggered.connect(self.actionManage_Custom_Models)
        # Window
        self._workspace.actionCascade.triggered.connect(self.actionCascade)
        self._workspace.actionTile.triggered.connect(self.actionTile)
        self._workspace.actionArrange_Icons.triggered.connect(self.actionArrange_Icons)
        self._workspace.actionNext.triggered.connect(self.actionNext)
        self._workspace.actionPrevious.triggered.connect(self.actionPrevious)
        # Analysis
        self._workspace.actionFitting.triggered.connect(self.actionFitting)
        self._workspace.actionInversion.triggered.connect(self.actionInversion)
        self._workspace.actionInvariant.triggered.connect(self.actionInvariant)
        # Help
        self._workspace.actionDocumentation.triggered.connect(self.actionDocumentation)
        self._workspace.actionTutorial.triggered.connect(self.actionTutorial)
        self._workspace.actionAcknowledge.triggered.connect(self.actionAcknowledge)
        self._workspace.actionAbout.triggered.connect(self.actionAbout)
        self._workspace.actionCheck_for_update.triggered.connect(self.actionCheck_for_update)

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
        print("actionOpen_Analysis TRIGGERED")
        pass

    def actionSave(self):
        """
        Menu Save Project
        """
        self.filesWidget.saveProject()

    def actionSave_Analysis(self):
        """
        """
        print("actionSave_Analysis TRIGGERED")

        pass

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
        """
        print("actionCopy TRIGGERED")
        pass

    def actionPaste(self):
        """
        """
        print("actionPaste TRIGGERED")
        pass

    def actionReport(self):
        """
        """
        print("actionReport TRIGGERED")
        pass

    def actionReset(self):
        """
        """
        logging.warning(" *** actionOpen_Analysis logging *******")
        print("actionReset print TRIGGERED")
        sys.stderr.write("STDERR - TRIGGERED")
        pass

    def actionExcel(self):
        """
        """
        print("actionExcel TRIGGERED")
        pass

    def actionLatex(self):
        """
        """
        print("actionLatex TRIGGERED")
        pass

    #============ VIEW =================
    def actionShow_Grid_Window(self):
        """
        """
        print("actionShow_Grid_Window TRIGGERED")
        pass

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

    def actionStartup_Settings(self):
        """
        """
        print("actionStartup_Settings TRIGGERED")
        pass

    def actionCategry_Manager(self):
        """
        """
        print("actionCategry_Manager TRIGGERED")
        pass

    #============ TOOLS =================
    def actionData_Operation(self):
        """
        """
        self.communicate.sendDataToPanelSignal.emit(self._data_manager.get_all_data())

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
        #self.DVCalculator.show()
        self.KIESSIGCalculator.show()

    def actionSlit_Size_Calculator(self):
        """
        """
        self.SlitSizeCalculator.show()

    def actionSAS_Resolution_Estimator(self):
        """
        """
        self.ResolutionCalculator.show()

    def actionGeneric_Scattering_Calculator(self):
        """
        """
        self.GENSASCalculator.show()

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

    def actionImage_Viewer(self):
        """
        """
        print("actionImage_Viewer TRIGGERED")
        pass

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
        print("actionFit_Results TRIGGERED")
        pass

    def actionChain_Fitting(self):
        """
        """
        print("actionChain_Fitting TRIGGERED")
        pass

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

    #============ ANALYSIS =================
    def actionFitting(self):
        """
        Change to the Fitting perspective
        """
        self.perspectiveChanged("Fitting")

    def actionInversion(self):
        """
        Change to the Inversion perspective
        """
        # For now we'll just update the analysis menu status but when the inversion is implemented delete from here
        self.checkAnalysisOption(self._workspace.actionInversion)
        # to here and uncomment the following line
        self.perspectiveChanged("Inversion")

    def actionInvariant(self):
        """
        Change to the Invariant perspective
        """
        self.perspectiveChanged("Invariant")

    #============ WINDOW =================
    def actionCascade(self):
        """
        Arranges all the child windows in a cascade pattern.
        """
        self._workspace.workspace.cascade()

    def actionTile(self):
        """
        Tile workspace windows
        """
        self._workspace.workspace.tile()

    def actionArrange_Icons(self):
        """
        Arranges all iconified windows at the bottom of the workspace
        """
        self._workspace.workspace.arrangeIcons()

    def actionNext(self):
        """
        Gives the input focus to the next window in the list of child windows.
        """
        self._workspace.workspace.activateNextWindow()

    def actionPrevious(self):
        """
        Gives the input focus to the previous window in the list of child windows.
        """
        self._workspace.workspace.activatePreviousWindow()

    #============ HELP =================
    def actionDocumentation(self):
        """
        Display the documentation

        TODO: use QNetworkAccessManager to assure _helpLocation is valid
        """
        self.showHelp(self._helpLocation)

    def actionTutorial(self):
        """
        Open the tutorial PDF file with default PDF renderer
        """
        # Not terribly safe here. Shell injection warning.
        # isfile() helps but this probably needs a better solution.
        if os.path.isfile(self._tutorialLocation):
            result = subprocess.Popen([self._tutorialLocation], shell=True)

    def actionAcknowledge(self):
        """
        Open the Acknowledgements widget
        """
        self.ackWidget.show()

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
        self.filesWidget.updateTheoryFromPerspective(index)

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

    def showPlotFromFilename(self, filename):
        """
        Pass the show plot request to the data explorer
        """
        if hasattr(self, "filesWidget"):
            self.filesWidget.displayFile(filename=filename, is_data=True)

    def showPlot(self, plot):
        """
        Pass the show plot request to the data explorer
        """
        if hasattr(self, "filesWidget"):
            self.filesWidget.displayData(plot)

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
        if isinstance(perspective, Perspectives.PERSPECTIVES["Fitting"]):
            self.checkAnalysisOption(self._workspace.actionFitting)
            # Put the fitting menu back in
            # This is a bit involved but it is needed to preserve the menu ordering
            self._workspace.menubar.removeAction(self._workspace.menuWindow.menuAction())
            self._workspace.menubar.removeAction(self._workspace.menuHelp.menuAction())
            self._workspace.menubar.addAction(self._workspace.menuFitting.menuAction())
            self._workspace.menubar.addAction(self._workspace.menuWindow.menuAction())
            self._workspace.menubar.addAction(self._workspace.menuHelp.menuAction())
        elif isinstance(perspective, Perspectives.PERSPECTIVES["Invariant"]):
            self.checkAnalysisOption(self._workspace.actionInvariant)
        # elif isinstance(perspective, Perspectives.PERSPECTIVES["Inversion"]):
        #     self.checkAnalysisOption(self._workspace.actionInversion)