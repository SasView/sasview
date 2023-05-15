import traceback
from typing import Optional, Callable

from datetime import datetime

import numpy as np
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Qt

from sas.qtgui.Perspectives.ParticleEditor.FunctionViewer import FunctionViewer
from sas.qtgui.Perspectives.ParticleEditor.PythonViewer import PythonViewer
from sas.qtgui.Perspectives.ParticleEditor.OutputViewer import OutputViewer
from sas.qtgui.Perspectives.ParticleEditor.CodeToolBar import CodeToolBar
from sas.qtgui.Perspectives.ParticleEditor.OutputCanvas import OutputCanvas

from sas.qtgui.Perspectives.ParticleEditor.UI.DesignWindowUI import Ui_DesignWindow

from sas.qtgui.Perspectives.ParticleEditor.function_processor import process_code, FunctionDefinitionFailed
from sas.qtgui.Perspectives.ParticleEditor.vectorise import vectorise_sld

from sas.qtgui.Perspectives.ParticleEditor.sampling import (
    SpatialSample, QSample, RandomSampleSphere, RandomSampleCube, GridSample)

from sas.qtgui.Perspectives.ParticleEditor.scattering import (
    OutputType, OrientationalDistribution, ScatteringCalculation, calculate_scattering)
from sas.qtgui.Perspectives.ParticleEditor.util import format_time_estimate

import sas.qtgui.Perspectives.ParticleEditor.UI.icons_rc
class DesignWindow(QtWidgets.QDialog, Ui_DesignWindow):
    def __init__(self, parent=None):
        super().__init__()

        self.setupUi(self)
        self.setWindowTitle("Placeholder title")
        self.parent = parent


        #
        # First Tab
        #

        hbox = QtWidgets.QHBoxLayout(self)

        splitter = QtWidgets.QSplitter(Qt.Vertical)

        self.pythonViewer = PythonViewer()
        self.outputViewer = OutputViewer()
        self.codeToolBar = CodeToolBar()

        self.pythonViewer.build_trigger.connect(self.doBuild)

        self.codeToolBar.saveButton.clicked.connect(self.onSave)
        self.codeToolBar.loadButton.clicked.connect(self.onLoad)
        self.codeToolBar.buildButton.clicked.connect(self.doBuild)
        self.codeToolBar.scatterButton.clicked.connect(self.doScatter)

        self.solvent_sld = 0.0


        topSection = QtWidgets.QVBoxLayout()
        topSection.addWidget(self.pythonViewer)
        topSection.addWidget(self.codeToolBar)
        topSection.setContentsMargins(0,0,0,5)

        topWidget = QtWidgets.QWidget()
        topWidget.setLayout(topSection)


        splitter.addWidget(topWidget)
        splitter.addWidget(self.outputViewer)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        hbox.addWidget(splitter)

        # Function viewer
        self.functionViewer = FunctionViewer()
        self.functionViewer.radius_control.radiusField.valueChanged.connect(self.onRadiusChanged)

        # A components
        hbox.addWidget(self.functionViewer)
        self.definitionTab.setLayout(hbox)


        #
        # Ensemble tab
        #

        # Populate combo boxes

        self.orientationCombo.addItem("Unoriented")
        self.orientationCombo.addItem("Fixed Orientation")

        self.structureFactorCombo.addItem("None") # TODO: Structure Factor Options

        self.solventSLDBox.valueChanged.connect(self.onSolventSLDBoxChanged)


        #
        # Calculation Tab
        #
        self.methodComboOptions = ["Sphere Monte Carlo", "Cube Monte Carlo", "Grid"]
        for option in self.methodComboOptions:
            self.methodCombo.addItem(option)

        # Spatial sampling changed
        self.methodCombo.currentIndexChanged.connect(self.updateSpatialSampling)
        self.sampleRadius.valueChanged.connect(self.updateSpatialSampling)
        self.nSamplePoints.valueChanged.connect(self.updateSpatialSampling)
        self.randomSeed.textChanged.connect(self.updateSpatialSampling)
        self.fixRandomSeed.clicked.connect(self.updateSpatialSampling)

        # Q sampling changed
        self.useLogQ.clicked.connect(self.updateQSampling)
        self.qMinBox.textChanged.connect(self.updateQSampling)
        self.qMaxBox.textChanged.connect(self.updateQSampling)
        self.qSamplesBox.valueChanged.connect(self.updateQSampling)

        #
        # Output Tab
        #

        self.outputCanvas = OutputCanvas()

        outputLayout = QtWidgets.QVBoxLayout()
        outputLayout.addWidget(self.outputCanvas)

        self.outputTab.setLayout(outputLayout)

        #
        # Misc
        #

        # Populate tables

        # Columns should be name, value, min, max, fit, [remove]
        self.parametersTable.setHorizontalHeaderLabels(["Name", "Value", "Min", "Max", "Fit", ""])
        self.parametersTable.horizontalHeader().setStretchLastSection(True)

        self.structureFactorParametersTable.setHorizontalHeaderLabels(["Name", "Value", "Min", "Max", "Fit", ""])
        self.structureFactorParametersTable.horizontalHeader().setStretchLastSection(True)

        # Set up variables

        self.spatialSampling: SpatialSample = self._spatialSampling()
        self.qSampling: QSample = self._qSampling()

        self.last_calculation_time: Optional[float] = None
        self.last_calculation_n: int = 0

        self.sld_function: Optional[np.ndarray] = None
        self.sld_coordinate_mapping: Optional[np.ndarray] = None
        self.magnetism_function: Optional[np.ndarray] = None
        self.magnetism_coordinate_mapping: Optional[np.ndarray] = None

    def onRadiusChanged(self):
        if self.radiusFromParticleTab.isChecked():
            self.sampleRadius.setValue(self.functionViewer.radius_control.radius())

    def onSolventSLDBoxChanged(self):
        sld = float(self.solventSLDBox.value())
        self.solvent_sld = sld
        # self.functionViewer.solvent_sld = sld # TODO: Think more about where to put this variable
        self.functionViewer.updateImage()

    def onSampleCountChanged(self):
        """ Called when the number of samples changes """


        # Update the estimate of time
        # Assume the amount of time is just determined by the number of
        # sample points (the sld calculation is the limiting factor)

        if self.last_calculation_time is not None:
            time_per_sample = self.last_calculation_time / self.last_calculation_n

            est_time = time_per_sample * int(self.nSamplePoints.value())

            self.timeEstimateLabel.setText(f"Estimated Time: {format_time_estimate(est_time)}")

    def onLoad(self):
        print("Load clicked")

    def onSave(self):
        print("Save clicked")

    def doBuild(self):
        """ Build functionality requested"""

        # Get the text from the window
        code = self.pythonViewer.toPlainText()

        self.outputViewer.reset()

        try:
            # Evaluate code
            function, xyz_converter, extra_parameter_names, extra_parameter_defs = \
                process_code(code,
                             text_callback=self.codeText,
                             warning_callback=self.codeError,
                             error_callback=self.codeError)

            if function is None:
                return False


            # Vectorise if needed
            maybe_vectorised = vectorise_sld(
                function,
                warning_callback=self.codeWarning,
                error_callback=self.codeError) # TODO: Deal with args

            if maybe_vectorised is None:
                return False

            self.functionViewer.setSLDFunction(maybe_vectorised, xyz_converter)
            self.sld_function = maybe_vectorised
            self.sld_coordinate_mapping = xyz_converter

            now = datetime.now()
            current_time = now.strftime("%Y-%m-%d %H:%M:%S")
            self.codeText(f"Built Successfully at {current_time}")
            return True

        except FunctionDefinitionFailed as e:
            self.codeError(e.args[0])
            return False

    def doScatter(self):
        """ Scatter functionality requested"""

        # attempt to build
        # don't do scattering if build fails

        build_success = self.doBuild()

        self.codeText("Calculating scattering...")

        if build_success:
            calc = self._scatteringCalculation()
            try:
                scattering_result = calculate_scattering(calc)
                self.last_calculation_time = scattering_result.calculation_time
                self.last_calculation_n = scattering_result.spatial_sampling_method._calculate_n_actual()

                self.codeText("Scattering calculation complete after %g seconds."%scattering_result.calculation_time)

                self.outputCanvas.data = scattering_result
                self.tabWidget.setCurrentIndex(5) # Move to output tab if complete

            except Exception:
                self.codeError(traceback.format_exc())


        else:
            self.codeError("Build failed, scattering cancelled")

    def onFit(self):
        """ Fit functionality requested"""
        pass

    def codeError(self, text):
        """ Show an error concerning input code"""
        self.outputViewer.addError(text)

    def codeText(self, text):
        """ Show info about input code / code stdout"""
        self.outputViewer.addText(text)

    def codeWarning(self, text):
        """ Show a warning about input code"""
        self.outputViewer.addWarning(text)

    def updateQSampling(self):
        """ Update the spatial sampling object """
        self.qSampling = self._qSampling()
        print(self.qSampling) # TODO: Remove

    def _qSampling(self) -> QSample:
        """ Calculate the q sampling object based on current gui settings"""
        is_log = self.useLogQ.isEnabled() and self.useLogQ.isChecked() # Only when it's an option
        min_q = float(self.qMinBox.text())
        max_q = float(self.qMaxBox.text())
        n_samples = int(self.qSamplesBox.value())

        return QSample(min_q, max_q, n_samples, is_log)

    def updateSpatialSampling(self):
        """ Update the spatial sampling object """
        self.spatialSampling = self._spatialSampling()
        self.sampleDetails.setText(self.spatialSampling.sampling_details())
        # print(self.spatialSampling)

    def _spatialSampling(self) -> SpatialSample:
        """ Calculate the spatial sampling object based on current gui settings"""
        sample_type = self.methodCombo.currentIndex()

        # All the methods need the radius, number of points, etc
        radius = float(self.sampleRadius.value())
        n_desired = int(self.nSamplePoints.value())
        seed = int(self.randomSeed.text()) if self.fixRandomSeed.isChecked() else None

        if sample_type == 0:
            return RandomSampleSphere(radius=radius, n_points_desired=n_desired, seed=seed)

        elif sample_type == 1:
            return RandomSampleCube(radius=radius, n_points_desired=n_desired, seed=seed)

        elif sample_type == 2:
            return GridSample(radius=radius, n_points_desired=n_desired)

        else:
            raise ValueError("Unknown index for spatial sampling method combo")

    def _scatteringCalculation(self):
        orientation_index = self.orientationCombo.currentIndex()

        if orientation_index == 0:
            orientation = OrientationalDistribution.UNORIENTED
        elif orientation_index == 1:
            orientation = OrientationalDistribution.FIXED
        else:
            raise ValueError("Unknown index for orientation combo")

        output_type = None
        if self.output1D.isChecked():
            output_type = OutputType.SLD_1D
        elif self.output2D.isChecked():
            output_type = OutputType.SLD_2D

        if output_type is None:
            raise ValueError("Uknown index for output type combo")

        return ScatteringCalculation(
            solvent_sld=self.solvent_sld,
            orientation=orientation,
            output_type=output_type,
            spatial_sampling_method=self.spatialSampling,
            q_sampling_method=self.qSampling,
            sld_function=self.sld_function,
            sld_function_from_cartesian=self.sld_coordinate_mapping,
            sld_function_parameters={},
            magnetism_function=None,
            magnetism_function_from_cartesian=None,
            magnetism_function_parameters=None,
            magnetism_vector=None)

def main():
    """ Demo/testing window"""

    from sas.qtgui.convertUI import main

    main()

    app = QtWidgets.QApplication([])
    window = DesignWindow()

    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
