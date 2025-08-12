import logging
import math
import os
import sys
import time
import timeit

import numpy
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.axes3d import Axes3D
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from scipy.spatial.transform import Rotation
from twisted.internet import threads

from sasdata.dataloader.data_info import Detector, Source

import sas.qtgui.Utilities.GuiUtils as GuiUtils
import sas.sascalc.calculator.gsc_model as gsc_model
from sas.qtgui.Plotting.Arrow3D import Arrow3D
from sas.qtgui.Plotting.PlotterBase import PlotterBase
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D
from sas.qtgui.Utilities.GenericReader import GenReader
from sas.qtgui.Utilities.ModelEditors.TabbedEditor.TabbedModelEditor import TabbedModelEditor
from sas.sascalc.calculator import sas_gen
from sas.sascalc.calculator.geni import create_beta_plot, f_of_q, radius_of_gyration
from sas.sascalc.fit import models

# Local UI
from .UI.GenericScatteringCalculator import Ui_GenericScatteringCalculator


class GenericScatteringCalculator(QtWidgets.QDialog, Ui_GenericScatteringCalculator):

    trigger_plot_3d = QtCore.Signal()
    calculationFinishedSignal = QtCore.Signal()
    loadingFinishedSignal = QtCore.Signal(list, bool)

    # class constants for textbox background colours
    TEXTBOX_DEFAULT_STYLESTRING = 'background-color: rgb(255, 255, 255);'
    TEXTBOX_WARNING_STYLESTRING = 'background-color: rgb(255, 226, 110);'
    TEXTBOX_ERROR_STYLESTRING = 'background-color: rgb(255, 182, 193);'

    def __init__(self, parent=None):
        super(GenericScatteringCalculator, self).__init__()
        self.setupUi(self)
        self.setFixedSize(self.minimumSizeHint())

        self.manager = parent
        self.communicator = self.manager.communicator()
        self.model = sas_gen.GenSAS()
        self.omf_reader = sas_gen.OMFReader()
        self.sld_reader = sas_gen.SLDReader()
        self.pdb_reader = sas_gen.PDBReader()
        self.vtk_reader = sas_gen.VTKReader()
        self.reader = None
        # sld data for nuclear and magnetic cases
        self.nuc_sld_data = None
        self.mag_sld_data = None
        self.verified = False
        # prevent layout shifting when widget hidden
        # TODO: Is there a way to lcoate this policy in the ui file?
        sizePolicy = self.lblVerifyError.sizePolicy()
        sizePolicy.setRetainSizeWhenHidden(True)
        self.lblVerifyError.setSizePolicy(sizePolicy)
        self.lblVerifyError.setVisible(False)

        self.parameters = []
        self.data = None
        self.datafile = None
        self.ext = None
        self.default_shape = str(self.cbShape.currentText())
        self.is_avg = False
        self.is_nuc = False
        self.is_mag = False
        self.is_beta = False
        self.data_to_plot = None
        self.data_betaQ = None
        self.fQ = []
        self.graph_num = 1      # index for name of graph

        # finish UI setup - install qml window
        self.setup_display()

        # combox box
        self.cbOptionsCalc.currentIndexChanged.connect(self.change_is_avg)
        # prevent layout shifting when widget hidden
        # TODO: Is there a way to lcoate this policy in the ui file?
        sizePolicy = self.cbOptionsCalc.sizePolicy()
        sizePolicy.setRetainSizeWhenHidden(True)
        self.cbOptionsCalc.setSizePolicy(sizePolicy)

        # code to highlight incompleted values in the GUI and prevent calculation
        # list of lineEdits to be checked
        self.lineEdits = [self.txtUpFracIn, self.txtUpFracOut, self.txtUpTheta, self.txtUpPhi, self.txtBackground,
                            self.txtScale, self.txtSolventSLD, self.txtTotalVolume, self.txtNoQBins, self.txtQxMax, self.txtQxMin,
                            self.txtMx, self.txtMy, self.txtMz, self.txtNucl, self.txtXnodes, self.txtYnodes,
                            self.txtZnodes, self.txtXstepsize, self.txtYstepsize, self.txtZstepsize, self.txtEnvYaw,
                            self.txtEnvPitch, self.txtEnvRoll, self.txtSampleYaw, self.txtSamplePitch, self.txtSampleRoll]
        self.invalidLineEdits = []
        for lineEdit in self.lineEdits:
            lineEdit.textChanged.connect(self.gui_text_changed_slot)     # when text is changed
            lineEdit.installEventFilter(self)                            # when textbox enabled/disabled

        # push buttons
        self.cmdClose.clicked.connect(self.hideWindow)
        self.cmdHelp.clicked.connect(self.onHelp)

        self.cmdNucLoad.clicked.connect(self.loadFile)
        self.cmdMagLoad.clicked.connect(self.loadFile)
        self.cmdCompute.clicked.connect(self.onCompute)
        self.cmdReset.clicked.connect(self.onReset)
        self.cmdSave.clicked.connect(self.onSaveFile)

        # checkboxes
        self.checkboxNucData.stateChanged.connect(self.change_data_type)
        self.checkboxMagData.stateChanged.connect(self.change_data_type)
        self.checkboxPluginModel.stateChanged.connect(self.update_file_name)
        self.checkboxLogSpace.stateChanged.connect(self.change_qValidator)


        # Connect plotting button, Use a function not lambda because of some bugs with referencing
        def plot3d_with_arrows():
            self.plot3d(has_arrow=True)

        self.cmdDraw.clicked.connect(plot3d_with_arrows)
        self.cmdDrawpoints.clicked.connect(self.plot3d)

        # update pixel no./total volume when changed in GUI
        self.txtXnodes.textChanged.connect(self.update_geometry_effects)
        self.txtYnodes.textChanged.connect(self.update_geometry_effects)
        self.txtZnodes.textChanged.connect(self.update_geometry_effects)
        self.txtXstepsize.textChanged.connect(self.update_geometry_effects)
        self.txtYstepsize.textChanged.connect(self.update_geometry_effects)
        self.txtZstepsize.textChanged.connect(self.update_geometry_effects)

        #check for presence of magnetism
        self.txtMx.textChanged.connect(self.check_for_magnetic_controls)
        self.txtMy.textChanged.connect(self.check_for_magnetic_controls)
        self.txtMz.textChanged.connect(self.check_for_magnetic_controls)

        #check for SLD changes
        #TODO: Implement a scientifically sound method for obtaining protein volume - Current value is a inprecise approximation. Until then Solvent SLD does not impact RG - SLD.
        # self.txtSolventSLD.editingFinished.connect(self.update_Rg)

        #update coord display
        self.txtEnvYaw.textChanged.connect(self.update_coords)
        self.txtEnvPitch.textChanged.connect(self.update_coords)
        self.txtEnvRoll.textChanged.connect(self.update_coords)
        self.txtSampleYaw.textChanged.connect(self.update_coords)
        self.txtSamplePitch.textChanged.connect(self.update_coords)
        self.txtSampleRoll.textChanged.connect(self.update_coords)
        self.txtUpTheta.textChanged.connect(self.update_polarisation_coords)
        self.txtUpPhi.textChanged.connect(self.update_polarisation_coords)

        # setup initial configuration
        self.checkboxNucData.setEnabled(False)
        self.checkboxMagData.setEnabled(False)
        self.change_data_type()
        # verify that the new enabled files are compatible

        self.verified = self.model.file_verification(self.nuc_sld_data, self.mag_sld_data)
        self.toggle_error_functionality()

        # validators
        # scale, volume and background must be positive
        validat_regex_pos = QtCore.QRegularExpression(r'^[+]?([.]\d+|\d+([.]\d+)?)$')

        self.txtScale.setValidator(QtGui.QRegularExpressionValidator(validat_regex_pos,
                                                          self.txtScale))
        self.txtBackground.setValidator(QtGui.QRegularExpressionValidator(
            validat_regex_pos, self.txtBackground))
        self.txtTotalVolume.setValidator(QtGui.QRegularExpressionValidator(
            validat_regex_pos, self.txtTotalVolume))

        # fraction of spin up between 0 and 1
        validat_regexbetween0_1 = QtCore.QRegularExpression(r'^(0(\.\d*)*|1(\.0+)?)$')
        self.txtUpFracIn.setValidator(
            QtGui.QRegularExpressionValidator(validat_regexbetween0_1, self.txtUpFracIn))
        self.txtUpFracOut.setValidator(
            QtGui.QRegularExpressionValidator(validat_regexbetween0_1, self.txtUpFracOut))

        # angles, SLD must be float values
        validat_regex_float = QtCore.QRegularExpression(r'^[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)([eE][+-]?[0-9]+)?$')
        self.txtUpTheta.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_float, self.txtUpTheta))
        self.txtUpPhi.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_float, self.txtUpPhi))

        self.txtSolventSLD.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_float, self.txtSolventSLD))
        self.txtNucl.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_float, self.txtNucl))

        self.txtMx.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_float, self.txtMx))
        self.txtMy.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_float, self.txtMy))
        self.txtMz.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_float, self.txtMz))

        self.txtXstepsize.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_float, self.txtXstepsize))
        self.txtYstepsize.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_float, self.txtYstepsize))
        self.txtZstepsize.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_float, self.txtZstepsize))

        self.txtEnvYaw.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_float, self.txtEnvYaw))
        self.txtEnvPitch.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_float, self.txtEnvPitch))
        self.txtEnvRoll.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_float, self.txtEnvRoll))
        self.txtSampleYaw.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_float, self.txtSampleYaw))
        self.txtSamplePitch.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_float, self.txtSamplePitch))
        self.txtSampleRoll.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_float, self.txtSampleRoll))

        self.change_qValidator()

        # 2 <= Qbin and nodes integers < 1000
        validat_regex_int = QtCore.QRegularExpression(r'^[2-9]|[1-9]\d{1,2}$')
        self.txtNoQBins.setValidator(QtGui.QRegularExpressionValidator(validat_regex_int,
                                                            self.txtNoQBins))

        # Plugin File Name
        rx = QtCore.QRegularExpression("^[A-Za-z0-9_]*$")
        self.txtFileName.setValidator(QtGui.QRegularExpressionValidator(rx))

        self.txtXnodes.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_int, self.txtXnodes))
        self.txtYnodes.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_int, self.txtYnodes))
        self.txtZnodes.setValidator(
            QtGui.QRegularExpressionValidator(validat_regex_int, self.txtZnodes))

        # plots - 3D in real space
        self.trigger_plot_3d.connect(self.plot3d)

        # plots - 3D in real space
        self.calculationFinishedSignal.connect(self.plot_1_2d)

        # notify main thread about file load complete
        self.loadingFinishedSignal.connect(self.complete_loading)

        # TODO the option Ellipsoid has not been implemented
        self.cbShape.currentIndexChanged.connect(self.selectedshapechange)

        # New font to display angstrom symbol
        new_font = 'font-family: -apple-system, "Helvetica Neue", "Ubuntu";'
        self.lblUnitSolventSLD.setStyleSheet(new_font)
        self.lblUnitVolume.setStyleSheet(new_font)
        self.lbl5.setStyleSheet(new_font)
        self.lblUnitMx.setStyleSheet(new_font)
        self.lblUnitMy.setStyleSheet(new_font)
        self.lblUnitMz.setStyleSheet(new_font)
        self.lblUnitNucl.setStyleSheet(new_font)
        self.lblUnitx.setStyleSheet(new_font)
        self.lblUnity.setStyleSheet(new_font)
        self.lblUnitz.setStyleSheet(new_font)

        # List to keep hold of plot3d windows so they don't get disposed by garbage collection
        self.plot3ds = []

    def setup_display(self):
        """
        This function sets up the GUI display of the different coordinate systems.
        Since these cannot be set in the .ui file they should be QWidgets added to the self.coord_display layout.
        This is one of four functions affecting the coordinate system visualisation which should be updated if
        a new 3D rendering library is used: `setup_display()`, `update_coords()`, `update_polarisation_coords()`, `set_polarisation_visible()`.
        """
        self.view_azim = 45
        self.view_elev = 45
        self.mouse_down = False

        sampleWindow = FigureCanvas(Figure())
        axes_sample = Axes3D(sampleWindow.figure, azim=self.view_azim, elev=self.view_elev, auto_add_to_figure=False)
        sampleWindow.figure.add_axes(axes_sample)

        envWindow = FigureCanvas(Figure())
        axes_env = Axes3D(envWindow.figure, azim=self.view_azim, elev=self.view_elev, auto_add_to_figure=False)
        envWindow.figure.add_axes(axes_env)

        beamWindow = FigureCanvas(Figure())
        axes_beam = Axes3D(beamWindow.figure, azim=self.view_azim, elev=self.view_elev, auto_add_to_figure=False)
        beamWindow.figure.add_axes(axes_beam)

        # TODO: Should be defined in init
        self.coord_windows = [sampleWindow, envWindow, beamWindow]
        self.coord_axes = [axes_sample, axes_env, axes_beam]
        self.coord_arrows = []

        titles = ["sample", "environment", "beamline"]
        for i, (window, axes) in enumerate(zip(self.coord_windows, self.coord_axes)):
            self.coordDisplay.addWidget(window)

            self.coord_axes[i].set_box_aspect((1, 1, 1))

            window.installEventFilter(self)

            # stack in order zs, xs, ys to match the coord system used in sasview
            arrows = []
            for x, y, z, color, in [[0, 1, 0, 'r'], [0, 0, 1, 'g'], [1, 0, 0, 'b']]:

                arrow = Arrow3D(axes.figure, [[0, x]], [[0, y]], [[0, z]],
                                colors=[color],
                                arrowstyle="->",
                                mutation_scale=10,
                                lw=2)

                arrow.set_realtime(True)
                axes.add_artist(arrow)

                arrows.append(arrow)


            self.coord_arrows.append(arrows)

            # Set axes properties
            axes.set_xlim3d(-1.1, 1.1)
            axes.set_ylim3d(-1.1, 1.1)
            axes.set_zlim3d(-1.1, 1.1)
            axes.set_axis_off()
            axes.set_title(titles[i])
            axes.disable_mouse_rotation()

        self.polarisation_arrow = Arrow3D(self.coord_axes[1].figure, [[0, 0.8]], [[0, 0]], [[0, 0]], [[1, 0, 0.7]], arrowstyle = "->", mutation_scale=10, lw=3)
        self.polarisation_arrow.set_realtime(True)
        self.coord_axes[1].add_artist(self.polarisation_arrow)

        self.coord_axes[0].text2D(0.7, 0.01, 'x', verticalalignment='bottom', horizontalalignment='left', color='red', fontsize=15, transform=self.coord_axes[0].transAxes)
        self.coord_axes[0].text2D(0.8, 0.01, 'y', verticalalignment='bottom', horizontalalignment='left', color='green', fontsize=15, transform=self.coord_axes[0].transAxes)
        self.coord_axes[0].text2D(0.9, 0.01, 'z', verticalalignment='bottom', horizontalalignment='left', color='blue', fontsize=15, transform=self.coord_axes[0].transAxes)

        self.p_text = self.coord_axes[1].text2D(0.6, 0.01, 'p', verticalalignment='bottom', horizontalalignment='left', color='#ff00bb', fontsize=15, transform=self.coord_axes[1].transAxes)
        self.p_text.set_visible(False)

        self.coord_axes[1].text2D(0.7, 0.01, 'u', verticalalignment='bottom', horizontalalignment='left', color='red', fontsize=15, transform=self.coord_axes[1].transAxes)
        self.coord_axes[1].text2D(0.8, 0.01, 'v', verticalalignment='bottom', horizontalalignment='left', color='green', fontsize=15, transform=self.coord_axes[1].transAxes)
        self.coord_axes[1].text2D(0.9, 0.01, 'w', verticalalignment='bottom', horizontalalignment='left', color='blue', fontsize=15, transform=self.coord_axes[1].transAxes)

        self.coord_axes[2].text2D(0.7, 0.01, 'U', verticalalignment='bottom', horizontalalignment='left', color='red', fontsize=15, transform=self.coord_axes[2].transAxes)
        self.coord_axes[2].text2D(0.8, 0.01, 'V', verticalalignment='bottom', horizontalalignment='left', color='green', fontsize=15, transform=self.coord_axes[2].transAxes)
        self.coord_axes[2].text2D(0.89, 0.01, 'W', verticalalignment='bottom', horizontalalignment='left', color='blue', fontsize=15, transform=self.coord_axes[2].transAxes)


    def update_coords(self):
        """
        This function rotates the visualisation of the coordinate systems
        This is one of four functions affecting the coordinate system visualisation which should be updated if
        a new 3D rendering library is used: `setup_display()`, `update_coords()`, `update_polarisation_coords()`, `set_polarisation_visible()`.
        """
        if self.txtEnvYaw.hasAcceptableInput() and self.txtEnvPitch.hasAcceptableInput() and \
                self.txtEnvRoll.hasAcceptableInput() and self.txtSampleYaw.hasAcceptableInput() and \
                self.txtSamplePitch.hasAcceptableInput() and self.txtSampleRoll.hasAcceptableInput():

            UVW_to_uvw, UVW_to_xyz = self.create_rotation_matrices()
            basis_vectors = numpy.array([[1,0,0],[0,1,0],[0,0,1]])

            #TODO: when scipy version updated can just use Rotation.as_matrix() to get new basis vectors - function name currently varies between versions used.
            uvw_matrix = UVW_to_uvw.apply(basis_vectors)

            xs, ys, zs = numpy.transpose(numpy.stack((numpy.zeros_like(uvw_matrix), uvw_matrix)), axes=(2, 1, 0))
            for i in range(3):
                # stack in order zs, xs, ys to match the coord system used in sasview
                self.coord_arrows[1][i].update_data([zs[i]], [xs[i]], [ys[i]])

            xyz_matrix = UVW_to_xyz.apply(basis_vectors)
            xs, ys, zs = numpy.transpose(numpy.stack((numpy.zeros_like(xyz_matrix), xyz_matrix)), axes=(2, 1, 0))
            for i in range(3):
                # stack in order zs, xs, ys to match the coord system used in sasview
                self.coord_arrows[0][i].update_data([zs[i]], [xs[i]], [ys[i]])

            self.update_polarisation_coords()


    def update_polarisation_coords(self):
        """
        This function rotates the visualisation of the polarisation vector
        This is one of four functions affecting the coordinate system visualisation which should be updated if
        a new 3D rendering library is used: `setup_display()`, `update_coords()`, `update_polarisation_coords()`, `set_polarisation_visible()`.
        """
        if self.txtUpTheta.hasAcceptableInput() and self.txtUpPhi.hasAcceptableInput():
            theta = numpy.radians(float(self.txtUpTheta.text()))
            phi = numpy.radians(float(self.txtUpPhi.text()))
            UVW_to_uvw, _ = self.create_rotation_matrices()
            p_vec = (UVW_to_uvw * Rotation.from_euler("ZY", [phi, theta])).apply(numpy.array([0, 0, 0.8])) # vector relative to beamline coords
            self.polarisation_arrow.update_data([[0, p_vec[2]]], [[0, p_vec[0]]], [[0, p_vec[1]]])

    def set_polarisation_visible(self, visible):
        """
        This function updates the visibility of the polarisation vector
        This is one of four functions affecting the coordinate system visualisation which should be updated if
        a new 3D rendering library is used: `setup_display()`, `update_coords()`, `update_polarisation_coords()`, `set_polarisation_visible()`.
        """
        self.polarisation_arrow.set_visible(visible)
        self.p_text.set_visible(visible)
        self.polarisation_arrow.base.canvas.draw()

    def reset_camera(self):
        self.view_azim = 45
        self.view_elev = 45
        self.mouse_down = False
        for axes in self.coord_axes:
            axes.view_init(elev=self.view_elev, azim=self.view_azim)
            axes.figure.canvas.draw()

    def gui_text_changed_slot(self):
        """Catches the signal that a textbox has beeen altered"""
        self.gui_text_changed(self.sender())

    def eventFilter(self, target, event):
        """Catches the event that a textbox has been enabled/disabled"""
        if target in self.lineEdits and event.type() == QtCore.QEvent.EnabledChange:
            self.gui_text_changed(target)
        elif target in self.coord_windows:
            if event.type() == QtCore.QEvent.MouseButtonPress:
                mEvent = QtGui.QMouseEvent(event)
                self.mouse_x = mEvent.x()
                self.mouse_y = mEvent.y()
                self.mouse_down = True
            elif event.type() == QtCore.QEvent.MouseButtonRelease:
                self.mouse_down = False
            elif event.type() == QtCore.QEvent.MouseMove and self.mouse_down:
                mEvent = QtGui.QMouseEvent(event)
                self.view_azim = (self.view_azim - mEvent.x() + self.mouse_x) % 360
                self.view_elev = min(max(self.view_elev + mEvent.y() - self.mouse_y, -90), 90)
                self.mouse_x = mEvent.x()
                self.mouse_y = mEvent.y()
                for axes in self.coord_axes:
                    axes.view_init(elev=self.view_elev, azim=self.view_azim)
                    axes.figure.canvas.draw()

        return False

    def gui_text_changed(self, sender):
        """check whether lineEdit values are valid

        This function checks whether lineEdits are valid, and if not highlights them and
        calls for functionality to be disabled.
        It checks for both errors and warnings. Error states highlight red and disable
        functionality. These are 'intermediate' states which do not match the regex.
        Warning states are highlighted orange and warn the user the value may be problematic.
        Warnings were previously checked for in the check_value() method.

        For warnings this checks that QMax and the number of Qbins is suitable
        given the user chosen values. Unlike the hard limits imposed by the
        regex, this does not prevent the user using the given value, but warns
        them that it may be unsuitable with a backcolour.

        :param sender: The QLineEdit in question
        :type sender: QWidget
        """

        senderInvalid = sender in self.invalidLineEdits
        # If the LineEdit is disabled (i.e. value set programmatically) we trust the value
        if (not sender.isEnabled()):
            if senderInvalid:
                self.invalidLineEdits.remove(sender)
            self.toggle_error_functionality()
            sender.setStyleSheet("")
        # If the LineEdit has been corrected from an invalid value restore functionality
        elif sender.hasAcceptableInput() and senderInvalid:
            self.invalidLineEdits.remove(sender)
            self.toggle_error_functionality()
            sender.setStyleSheet(self.TEXTBOX_DEFAULT_STYLESTRING)
        # If the LineEdit has had an invalid value stored then remove functionality
        elif (not sender.hasAcceptableInput()) and (not senderInvalid):
            self.invalidLineEdits.append(sender)
            self.toggle_error_functionality()
            sender.setStyleSheet(self.TEXTBOX_ERROR_STYLESTRING)
        # If the LineEdit is an acceptable value according to the regex apply warnings
        # This functionality was previously found in check_value()
        if sender not in self.invalidLineEdits:
            if sender == self.txtNoQBins :
                xnodes = float(self.txtXnodes.text())
                ynodes = float(self.txtYnodes.text())
                znodes = float(self.txtZnodes.text())
                value = float(str(self.txtNoQBins.text()))
                max_step =  3*max(xnodes, ynodes, znodes)
                    # limits qmin > maxq / nodes
                if value < 2 or value > max_step:
                    self.txtNoQBins.setStyleSheet(self.TEXTBOX_WARNING_STYLESTRING)
                else:
                    self.txtNoQBins.setStyleSheet(self.TEXTBOX_DEFAULT_STYLESTRING)
            elif sender == self.txtQxMax:
                xstepsize = float(self.txtXstepsize.text())
                ystepsize = float(self.txtYstepsize.text())
                zstepsize = float(self.txtZstepsize.text())
                value = float(str(self.txtQxMax.text()))
                max_q = numpy.pi / (max(xstepsize, ystepsize, zstepsize))
                if value <= 0 or value > max_q or value < float(self.txtQxMin.text()):
                    self.txtQxMax.setStyleSheet(self.TEXTBOX_WARNING_STYLESTRING)
                else:
                    self.txtQxMax.setStyleSheet(self.TEXTBOX_DEFAULT_STYLESTRING)
                #if 2D scattering, program sets qmin to -qmax
                if not self.is_avg:
                    self.txtQxMin.setText(str(-value))
            elif sender == self.txtQxMin and self.is_avg:
                xstepsize = float(self.txtXstepsize.text())
                ystepsize = float(self.txtYstepsize.text())
                zstepsize = float(self.txtZstepsize.text())
                value = float(str(self.txtQxMin.text()))
                min_q = numpy.pi / (min(xstepsize, ystepsize, zstepsize))
                if value <= 0 or value > min_q or value > float(self.txtQxMax.text()):
                    self.txtQxMin.setStyleSheet(self.TEXTBOX_WARNING_STYLESTRING)
                else:
                    self.txtQxMin.setStyleSheet(self.TEXTBOX_DEFAULT_STYLESTRING)



    def selectedshapechange(self):
        """
        TODO Temporary solution to display information about option 'Ellipsoid'
        """
        print("The option Ellipsoid has not been implemented yet.")
        self.communicator.statusBarUpdateSignal.emit(
            "The option Ellipsoid has not been implemented yet.")

    def toggle_error_functionality(self):
        """Disables/Enables some functionality if the state of the GUI means calculation cannot proceed

        This function is called during any process whenever there is a risk that the state
        of the GUI will make the data invalid for plotting, drawing or saving. If that is the
        case then this functionality is disabled. This function is currently called when two
        files are being verified for compatibility, and when textboxes enter 'intermediate' states.
        """
        verificationEnable = self.verified or not (self.is_mag and self.is_nuc)
        lineEditsEnable = len(self.invalidLineEdits) == 0
        # disable necessary buttons to prevent the attempted merging of incompatible files
        self.cmdDraw.setEnabled(verificationEnable and lineEditsEnable)
        self.cmdDrawpoints.setEnabled(verificationEnable and lineEditsEnable)
        self.cmdSave.setEnabled(verificationEnable and lineEditsEnable)
        self.cmdCompute.setEnabled(verificationEnable and lineEditsEnable)




    def change_data_type(self):
        """Adjusts the GUI for the enabled nuclear/magnetic data files

        When different combinations of nuclear and magnetic data files are loaded
        various options must be enabled/disabled or hidden/made visible. This function
        controls that behaviour and is called whenever the checkboxes for enabling files
        are altered. If the data file for a given type of data is not loaded then the
        average value textbox is enabled to allow the user to give a constant value for
        all points. If no data files are loaded then the node and stepsize textboxes are
        enabled to allow the user to specify a simple rectangular lattice.
        """
        # update information on which files are enabled
        self.is_nuc = self.checkboxNucData.isChecked()
        self.is_mag = self.checkboxMagData.isChecked()
        # enable the corresponding text displays to show this to the user clearly
        self.txtNucData.setEnabled(self.is_nuc)
        self.txtMagData.setEnabled(self.is_mag)
        # only allow editing of mean values if no data file for that vlaue has been loaded
        # user provided mean values are taken as a constant across all points
        self.txtMx.setEnabled(not self.is_mag)
        self.txtMy.setEnabled(not self.is_mag)
        self.txtMz.setEnabled(not self.is_mag)
        if not self.is_mag:
            self.txtMx.setText("0.0")
            self.txtMy.setText("0.0")
            self.txtMz.setText("0.0")
        self.txtNucl.setEnabled(not self.is_nuc)
        if not self.is_nuc:
            self.txtNucl.setText("0.0")
        # The ability to change the number of nodes and stepsizes only if no laoded data file enabled
        both_disabled =  (not self.is_mag) and (not self.is_nuc)
        if both_disabled:
            self.txtMx.setText("0.0")
            self.txtMy.setText("0.0")
            self.txtMz.setText("0.0")
            self.txtNucl.setText("6.97e-06")
            self.txtXnodes.setText("10")
            self.txtYnodes.setText("10")
            self.txtZnodes.setText("10")
            self.txtXstepsize.setText("6")
            self.txtYstepsize.setText("6")
            self.txtZstepsize.setText("6")
        self.txtXnodes.setEnabled(both_disabled)
        self.txtYnodes.setEnabled(both_disabled)
        self.txtZnodes.setEnabled(both_disabled)
        self.txtXstepsize.setEnabled(both_disabled)
        self.txtYstepsize.setEnabled(both_disabled)
        self.txtZstepsize.setEnabled(both_disabled)
        # update the gui with new values - sets the average values from enabled files
        self.update_gui()
        self.check_for_magnetic_controls()

    def change_qValidator(self):
        #Default Q range to calculate P(Q) is from 0.0003 to 0.3 A^-1.
        #The Q range needed for calculating P(Q) depends on the protein size.
        #It is perhaps better to use values based on RG in future.
        #For example: Q_min * RG = 0.2 and Q_max * RG = 15 could be a good start
        #Note: Fitting window defaults to .5 and .0005.
        if float(self.txtQxMax.text()) == 0:
            self.txtQxMax.setText("0.3")
        if float(self.txtQxMin.text()) == 0:
            self.txtQxMin.setText("0.0003")

        min = 0 if not self.checkboxLogSpace.isChecked() else 1e-10
        # 0 < Qmin&QMax <= 1000
        self.txtQxMax.setValidator(QtGui.QDoubleValidator(min, 1000, 10, self.txtQxMax))
        self.txtQxMin.setValidator(QtGui.QDoubleValidator(min, 1000, 10, self.txtQxMin))

    def update_cbOptionsCalc_visibility(self):
        # Only allow 1D averaging if no magnetic data and not elements
        allow = not self.is_mag
        if self.is_nuc and allow:
            allow = not self.nuc_sld_data.is_elements
        self.cbOptionsCalc.setVisible(allow)
        if (allow):
            # A helper function to set up the averaging system
            self.change_is_avg()
        else:
            # If magnetic data present then no averaging is allowed
            self.is_avg = False
            self.txtMx.setEnabled(not self.is_mag)
            self.txtMy.setEnabled(not self.is_mag)
            self.txtMz.setEnabled(not self.is_mag)
            self.txtQxMin.setEnabled(not self.is_mag)
            self.checkboxLogSpace.setChecked(not self.is_mag)
            self.checkboxLogSpace.setEnabled(not self.is_mag)


    def change_is_avg(self):
        """Adjusts the GUI for whether 1D averaging is enabled

        If the user has chosen to carry out Debye full averaging then the magnetic sld
        values must be set to 0, and made uneditable - because the calculator in geni.py
        is incapable of averaging systems with non-zero magnetic slds or polarisation.

        This function is called whenever different files are enabled or the user edits the
        averaging combobox.
        """
        # update the averaging option fromthe button on the GUI
        # required as the button may have been previously hidden with
        # any value, and preserves this - we must update the variable to match the GUI
        self.is_avg = (self.cbOptionsCalc.currentIndex() in (1,2))
        # did user request Beta(Q) calculation?
        self.is_beta = (self.cbOptionsCalc.currentIndex() == 2)
        # If averaging then set to 0 and diable the magnetic SLD textboxes
        self.txtMx.setEnabled(not self.is_avg)
        self.txtMy.setEnabled(not self.is_avg)
        self.txtMz.setEnabled(not self.is_avg)
        self.txtQxMin.setEnabled(self.is_avg)
        self.checkboxLogSpace.setChecked(self.is_avg)
        self.checkboxLogSpace.setEnabled(self.is_avg)
        self.checkboxPluginModel.setEnabled(self.is_avg)

        if self.is_avg:
            self.txtMx.setText("0.0")
            self.txtMy.setText("0.0")
            self.txtMz.setText("0.0")
            self.txtQxMin.setText(str(float(self.txtQxMax.text())*.001))

        # If not averaging then re-enable the magnetic sld textboxes
        else:
            self.txtQxMin.setText(str(float(self.txtQxMax.text())*-1))
            self.checkboxPluginModel.setChecked(False)
            self.txtFileName.setEnabled(False)

    def check_for_magnetic_controls(self):
        if self.txtMx.hasAcceptableInput() and self.txtMy.hasAcceptableInput() and self.txtMz.hasAcceptableInput():
            if (not self.is_mag) and float(self.txtMx.text()) == 0 and float(self.txtMy.text()) == 0 and float(self.txtMy.text()) == 0:
                self.txtUpFracIn.setEnabled(False)
                self.txtUpFracOut.setEnabled(False)
                self.txtUpTheta.setEnabled(False)
                self.txtUpPhi.setEnabled(False)
                self.set_polarisation_visible(False)
                return
        self.txtUpFracIn.setEnabled(True)
        self.txtUpFracOut.setEnabled(True)
        self.txtUpTheta.setEnabled(True)
        self.txtUpPhi.setEnabled(True)
        self.set_polarisation_visible(True)

    def loadFile(self):
        """Opens a menu to choose the datafile to load

        Opens a file dialog to allow the user to select a datafile to be loaded.
        If a nuclear sld datafile is loaded then the allowed file types are: .SLD .sld .PDB .pdb
        If a magnetic sld datafile is loaded then the allowed file types are: .SLD .sld .OMF .omf
        This function then loads in the requested datafile, but does not enable it.
        If no previous datafile of this type was loaded then the checkbox to enable
        this file is enabled.

        :param load_nuc: Specifies whether the loaded file is nuclear or magnetic data. Defaults to `True`.
                        `load_nuc=True` gives nuclear sld data.
                        `load_nuc=False` gives magnetic sld data.
        :type load_nuc: bool
        """
        try:
            load_nuc = self.sender() == self.cmdNucLoad
            # request a file from the user
            if load_nuc:
                f_type = """
                    All supported files (*.SLD *.sld *.pdb *.PDB, *.vtk, *.VTK);;
                        SLD files (*.SLD *.sld);;
                        PDB files (*.pdb *.PDB);;
                        VTK files (*.vtk *.VTK);;
                        All files (*.*)
                """
            else:
                f_type = """
                    All supported files (*.OMF *.omf *.SLD *.sld, *.vtk, *.VTK);;
                        OMF files (*.OMF *.omf);;
                        SLD files (*.SLD *.sld);;
                        VTK files (*.vtk *.VTK);;
                        All files (*.*)
                """
            self.datafile = QtWidgets.QFileDialog.getOpenFileName(self, "Choose a file", "", f_type)[0]
            # If a file has been sucessfully chosen
            if self.datafile:
                # set basic data about the file
                self.default_shape = str(self.cbShape.currentText())
                self.ext = os.path.splitext(str(self.datafile))[1]
                # select the required loader for the data format
                if self.ext in self.omf_reader.ext and (not load_nuc):
                    # only load omf files for magnetic data
                    loader = self.omf_reader
                elif self.ext in self.sld_reader.ext:
                    loader = self.sld_reader
                elif self.ext in self.vtk_reader.ext:
                    loader = self.vtk_reader
                elif self.ext in self.pdb_reader.ext and load_nuc:
                    # only load pdb files for nuclear data
                    loader = self.pdb_reader
                else:
                    logging.warning("The selected file does not have a suitable file extension")
                    return

                if self.reader is not None and self.reader.isrunning():
                    self.reader.stop()
                self.cmdNucLoad.setEnabled(False)
                self.cmdNucLoad.setText('Loading...')
                self.cmdMagLoad.setEnabled(False)
                self.cmdMagLoad.setText('Loading...')
                self.cmdCompute.setEnabled(False)
                self.cmdCompute.setText('Loading...')
                self.communicator.statusBarUpdateSignal.emit(
                    "Loading File {}".format(os.path.basename(
                        str(self.datafile))))
                self.reader = GenReader(path=str(self.datafile), loader=loader,
                                        completefn=lambda data=None: self.complete_loading_ex(data=data, load_nuc=load_nuc),
                                        updatefn=self.load_update)
                self.reader.queue()
        except (OSError, RuntimeError):
            log_msg = "Generic SAS Calculator: %s" % sys.exc_info()[1]
            logging.info(log_msg)
            raise
        return

    def load_update(self):
        """ Legacy function used in GenRead """
        if self.reader.isrunning():
            status_type = "progress"
        else:
            status_type = "stop"
        logging.info(status_type)

    def complete_loading_ex(self, data=None, load_nuc=True):
        """Send the finish message from calculate threads to main thread

        :param data: The data loaded from the requested file.
        :type data: OMFData, MagSLD depending on filetype
        :param load_nuc: Specifies whether the loaded file is nuclear or magnetic
            data. Defaults to `True`.
            `load_nuc=True` gives nuclear sld data.
            `load_nuc=False` gives magnetic sld data.
        :type load_nuc: bool
        """
        self.loadingFinishedSignal.emit(data, load_nuc)

    def complete_loading(self, data=None, load_nuc=True):
        """Function which handles the datafiles once they have been loaded in - used in GenRead

        Once the data has been loaded in by the required reader it is necessary to do a small
        amount of final processing to put them in the required form. This involves converting
        all the data to instances of MagSLD and reporting any errors. Additionally, verification
        of the newly loaded file is carried out.

        :param data: The data loaded from the requested file.
        :type data: OMFData, MagSLD depending on filetype
        :param load_nuc: Specifies whether the loaded file is nuclear or magnetic
            data. Defaults to `True`.
            `load_nuc=True` gives nuclear sld data.
            `load_nuc=False` gives magnetic sld data.
        :type load_nuc: bool
        """
        assert isinstance(data, list)
        assert len(data)==1
        data = data[0]
        self.cbShape.setEnabled(False)
        self.cmdNucLoad.setEnabled(True)
        self.cmdNucLoad.setText('Load')
        self.cmdMagLoad.setEnabled(True)
        self.cmdMagLoad.setText('Load')
        self.cmdCompute.setEnabled(True)
        self.cmdCompute.setText('Compute')
        if data is None:
            return
        try:
            is_pdbdata = False
            if load_nuc:
                self.txtNucData.setText(os.path.basename(str(self.datafile)))
            else:
                self.txtMagData.setText(os.path.basename(str(self.datafile)))
            if self.ext in self.omf_reader.ext:
                # only magnetic data can be read from omf files
                self.mag_sld_data = data
                self.check_units()
            elif self.ext in self.sld_reader.ext or self.ext in self.vtk_reader.ext:
                if load_nuc:
                    self.nuc_sld_data = data
                else:
                    self.mag_sld_data = data
            elif self.ext in self.pdb_reader.ext:
                # only nuclear data can be read from pdb files
                self.nuc_sld_data = data
                is_pdbdata = True
        except OSError:
            log_msg = "Loading Error: " \
                      "This file format is not supported for GenSAS."
            logging.warning(log_msg)
            raise
        except ValueError:
            log_msg = "Could not find any data"
            logging.info(log_msg)
            raise
        logging.info("Load Complete")
        # Once data files are loaded allow them to be enabled and then enable them
        if load_nuc:
            self.checkboxNucData.setEnabled(True)
            self.checkboxNucData.setChecked(True)
        else:
            self.checkboxMagData.setEnabled(True)
            self.checkboxMagData.setChecked(True)
        self.update_gui()
        # reset verification now we have loaded new files
        self.verify = False

        self.verified = self.model.file_verification(self.nuc_sld_data, self.mag_sld_data)
        self.toggle_error_functionality()

    def check_units(self):
        """
        Check if the units from the OMF file correspond to the default ones
        displayed on the interface.
        If not, modify the GUI with the correct units
        """
        # TODO: adopt the convention of font and symbol for the updated values
        if sas_gen.OMFData().valueunit != 'A^(-2)':
            value_unit = sas_gen.OMFData().valueunit
            self.lbl_unitMx.setText(value_unit)
            self.lbl_unitMy.setText(value_unit)
            self.lbl_unitMz.setText(value_unit)
            self.lbl_unitNucl.setText(value_unit)
        if sas_gen.OMFData().meshunit != 'A':
            mesh_unit = sas_gen.OMFData().meshunit
            self.lbl_unitx.setText(mesh_unit)
            self.lbl_unity.setText(mesh_unit)
            self.lbl_unitz.setText(mesh_unit)
            self.lbl_unitVolume.setText(mesh_unit+"^3")

    def update_gui(self):
        """Update the interface and model with values from loaded data

        This function updates the model parameter 'total_volume' with values from the loaded data
        and then updates all values in the gui with either model paramters or paramaters from the
        loaded data.
        """
        self.update_cbOptionsCalc_visibility()
        if self.is_nuc:
            if self.nuc_sld_data.is_elements:
                self.model.params['total_volume'] = numpy.sum(self.nuc_sld_data.vol_pix)
            else:
                self.model.params['total_volume'] = len(self.nuc_sld_data.sld_n)*self.nuc_sld_data.vol_pix[0]
        elif self.is_mag:
            if self.mag_sld_data.is_elements:
                self.model.params['total_volume'] = numpy.sum(self.mag_sld_data.vol_pix)
            else:
                self.model.params['total_volume'] = len(self.mag_sld_data.sld_n)*self.mag_sld_data.vol_pix[0]
        else:
            # use same calculation of total volume as when converting OMF to SLD
            self.model.params['total_volume'] = (float(self.txtXstepsize.text()) * float(self.txtYstepsize.text())
                                                 * float(self.txtZstepsize.text()) * float(self.txtXnodes.text())
                                                 * float(self.txtYnodes.text()) * float(self.txtZnodes.text()))

        # add condition for activation of save button
        self.cmdSave.setEnabled(True)

        # Volume to write to interface: npts x volume of first pixel
        self.txtTotalVolume.setText(str(self.model.params['total_volume']))
        # Chagne capitalisation for consistency with other values
        if self.txtTotalVolume.text() == "nan":
            self.txtTotalVolume.setText("NaN")

        # update the number of pixels with values from the loaded data or GUI if no datafiles enabled
        if self.is_nuc:
            if self.nuc_sld_data.is_elements:
                self.txtNoPixels.setText(str(len(self.nuc_sld_data.elements)))
            else:
                self.txtNoPixels.setText(str(len(self.nuc_sld_data.sld_n)))
        elif self.is_mag:
            if self.mag_sld_data.is_elements:
                self.txtNoPixels.setText(str(len(self.mag_sld_data.elements)))
            else:
                self.txtNoPixels.setText(str(len(self.mag_sld_data.sld_mx)))
        elif not(self.txtXnodes.hasAcceptableInput() and self.txtYnodes.hasAcceptableInput() and self.txtZnodes.hasAcceptableInput()):
            self.txtNoPixels.setText("NaN")
        else:
            self.txtNoPixels.setText(str(int(float(self.txtXnodes.text())
                                         * float(self.txtYnodes.text()) * float(self.txtZnodes.text()))))
        self.txtNoPixels.setEnabled(False)

        # Fill right hand side of GUI
        if self.is_mag:
            self.txtMx.setText(GuiUtils.formatValue(self.mag_sld_data.sld_mx))
            self.txtMy.setText(GuiUtils.formatValue(self.mag_sld_data.sld_my))
            self.txtMz.setText(GuiUtils.formatValue(self.mag_sld_data.sld_mz))
        if self.is_nuc:
            self.txtNucl.setText(GuiUtils.formatValue(self.nuc_sld_data.sld_n))
            self.txtXnodes.setText(GuiUtils.formatValue(self.nuc_sld_data.xnodes))
            self.txtYnodes.setText(GuiUtils.formatValue(self.nuc_sld_data.ynodes))
            self.txtZnodes.setText(GuiUtils.formatValue(self.nuc_sld_data.znodes))
            self.txtXstepsize.setText(GuiUtils.formatValue(self.nuc_sld_data.xstepsize))
            self.txtYstepsize.setText(GuiUtils.formatValue(self.nuc_sld_data.ystepsize))
            self.txtZstepsize.setText(GuiUtils.formatValue(self.nuc_sld_data.zstepsize))
        if self.is_mag and ((not self.is_nuc) or self.txtXnodes.text() == "NaN"):
            # If unable to get node data from nuclear system (not enabled or not present)
            self.txtXnodes.setText(GuiUtils.formatValue(self.mag_sld_data.xnodes))
            self.txtYnodes.setText(GuiUtils.formatValue(self.mag_sld_data.ynodes))
            self.txtZnodes.setText(GuiUtils.formatValue(self.mag_sld_data.znodes))
            self.txtXstepsize.setText(GuiUtils.formatValue(self.mag_sld_data.xstepsize))
            self.txtYstepsize.setText(GuiUtils.formatValue(self.mag_sld_data.ystepsize))
            self.txtZstepsize.setText(GuiUtils.formatValue(self.mag_sld_data.zstepsize))
        # otherwise leave as set since editable by user
        self.update_Rg()


    def update_Rg(self):
        #update RG boxes or run RG calculation
        if self.is_nuc:
            if self.nuc_sld_data.is_elements:
                self.txtRgMass.setText("N/A")
                self.txtRG.setText("N/A ")
                logging.info("SasView does not support computation of Radius of Gyration for elements.")
            else:
                rgVals = radius_of_gyration(self.nuc_sld_data)  #[String, String, Float], float used for plugin model
                self.txtRgMass.setText(rgVals[0])
                self.txtRG.setText(rgVals[1])
                self.rGMass = rgVals[2]                         #used in plugin model

        elif self.is_mag:
            self.txtRgMass.setText("N/A")
            self.txtRG.setText("N/A")
            logging.info("SasView does not support computation of Radius of Gyration for Magnetic Data.")
        else:
            self.txtRgMass.setText("No Data")
            self.txtRG.setText("No Data")



    def update_geometry_effects(self):
        """This function updates the number of pixels and total volume when the number of nodes/stepsize is changed

        This function only has an effect if no files are enabled otherwise the number of pixels and total
        volume may be set differently by the data from the file.
        """
        if self.is_mag or self.is_nuc:
            # don't change the number if this is being set from a file as then the number of pixels may differ
            return
        if not(self.txtXnodes.hasAcceptableInput() and self.txtYnodes.hasAcceptableInput() and self.txtZnodes.hasAcceptableInput()):
            # do not try to update if textbox invalid - this cannot be used for computation anyway
            self.txtNoPixels.setText("NaN")
            self.txtTotalVolume.setText("NaN")
            return
        self.txtNoPixels.setText(str(int(float(self.txtXnodes.text())
                                         * float(self.txtYnodes.text()) * float(self.txtZnodes.text()))))
        if not(self.txtXstepsize.hasAcceptableInput() and self.txtYstepsize.hasAcceptableInput() and self.txtZstepsize.hasAcceptableInput()):
            # do not try to update if textbox invalid - this cannot be used for computation anyway
            self.txtTotalVolume.setText("NaN")
            return
        self.model.params['total_volume'] = (float(self.txtXstepsize.text()) * float(self.txtYstepsize.text())
                                                 * float(self.txtZstepsize.text()) * float(self.txtXnodes.text())
                                                 * float(self.txtYnodes.text()) * float(self.txtZnodes.text()))
        self.txtTotalVolume.setText(str(self.model.params['total_volume']))
        # If nodes or stepsize changed then this may effect what values are allowed
        self.gui_text_changed(sender=self.txtNoQBins)
        self.gui_text_changed(sender=self.txtQxMax)
        self.gui_text_changed(sender=self.txtQxMin)

    def write_new_values_from_gui(self):
        """Update parameters in model using modified inputs from GUI

        Before the model is used to calculate any scattering patterns it needs
        to be updated with values from the gui. This does not affect any fixed values,
        whose textboxes are disabled, and means that any user chosen changes are made.
        It also ensure that at all times the values in the GUI reflect the data output.
        """
        if self.txtScale.isModified():
            self.model.params['scale'] = float(self.txtScale.text())

        if self.txtBackground.isModified():
            self.model.params['background'] = float(self.txtBackground.text())

        if self.txtSolventSLD.isModified():
            self.model.params['solvent_SLD'] = float(self.txtSolventSLD.text())

        # Different condition for total volume to get correct volume after
        # applying set_sld_data in compute
        if self.txtTotalVolume.isModified() \
                or self.model.params['total_volume'] != float(self.txtTotalVolume.text()):
            self.model.params['total_volume'] = float(self.txtTotalVolume.text())

        if self.txtUpFracIn.isModified():
            self.model.params['Up_frac_in'] = float(self.txtUpFracIn.text())

        if self.txtUpFracOut.isModified():
            self.model.params['Up_frac_out'] = float(self.txtUpFracOut.text())

        if self.txtUpTheta.isModified():
            self.model.params['Up_theta'] = float(self.txtUpTheta.text())

        if self.txtUpPhi.isModified():
            self.model.params['Up_phi'] = float(self.txtUpPhi.text())

    def onHelp(self):
        """
        Bring up the Generic Scattering calculator Documentation whenever
        the HELP button is clicked.
        Calls Documentation Window with the path of the location within the
        documentation tree (after /doc/ ....".
        """
        location = "/user/qtgui/Calculators/sas_calculator_help.html"
        self.manager.showHelp(location)

    def onReset(self):
        """ Reset the GUI to its default state

        This resets all GUI parameters to their default values and also resets
        all GUI states such as loaded files, stored data, verification and disabled/enabled
        widgets.
        """
        try:
            # reset values in textedits
            self.txtUpFracIn.setText("1.0")
            self.txtUpFracOut.setText("1.0")
            self.txtUpTheta.setText("0.0")
            self.txtUpPhi.setText("0.0")
            self.txtBackground.setText("0.0")
            self.txtScale.setText("1.0")
            self.txtSolventSLD.setText("0.0")
            self.txtTotalVolume.setText("216000.0")
            self.txtNoQBins.setText("30")
            self.txtQxMax.setText("0.3")
            self.txtQxMin.setText("0.0003")
            self.txtNoPixels.setText("1000")
            self.txtMx.setText("0.0")
            self.txtMy.setText("0.0")
            self.txtMz.setText("0.0")
            self.txtNucl.setText("6.97e-06")
            self.txtXnodes.setText("10")
            self.txtYnodes.setText("10")
            self.txtZnodes.setText("10")
            self.txtXstepsize.setText("6")
            self.txtYstepsize.setText("6")
            self.txtZstepsize.setText("6")
            self.txtEnvYaw.setText("0.0")
            self.txtEnvPitch.setText("0.0")
            self.txtEnvRoll.setText("0.0")
            self.txtSampleYaw.setText("0.0")
            self.txtSamplePitch.setText("0.0")
            self.txtSampleRoll.setText("0.0")
            self.reset_camera()
            # re-enable any options disabled by failed verification

            self.verified = False
            self.toggle_error_functionality()
            # reset option for calculation
            self.cbOptionsCalc.setCurrentIndex(0)
            # reset shape button
            self.cbShape.setCurrentIndex(0)
            self.cbShape.setEnabled(True)
            # reset compute button
            self.cmdCompute.setText('Compute')
            self.cmdCompute.setEnabled(True)
            # reset Load button and textedit
            self.txtNucData.setText('No File Loaded')
            self.cmdNucLoad.setEnabled(True)
            self.cmdNucLoad.setText('Load')
            self.txtMagData.setText('No File Loaded')
            self.cmdMagLoad.setEnabled(True)
            self.cmdMagLoad.setText('Load')
            # disable all file checkboxes, as no files are now loaded
            self.checkboxNucData.setEnabled(False)
            self.checkboxMagData.setEnabled(False)
            self.checkboxNucData.setChecked(False)
            self.checkboxMagData.setChecked(False)
            # reset all file data to its default empty state
            self.is_nuc = False
            self.is_mag = False
            self.is_beta = False
            self.nuc_sld_data = None
            self.mag_sld_data = None
            self.beta_data = None
            # update the gui for the no files loaded case
            self.change_data_type()
            # verify that the new enabled files are compatible

            self.verified = self.model.file_verification(self.nuc_sld_data, self.mag_sld_data)
            self.toggle_error_functionality()


        finally:
            pass

    def _create_default_2d_data(self):
        """Create the 2D data range for qx,qy

        Copied from previous version
        Create 2D data by default

        .. warning:: This data is never plotted.
        """
        self.qmax_x = float(self.txtQxMax.text())
        self.npts_x = int(self.txtNoQBins.text())
        self.data = Data2D()
        self.data.is_data = False
        # Default values
        self.data.detector.append(Detector())
        index = len(self.data.detector) - 1
        self.data.detector[index].distance = 8000  # mm
        self.data.source.wavelength = 6  # A
        self.data.detector[index].pixel_size.x = 5  # mm
        self.data.detector[index].pixel_size.y = 5  # mm
        self.data.detector[index].beam_center.x = self.qmax_x
        self.data.detector[index].beam_center.y = self.qmax_x
        xmax = self.qmax_x
        xmin = -xmax
        ymax = self.qmax_x
        ymin = -ymax
        qstep = self.npts_x

        x = numpy.linspace(start=xmin, stop=xmax, num=qstep, endpoint=True)
        y = numpy.linspace(start=ymin, stop=ymax, num=qstep, endpoint=True)
        # use data info instead
        new_x = numpy.tile(x, (len(y), 1))
        new_y = numpy.tile(y, (len(x), 1))
        new_y = new_y.swapaxes(0, 1)
        # all data require now in 1d array
        qx_data = new_x.flatten()
        qy_data = new_y.flatten()
        q_data = numpy.sqrt(qx_data * qx_data + qy_data * qy_data)
        # set all True (standing for unmasked) as default
        mask = numpy.ones(len(qx_data), dtype=bool)
        self.data.source = Source()
        self.data.data = numpy.ones(len(mask))
        self.data.err_data = numpy.ones(len(mask))
        self.data.qx_data = qx_data
        self.data.qy_data = qy_data
        self.data.q_data = q_data
        self.data.mask = mask
        # store x and y bin centers in q space
        self.data.x_bins = x
        self.data.y_bins = y
        # max and min taking account of the bin sizes
        self.data.xmin = xmin
        self.data.xmax = xmax
        self.data.ymin = ymin
        self.data.ymax = ymax

    def _create_default_sld_data(self):
        """Creates default sld data for use if no file has been loaded

        Copied from previous version

        .. warning:: deprecated
        """
        sld_n_default = 6.97e-06  # what is this number??
        omfdata = sas_gen.OMFData()
        omf2sld = sas_gen.OMF2SLD()
        omf2sld.set_data(omfdata, self.default_shape)
        self.sld_data = omf2sld.output
        self.sld_data.is_data = False
        self.sld_data.filename = "Default SLD Profile"
        self.sld_data.set_sldn(sld_n_default)

    def _create_default_1d_data(self):
        """Create the 1D data range for q

        Copied from previous version
        Create 1D data by default

        .. warning:: This data is never plotted.

        residuals.x = data_copy.x[index]
        residuals.dy = numpy.ones(len(residuals.y))
        residuals.dx = None
        residuals.dxl = None
        residuals.dxw = None
        """
        self.qmax_x = float(self.txtQxMax.text())
        self.qmin_x = float(self.txtQxMin.text())
        self.npts_x = int(self.txtNoQBins.text())
        self.xValues = numpy.array(self.npts_x)
        # Default values
        xmax = self.qmax_x
        xmin = self.qmin_x
        qstep = self.npts_x
        if self.checkboxLogSpace.isChecked():
            self.xValues = numpy.logspace(start=math.log(xmin,10),
                                stop=math.log(xmax,10),
                                num=qstep,
                                endpoint=True)
        else:
            self.xValues = numpy.linspace(start=xmin,
                           stop=xmax,
                           num=qstep,
                           endpoint=True)
        # store x and y bin centers in q space
        y = numpy.ones(len(self.xValues))
        dy = numpy.zeros(len(self.xValues))
        dx = numpy.zeros(len(self.xValues))
        self.data = Data1D(x=self.xValues, y=y)
        self.data.dx = dx
        self.data.dy = dy

    def create_full_sld_data(self):
        """Create the sld data to be used in the final calculation

        This function creates an instance of MagSLD which contains
        the required data for sas_gen and 3D plotting. It is the suitable combination of
        data from the magnetic data, nuclear data and set GUI parameters. Where nuclear
        and magnetic files are enabled it sometimes has to make a choice regarding which
        version of a parameter to keep. This is usually the nuclear data version, as in
        the case of .pdb files being used this version will contain more complete data.

        :return: The full sld data created from the various different sources
        :rtype: MagSLD
        """
        # CARRY OUT COMPATIBILITY CHECK - ELSE RETURN None
        # Set default data when nothing loaded yet
        omfdata = sas_gen.OMFData()
        # load in user chosen position data
        # If no file given this will be used to generate the position data
        if (not self.is_mag) and (not self.is_nuc):
            omfdata.xnodes = int(self.txtXnodes.text())
            omfdata.ynodes = int(self.txtYnodes.text())
            omfdata.znodes = int(self.txtZnodes.text())
            omfdata.xstepsize = float(self.txtXstepsize.text())
            omfdata.ystepsize = float(self.txtYstepsize.text())
            omfdata.zstepsize = float(self.txtZstepsize.text())
        # convert into sld format
        omf2sld = sas_gen.OMF2SLD()
        omf2sld.set_data(omfdata, self.default_shape)
        sld_data = omf2sld.get_output()

        # only to be done once - load in the position data of the atoms
        # verification ensures that this is the same across nuclear and magnetic datafiles
        if self.is_nuc:
            sld_data.vol_pix = self.nuc_sld_data.vol_pix
            sld_data.pos_x = self.nuc_sld_data.pos_x
            sld_data.pos_y = self.nuc_sld_data.pos_y
            sld_data.pos_z = self.nuc_sld_data.pos_z
            sld_data.data_length = len(self.nuc_sld_data.pos_x)
        elif self.is_mag:
            sld_data.vol_pix = self.mag_sld_data.vol_pix
            sld_data.pos_x = self.mag_sld_data.pos_x
            sld_data.pos_y = self.mag_sld_data.pos_y
            sld_data.pos_z = self.mag_sld_data.pos_z
            sld_data.data_length = len(self.mag_sld_data.pos_x)

        if self.is_nuc:
            if self.nuc_sld_data.is_elements:
                sld_data.set_elements(self.nuc_sld_data.elements, self.nuc_sld_data.are_elements_array)
        elif self.is_mag:
            if self.mag_sld_data.is_elements:
                sld_data.set_elements(self.mag_sld_data.elements, self.mag_sld_data.are_elements_array)

        # set the sld data from the required model file/GUI textbox
        if (self.is_nuc):
            sld_data.set_sldn(self.nuc_sld_data.sld_n)
        else:
            sld_data.set_sldn(float(self.txtNucl.text()), non_zero_mag_only=False)
        if (self.is_mag):
            sld_data.set_sldms(self.mag_sld_data.sld_mx, self.mag_sld_data.sld_my, self.mag_sld_data.sld_mz)
        else:
            sld_data.set_sldms(float(self.txtMx.text()),
                               float(self.txtMy.text()),
                               float(self.txtMz.text()))
        # Provide data giving connections between atoms for 3D drawing
        # This SHOULD only occur in nuclear data files as it is a feature of
        # pdb files - however the option for it to be drawn from magnetic files
        # if present is given in case the sld file format is expanded to include them
        if self.is_nuc:
            if self.nuc_sld_data.has_conect:
                sld_data.has_conect = True
                sld_data.line_x = self.nuc_sld_data.line_x
                sld_data.line_y = self.nuc_sld_data.line_y
                sld_data.line_z = self.nuc_sld_data.line_z
            # If the nuclear data does not contain conect data try to find it in the magnetic data.
            # TODO: combine both lists properly. Probably only necessary if a filetype for magnetic data
            #       is used which can contain such data.
            elif self.is_mag:
                if self.mag_sld_data.has_conect:
                    sld_data.has_conect=True
                    sld_data.line_x = self.mag_sld_data.line_x
                    sld_data.line_y = self.mag_sld_data.line_y
                    sld_data.line_z = self.mag_sld_data.line_z

        # take pixel data from nuclear sld as preference because may contatin atom types from pdb files
        if self.is_nuc:
            sld_data.pix_type = self.nuc_sld_data.pix_type
            sld_data.pix_symbol = self.nuc_sld_data.pix_symbol
        elif self.is_mag:
            sld_data.pix_type = self.mag_sld_data.pix_type
            sld_data.pix_symbol = self.mag_sld_data.pix_symbol
        return sld_data

    def create_rotation_matrices(self):
        """Create the rotation matrices between different coordinate systems

        UVW coords: beamline coords
        uvw coords: environment coords
        xyz coords: sample coords

        The GUI contains values of yaw, pitch and roll from uvw to xyz coordinates and
        from UVW to uvw. These are right handed coordinate systems with UVW being the beamline
        coordinate system with:

        U: horizonatal axis

        V: vertical axis

        W: axis back from detector to sample

        The rotation given by the user transforms the BASIS VECTORS - the user gives
        the trasformation from beamline coords to samplecoords for example - so from there perspective the
        beamline is the fixed object and the environment and sample rotate. The rotation is first a yaw angle
        about the V axis (UVW -> U'V'W') then a pitch angle about the U' axis (U'V'W' -> U''V''W'') and
        finally a roll rotation abot the W'' axis (U''V''W'' -> uvw).

        This function expects that the textbox values are correct.

        :return: two rotations, the first from UVW to xyz coords, the second from UVW to uvw coords
        :rtype: tuple of scipy.spatial.transform.Rotation
        """
        # in reverse
        # NOTE: If scipy version is updated above 1.4.0 in the future then this conversion can be replaced with the degrees=True argument
        # UVW to uvw
        env = Rotation.from_euler("YXZ", [numpy.radians(float(self.txtEnvYaw.text())),
                                          numpy.radians(float(self.txtEnvPitch.text())),
                                          numpy.radians(float(self.txtEnvRoll.text()))])
        # uvw to xyz
        sample = Rotation.from_euler("YXZ", [numpy.radians(float(self.txtSampleYaw.text())),
                                             numpy.radians(float(self.txtSamplePitch.text())),
                                             numpy.radians(float(self.txtSampleRoll.text()))])
        return env, sample*env

    def onCompute(self):
        """Execute the computation of I(qx, qy)

        Copied from previous version
        """
        try:
            # create the combined sld data and update from gui
            sld_data = self.create_full_sld_data()
            # TODO: implement fourier transform for meshes with multiple element or face types
            # The easy option is to simply convert all elements to tetrahedra - but this could rapidly
            # increase the calculation time.
            if sld_data.is_elements:
                if not sld_data.are_elements_array:
                    logging.warning("SasView does not currently support computation of meshes with multiple element or face types")
                    return
            self.model.set_sld_data(sld_data)
            UVW_to_uvw, UVW_to_xyz = self.create_rotation_matrices()
            # We do NOT need to invert these matrices - they are UVW to xyz for the basis vectors
            # and therefore xyz to UVW for the components of the vectors - as we desire
            self.model.set_rotations(UVW_to_uvw, UVW_to_xyz)
            self.write_new_values_from_gui()
            # create 2D or 1D data as appropriate
            if self.is_avg or self.is_avg is None:
                self._create_default_1d_data()
                inputs = [self.data.x, []]
            else:
                self._create_default_2d_data()
                inputs = [self.data.qx_data, self.data.qy_data]
            logging.info("Computation is in progress...")
            self.cmdCompute.setText('Cancel')
            self.cmdCompute.setToolTip("<html><head/><body><p>Cancel the computation of the scattering calculation.</p></body></html>")
            self.cmdCompute.clicked.disconnect()
            self.cmdCompute.clicked.connect(self.onCancel)
            self.cancelCalculation = False
            #self.cmdCompute.setEnabled(False)
            d = threads.deferToThread(self.complete, inputs, self._update)

            # Add deferred callback for call return
            # d.addCallback(self.plot_1_2d)
            d.addCallback(self.calculateComplete)
            d.addErrback(self.calculateFailed)
        except Exception:
            log_msg = f"{sys.exc_info()[1]}. stop"
            logging.info(log_msg)
        return

    def onCancel(self):
        """Notify the calculation thread that the user has cancelled the calculation.
        """
        self.cancelCalculation = True
        self.cmdCompute.setEnabled(False) # don't allow user to start a new calculation until this one finishes cancelling

    def _update(self, time=None, percentage=None):
        """
        Copied from previous version
        """
        if percentage is not None:
            msg = "%d%% complete..." % int(percentage)
        else:
            msg = "Computing..."
        logging.info(msg)

    def calculateFailed(self, reason):
        """
        """
        print("Calculate Failed with:\n", reason)
        pass

    def calculateComplete(self, d):
        """
        Notify the main thread
        """
        self.calculationFinishedSignal.emit()

    def complete(self, input, update=None):
        """Carry out the compuation of I(qx, qy) in a new thread

        Gen compute complete function

        This function separates the range of q or (qx,qy) into chunks and then
        calculates each chunk with calls to the model.

        :param input: input list [qx_data, qy_data, i_out]
        :type input: list
        """
        timer = timeit.default_timer
        update_rate = 1.0       # seconds between updates
        next_update = timer() + update_rate if update is not None else numpy.inf
        nq = len(input[0])
        chunk_size = 32 if self.is_avg else 256
        out = []
        # the 1D AUSAXS calculator cannot be chunked
        if self.is_avg and not len(input[1]):
            self.data_to_plot = self.model.runXY(input)

        # chunk the other calculations to allow cancellation
        else:
            for ind in range(0, nq, chunk_size):
                t = timer()
                if t > next_update:
                    update(time=t, percentage=100*ind/nq)
                    time.sleep(0.01)
                    next_update = t + update_rate
                if self.is_avg:
                    inputi = [input[0][ind:ind + chunk_size], []]
                    outi = self.model.run(inputi)
                else:
                    inputi = [input[0][ind:ind + chunk_size],
                            input[1][ind:ind + chunk_size]]
                    outi = self.model.runXY(inputi)
                out.append(outi)
                if self.cancelCalculation:
                    update(time=t, percentage=100*(ind + chunk_size)/nq) # ensure final progress shown
                    self.data_to_plot = numpy.full(nq, numpy.nan)
                    self.data_to_plot[:ind + chunk_size] = numpy.hstack(out)
                    logging.info('Gen computation cancelled.')
                    break
            else:
                out = numpy.hstack(out)
                self.data_to_plot = out
                logging.info('Gen computation completed.')

        # if Beta(Q) Calculation has been requested, run calculation
        if self.is_beta:
            self.data_betaQ  = create_beta_plot(self.xValues, self.nuc_sld_data, self.data_to_plot)

        if self.checkboxPluginModel.isChecked():
            self.fQ = f_of_q(self.xValues, self.nuc_sld_data)
            model_str, model_path = gsc_model.generate_plugin(self.txtFileName.text(), self.data_to_plot, self.xValues,
                                                              self.fQ, self.rGMass)
            TabbedModelEditor.writeFile(model_path, model_str)
            self.manager.communicate.customModelDirectoryChanged.emit()

            # Notify the user
            msg = "Custom model " + str(model_path.absolute()) + " successfully created."
            logging.info(msg)

        self.cmdCompute.setText('Compute')
        self.cmdCompute.setToolTip("<html><head/><body><p>Compute the scattering pattern and display 1D or 2D plot depending on the settings.</p></body></html>")
        self.cmdCompute.clicked.disconnect()
        self.cmdCompute.clicked.connect(self.onCompute)
        self.cmdCompute.setEnabled(True)
        return

    def hideWindow(self):
        """
        Hide the window when the close button is clicked
        """
        self.hide()

    def closeEvent(self, event):
        """
        Overwrite the close event and hide the window instead of closing it
        """
        self.hideWindow()
        # Clear the status bar
        self.communicator.statusBarUpdateSignal.emit("")
        event.ignore()

    def update_file_name(self):
        if self.checkboxPluginModel.isChecked():
            self.txtFileName.setText(self.getFileName())
            self.txtFileName.setEnabled(True)
        else:
            self.txtFileName.setText("")
            self.txtFileName.setEnabled(False)

    def getFileName(self):
        plugin_location = models.find_plugins_dir()
        i = 0
        while True:
            full_path = os.path.join(plugin_location, "custom_gsc" + str(i))
            if os.path.splitext(full_path)[1] != ".py":
                full_path += ".py"
            if not os.path.exists(full_path):
                break
            else:
                i += 1

        return ("custom_gsc" + str(i))


    def onSaveFile(self):
        """Save data as .sld file"""
        path = os.path.dirname(str(self.datafile))
        default_name = os.path.join(path, 'sld_file')
        parent = self
        directory =  default_name
        filter = 'SLD file (*.sld)'
        # Query user for filename.
        filename_tuple = QtWidgets.QFileDialog.getSaveFileName(parent, 'Save SLD file', directory, filter, "")
        filename = filename_tuple[0]
        if filename:
            try:
                _, extension = os.path.splitext(filename)
                if not extension:
                    filename = '.'.join((filename, 'sld'))
                sld_data = self.create_full_sld_data()
                sas_gen.SLDReader().write(filename, sld_data)
            except Exception:
                raise

    def file_name(self):
        """Creates a suitable filename for display on graphs depending on which files are enabled

        :return: the filename
        :rtype: str
        """
        if self.is_nuc:
            if self.is_mag:
                if self.nuc_sld_data.filename == self.mag_sld_data.filename:
                    return self.nuc_sld_data.filename
                else:
                    return self.nuc_sld_data.filename + " & " + self.mag_sld_data.filename
            else:
                return self.nuc_sld_data.filename
        else:
            if self.is_mag:
                return self.mag_sld_data.filename
            else:
                return "Rectangular grid from GUI"


    def plot3d(self, has_arrow=False):
        """ Generate 3D plot in real space with or without arrows

        :param has_arrow: Whether to plot arrows for the magnetic field on the plot.
            Defaults to `False`
        :type has_arrow: bool
        """
        sld_data = self.create_full_sld_data()
        self.write_new_values_from_gui()
        graph_title = f" Graph {self.graph_num}: {self.file_name()} 3D SLD Profile"
        if has_arrow:
            graph_title += ' - Magnetic Vector as Arrow'

        plot3D = Plotter3D(self, self, graph_title)
        plot3D.plot(sld_data, has_arrow=has_arrow)
        plot3D.show()

        self.plot3ds.append(plot3D)

        self.graph_num += 1

    def plot_1_2d(self):
        """ Generate 1D or 2D plot, called in Compute"""
        if self.is_avg or self.is_avg is None:
            data = Data1D(x=self.data.x, y=self.data_to_plot)
            data.title = f"GenSAS {self.file_name()}  #{int(self.graph_num)} 1D"
            data.xaxis(r'\rm{Q_{x}}', r'\AA^{-1}')
            data.yaxis(r'\rm{Intensity}', 'cm^{-1}')
            data.id = data.title # required for serialization

            self.graph_num += 1
            if self.is_beta:
                dataBetaQ = Data1D(x=self.data.x, y=self.data_betaQ)
                dataBetaQ.title = f"GenSAS {self.file_name()}  #{int(self.graph_num)} BetaQ"
                dataBetaQ.xaxis(r'\rm{Q_{x}}', r'\AA^{-1}')
                dataBetaQ.yaxis(r'\rm{Beta(Q)}', 'cm^{-1}')
                dataBetaQ.id = dataBetaQ.title # required for serialization

                self.graph_num += 1
        else:
            data = Data2D(image=numpy.nan_to_num(self.data_to_plot),
                          qx_data=self.data.qx_data,
                          qy_data=self.data.qy_data,
                          q_data=self.data.q_data,
                          xmin=self.data.xmin, xmax=self.data.ymax,
                          ymin=self.data.ymin, ymax=self.data.ymax,
                          err_image=self.data.err_data)
            data.title = f"GenSAS {self.file_name()}  #{int(self.graph_num)} 2D"
            data.id = f"gsc_2d_{self.graph_num}" # required for serialization
            zeros = numpy.ones(data.data.size, dtype=bool)
            data.mask = zeros
            data.xmin = self.data.xmin
            data.xmax = self.data.xmax
            data.ymin = self.data.ymin
            data.ymax = self.data.ymax

            self.graph_num += 1
            # TODO
        new_item = GuiUtils.createModelItemWithPlot(data, name=data.title)
        self.communicator.updateModelFromPerspectiveSignal.emit(new_item)
        self.communicator.forcePlotDisplaySignal.emit([new_item, data])
        if self.is_beta:
            new_item = GuiUtils.createModelItemWithPlot(dataBetaQ, name=dataBetaQ.title)
            self.communicator.updateModelFromPerspectiveSignal.emit(new_item)
            self.communicator.forcePlotDisplaySignal.emit([new_item, dataBetaQ])

class Plotter3DWidget(PlotterBase):
    """
    3D Plot widget for use with a QDialog
    """
    def __init__(self, parent=None, parent_window=None, manager=None):
        super(Plotter3DWidget, self).__init__(parent,  manager=manager)
        self.parent_window = parent_window

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data=None):
        """ data setter """
        self._data = data

    def plot(self, data=None, has_arrow=False):
        """
        Plot 3D self._data
        """
        if not data:
            return
        self.data = data
        # assert(self._data)
        # Prepare and show the plot
        self.showPlot(data=self.data, has_arrow=has_arrow)

    def showPlot(self, data, has_arrow=False):
        """
        Render and show the current data
        """
        # If we don't have any data, skip.
        if data is None:
            return
        # This import takes forever - place it here so the main UI starts faster
        from mpl_toolkits.mplot3d import Axes3D
        color_dic = {'H': 'blue', 'D': 'purple', 'N': 'orange',
                     'O': 'red', 'C': 'green', 'P': 'cyan', 'Other': 'k'}
        marker = ','
        m_size = 2

        pos_x = data.pos_x
        pos_y = data.pos_y
        pos_z = data.pos_z
        sld_mx = data.sld_mx
        sld_my = data.sld_my
        sld_mz = data.sld_mz
        sld_tot = numpy.fabs(sld_mx) + numpy.fabs(sld_my) + \
                numpy.fabs(sld_mz) + numpy.fabs(data.sld_n)
        if data.is_elements: # Do not assign values to points if values are element-wise
            is_nonzero = numpy.ones_like(pos_x, dtype=bool)
            is_zero = numpy.zeros_like(pos_x, dtype=bool)
        else:
            is_nonzero = sld_tot > 0.0
            is_zero = sld_tot == 0.0
        pix_symbol = data.pix_symbol

        if data.pix_type == 'atom':
            marker = 'o'
            m_size = 3.5

        self.figure.clear()
        self.figure.subplots_adjust(left=0.1, right=.8, bottom=.1)
        ax = Axes3D(self.figure, auto_add_to_figure=False)
        self.figure.add_axes(ax)
        ax.set_xlabel(rf'x ($\A{data.pos_unit}$)')
        ax.set_ylabel(rf'z ($\A{data.pos_unit}$)')
        ax.set_zlabel(rf'y ($\A{data.pos_unit}$)')

        # I. Plot null points
        if is_zero.any():
            im = ax.plot(pos_x[is_zero], pos_z[is_zero], pos_y[is_zero],
                           marker, c="y", alpha=0.5, markeredgecolor='y',
                           markersize=m_size)
            pos_x = pos_x[is_nonzero]
            pos_y = pos_y[is_nonzero]
            pos_z = pos_z[is_nonzero]
            sld_mx = sld_mx[is_nonzero]
            sld_my = sld_my[is_nonzero]
            sld_mz = sld_mz[is_nonzero]
            pix_symbol = data.pix_symbol[is_nonzero]
        # II. Plot selective points in color
        other_color = numpy.ones(len(pix_symbol), dtype='bool')
        for key in list(color_dic.keys()):
            chosen_color = pix_symbol == key
            if numpy.any(chosen_color):
                other_color = other_color & (chosen_color != True)
                color = color_dic[key]
                im = ax.plot(pos_x[chosen_color], pos_z[chosen_color],
                         pos_y[chosen_color], marker, c=color, alpha=0.5,
                         markeredgecolor=color, markersize=m_size, label=key)
        # III. Plot All others
        if numpy.any(other_color):
            a_name = ''
            if data.pix_type == 'atom':
                # Get atom names not in the list
                a_names = [symb for symb in pix_symbol \
                           if symb not in list(color_dic.keys())]
                a_name = a_names[0]
                for name in a_names:
                    new_name = ", " + name
                    if a_name.count(name) == 0:
                        a_name += new_name
            # plot in black
            ax.plot(pos_x[other_color], pos_z[other_color],
                    pos_y[other_color], marker, c="k", alpha=0.5,
                    markeredgecolor="k", markersize=m_size, label=a_name)
        if data.pix_type == 'atom':
            ax.legend(loc='upper left', prop={'size': 10})
        # IV. Draws atomic bond with grey lines if any
        if data.has_conect:
            for ind in range(len(data.line_x)):
                ax.plot(data.line_x[ind], data.line_z[ind],
                        data.line_y[ind], '-', lw=0.6, c="grey",
                        alpha=0.3)
        # V. Draws magnetic vectors
        if has_arrow and len(pos_x) > 0:
            def _draw_arrow(input=None, update=None):
                """
                draw magnetic vectors w/arrow
                """
                max_mx = max(numpy.fabs(sld_mx))
                max_my = max(numpy.fabs(sld_my))
                max_mz = max(numpy.fabs(sld_mz))
                max_m = max(max_mx, max_my, max_mz)
                if data.xstepsize is None or data.ystepsize is None or data.zstepsize is None:
                    if data.is_elements:
                        vol_per_element = numpy.sum(data.vol_pix)/len(data.elements)
                    else:
                        vol_per_element = numpy.sum(data.vol_pix)/len(data.pos_x)
                    max_step = numpy.cbrt(vol_per_element)
                else:
                    max_step = max(data.xstepsize, data.ystepsize, data.zstepsize)
                    if max_step <= 0:
                        max_step = 5
                try:
                    if max_m != 0:
                        unit_x2 = sld_mx / max_m
                        unit_y2 = sld_my / max_m
                        unit_z2 = sld_mz / max_m
                        # 0.8 is for avoiding the color becomes white=(1,1,1))
                        color_x = numpy.fabs(unit_x2 * 0.8)
                        color_y = numpy.fabs(unit_y2 * 0.8)
                        color_z = numpy.fabs(unit_z2 * 0.8)
                        if data.is_elements: # convert positions to match elements
                            # TODO: pos_x does not exist within the function - have to relocate from data, sld_mx etc. do carry through, why?
                            if data.are_elements_array:
                                vertices = numpy.unique(data.elements.reshape((data.elements.shape[0], -1)), axis=-1)
                                pos_x = numpy.mean(data.pos_x[vertices], axis=-1)
                                pos_y = numpy.mean(data.pos_y[vertices], axis=-1)
                                pos_z = numpy.mean(data.pos_z[vertices], axis=-1)
                            else:
                                vertices = [list(set([vertex for face in element for vertex in face])) for element in data.elements]
                                pos_x = numpy.array([numpy.mean([data.pos_x[vertex] for vertex in element]) for element in vertices])
                                pos_y = numpy.array([numpy.mean([data.pos_y[vertex] for vertex in element]) for element in vertices])
                                pos_z = numpy.array([numpy.mean([data.pos_z[vertex] for vertex in element]) for element in vertices])
                        x2 = pos_x + unit_x2 * max_step
                        y2 = pos_y + unit_y2 * max_step
                        z2 = pos_z + unit_z2 * max_step
                        x_arrow = numpy.column_stack((pos_x, x2))
                        y_arrow = numpy.column_stack((pos_y, y2))
                        z_arrow = numpy.column_stack((pos_z, z2))
                        colors = numpy.column_stack((color_x, color_y, color_z))
                        arrows = Arrow3D(self.figure, x_arrow, z_arrow, y_arrow,
                                        colors, mutation_scale=10, lw=1,
                                        arrowstyle="->", alpha=0.5)
                        ax.add_artist(arrows)
                except Exception:
                    pass

                log_msg = "Arrow Drawing completed.\n"
                logging.info(log_msg)

            log_msg = "Arrow Drawing is in progress..."
            logging.info(log_msg)

            # Defer the drawing of arrows to another thread
            d = threads.deferToThread(_draw_arrow, ax)

        self.figure.canvas.resizing = False
        self.figure.canvas.draw()

        self.parent_window.setFocus()
        self.setFocus()

    def createContextMenu(self):
        """
        Define common context menu and associated actions for the MPL widget
        """
        self.defaultContextMenu()

    def createContextMenuQuick(self):
        """
        Define context menu and associated actions for the quickplot MPL widget
        """
        return

    def closeEvent(self, event):
        """
        Overwrite the close event adding helper notification
        """
        event.accept()


class Plotter3D(QtWidgets.QDialog, Plotter3DWidget):
    def __init__(self, gsc_instance: GenericScatteringCalculator | None, parent=None, graph_title=''):
        self.graph_title = graph_title
        Plotter3DWidget.__init__(self, parent_window=self, manager=parent)
        self.setWindowTitle(self.graph_title)
        self.gsc_instance = gsc_instance

        icon = QIcon()
        icon.addFile(":/res/ball.ico", QSize(), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        # Make sure we remove reference to this plot so that it can be garbage collected

        if self.gsc_instance is not None:
            self.gsc_instance.plot3ds.remove(self)

        event.accept()
