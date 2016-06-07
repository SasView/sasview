import sys

from PyQt4 import QtCore
from PyQt4 import QtGui

# General SAS imports
import LocalConfig
from GuiUtils import *

# Perspectives
from Perspectives.Invariant.InvariantPerspective import InvariantWindow
from DataExplorer import DataExplorerWindow
from WelcomePanel import WelcomePanel

class GuiManager(object):
    """
    Main SasView window functionality
    """
    def __init__(self, mainWindow=None, reactor=None, parent=None):
        """
        
        """
        self._workspace = mainWindow
        self._parent = parent

        # Reactor passed from above
        self.setReactor(reactor)

        # Add signal callbacks
        self.addCallbacks()

        # Create the data manager
        #self._data_manager = DataManager()

        # Create action triggers
        self.addTriggers()

        # Populate menus with dynamic data
        # 
        # Analysis/Perspectives - potentially
        # Window/current windows
        #

        # Widgets
        #
        # Add FileDialog widget as docked
        self.filesWidget = DataExplorerWindow(parent, self)
        #flags = (QtCore.Qt.Window | QtCore.Qt.WindowTitleHint | QtCore.Qt.CustomizeWindowHint)

        self.dockedFilesWidget = QtGui.QDockWidget("File explorer", self._workspace)
        self.dockedFilesWidget.setWidget(self.filesWidget)
        self._workspace.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dockedFilesWidget)
        # Disable the close button (?)
        # Show the Welcome panel
        self.welcomePanel = WelcomePanel()
        self._workspace.workspace.addWindow(self.welcomePanel)

        #==========================================================
        # TEMP PROTOTYPE
        # Add InvariantWindow to the workspace.
        self.invariantWidget = InvariantWindow(self)
        self._workspace.workspace.addWindow(self.invariantWidget)

        # Default perspective
        self._current_perspective = self.invariantWidget
     

    def fileRead(self, data):
        """
        """
        #print("FILE %s "%data)
        pass
    
    def updatePerspective(self, data):
        """
        """
        assert isinstance(data, list)
        if self._current_perspective is not None:
            self._current_perspective.setData(data.values())
        else:
            msg = "No perspective is currently active."
            logging.info(msg)
        
            
    def communicator(self):
        """
        """
        return self.communicate

    def reactor(self):
        """
        """
        return self._reactor

    def setReactor(self, reactor):
        """
        """
        self._reactor = reactor

    def perspective(self):
        """
        """
        return self._current_perspective

    def updateStatusBar(self, text):
        """
        """
        self._workspace.statusbar.showMessage(text)

    #def createGuiData(self, item, p_file):
    #    """
    #    """
    #    return self._data_manager.create_gui_data(item, p_file)

    def addData(self, data_list):
        """
        receive a dictionary of data from loader
        store them its data manager if possible
        send to data the current active perspective if the data panel
        is not active.
        :param data_list: dictionary of data's ID and value Data
        """
        #Store data into manager
        #self._data_manager.add_data(data_list)

        # set data in the data panel
        #if self._data_panel is not None:
        #    data_state = self._data_manager.get_data_state(data_list.keys())
        #    self._data_panel.load_data_list(data_state)

        #if the data panel is shown wait for the user to press a button
        #to send data to the current perspective. if the panel is not
        #show  automatically send the data to the current perspective
        #style = self.__gui_style & GUIFRAME.MANAGER_ON
        #if style == GUIFRAME.MANAGER_ON:
        #    #wait for button press from the data panel to set_data
        #    if self._data_panel is not None:
        #        self._data_panel.frame.Show(True)
        #else:
            #automatically send that to the current perspective
        #self.setData(data_id=data_list.keys())
        pass

    def setData(self, data):
        """
        Sends data to current perspective
        """
        if self._current_perspective is not None:
            self._current_perspective.setData(data.values())
        else:
            msg = "Guiframe does not have a current perspective"
            logging.info(msg)

    def addCallbacks(self):
        """
        """
        self.communicate = Communicate()
        self.communicate.fileDataReceivedSignal.connect(self.fileRead)
        self.communicate.statusBarUpdateSignal.connect(self.updateStatusBar)
        self.communicate.updatePerspectiveWithDataSignal.connect(self.updatePerspective)

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
        self._workspace.actionFit_Results.triggered.connect(self.actionFit_Results)
        self._workspace.actionChain_Fitting.triggered.connect(self.actionChain_Fitting)
        self._workspace.actionEdit_Custom_Model.triggered.connect(self.actionEdit_Custom_Model)
        # Window
        self._workspace.actionCascade.triggered.connect(self.actionCascade)
        self._workspace.actionTile_Horizontally.triggered.connect(self.actionTile_Horizontally)
        self._workspace.actionTile_Vertically.triggered.connect(self.actionTile_Vertically)
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
        """
        print("actionLoadData TRIGGERED")
        pass

    def actionLoad_Data_Folder(self):
        """
        """
        print("actionLoad_Data_Folder TRIGGERED")
        pass

    def actionOpen_Project(self):
        """
        """
        print("actionOpen_Project TRIGGERED")
        pass

    def actionOpen_Analysis(self):
        """
        """
        print("actionOpen_Analysis TRIGGERED")
        pass

    def actionSave(self):
        """
        """
        print("actionSave TRIGGERED")
        pass

    def actionSave_Analysis(self):
        """
        """
        print("actionSave_Analysis TRIGGERED")
        pass

    def actionQuit(self):
        """
        """
        print("actionQuit TRIGGERED")
        pass

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
        print("actionReset TRIGGERED")
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
        """
        print("actionHide_Toolbar TRIGGERED")
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
        print("actionData_Operation TRIGGERED")
        pass

    def actionSLD_Calculator(self):
        """
        """
        print("actionSLD_Calculator TRIGGERED")
        pass

    def actionDensity_Volume_Calculator(self):
        """
        """
        print("actionDensity_Volume_Calculator TRIGGERED")
        pass

    def actionSlit_Size_Calculator(self):
        """
        """
        print("actionSlit_Size_Calculator TRIGGERED")
        pass

    def actionSAS_Resolution_Estimator(self):
        """
        """
        print("actionSAS_Resolution_Estimator TRIGGERED")
        pass

    def actionGeneric_Scattering_Calculator(self):
        """
        """
        print("actionGeneric_Scattering_Calculator TRIGGERED")
        pass

    def actionPython_Shell_Editor(self):
        """
        """
        print("actionPython_Shell_Editor TRIGGERED")
        pass

    def actionImage_Viewer(self):
        """
        """
        print("actionImage_Viewer TRIGGERED")
        pass

    #============ FITTING =================
    def actionNew_Fit_Page(self):
        """
        """
        print("actionNew_Fit_Page TRIGGERED")
        pass

    def actionConstrained_Fit(self):
        """
        """
        print("actionConstrained_Fit TRIGGERED")
        pass

    def actionCombine_Batch_Fit(self):
        """
        """
        print("actionCombine_Batch_Fit TRIGGERED")
        pass

    def actionFit_Options(self):
        """
        """
        print("actionFit_Options TRIGGERED")
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

    def actionEdit_Custom_Model(self):
        """
        """
        print("actionEdit_Custom_Model TRIGGERED")
        pass

    #============ ANALYSIS =================
    def actionFitting(self):
        """
        """
        print("actionFitting TRIGGERED")
        pass

    def actionInversion(self):
        """
        """
        print("actionInversion TRIGGERED")
        pass

    def actionInvariant(self):
        """
        """
        print("actionInvariant TRIGGERED")
        pass

    #============ WINDOW =================
    def actionCascade(self):
        """
        """
        print("actionCascade TRIGGERED")
        pass

    def actionTile_Horizontally(self):
        """
        """
        print("actionTile_Horizontally TRIGGERED")
        pass

    def actionTile_Vertically(self):
        """
        """
        print("actionTile_Vertically TRIGGERED")
        pass

    def actionArrange_Icons(self):
        """
        """
        print("actionArrange_Icons TRIGGERED")
        pass

    def actionNext(self):
        """
        """
        print("actionNext TRIGGERED")
        pass

    def actionPrevious(self):
        """
        """
        print("actionPrevious TRIGGERED")
        pass

    #============ HELP =================
    def actionDocumentation(self):
        """
        """
        print("actionDocumentation TRIGGERED")
        pass

    def actionTutorial(self):
        """
        """
        print("actionTutorial TRIGGERED")
        pass

    def actionAcknowledge(self):
        """
        """
        print("actionAcknowledge TRIGGERED")
        pass

    def actionAbout(self):
        """
        """
        print("actionAbout TRIGGERED")
        pass

    def actionCheck_for_update(self):
        """
        """
        print("actionCheck_for_update TRIGGERED")
        pass

