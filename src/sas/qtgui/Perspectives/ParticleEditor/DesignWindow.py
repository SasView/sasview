import traceback
from datetime import datetime

import numpy as np
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy, QSpacerItem

from sas.qtgui.Perspectives.ParticleEditor.AngularSamplingMethodSelector import AngularSamplingMethodSelector
from sas.qtgui.Perspectives.ParticleEditor.calculations.calculate import calculate_scattering
from sas.qtgui.Perspectives.ParticleEditor.CodeToolBar import CodeToolBar
from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import (
    AngularDistribution,
    CalculationParameters,
    CoordinateSystemTransform,
    MagnetismDefinition,
    ParticleDefinition,
    QSample,
    ScatteringCalculation,
    ScatteringOutput,
    SLDDefinition,
    SLDFunction,
    SpatialDistribution,
)
from sas.qtgui.Perspectives.ParticleEditor.function_processor import FunctionDefinitionFailed, process_code
from sas.qtgui.Perspectives.ParticleEditor.FunctionViewer import FunctionViewer
from sas.qtgui.Perspectives.ParticleEditor.OutputViewer import OutputViewer
from sas.qtgui.Perspectives.ParticleEditor.ParameterFunctionality.ParameterTable import ParameterTable
from sas.qtgui.Perspectives.ParticleEditor.ParameterFunctionality.ParameterTableButtons import ParameterTableButtons
from sas.qtgui.Perspectives.ParticleEditor.ParameterFunctionality.ParameterTableModel import ParameterTableModel
from sas.qtgui.Perspectives.ParticleEditor.Plots.QCanvas import QCanvas
from sas.qtgui.Perspectives.ParticleEditor.PythonViewer import PythonViewer
from sas.qtgui.Perspectives.ParticleEditor.sampling.points import Grid as GridSampling
from sas.qtgui.Perspectives.ParticleEditor.sampling.points import RandomCube as UniformCubeSampling
from sas.qtgui.Perspectives.ParticleEditor.UI.DesignWindowUI import Ui_DesignWindow
from sas.qtgui.Perspectives.ParticleEditor.util import format_time_estimate
from sas.qtgui.Perspectives.ParticleEditor.vectorise import vectorise_sld


def safe_float(text: str):
    try:
        return float(text)
    except:
        return 0.0


class DesignWindow(QtWidgets.QDialog, Ui_DesignWindow):
    """ Main window for the particle editor"""
    def __init__(self, parent=None):
        super().__init__()

        self.setupUi(self)
        self.setWindowTitle("Placeholder title")
        self.parent = parent

        # TODO: Set validators on fields

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
        # Parameters Tab
        #

        self._parameterTableModel = ParameterTableModel()
        self.parametersTable = ParameterTable(self._parameterTableModel)
        self.parameterTabButtons = ParameterTableButtons()

        self.parameterTabLayout.addWidget(self.parametersTable)
        self.parameterTabLayout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.parameterTabLayout.addWidget(self.parameterTabButtons)

        #
        # Ensemble tab
        #


        self.angularSamplingMethodSelector = AngularSamplingMethodSelector()

        self.topLayout.addWidget(self.angularSamplingMethodSelector, 0, 1)

        self.structureFactorCombo.addItem("None") # TODO: Structure Factor Options


        #
        # Calculation Tab
        #
        self.methodComboOptions = ["Grid", "Random"]
        for option in self.methodComboOptions:
            self.methodCombo.addItem(option)

        # Spatial sampling changed
        self.nSamplePoints.valueChanged.connect(self.onTimeEstimateParametersChanged)

        # Q sampling changed
        # self.useLogQ.clicked.connect(self.updateQSampling)
        # self.qMinBox.textChanged.connect(self.updateQSampling)
        # self.qMaxBox.textChanged.connect(self.updateQSampling)
        # self.qSamplesBox.valueChanged.connect(self.updateQSampling)

        self.qSamplesBox.valueChanged.connect(self.onTimeEstimateParametersChanged)

        #
        # Output Tabs
        #

        self.outputCanvas = QCanvas()

        outputLayout = QtWidgets.QVBoxLayout()
        outputLayout.addWidget(self.outputCanvas)

        self.qSpaceTab.setLayout(outputLayout)

        #
        # Misc
        #

        # Populate tables

        self.structureFactorParametersTable.setHorizontalHeaderLabels(["Name", "Value", "Min", "Max", "Fit", ""])
        self.structureFactorParametersTable.horizontalHeader().setStretchLastSection(True)

        # Set up variables

        self.last_calculation_time: float | None = None
        self.last_calculation_n_r: int = 0
        self.last_calculation_n_q: int = 0

        self.sld_function: SLDFunction | None = None
        self.sld_coordinate_mapping: CoordinateSystemTransform | None = None
        self.magnetism_function: np.ndarray | None = None
        self.magnetism_coordinate_mapping: np.ndarray | None = None

    def onRadiusChanged(self):
        if self.radiusFromParticleTab.isChecked():
            self.sampleRadius.setValue(self.functionViewer.radius_control.radius())

    def onTimeEstimateParametersChanged(self):
        """ Called when the number of samples changes """

        # TODO: This needs to be updated based on the number of angular samples now
        # Should have a n_points term
        # Should have a n_points*n_angles

        # Update the estimate of time
        # Assume the amount of time is just determined by the number of
        # sample points (the sld calculation is the limiting factor)

        if self.last_calculation_time is not None:
            time_per_sample = self.last_calculation_time / self.last_calculation_n_r

            est_time = time_per_sample * int(self.nSamplePoints.value()) * int(self.qSamplesBox.value())

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
            # TODO: Make solvent SLD available (process code_takes it as a parameter currently)

            # Evaluate code
            function, xyz_converter, extra_parameter_names, extra_parameter_defs = \
                process_code(code,
                             text_callback=self.codeText,
                             warning_callback=self.codeError,
                             error_callback=self.codeError)

            if function is None:
                return False

            # TODO: Magnetism
            self.parametersTable.update_contents(function, None)


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


    def angularDistribution(self) -> AngularDistribution:
        """ Get the AngularDistribution object that represents the GUI selected orientational distribution"""
        return self.angularSamplingMethodSelector.generate_sampler()

    def qSampling(self) -> QSample:
        q_min = float(self.qMinBox.text()) # TODO: Use better box
        q_max = float(self.qMaxBox.text())
        n_q = int(self.qSamplesBox.value())
        is_log = bool(self.useLogQ.isChecked())

        return QSample(q_min, q_max, n_q, is_log)

    def spatialSampling(self) -> SpatialDistribution:
        """ Calculate the spatial sampling object based on current gui settings"""
        sample_type = self.methodCombo.currentIndex()

        # All the methods need the radius, number of points, etc
        radius = float(self.sampleRadius.value())
        n_points = int(self.nSamplePoints.value())
        seed = int(self.randomSeed.text()) if self.fixRandomSeed.isChecked() else None

        if sample_type == 0:
            return GridSampling(radius=radius, desired_points=n_points)
            # return MixedSphereSample(radius=radius, n_points=n_points, seed=seed)

        elif sample_type == 1:
            return UniformCubeSampling(radius=radius, desired_points=n_points, seed=seed)
            # return MixedCubeSample(radius=radius, n_points=n_points, seed=seed)

        else:
            raise ValueError("Unknown index for spatial sampling method combo")

    def sldDefinition(self) -> SLDDefinition:

        if self.sld_function is not None:

            return SLDDefinition(
                self.sld_function,
                self.sld_coordinate_mapping)

        else:
            raise NotImplementedError("Careful handling of SLD Definitions not implemented yet")

    def magnetismDefinition(self) -> MagnetismDefinition | None:
        return None

    def particleDefinition(self) -> ParticleDefinition:
        """ Get the ParticleDefinition object that contains the SLD and magnetism functions """

        return ParticleDefinition(
            self.sldDefinition(),
            self.magnetismDefinition())

    def parametersForCalculation(self) -> CalculationParameters:
        return self._parameterTableModel.calculation_parameters()

    def polarisationVector(self) -> np.ndarray:
        """ Get a numpy vector representing the GUI specified polarisation vector"""
        return np.array([0,0,1])

    def currentSeed(self):
        return self.randomSeed

    def scatteringCalculation(self) -> ScatteringCalculation:
        """ Get the ScatteringCalculation object that represents the calculation that
        is to be passed to the solver"""
        angular_distribution = self.angularDistribution()
        spatial_sampling = self.spatialSampling()
        q_sampling = self.qSampling()
        particle_definition = self.particleDefinition()
        parameter_definition = self.parametersForCalculation()
        polarisation_vector = self.polarisationVector()
        seed = self.currentSeed()
        bounding_surface_check = self.continuityCheck.isChecked()

        return ScatteringCalculation(
            q_sampling=q_sampling,
            angular_sampling=angular_distribution,
            spatial_sampling_method=spatial_sampling,
            particle_definition=particle_definition,
            parameter_settings=parameter_definition,
            polarisation_vector=polarisation_vector,
            seed=seed,
            bounding_surface_sld_check=bounding_surface_check,
            sample_chunk_size_hint=100_000
            )

    def doScatter(self):
        """ Scatter functionality requested"""

        # attempt to build
        # don't do scattering if build fails

        build_success = self.doBuild()

        self.codeText("Calculating scattering...")

        if build_success:
            calc = self.scatteringCalculation()
            try:
                scattering_result = calculate_scattering(calc)

                # Time estimates
                self.last_calculation_time = scattering_result.calculation_time
                self.last_calculation_n_r = calc.spatial_sampling_method.n_points

                self.onTimeEstimateParametersChanged()

                # Output info
                self.codeText("Scattering calculation complete after %g seconds."%scattering_result.calculation_time)
                self.display_calculation_result(scattering_result)

            except Exception:
                self.codeError(traceback.format_exc())


        else:
            self.codeError("Build failed, scattering cancelled")

    def display_calculation_result(self, scattering_result: ScatteringOutput):
        """ Update graphs and select tab"""

        # Plot
        self.outputCanvas.data = scattering_result

        self.tabWidget.setCurrentIndex(5)  # Move to output tab if complete
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

    def qSampling(self) -> QSample:
        """ Calculate the q sampling object based on current gui settings"""
        is_log = self.useLogQ.isEnabled() and self.useLogQ.isChecked() # Only when it's an option
        min_q = float(self.qMinBox.text())
        max_q = float(self.qMaxBox.text())
        n_samples = int(self.qSamplesBox.value())

        return QSample(min_q, max_q, n_samples, is_log)


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
