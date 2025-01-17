##########################################################################################
"""My code to implement paths such that the modules can be found by Python and the program can run"""
import sys
import os

additional_path = ['C:/Users/Qerne/OneDrive/Documents/VSCode/Projects/Thesis/SasView_dev_version/sasview/src', 
                   'C:/Users/Qerne/OneDrive/Documents/VSCode/Projects/Thesis/SasView_dev_version/sasmodels', 
                   'C:/Users/Qerne/OneDrive/Documents/VSCode/Projects/Thesis/SasView_dev_version/sasdata']

# Add the directory to sys.path
for path in additional_path:
    absolute_path = os.path.abspath(path)
    if absolute_path not in sys.path:
        sys.path.append(absolute_path)

#print("Python is searching for modules in the following directories:")
#for path in sys.path:
#    print(path)
##########################################################################################

# Global
import sys
import re
from types import MethodType
from typing import Union
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QPushButton, QCheckBox, QFrame, QLineEdit

# Local SasView
from sas.qtgui.Utilities.TabbedModelEditor import TabbedModelEditor
from sas.qtgui.Perspectives.perspective import Perspective

from UI.DesignWindowUI import Ui_DesignWindow
from ViewerModel import ViewerModel
from ButtonOptions import ButtonOptions
from Tables.subunitTable import SubunitTable, OptionLayout
from Constraints import Constraints
from PlotAspects.plotAspects import Canvas

from calculations.Shape2SAS import (getTheoreticalScattering, getPointDistribution, getSimulatedScattering, 
                                                                     ModelProfile, ModelSystem, SimulationParameters, 
                                                                     Qsampling, TheoreticalScatteringCalculation, 
                                                                     SimulateScattering)
from PlotAspects.plotAspects import ViewerPlotDesign
from genPlugin import generatePlugin


class DesignWindow(QDialog, Ui_DesignWindow, Perspective):
    """Main window for the Shape2SAS fitting tool"""

    name = "Shape2SAS"
    ext = "data_file"

    @property
    def title(self) -> str:
        """ Window title"""
        return "Shape2SAS"

    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Shape2SAS")
        self.parent = parent

        self._manager = parent

        ############Building GUI##############
        ###create build model tab
        #Add buttons to the modelTabButtonOptions
        self.modelTabButtonOptions = ButtonOptions()
        self.modelTabButtonOptions.help.setToolTip("Go to help page")
        self.modelTabButtonOptions.closePage.setToolTip("Close Shape2SAS")
        self.modelTabButtonOptions.reset.setToolTip("Reset this page to default")
        self.modelTabButtonOptions.horizontalLayout_5.setContentsMargins(0, 0, 10, 10)

        self.line1 = QFrame()
        self.line1.setFrameShape(QFrame.VLine)
        self.modelTabButtonOptions.horizontalLayout_5.insertWidget(1, self.line1)

        self.checkTheoreticalScattering = QCheckBox("Include Scattering")
        self.checkTheoreticalScattering.setToolTip("Include a theoretical scattering profile when plotting the model")
        self.modelTabButtonOptions.horizontalLayout_5.insertWidget(1, self.checkTheoreticalScattering)
        self.plot = QPushButton("Plot")
        self.modelTabButtonOptions.horizontalLayout_5.insertWidget(1, self.plot)
        self.plot.setToolTip("Plot the model")

        self.line2 = QFrame()
        self.line2.setFrameShape(QFrame.VLine)
        self.modelTabButtonOptions.horizontalLayout_5.insertWidget(1, self.line2)

        self.plugin = QPushButton("To plugin model")
        self.plugin.setMinimumSize(110, 24)
        self.plugin.setMaximumSize(110, 24)
        self.plugin.setToolTip("Go to the plugin model page")
        self.modelTabButtonOptions.horizontalLayout_5.insertWidget(1, self.plugin)

        #connect buttons
        self.modelTabButtonOptions.reset.clicked.connect(self.onSubunitTableReset)
        self.modelTabButtonOptions.closePage.clicked.connect(self.onClickingClose)
        self.plot.clicked.connect(self.onClickingPlot)
        self.plugin.clicked.connect(self.showConstraintWindow)

        #create layout for build model tab
        self.viewerModel = ViewerModel()
        self.subunitTable = SubunitTable()

        modelVbox = QVBoxLayout()
        modelHbox = QHBoxLayout()
        
        modelVbox.setContentsMargins(0,0,0,0)
        modelHbox.setContentsMargins(10,0,10,0)
        modelSection = QWidget()
        modelHbox.addWidget(self.subunitTable)
        modelHbox.addWidget(self.viewerModel.Viewmodel_modul)
        modelSection.setLayout(modelHbox)

        modelVbox.addWidget(modelSection)
        modelVbox.addWidget(self.modelTabButtonOptions)
        self.model.setLayout(modelVbox)

        ###Building Virtual SAXS Experiment tab
        #create and set layout for buttons
        self.SAXSTabButtons = ButtonOptions()
        self.SAXSTabButtons.help.setToolTip("Go to help page")
        self.SAXSTabButtons.closePage.setToolTip("Close Shape2SAS")
        self.SAXSTabButtons.reset.setToolTip("Reset this page to default")
        self.SAXSTabButtons.reset.clicked.connect(self.onSAXSExperimentReset)
        self.plotSAXS = QPushButton("Plot SAXS")
        self.plotSAXS.setMinimumSize(110, 24)
        self.plotSAXS.setMaximumSize(110, 24)
        self.plotSAXS.setToolTip("Plot simulated SAXS data")
        self.SAXSTabButtons.horizontalLayout_5.insertWidget(1, self.plotSAXS)
        self.sendSimToSasView = QPushButton("Create SAXS file")
        self.sendSimToSasView.setMinimumSize(110, 24)
        self.sendSimToSasView.setMaximumSize(110, 24)
        self.sendSimToSasView.setToolTip("Send simulated SAXS data to SasView Data Explorer")
        self.SAXSTabButtons.horizontalLayout_5.setContentsMargins(0, 0, 0, 10)
        self.SAXSTabButtons.horizontalLayout_5.insertWidget(1, self.sendSimToSasView)
        self.gridLayout_5.addWidget(self.SAXSTabButtons, 2, 0, 1, 2, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        self.SAXSExperiment.setLayout(self.gridLayout_5)

        #connect buttons
        self.sendSimToSasView.clicked.connect(self.getSimulatedSAXSData)
        self.structureFactor.currentIndexChanged.connect(self.showStructureFactorOptions)
        self.plotSAXS.clicked.connect(self.showSimulatedSAXSData)
        self.sendSimToSasView.clicked.connect(self.sendSimulatedSAXSToDataExplorer)
        self.SAXSTabButtons.closePage.clicked.connect(self.onClickingClose)

        ###Building Virtual SANS Experiment tab
        #TODO: implement in a future project

        ###Building Constraint window
        self.constraint = Constraints()
        self.subunitTable.add.clicked.connect(self.addToVariableTable)
        self.subunitTable.delete.clicked.connect(self.deleteFromVariableTable)
        self.constraint.variableTable.setConstraints.clicked.connect(self.setConstraintsToTextEditor)
        self.constraint.createPlugin.clicked.connect(self.getPluginModel)
        self.constraint.buttonOptions.reset.clicked.connect(self.onConstraintReset)
        self.constraint.buttonOptions.closePage.clicked.connect(self.onClickingClose)

        #create png of each tab
        #self.modelTabButtonOptions.help.clicked.connect(self.export_widget_with_tabs_to_png)


    def showConstraintWindow(self):
        """Get the Constraint window"""

        self.constraint.show()
        QTimer.singleShot(500, self.capture_constraint_window)
    

    def checkedVariables(self):
        """Get checked variables from the variable table
        with inserted restricted rows"""

        columns = self.constraint.variableTable.getCheckedVariables()
        for column in range(len(columns)):
            for row in range(len(self.subunitTable.restrictedRowsPos[column])):
                columns[column].insert(self.subunitTable.restrictedRowsPos[column][row], False)

        return columns


    def getConstraintsToTextEditor(self):
        """Set translation and parameters constraints to the text editor"""
        columns = self.checkedVariables()

        #no subunits inputted
        if not columns:
            return
        
        #no parameters inputted
        if not any(any(column) for column in columns):
            return

        toTextEditor = ['# name, units, default, [min, max], type, description']

        dimPos = [OptionLayout.x, OptionLayout.y, OptionLayout.z]
        #create parameter lists for the text editor to be edited
        for column in range(len(columns)):
            for row in range(len(columns[column])):
                if columns[column][row]:
                    enumMember = list(OptionLayout)[row]

                    if enumMember in dimPos:
                        val = self.getSubunitTableCell(OptionLayout.get_position(OptionLayout.Subunit), column)
                    else:
                        val = enumMember.value

                    #get units, bounds and types from method
                    attr = getattr(OptionLayout, val)
                    method = MethodType(attr, OptionLayout)
                    _, _, units, _, types, bounds = method()

                    #get inputted value from cell
                    inputVal = self.getSubunitTableCell(row, column)
                    inputName = self.getTableName(column, row)

                    #create parameter list
                    parameter = [inputName, units[enumMember], inputVal, bounds[enumMember], 
                                 types[enumMember], f"{inputName} for column {column + 1}"]
        
                    toTextEditor.append(parameter)

        formatted = "[\n " + ",\n ".join(str(pars) for pars in toTextEditor) + "\n]"

        return formatted
    

    def setConstraintsToTextEditor(self):
        """Set constraints to the text editor"""

        constraints = self.getConstraintsToTextEditor()
        if constraints:
            formatted = constraints
            modelName = self.constraint.variableTable.pluginModelName.text()
            self.constraint.setConstraints(formatted, modelName)


    def checkStateOfConstraints(self, fitPar: list[str], modelName: str):
        """Check if the user has written constraints. Otherwise return Default"""

        constraintsStr = self.constraint.constraintTextEditor.txtEditor.toPlainText()

        #Has anything been written to the text editor
        if constraintsStr:
            #TODO: print to GUI output texteditor
            return self.constraint.getConstraints(constraintsStr, fitPar, modelName)
        
        #Did the user only check parameters and click generate plugin
        elif fitPar:
            #Get default constraints
            fitParLists = self.getConstraintsToTextEditor()
            defaultConstraintsStr = self.constraint.getConstraintText(fitParLists, modelName)
            #TODO: print to GUI output texteditor
            return self.constraint.getConstraints(defaultConstraintsStr, fitPar, modelName)
        
        #If not, return empty
        else:
            #all parameters are constant
            #TODO: print to GUI output texteditor
            return "", "", ""

    def addToVariableTable(self):
        """Set up parameters to the variable table"""
        column = self.subunitTable.model.columnCount() - 1 #-1 to account for the added column
        names = self.getTableNames(self.ifEmptyName, column)

        #set variables in variable table
        self.constraint.variableTable.setVariableTableData(names, column)


    def deleteFromVariableTable(self):
        """Delete parameters from the variable table"""
        selected_column = self.subunitTable.selected_val - 1 #SubunitTable column index position
        row_pos = self.constraint.variableTable.getAllTableColumnsPos()

        #if no columns in the subunit table
        if not self.subunitTable.model.columnCount():
            numNames = self.constraint.variableTable.variableModel.rowCount()

        #if selected column is the last column
        elif row_pos[selected_column] == row_pos[-1]:
            numNames = self.constraint.variableTable.variableModel.rowCount() - row_pos[-1]

        else:
            numNames = row_pos[selected_column + 1] - row_pos[selected_column]

        #Delete rows associated with the subunit table column from variable table
        for delete in [row_pos[selected_column] for _ in range(numNames)]:
            self.constraint.variableTable.removeTableData(delete)
        
        #Update column number in table
        columnNum = selected_column + 1 #column number name
        for row in row_pos[selected_column + 1:]: #get all values after selected_column
            row = row - numNames
            self.constraint.variableTable.variableModel.item(row, 1).setText(str(columnNum))
            columnNum += 1


    def showStructureFactorOptions(self):
        """Show options for structure factor"""
        #get chosen structure factor
        index = self.structureFactor.currentIndex()
        #show options for chosen structure factor
        self.stackedWidget.setCurrentIndex(index)


    def getStructureFactorValues(self):
        """Read structure factor options from chosen structure factor"""
        S_vals = []

        #get chosen structure factor
        index = self.structureFactor.currentIndex()
        #find chosen widget containing the chosen structure factor options
        self.stackedWidget.setCurrentIndex(index)
        currentWidget = self.stackedWidget.currentWidget()
        lineEdits = currentWidget.findChildren(QLineEdit)

        #get concentration value for Hardsphere case
        #TODO: concentration is already an input value. Maybe add 
        #a texbox to explain that to the user if stackedWidget chosen?
        if index == 1:
            conc = self.volumeFraction
            S_vals.append(float(conc.text()))


        for val in lineEdits:
            S_vals.append(float(val.text()))


        return S_vals


    def getSubunitTableCell(self, row: int, column: int) -> Union[float, str]:
        """Get model data from a single cell."""

        val = self.subunitTable.model.item(row, column).data(Qt.EditRole)

        return val
    

    @staticmethod
    def ifEmptyValue(value: Union[float, str], values: list[Union[float, str]], *args, **kwargs):
        """condition method. Append if not empty"""
        
        if not value == "":
            values.append(value)


    @staticmethod
    def ifFitPar(value: Union[float, str], values: list[Union[float, str]], *args, **kwargs):
        """condition method. Append FitPar if condition. Otherwise append constant"""

        conditionFitPar = kwargs['conditionFitPar'] #list[list[str]]
        conditionBool = kwargs['conditionBool'] #list[list[bool]]
        row, column = args #int, int
        
        if not value == "":
            if conditionBool[column][row]:
                values.append(conditionFitPar[column][row])
            else:
                values.append(value)
    

    def getSubunitTableRow(self, condition: MethodType, row: int, **kwargs) -> list[Union[float, str]]:
        """Get model data from a single row"""

        values = []
        columns = self.subunitTable.model.columnCount()
        for column in range(columns):
            value = self.getSubunitTableCell(row, column)
            condition(value, values, row, column, **kwargs)

        return values


    def getSubunitTableSets(self, condition: MethodType, rows: list[int], **kwargs) -> list[list[Union[float, str]]]:
        """Get a set of rows per column in subunit table"""

        sets = []
        columns = self.subunitTable.model.columnCount()

        for column in range(columns):
            set = []
            for row in rows:
                value = self.getSubunitTableCell(row, column)
                condition(value, set, row, column, **kwargs)
            sets.append(set)
        return sets


    def getModelData(self, condition: MethodType, **kwargs) -> list[list[Union[float, str]]]:
        """Get all data in the subunit table"""

        #no subunits inputted
        columns = self.subunitTable.model.columnCount()
        if not self.subunitTable.model.item(1, columns - 1):
            return

        subunit = self.getSubunitTableRow(condition, OptionLayout.get_position(OptionLayout.Subunit), **kwargs)
        dimensions = self.getSubunitTableSets(condition, [OptionLayout.get_position(OptionLayout.x), 
                                                        OptionLayout.get_position(OptionLayout.y), 
                                                        OptionLayout.get_position(OptionLayout.z)], **kwargs)

        p_s = self.getSubunitTableRow(condition, OptionLayout.get_position(OptionLayout.ΔSLD), **kwargs)

        com = self.getSubunitTableSets(condition, [OptionLayout.get_position(OptionLayout.COM_x), 
                                                OptionLayout.get_position(OptionLayout.COM_y), 
                                                OptionLayout.get_position(OptionLayout.COM_z)], **kwargs)
        
        rotation_points = self.getSubunitTableSets(condition, [OptionLayout.get_position(OptionLayout.RP_x),
                                                OptionLayout.get_position(OptionLayout.RP_y),
                                                OptionLayout.get_position(OptionLayout.RP_z)], **kwargs)
        
        rotation = self.getSubunitTableSets(condition, [OptionLayout.get_position(OptionLayout.α),
                                            OptionLayout.get_position(OptionLayout.β),
                                            OptionLayout.get_position(OptionLayout.γ)], **kwargs)
        
        #set bool to checkbox
        if self.subunitTable.overlap.isChecked():
            exclude_overlap = True
        else:
            exclude_overlap = False

        return [subunit, dimensions, p_s, com, rotation_points, rotation, exclude_overlap]


    def getModelProfile(self, condition: MethodType, **kwargs) -> ModelProfile:
        """Get model profile"""

        subunit, dimensions, p_s, com, rotation_points, rotation, exclude_overlap = self.getModelData(condition, **kwargs)

        return ModelProfile(subunits=subunit, p_s=p_s, dimensions=dimensions, com=com, 
                           rotation_points=rotation_points, rotation=rotation, exclude_overlap=exclude_overlap)
    

    def getViewFeatures(self) -> ViewerPlotDesign:
        """Get values affecting the illustrative aspect of Viewer"""
        colour = []

        columns = self.subunitTable.model.columnCount()
        for column in range(columns):
            colour.append(self.getSubunitTableCell(OptionLayout.get_position(OptionLayout.Colour), column))
        
        return ViewerPlotDesign(colour=colour)
    

    def onClickingPlot(self):
        """Get 3D plot of the designed model in the Build model tab. 
        If checked, plot theoretical scattering from the designed model."""

        columns = self.subunitTable.model.columnCount()
        if not self.subunitTable.model.item(1, columns - 1):
            return

        modelProfile = self.getModelProfile(self.ifEmptyValue)
        
        plotDesign = self.getViewFeatures()
        modelDistribution = getPointDistribution(modelProfile, 3000)
        self.viewerModel.setPlot(modelDistribution, plotDesign)

        #on being checked, plot theoretical scattering
        if self.checkTheoreticalScattering.isChecked():
            scattering = TheoreticalScatteringCalculation(System=ModelSystem(PointDistribution=modelDistribution, 
                                                                        Stype="None", par=[], 
                                                                        polydispersity=0.0, conc=0.02, 
                                                                        sigma_r=0.0), 
                                                                        Calculation=SimulationParameters())
            theoreticalScattering = getTheoreticalScattering(scattering)
            self.viewerModel.setScatteringPlot(theoreticalScattering)

        else:
            self.viewerModel.setClearScatteringPlot()


    def onSubunitTableReset(self):
        """Reset subunit table to default"""
        self.subunitTable.onClearSubunitTable()
        self.constraint.variableTable.onClearTable()
        self.viewerModel.setClearScatteringPlot()
        self.viewerModel.setClearModelPlot()
        self.checkTheoreticalScattering.setChecked(False)
        self.subunitTable.overlap.setChecked(True)
        self.subunitTable.subunit.setCurrentIndex(0)



    def onSAXSExperimentReset(self):
        """Reset Virtual SAXS Experiment tab to default"""
        self.interfaceRoughness.setText("0.0")
        self.polydispersity.setText("0.0")
        self.volumeFraction.setText("0.02")
        self.exposureTime.setText("500")
        self.qMin.setText("0.001")
        self.qMax.setText("0.5")
        self.Nq.setText("400")
        self.Npr.setText("100")
        self.NSimPoints.setText("3000")
        self.modelName.setText("Model_1")
        self.structureFactor.setCurrentIndex(0)
        self.hardSphereRadius.setText("50.0")
        self.aggregateFrac.setText("0.1")
        self.EffctiveRadius.setText("50.0")
        self.particlePerAggregate.setText("80")

        # Clear the plot in the Virtual SAXS Experiment tab
        self.canvas.figure.clf()
        self.canvas.draw()

    def onConstraintReset(self):
        """Reset Constraint window to default"""

        self.constraint.clearConstraints()
        self.constraint.variableTable.setUncheckToAllCheckBoxes()
        self.constraint.variableTable.prPoints.setText("100")
        self.constraint.variableTable.Npoints.setText("3000")
        self.constraint.variableTable.pluginModelName.setText("Model_1")

    def onClickingClose(self):
        """Close Shape2SAS GUI"""

        self.close()
        self.constraint.onClosingConstraints()
    

    def onClickingHelp(self):
        """Opening the help window"""
        print("Help")
        #TODO: creat HTML help file to be displayed


    @staticmethod
    def ifNoCondition(name: str, names: list[str], **kwargs):
        """condition method. Append"""
        
        names.append(name)


    @staticmethod
    def ifEmptyName(name: str, names: list[str], **kwargs):
        """condition method. Append if not empty"""
        
        if name:
            names.append(name)


    def getTableName(self, column: int, row: int) -> str:
        """Get the parameter name of a cell in the subunit table"""

        name = re.match(r'^[^\s=]+', self.subunitTable.model.item(row, column).text())
        if name:
            return name.group()


    def getTableNames(self, condition: MethodType, column: int, **kwargs) -> list[str]:
        """Get the parameter names of a column in the subunit table"""
            
        names = []
        layout = list(OptionLayout)
        layout.remove(OptionLayout.Colour)

        for name in layout:
            layoutName = self.getTableName(column, OptionLayout.get_position(name))
            condition(layoutName, names, **kwargs)

        return names


    def getAllTableNames(self, condition: MethodType, **kwargs) -> list[list[str]]:
        """Get all parameter names in the subunit table"""
        names = []
        columns = self.subunitTable.model.columnCount()

        for column in range(columns):
            names.append(self.getTableNames(condition, column, **kwargs))

        return names
    

    def getFitParameters(self) -> list[str]:
        """return names of the chosen fit parameters"""

        return self.constraint.variableTable.getCheckedTableNamesVariables()


    def getPluginModel(self):
        """Generating a plugin model and sends it to
        the Plugin Models folder in SasView"""

        #no subunits inputted
        columns = self.subunitTable.model.columnCount() #TODO: maybe give a warning to output texteditor
        if not self.subunitTable.model.item(1, columns - 1):
            return

        Npoints = int(self.constraint.variableTable.Npoints.text())
        prPoints = int(self.constraint.variableTable.prPoints.text())
        modelName = self.constraint.variableTable.pluginModelName.text()
        parNames = self.getAllTableNames(self.ifNoCondition)
        checkedVars = self.checkedVariables()

        #get chosen fit parameters
        fitPar = self.getFitParameters()

        #TODO: Check if constraint button have been clicked. 
        # otherwise return default constraints to checked parameters
        constrainParameters = self.checkStateOfConstraints(fitPar, modelName)

        #conditional subunit table parameters
        modelProfile = self.getModelProfile(self.ifFitPar, conditionBool=checkedVars, conditionFitPar=parNames)

        model_str, full_path = generatePlugin(modelProfile, constrainParameters, fitPar, Npoints, prPoints, modelName)

        #Write file to plugin model folder
        print(full_path)
        TabbedModelEditor.writeFile(full_path, model_str)


    def onCheckingInput(self, input: str, default: str) -> str:
        """Check if the input not None. Otherwise, return default value"""

        if not input.text():
            return default
        else:
            return input.text()

    def plotSimulatedSAXSData(self):
        """Plotting simulated SAXS data in the Virtual SAXS Experiment tab"""
        self.scatteringProf


    def getSimulatedSAXSData(self):
        """Generating simulated data and sends it to
        the Data Explorer in SasView"""

        columns = self.subunitTable.model.columnCount()
        if not self.subunitTable.model.item(1, columns - 1):
            return

        #Calculations
        qmin = float(self.onCheckingInput(self.qMin, "0.001"))
        qmax = float(self.onCheckingInput(self.qMax, "0.5"))

        Nq = int(self.onCheckingInput(self.Nq, "400"))
        Npr = int(self.onCheckingInput(self.Npr, "100"))
        N = int(self.onCheckingInput(self.NSimPoints, "3000"))

        name = self.onCheckingInput(self.modelName, "Model_1")

        par = self.getStructureFactorValues()

        #SAXS parameters
        Stype = self.structureFactor.currentText()

        sigma_r = float(self.onCheckingInput(self.interfaceRoughness, "0.0"))
        polydispersity = float(self.onCheckingInput(self.polydispersity, "0.0"))
        conc = float(self.onCheckingInput(self.volumeFraction, "0.02"))
        exposure = float(self.onCheckingInput(self.exposureTime, "500"))

        #Generate simulated data
        q = Qsampling.onQsampling(qmin, qmax, Nq)
        Sim_par = SimulationParameters(q=q, prpoints=Npr, Npoints=N)
        Profile = self.getModelProfile(self.ifEmptyValue)

        Distr = getPointDistribution(Profile, N)

        Theo_calc = TheoreticalScatteringCalculation(System=ModelSystem(PointDistribution=Distr, 
                                                                        Stype=Stype, par=par, 
                                                                        polydispersity=polydispersity, 
                                                                        conc=conc, 
                                                                        sigma_r=sigma_r), 
                                                                        Calculation=Sim_par)
        Theo_I = getTheoreticalScattering(Theo_calc)
        Sim_calc = SimulateScattering(q=Theo_I.q, I0=Theo_I.I0, I=Theo_I.I, exposure=exposure)
        Sim_SAXS = getSimulatedScattering(Sim_calc)


        return Sim_SAXS
    

    def showSimulatedSAXSData(self):
        """Plotting simulated SAXS data in the Virtual SAXS Experiment tab"""

        #check if subunit table is empty
        columns = self.subunitTable.model.columnCount()
        if not self.subunitTable.model.item(1, columns - 1):
            return

        #Clear layout for last plot
        if self.scatteringScene.count():
            widget = self.scatteringScene.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        self.canvas = Canvas(parent=self.scatteringProf)
        self.canvas.fig.subplots_adjust(left=0.20, right=0.95, top=0.85, bottom=0.15) #TODO: find a better way to set this

        self.setFig = self.canvas.fig.add_subplot(111)

        simSAXS = self.getSimulatedSAXSData()
        modelName = self.modelName.text()

        self.setFig.set_title(f"Simulated SAXS for {modelName}")
        self.setFig.set_xlabel("q")
        self.setFig.set_ylabel("I(q)")
        self.setFig.errorbar(simSAXS.q, simSAXS.I_sim, yerr=simSAXS.I_err, color="black", label="I(q)")

        self.setFig.set_xscale('log')
        self.setFig.set_yscale('log')

        self.setFig.legend()
        self.setFig.grid(True)

        self.scatteringScene.addWidget(self.canvas)
        self.scatteringProf.setLayout(self.scatteringScene)

    def sendSimulatedSAXSToDataExplorer(self):
        """Send simulated data to the Data Explorer in SasView"""
        print("Send simulated data to Data Explorer")
        #Send data to SasView Data Explorer


    ####CAPTURE IMAGE OF TABS
    def capture_widget_with_tabs(self):
        # Introduce a small delay before starting the capture process
        QTimer.singleShot(500, lambda: self._capture_tab(0))

    def _capture_tab(self, index):
        if index >= self.tabWidget.count():
            return

        screen = QApplication.primaryScreen()
        self.tabWidget.setCurrentIndex(index)
        QApplication.processEvents()  # Ensure the tab is fully rendered
        QTimer.singleShot(100, lambda: self._capture_and_save(screen, index))

    def _capture_and_save(self, screen, index):
        # Bring the window to the front
        self.raise_()
        self.activateWindow()
        QApplication.processEvents()  # Ensure the window is fully rendered
        # Capture the entire window, including the title bar
        pixmap = screen.grabWindow(self.winId())
        pixmap.save(f"widget_with_tab_{index+1}.png")
        print(f"Saved widget with tab {index+1} as widget_with_tab_{index+1}.png")
        # Capture the next tab
        self._capture_tab(index + 1)

    def export_widget_with_tabs_to_png(self):
        self.capture_widget_with_tabs()

    
    def capture_constraint_window(self):
        screen = QApplication.primaryScreen()
        # Bring the constraint window to the front
        self.constraint.raise_()
        self.constraint.activateWindow()
        QApplication.processEvents()  # Ensure the window is fully rendered
        # Capture the entire constraint window, including the title bar
        pixmap = screen.grabWindow(self.constraint.winId())
        pixmap.save("constraint_window.png")
        print("Saved constraint window as constraint_window.png")


if __name__ == "__main__":
    app = QApplication([])
    widget = DesignWindow()
    widget.show()
    sys.exit(app.exec())
