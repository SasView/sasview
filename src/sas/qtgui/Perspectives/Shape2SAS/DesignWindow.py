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
# This Python file uses the following encoding: utf-8
import sys
import re

from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

from PySide6.QtWidgets import QPushButton, QCheckBox, QFrame

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from UI.DesignWindowUI import Ui_DesignWindow

from sas.qtgui.Perspectives.Shape2SAS.ViewerModel import ViewerModel
from sas.qtgui.Perspectives.Shape2SAS.ButtonOptions import ButtonOptions
from sas.qtgui.Perspectives.Shape2SAS.Tables.subunitTable import SubunitTable, OPTIONLAYOUT

from sas.qtgui.Perspectives.Shape2SAS.calculations.Shape2SAS import (getTheoreticalScattering, getPointDistribution, getSimulatedScattering, 
                                                                     ModelProfile, ModelSystem, SimulationParameters, 
                                                                     ModelPointDistribution, TheoreticalScatteringCalculation, 
                                                                     SimulatedScattering, SimulateScattering)
from sas.qtgui.Perspectives.Shape2SAS.PlotAspects.plotAspects import ViewerPlotDesign
from sas.qtgui.Perspectives.Shape2SAS.genPlugin import generatePlugin

class DesignWindow(QDialog, Ui_DesignWindow):
    """Main window for the Shape2SAS fitting tool"""
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Placeholder title")
        self.parent = parent

        ############Building GUI##############
        #Building Build model tab
        modelVbox = QVBoxLayout()
        modelHbox = QHBoxLayout()
        
        modelVbox.setContentsMargins(0,0,0,0)
        modelHbox.setContentsMargins(10,0,10,0)
        self.viwerModel = ViewerModel()

        self.subunitTable = SubunitTable()
        self.modelButtonOptions = ButtonOptions()

        self.line1 = QFrame()
        self.line1.setFrameShape(QFrame.VLine)
        self.modelButtonOptions.horizontalLayout_5.insertWidget(1, self.line1)

        self.checkTheoreticalScattering = QCheckBox("Include Scattering")
        self.modelButtonOptions.horizontalLayout_5.insertWidget(1, self.checkTheoreticalScattering)
        self.plot = QPushButton("Plot")
        self.modelButtonOptions.horizontalLayout_5.insertWidget(1, self.plot)
        self.plot.clicked.connect(self.onClickingPlot)

        self.line2 = QFrame()
        self.line2.setFrameShape(QFrame.VLine)
        self.modelButtonOptions.horizontalLayout_5.insertWidget(1, self.line2)

        self.plugin = QPushButton("Create Plugin")
        self.plugin.setMinimumSize(110, 24)
        self.plugin.setMaximumSize(110, 24)
        self.modelButtonOptions.horizontalLayout_5.insertWidget(1, self.plugin)
        self.plugin.clicked.connect(self.getPluginModel)
        
        modelSection = QWidget()
        modelHbox.addWidget(self.subunitTable)
        modelHbox.addWidget(self.viwerModel.Viewmodel_modul)
        modelSection.setLayout(modelHbox)

        modelVbox.addWidget(modelSection)
        modelVbox.addWidget(self.modelButtonOptions)
        self.model.setLayout(modelVbox)
        
        #Building Calculations tab
        self.calculationButtons = ButtonOptions()
        self.gridLayout_4.addWidget(self.calculationButtons, 0, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        

        #Building Virtual SAXS Experiment tab
        self.SAXSbuttons = ButtonOptions()
        self.simulate = QPushButton("Simulate SAXS")
        self.simulate.setMinimumSize(110, 24)
        self.simulate.setMaximumSize(110, 24)
        self.SAXSbuttons.horizontalLayout_5.insertWidget(1, self.simulate)
        self.simulate.clicked.connect(self.getSimulatedSAXSData)

        self.gridLayout_5.addWidget(self.SAXSbuttons, 0, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        self.SAXSExperiment.setLayout(self.gridLayout_5)

        #Building Virtual SANS Experiment tab
        #TODO: A future project to implement this tab


    def getModelProfileRow(self, name: str, default: float, column: int) -> list:
        """Get model data from a single row in a column and convert to float"""

        val = self.subunitTable.model.item(name, column).data(Qt.EditRole)

        if val:
            return val
        else:
            return default

    def getModelProfile(self) -> ModelProfile:
        """Get model profile"""

        subunits = []
        p_s = []
        dimensions = []
        com = []
        rotation_points = []
        rotation = []
        columns = self.subunitTable.model.columnCount()

        #no subunits inputted
        if not self.subunitTable.model.item(1, columns - 1):
            return
            
        default = self.subunitTable.defaultValue

        #append inputted data to lists
        for column in range(columns):
            subunit = self.subunitTable.model.item(OPTIONLAYOUT["Subunit"], column).text()
            subunits.append(subunit)
            p_s.append(self.getModelProfileRow(OPTIONLAYOUT["ΔSLD"], default[OPTIONLAYOUT["ΔSLD"]], column))

            dims = []
            if default[OPTIONLAYOUT["x"]][subunit]:
                dim_x = self.getModelProfileRow(OPTIONLAYOUT["x"], default[OPTIONLAYOUT["x"]][subunit], column)
                dims.append(dim_x)
            if default[OPTIONLAYOUT["y"]][subunit]:
                dim_y = self.getModelProfileRow(OPTIONLAYOUT["y"], default[OPTIONLAYOUT["y"]][subunit], column)
                dims.append(dim_y)
            if default[OPTIONLAYOUT["z"]][subunit]:
                dim_z = self.getModelProfileRow(OPTIONLAYOUT["z"], default[OPTIONLAYOUT["z"]][subunit], column)
                dims.append(dim_z)
            dimensions.append(dims)

            com_x = self.getModelProfileRow(OPTIONLAYOUT["COM_x"], default[OPTIONLAYOUT["COM_x"]], column)
            com_y = self.getModelProfileRow(OPTIONLAYOUT["COM_y"], default[OPTIONLAYOUT["COM_y"]], column)
            com_z = self.getModelProfileRow(OPTIONLAYOUT["COM_z"], default[OPTIONLAYOUT["COM_z"]], column)
            com.append([com_x, com_y, com_z])

            rot_x = self.getModelProfileRow(OPTIONLAYOUT["RP_x"], default[OPTIONLAYOUT["RP_x"]], column)
            rot_y = self.getModelProfileRow(OPTIONLAYOUT["RP_y"], default[OPTIONLAYOUT["RP_y"]], column)
            rot_z = self.getModelProfileRow(OPTIONLAYOUT["RP_z"], default[OPTIONLAYOUT["RP_z"]], column)
            rotation_points.append([rot_x, rot_y, rot_z])

            rot_alpha = self.getModelProfileRow(OPTIONLAYOUT["α"], default[OPTIONLAYOUT["α"]], column)
            rot_beta = self.getModelProfileRow(OPTIONLAYOUT["β"], default[OPTIONLAYOUT["β"]], column)
            rot_gamma = self.getModelProfileRow(OPTIONLAYOUT["γ"], default[OPTIONLAYOUT["γ"]], column)
            rotation.append([rot_alpha, rot_beta, rot_gamma])

        #set bool to checkbox  
        if self.subunitTable.overlap.isChecked():
            exclude_overlap = True
        else:
            exclude_overlap = False
        
        return ModelProfile(subunits=subunits, p_s=p_s, dimensions=dimensions, com=com, 
                           rotation_points=rotation_points, rotation=rotation, exclude_overlap=exclude_overlap)
    

    def getViewPlotDesign(self) -> ViewerPlotDesign:
        """Get values affecting the illustrative aspect of Viewer"""
        colour = []

        columns = self.subunitTable.model.columnCount()
        for column in range(columns):
            colour.append(self.getModelProfileRow(OPTIONLAYOUT["Colour"], "Green", column))
        
        return ViewerPlotDesign(colour=colour)
    

    def onClickingPlot(self):
        """Plotting the designed model in the Build model tab. 
        If checked, plot theoretical scattering as well"""

        modelProfile = self.getModelProfile()
        if not modelProfile:
            return
        
        plotDesign = self.getViewPlotDesign()
        modelDistribution = getPointDistribution(modelProfile, 3000)
        self.viwerModel.setPlot(modelDistribution, plotDesign)

        #on being checked, plot theoretical scattering
        #TODO: Get Structure factor to work
        if self.checkTheoreticalScattering.isChecked():
            scattering = TheoreticalScatteringCalculation(System=ModelSystem(PointDistribution=modelDistribution, 
                                                                        Stype="None", par=[], 
                                                                        polydispersity=0.0, conc=0.2, 
                                                                        sigma_r=0.0), 
                                                                        Calculation=SimulationParameters())
            theoreticalScattering = getTheoreticalScattering(scattering)
            self.viwerModel.setScatteringPlot(theoreticalScattering)

        else:
            self.viwerModel.setClearScatteringPlot()


    def onClickingReset(self):
        """Reset tab to default"""
        print("Saving")
        #Do something


    def onClickingClose(self):
        """Close Shape2SAS GUI"""
        print("closing")
        #Do something
    

    def onClickingHelp(self):
        """Opening the help window"""
        print("Help")
        #Do something

    
    def getDimensionNames(self):
        """Get the names of the dimensions"""

        dim_names = []

        columns = self.subunitTable.model.columnCount()

        for column in range(columns):
            
            dim_name = []

            name_x = re.match(r'^[a-zA-Z]+', self.subunitTable.model.item(OPTIONLAYOUT["x"], column).text())
            if name_x:
                dim_name.append(name_x.group())
            name_y = re.match(r'^[a-zA-Z]+', self.subunitTable.model.item(OPTIONLAYOUT["y"], column).text())
            if name_y:
                dim_name.append(name_y.group())
            name_z = re.match(r'^[a-zA-Z]+', self.subunitTable.model.item(OPTIONLAYOUT["z"], column).text())
            if name_z:
                dim_name.append(name_z.group())

            dim_names.append(dim_name)
        
        return dim_names


    def getPluginModel(self):
        """Generating a plugin model and sends it to
        the Plugin Models folder in SasView"""
        name = "model_1"

        modelProfile = self.getModelProfile()
        dim_names = self.getDimensionNames()

        model_str, full_path = generatePlugin(modelProfile, dim_names, name)

        print(model_str, full_path)


    def onCheckingInput(self, input: str, default: str) -> str:
        """Check if the input is valid. Otherwise, return default value"""

        if not input.text():
            return default
        else:
            return input.text()

    def getSimulatedSAXSData(self):
        """Generating simulated data and sends it to
        the Data Explorer in SasView"""
        
        #Calculations
        qmin = float(self.onCheckingInput(self.lineEdit, "0.001"))
        qmax = float(self.onCheckingInput(self.lineEdit_14, "0.5"))

        Nq = int(self.onCheckingInput(self.lineEdit_15, "400"))
        Np = int(self.onCheckingInput(self.lineEdit_16, "100"))
        N = int(self.onCheckingInput(self.lineEdit_17, "3000"))

        name = self.onCheckingInput(self.lineEdit_19, "Model_1")

        #SAXS parameters
        Stype = self.comboBox.currentText()

        sigma_r = float(self.onCheckingInput(self.lineEdit_5, "0.0"))
        polydispersity = float(self.onCheckingInput(self.lineEdit_4, "0.0"))
        conc = float(self.onCheckingInput(self.lineEdit_3, "0.2"))
        exposure = float(self.onCheckingInput(self.lineEdit_2, "500"))

        #Generate simulated data
        Sim_par = SimulationParameters(qmin=qmin, qmax=qmax, Nq=Nq, prpoints=Np, Npoints=N)
        Profile = self.getModelProfile()

        Distr = getPointDistribution(Profile, N)
        Theo_calc = TheoreticalScatteringCalculation(System=ModelSystem(PointDistribution=Distr, 
                                                                        Stype=Stype, par=[], 
                                                                        polydispersity=polydispersity, 
                                                                        conc=conc, 
                                                                        sigma_r=sigma_r), 
                                                                        Calculation=Sim_par)
        Theo_I = getTheoreticalScattering(Theo_calc)
        Sim_calc = SimulateScattering(q=Theo_I.q, I0=Theo_I.I0, I=Theo_I.I, exposure=exposure)
        Sim_SAXS = getSimulatedScattering(Sim_calc)

        print(Sim_SAXS)

        #Send data to SasView Data Explorer
        #IExperimental.save_Iexperimental


if __name__ == "__main__":
    app = QApplication([])
    widget = DesignWindow()
    widget.show()
    sys.exit(app.exec())
