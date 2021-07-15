import sys
import os
import numpy
import logging
import time
import timeit

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from twisted.internet import threads

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.GenericReader import GenReader
from sas.sascalc.dataloader.data_info import Detector
from sas.sascalc.dataloader.data_info import Source
from sas.sascalc.calculator import sas_gen
from sas.qtgui.Plotting.PlotterBase import PlotterBase
from sas.qtgui.Plotting.Plotter2D import Plotter2D
from sas.qtgui.Plotting.Plotter import Plotter

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D

# Local UI
from .UI.GenericScatteringCalculator import Ui_GenericScatteringCalculator

_Q1D_MIN = 0.001


class GenericScatteringCalculator(QtWidgets.QDialog, Ui_GenericScatteringCalculator):

    trigger_plot_3d = QtCore.pyqtSignal()
    calculationFinishedSignal = QtCore.pyqtSignal()
    loadingFinishedSignal = QtCore.pyqtSignal(list, bool)

    def __init__(self, parent=None):
        super(GenericScatteringCalculator, self).__init__()
        self.setupUi(self)
        # disable the context help icon
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        self.manager = parent
        self.communicator = self.manager.communicator()
        self.model = sas_gen.GenSAS()
        self.omf_reader = sas_gen.OMFReader()
        self.sld_reader = sas_gen.SLDReader()
        self.pdb_reader = sas_gen.PDBReader()
        self.reader = None
        #sld data for nuclear and magnetic cases
        self.nuc_sld_data = None
        self.mag_sld_data = None
        #verification information to avoid recalculating
        #verification carried out whenever files are selected/deselected
        #verification reset whenever a new files loaded
        self.verification_occurred = False # has verification happened on these files
        self.verified = False # was the verification successsful
        # verification error label
        #prevent layout shifting when widget hidden (could this be placed i nthe .ui file?)
        sizePolicy = self.lblVerifyError.sizePolicy()
        sizePolicy.setRetainSizeWhenHidden(True)
        self.lblVerifyError.setSizePolicy(sizePolicy)
        self.lblVerifyError.setVisible(False)

        self.parameters = []
        self.data = None
        self.datafile = None
        self.file_name = ''
        self.ext = None
        self.default_shape = str(self.cbShape.currentText())
        self.is_avg = False
        self.is_nuc = False
        self.is_mag = False
        self.data_to_plot = None
        self.graph_num = 1  # index for name of graph

        # combox box
        self.cbOptionsCalc.currentIndexChanged.connect(self.change_is_avg)
        #prevent layout shifting when widget hidden (could this be placed i nthe .ui file?)
        sizePolicy = self.cbOptionsCalc.sizePolicy()
        sizePolicy.setRetainSizeWhenHidden(True)
        self.cbOptionsCalc.setSizePolicy(sizePolicy)


        # push buttons
        self.cmdClose.clicked.connect(self.accept)
        self.cmdHelp.clicked.connect(self.onHelp)

        self.cmdNucLoad.clicked.connect(lambda: self.loadFile(load_nuc=True))
        self.cmdMagLoad.clicked.connect(lambda: self.loadFile(load_nuc=False))
        self.cmdCompute.clicked.connect(self.onCompute)
        self.cmdReset.clicked.connect(self.onReset)
        self.cmdSave.clicked.connect(self.onSaveFile)

        #checkboxes
        self.checkboxNucData.stateChanged.connect(self.change_data_type)
        self.checkboxMagData.stateChanged.connect(self.change_data_type)

        self.cmdDraw.clicked.connect(lambda: self.plot3d(has_arrow=True))
        self.cmdDrawpoints.clicked.connect(lambda: self.plot3d(has_arrow=False))

        #update pixel no./total volume when changed in GUI
        self.txtXnodes.textChanged.connect(self.update_geometry_effects)
        self.txtYnodes.textChanged.connect(self.update_geometry_effects)
        self.txtZnodes.textChanged.connect(self.update_geometry_effects)
        self.txtXstepsize.textChanged.connect(self.update_geometry_effects)
        self.txtYstepsize.textChanged.connect(self.update_geometry_effects)
        self.txtZstepsize.textChanged.connect(self.update_geometry_effects)

        #setup initial configuration
        self.checkboxNucData.setEnabled(False)
        self.checkboxMagData.setEnabled(False)
        self.change_data_type()

        # validators
        # scale, volume and background must be positive
        validat_regex_pos = QtCore.QRegExp('^[+]?([.]\d+|\d+([.]\d+)?)$')
        self.txtScale.setValidator(QtGui.QRegExpValidator(validat_regex_pos,
                                                          self.txtScale))
        self.txtBackground.setValidator(QtGui.QRegExpValidator(
            validat_regex_pos, self.txtBackground))
        self.txtTotalVolume.setValidator(QtGui.QRegExpValidator(
            validat_regex_pos, self.txtTotalVolume))

        # fraction of spin up between 0 and 1
        validat_regexbetween0_1 = QtCore.QRegExp('^(0(\.\d*)*|1(\.0+)?)$')
        self.txtUpFracIn.setValidator(
            QtGui.QRegExpValidator(validat_regexbetween0_1, self.txtUpFracIn))
        self.txtUpFracOut.setValidator(
            QtGui.QRegExpValidator(validat_regexbetween0_1, self.txtUpFracOut))

        # angles, SLD must be float values
        validat_regex_float = QtCore.QRegExp('[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)')
        self.txtUpTheta.setValidator(
            QtGui.QRegExpValidator(validat_regex_float, self.txtUpTheta))
        self.txtUpPhi.setValidator(
            QtGui.QRegExpValidator(validat_regex_float, self.txtUpPhi))

        self.txtSolventSLD.setValidator(
            QtGui.QRegExpValidator(validat_regex_float, self.txtSolventSLD))
        self.txtNucl.setValidator(
            QtGui.QRegExpValidator(validat_regex_float, self.txtNucl))        

        self.txtMx.setValidator(
            QtGui.QRegExpValidator(validat_regex_float, self.txtMx))
        self.txtMy.setValidator(
            QtGui.QRegExpValidator(validat_regex_float, self.txtMy))
        self.txtMz.setValidator(
            QtGui.QRegExpValidator(validat_regex_float, self.txtMz))                

        self.txtXstepsize.setValidator(
            QtGui.QRegExpValidator(validat_regex_float, self.txtXstepsize))
        self.txtYstepsize.setValidator(
            QtGui.QRegExpValidator(validat_regex_float, self.txtYstepsize))
        self.txtZstepsize.setValidator(
            QtGui.QRegExpValidator(validat_regex_float, self.txtZstepsize))            

        # 0 < Qmax <= 1000
        validat_regex_q = QtCore.QRegExp('^1000$|^[+]?(\d{1,3}([.]\d+)?)$')
        self.txtQxMax.setValidator(QtGui.QRegExpValidator(validat_regex_q,
                                                          self.txtQxMax))
        #check for max q cut-off
        self.txtQxMax.textChanged.connect(self.check_value) 

        # 2 <= Qbin and nodes integers < 1000
        validat_regex_int = QtCore.QRegExp('^[1-9]\d{3}$')        
        self.txtNoQBins.setValidator(QtGui.QRegExpValidator(validat_regex_int,
                                                            self.txtNoQBins))
        #check for min q resolution
        self.txtNoQBins.textChanged.connect(self.check_value) 

        self.txtXnodes.setValidator(
            QtGui.QRegExpValidator(validat_regex_int, self.txtXnodes))
        self.txtYnodes.setValidator(
            QtGui.QRegExpValidator(validat_regex_int, self.txtYnodes))
        self.txtZnodes.setValidator(
            QtGui.QRegExpValidator(validat_regex_int, self.txtZnodes))         

        # plots - 3D in real space
        self.trigger_plot_3d.connect(lambda: self.plot3d(has_arrow=False))

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

    def selectedshapechange(self):
        """
        TODO Temporary solution to display information about option 'Ellipsoid'
        """
        print("The option Ellipsoid has not been implemented yet.")
        self.communicator.statusBarUpdateSignal.emit(
            "The option Ellipsoid has not been implemented yet.")

    def disable_verification_error_functionality(self, msg=None):
        """Disables some functionality if verification fails.

        This function is called during the verification process for combining
        two different files for nuclear and magnetic data. It is called when
        verification fails, in order to disable the functionality of the GUI
        which requires the files to be compatible (save, draw and compute). It
        also optionally alters the error message for the user.

        :param msg: The error message which should be displayed to the user on
            the GUI. Defaults to `None` in which case the error message is not
            changed.
        :type msg: str or None
        """
        #disable necessary buttons to prevent the attempted merging of incompatible files
        self.cmdDraw.setEnabled(False)
        self.cmdDrawpoints.setEnabled(False)
        self.cmdSave.setEnabled(False)
        self.cmdCompute.setEnabled(False)
        #alter the error message if a new message is provided
        #verification is only carried out once so if msg=None do not set the msg to ""
        #   but simply don't alter it - this means the message is preserved and re-verification
        #   is not called when the files have not been changed
        if msg is not None:
            self.lblVerifyError.setText('<font color="#FF0000">' + msg + '</font>')
        #display the message
        self.lblVerifyError.setVisible(True)

    def enable_verification_error_functionality(self):
        """(Re-)enables some functionality if verification succeeds or is unnecessary

        This function is called during the verification process for combining
        two different files for nuclear and magnetic data. It is called when
        verification succeeds, or is no longer necessary as fewer than two files are
        now under consideration. It re-enables all of the functionality disabled
        by disable_verification_error_functionality(), i.e. save, draw and compute.
        It also hides the error message from the user.
        """
        #reenable necessary buttons
        self.cmdDraw.setEnabled(True)
        self.cmdDrawpoints.setEnabled(True)
        self.cmdSave.setEnabled(True)
        self.cmdCompute.setEnabled(True)
        #hide error message
        self.lblVerifyError.setVisible(False)

    def verify_files_match(self):
        """Verifies that enabled files are compatible and can be combined

        When the user wishes to combine two different files for nuclear and magnetic
        data they must have the same 3D data points in real-space. This function
        decides whther verification of this is necessary and if so carries it out.
        In the case that the two files have the same real-space data points in different
        orders this function re-orders the stored data within the MagSLD objects to make
        them align. The full verification is only carried out once for any pair of loaded
        files.
        """
        if not (self.is_mag and self.is_nuc):
            #no conflicts if only 1/0 file(s) loaded - therefore restore functionality
            self.enable_verification_error_functionality()
            return
        # check if files already verified
        if self.verification_occurred:
            if self.verified:
                self.enable_verification_error_functionality()
            else:
                self.disable_verification_error_functionality()
            return
        # check each file has the same number of coords
        if self.nuc_sld_data.pos_x.size != self.mag_sld_data.pos_x.size:
            self.disable_verification_error_functionality("ERROR: files have a different number of data points")
            self.verification_occurred = True
            self.verified = False
            return
        #check the coords match up 1-to-1
        nuc_coords = numpy.array(numpy.column_stack((self.nuc_sld_data.pos_x, self.nuc_sld_data.pos_y, self.nuc_sld_data.pos_z)))
        mag_coords = numpy.array(numpy.column_stack((self.mag_sld_data.pos_x, self.mag_sld_data.pos_y, self.mag_sld_data.pos_z)))
        if numpy.array_equal(nuc_coords, mag_coords): #should this have a floating point tolerance??
            #arrays are already sorted in the same order, so files match
            self.enable_verification_error_functionality()
            self.verification_occurred = True
            self.verified = True
            return
        # now check if coords are in wrong order or don't match
        nuc_sort_order = numpy.lexsort((self.nuc_sld_data.pos_z, self.nuc_sld_data.pos_y, self.nuc_sld_data.pos_x))
        mag_sort_order = numpy.lexsort((self.mag_sld_data.pos_z, self.mag_sld_data.pos_y, self.mag_sld_data.pos_x))
        nuc_coords = nuc_coords[nuc_sort_order]
        mag_coords = mag_coords[mag_sort_order]
        #check if sorted data points are equal
        if numpy.array_equal(nuc_coords, mag_coords):
            #if data points are equal then resort both lists into the same order
            #is this too time consuming for long lists? logging info?
            #1) coords
            self.nuc_sld_data.pos_x, self.nuc_sld_data.pos_y, self.nuc_sld_data.pos_z = numpy.hsplit(nuc_coords, 3)
            self.mag_sld_data.pos_x, self.mag_sld_data.pos_y, self.mag_sld_data.pos_z = numpy.hsplit(mag_coords, 3)
            #2) other array params that must be in same order as coords
            params = ["sld_n", "sld_mx", "sld_my", "sld_mz", "vol_pix", "pix_symbol"]
            for item in params:
                nuc_val = getattr(self.nuc_sld_data, item)
                if nuc_val is not None:
                    #data should already be a numpy array, we cast to an ndarray as a check
                    #very fast if data is already an instance of ndarray as expected becuase function
                    #returns the array as-is
                    setattr(self.nuc_sld_data, item, numpy.asanyarray(nuc_val)[nuc_sort_order])
                mag_val = getattr(self.mag_sld_data, item)
                if nuc_val is not None:
                    setattr(self.mag_sld_data, item, numpy.asanyarray(mag_val)[mag_sort_order])
            #Do NOT need to edit CONECT data (line_x, line_y, line_z as these lines are given by
            #absolute positions not references to pos_x, pos_y, pos_z).
            self.enable_verification_error_functionality()
            self.verification_occurred = True
            self.verified = True
            return
        else:
            # if sorted lists not equal then data points aren't equal
            self.disable_verification_error_functionality("ERROR: files have different real space position data")
            self.verification_occurred = True
            self.verified = False
            return
        

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
        #update information on which files are enabled
        self.is_nuc = self.checkboxNucData.isChecked()
        self.is_mag = self.checkboxMagData.isChecked()
        #enable the corresponding text displays to show this to the user clearly
        self.txtNucData.setEnabled(self.is_nuc)
        self.txtMagData.setEnabled(self.is_mag)
        #only allow editing of mean values if no data file for that vlaue has been loaded
        #user provided mean values are taken as a constant across all points
        self.txtMx.setEnabled(not self.is_mag)
        self.txtMy.setEnabled(not self.is_mag)
        self.txtMz.setEnabled(not self.is_mag)
        self.txtNucl.setEnabled(not self.is_nuc)
        #The ability to change the number of nodes and stepsizes only if no laoded data file enabled
        both_disabled =  (not self.is_mag) and (not self.is_nuc)
        self.txtXnodes.setEnabled(both_disabled)
        self.txtYnodes.setEnabled(both_disabled)
        self.txtZnodes.setEnabled(both_disabled)
        self.txtXstepsize.setEnabled(both_disabled)
        self.txtYstepsize.setEnabled(both_disabled)
        self.txtZstepsize.setEnabled(both_disabled)
        #Only allow 1D averaging if no magnetic data
        self.cbOptionsCalc.setVisible(not self.is_mag)
        if (not self.is_mag):
            #A helper function to set up the averaging system
            self.change_is_avg()
        else:
            #If magnetic data present then no averaging is allowed
            self.is_avg = False
        # update the gui with new values - sets the average values from enabled files
        self.update_gui()
        # verify that the new enabled files are compatible
        self.verify_files_match()
        
    def change_is_avg(self):
        """Adjusts the GUI for whether 1D averaging is enabled

        If the user has chosen to carry out Debye full averaging then the magnetic sld
        values must be set to 0, and made uneditable - because the calculator in geni.py
        is incapable of averaging systems with non-zero magnetic slds or polarisation.

        This function is called whenever different files are enabled or the user edits the
        averaging combobox.
        """
        #update the averaging option fromthe button on the GUI
        #required as the button may have been previously hidden with
        #any value, and preserves this - we must update the variable to match the GUI
        self.is_avg = (self.cbOptionsCalc.currentIndex() == 1)
        #If averaging then set to 0 and diable the magnetic SLD textboxes
        if self.is_avg:
            self.txtMx.setEnabled(False)
            self.txtMy.setEnabled(False)
            self.txtMz.setEnabled(False)
            self.txtMx.setText("0")
            self.txtMy.setText("0")
            self.txtMz.setText("0")
        #If not averaging then re-enable the magnetic sld textboxes
        else:
            self.txtMx.setEnabled(True)
            self.txtMy.setEnabled(True)
            self.txtMz.setEnabled(True)

    def loadFile(self, load_nuc=True):
        """Opens a menu to choose the datafile to load

        Opens a file dialog to allow the user to select a datafile to be loaded.
        If a nuclear sld datafile is loaded then the allowed file types are:
            .SLD .sld .PDB .pdb
        If a magnetic sld datafile is loaded then the allowed file types are:
            .SLD .sld .OMF .omf
        This function then loads in the requested datafile, but does not enable it.
        If no previous datafile of this type was loaded then the checkbox to enable
        this file is enabled.

        :param load_nuc: Specifies whether the loaded file is nuclear or magnetic
            data. Defaults to `True`.
            `load_nuc=True` gives nuclear sld data.
            `load_nuc=False` gives magnetic sld data.
        :type load_nuc: bool
        """
        try:
            #request a file from the user
            if load_nuc:
                self.datafile = QtWidgets.QFileDialog.getOpenFileName(
                    self, "Choose a file", "","All supported files (*.SLD *.sld *.pdb *.PDB);;"
                                            "SLD files (*.SLD *.sld);;"
                                            "PDB files (*.pdb *.PDB);;"
                                            "All files (*.*)")[0]
            else:
                self.datafile = QtWidgets.QFileDialog.getOpenFileName(
                    self, "Choose a file", "","All supported files (*.OMF *.omf *.SLD *.sld);;"
                                            "OMF files (*.OMF *.omf);;"
                                            "SLD files (*.SLD *.sld);;"
                                            "All files (*.*)")[0]
            # If a file has been sucessfully chosen
            if self.datafile:
                #set basic data about the file
                self.default_shape = str(self.cbShape.currentText())
                self.file_name = os.path.basename(str(self.datafile))
                self.ext = os.path.splitext(str(self.datafile))[1]
                #select the required loader for the data format
                if self.ext in self.omf_reader.ext and (not load_nuc):
                    #only load omf files for magnetic data
                    loader = self.omf_reader
                elif self.ext in self.sld_reader.ext:
                    loader = self.sld_reader
                elif self.ext in self.pdb_reader.ext and load_nuc:
                    #only load pdb files for nuclear data
                    loader = self.pdb_reader
                else:
                    loader = None

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
        except (RuntimeError, IOError):
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
        all the data to instances of MagSLD and reporting any errors. Additionally verification
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
        try:
            is_pdbdata = False
            if load_nuc:
                self.txtNucData.setText(os.path.basename(str(self.datafile)))
            else:
                self.txtMagData.setText(os.path.basename(str(self.datafile)))
            if self.ext in self.omf_reader.ext:
                gen = sas_gen.OMF2SLD()
                gen.set_data(data)
                #only magnetic data can be read from omf files
                self.mag_sld_data = gen.get_magsld()
                self.check_units()
            elif self.ext in self.sld_reader.ext:
                if load_nuc:
                    self.nuc_sld_data = data
                else:
                    self.mag_sld_data = data
            elif self.ext in self.pdb_reader.ext:
                #only nuclear data can be read from pdb files
                self.nuc_sld_data = data
                is_pdbdata = True
        except IOError:
            log_msg = "Loading Error: " \
                      "This file format is not supported for GenSAS."
            logging.info(log_msg)
            raise
        except ValueError:
            log_msg = "Could not find any data"
            logging.info(log_msg)
            raise
        logging.info("Load Complete")
        self.cmdNucLoad.setEnabled(True)
        self.cmdNucLoad.setText('Load')
        self.cmdMagLoad.setEnabled(True)
        self.cmdMagLoad.setText('Load')
        self.cmdCompute.setEnabled(True)
        self.cmdCompute.setText('Compute')
        #Once data files are loaded allow them to be enabled
        if load_nuc:
            self.checkboxNucData.setEnabled(True)
        else:
            self.checkboxMagData.setEnabled(True)
        # update GUI if these files are already enabled
        if (load_nuc and self.is_nuc) or ((not load_nuc) and self.is_mag):
            self.update_gui()
        # reset verification now we have loaded new files
        self.verification_occurred = False
        self.verified = False
        self.verify_files_match()

    def check_units(self):
        """
        Check if the units from the OMF file correspond to the default ones
        displayed on the interface.
        If not, modify the GUI with the correct unit
        """
        #  TODO: adopt the convention of font and symbol for the updated values
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

    def check_value(self, update_all=False):
        """Check range of text edits for QMax and Number of Qbins
        
        This function checks that QMax and the number of Qbins is suitable
        given the user chosen values. Unlike the hard limits imposed by the
        regex, this does not prevent the user using the given value, but warns
        them that it may be unsuitable with a red back-color.

        :params update_all: If this value is set to true then both values will be checked
            verified - useful when the call is being made generally and not due to one of the
            values being changed by the user directly. Defaults to `False`
        :type update_all: bool
        """

        text_edit = self.sender()
        sld_data = self.create_full_sld_data()
        if update_all:
            self.txtQxMax.setStyleSheet('background-color: rgb(255, 255, 255);')
            self.txtNoQBins.setStyleSheet('background-color: rgb(255, 255, 255);')
        else:
            text_edit.setStyleSheet('background-color: rgb(255, 255, 255);')
        if (sld_data != None):
            if (text_edit == self.txtQxMax or update_all) and self.txtQxMax.text():
                value = float(str(self.txtQxMax.text()))
                max_q = numpy.pi / (max(sld_data.xstepsize, sld_data.ystepsize, sld_data.zstepsize) )                   
                if value <= 0 or value > max_q:
                    self.txtQxMax.setStyleSheet('background-color: rgb(255, 182, 193);')
                else:
                    self.txtQxMax.setStyleSheet('background-color: rgb(255, 255, 255);')
            if (text_edit == self.txtNoQBins or update_all) and self.txtNoQBins.text():
                value = float(str(self.txtNoQBins.text()))
                max_step =  3*max(sld_data.xnodes, sld_data.ynodes, sld_data.znodes) 
                    #limits qmin > maxq / nodes                 
                if value < 2 or value > max_step:
                    self.txtNoQBins.setStyleSheet('background-color: rgb(255, 182, 193);')
                else:
                    self.txtNoQBins.setStyleSheet('background-color: rgb(255, 255, 255);')

    def format_value(self, value):
        """Formats certain data for the GUI.
        
        Some data stored by the sld file is a numpy array - in which case the average is formatted.
        Other data is a single value in which case the value is formatted. The formatting is done
        by GuiUtils.formatNumber(). If the value is `None` then the string "NaN" is returned

        :param value: The value to be formatted
        :type value: int, float, numpy.array
        :return: The formatted value
        :rtype: str
        """
        if value is None:
            return "NaN"
        else:
            if isinstance(value, numpy.ndarray):
                value = str(GuiUtils.formatNumber(numpy.average(value), True))
            else:
                value = str(GuiUtils.formatNumber(value, True))
            return value

    def update_gui(self):
        """Update the interface and model with values from loaded data
        
        This function updates the model parameter 'total_volume' with values from the loaded data
        and then updates all values in the gui with either model paramters or paramaters from the
        loaded data.
        """
        if self.is_nuc:
            self.model.params['total_volume'] = len(self.nuc_sld_data.sld_n)*self.nuc_sld_data.vol_pix[0]
        elif self.is_mag:
            self.model.params['total_volume'] = len(self.mag_sld_data.sld_n)*self.mag_sld_data.vol_pix[0]
        else:
            # use same calculation of total volume as when converting OMF to SLD
            self.model.params['total_volume'] = (float(self.txtXstepsize.text()) * float(self.txtYstepsize.text())
                                                 * float(self.txtZstepsize.text()) * float(self.txtXnodes.text())
                                                 * float(self.txtYnodes.text()) * float(self.txtZnodes.text()))

        # add condition for activation of save button
        self.cmdSave.setEnabled(True)

        # activation of 3D plots' buttons (with and without arrows)

        self.txtScale.setText(str(self.model.params['scale']))
        self.txtBackground.setText(str(self.model.params['background']))
        self.txtSolventSLD.setText(str(self.model.params['solvent_SLD']))

        # Volume to write to interface: npts x volume of first pixel
        self.txtTotalVolume.setText(str(self.model.params['total_volume']))

        self.txtUpFracIn.setText(str(self.model.params['Up_frac_in']))
        self.txtUpFracOut.setText(str(self.model.params['Up_frac_out']))
        self.txtUpTheta.setText(str(self.model.params['Up_theta']))
        self.txtUpPhi.setText(str(self.model.params['Up_phi']))

        #update the number of pixels with values from the loaded data or GUI if no datafiles enabled
        if self.is_nuc:
            self.txtNoPixels.setText(str(len(self.nuc_sld_data.sld_n)))
        elif self.is_mag:
            self.txtNoPixels.setText(str(len(self.mag_sld_data.sld_mx)))
        else:
            self.txtNoPixels.setText(str(int(float(self.txtXnodes.text())
                                         * float(self.txtYnodes.text()) * float(self.txtZnodes.text()))))
        self.txtNoPixels.setEnabled(False)

        # Fill right hand side of GUI
        if self.is_mag:
            self.txtMx.setText(self.format_value(self.mag_sld_data.sld_mx))
            self.txtMy.setText(self.format_value(self.mag_sld_data.sld_my))
            self.txtMz.setText(self.format_value(self.mag_sld_data.sld_mz))
        if self.is_nuc:
            self.txtNucl.setText(self.format_value(self.nuc_sld_data.sld_n))
        if self.is_nuc:
            self.txtXnodes.setText(self.format_value(self.nuc_sld_data.xnodes))
            self.txtYnodes.setText(self.format_value(self.nuc_sld_data.ynodes))
            self.txtZnodes.setText(self.format_value(self.nuc_sld_data.znodes))
            self.txtXstepsize.setText(self.format_value(self.nuc_sld_data.xstepsize))
            self.txtYstepsize.setText(self.format_value(self.nuc_sld_data.ystepsize))
            self.txtZstepsize.setText(self.format_value(self.nuc_sld_data.zstepsize))
        if self.is_mag and ((not self.is_nuc) or self.txtXnodes.text() == "NaN"):
            # If unable to get node data from nuclear system (not enabled or not present)
            self.txtXnodes.setText(self.format_value(self.mag_sld_data.xnodes))
            self.txtYnodes.setText(self.format_value(self.mag_sld_data.ynodes))
            self.txtZnodes.setText(self.format_value(self.mag_sld_data.znodes))
            self.txtXstepsize.setText(self.format_value(self.mag_sld_data.xstepsize))
            self.txtYstepsize.setText(self.format_value(self.mag_sld_data.ystepsize))
            self.txtZstepsize.setText(self.format_value(self.mag_sld_data.zstepsize))
        #otherwise leave as set since editable by user

        #If nodes or stepsize changed then this may effect what values are allowed
        self.check_value(update_all=True)
    
    def update_geometry_effects(self):
        """This function updates the number of pixels and total volume when the number of nodes/stepsize is changed

        This function only has an effect if no files are enabled otherwise the number of pixels and total
        volume may be set differently by the data from the file.
        """
        if self.is_mag or self.is_nuc:
            #don't change the number if this is being set from a file as then the number of pixels may differ
            return
        if self.txtXnodes.text() == "" or self.txtYnodes.text() == "" or self.txtZnodes.text() == "":
            #do not try to update if textbox blank - this will throw an error in update_gui() anyway if left blank
            #user is most likely just removing the value to change it
            return
        self.txtNoPixels.setText(str(int(float(self.txtXnodes.text())
                                         * float(self.txtYnodes.text()) * float(self.txtZnodes.text()))))
        if self.txtXstepsize.text() == "" or self.txtYstepsize.text() == "" or self.txtZstepsize.text() == "":
            #do not try to update if textbox blank - this will throw an error in update_gui() anyway if left blank
            #user is most likely just removing the value to change it
            return
        self.model.params['total_volume'] = (float(self.txtXstepsize.text()) * float(self.txtYstepsize.text())
                                                 * float(self.txtZstepsize.text()) * float(self.txtXnodes.text())
                                                 * float(self.txtYnodes.text()) * float(self.txtZnodes.text()))
        self.txtTotalVolume.setText(str(self.model.params['total_volume']))
        #If nodes or stepsize changed then this may effect what values are allowed
        self.check_value(update_all=True)

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
            self.txtNoQBins.setText("50")
            self.txtQxMax.setText("0.3")
            self.txtNoPixels.setText("1000")
            self.txtMx.setText("0")
            self.txtMy.setText("0")
            self.txtMz.setText("0")
            self.txtNucl.setText("6.97e-06")
            self.txtXnodes.setText("10")
            self.txtYnodes.setText("10")
            self.txtZnodes.setText("10")
            self.txtXstepsize.setText("6")
            self.txtYstepsize.setText("6")
            self.txtZstepsize.setText("6")
            #re-enable any options disabled by failed verification
            self.verification_occurred = False
            self.verified = False
            self.enable_verification_error_functionality()
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
            #disable all file checkboxes, as no files are now loaded
            self.checkboxNucData.setEnabled(False)
            self.checkboxMagData.setEnabled(False)
            self.checkboxNucData.setChecked(False)
            self.checkboxMagData.setChecked(False)
            #reset all file data to its default empty state
            self.is_nuc = False
            self.is_mag = False
            self.nuc_sld_data = None
            self.mag_sld_data = None
            #update the gui for the no files loaded case
            self.change_data_type()


        finally:
            pass

    def _create_default_2d_data(self):
        """Create the 2D data range for qx,qy

        Copied from previous version
        Create 2D data by default

        :warning: This data is never plotted.
        """
        self.qmax_x = float(self.txtQxMax.text())
        self.npts_x = int(self.txtNoQBins.text())
        self.data = Data2D()
        self.data.is_data = False
        # # Default values
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

        :deprecated:
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

        :warning: This data is never plotted.

                    residuals.x = data_copy.x[index]
            residuals.dy = numpy.ones(len(residuals.y))
            residuals.dx = None
            residuals.dxl = None
            residuals.dxw = None
        """
        self.qmax_x = float(self.txtQxMax.text())
        self.npts_x = int(self.txtNoQBins.text())
        #  Default values
        xmax = self.qmax_x
        xmin = self.qmax_x * _Q1D_MIN
        qstep = self.npts_x
        x = numpy.linspace(start=xmin, stop=xmax, num=qstep, endpoint=True)
        # store x and y bin centers in q space
        y = numpy.ones(len(x))
        dy = numpy.zeros(len(x))
        dx = numpy.zeros(len(x))
        self.data = Data1D(x=x, y=y)
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
        #CARRY OUT COMPATIBILITY CHECK - ELSE RETURN None
        # Set default data when nothing loaded yet
        omfdata = sas_gen.OMFData()
        #load in user chosen position data
        #If no file given this will be used to generate the position data
        #Otherwise it is still used as part of the verification process in check_value()
        omfdata.xnodes = int(self.txtXnodes.text())
        omfdata.ynodes = int(self.txtYnodes.text())
        omfdata.znodes = int(self.txtZnodes.text())
        omfdata.xstepsize = float(self.txtXstepsize.text())
        omfdata.ystepsize = float(self.txtYstepsize.text())
        omfdata.zstepsize = float(self.txtZstepsize.text())
        #convert into sld format
        omf2sld = sas_gen.OMF2SLD()
        omf2sld.set_data(omfdata, self.default_shape)
        sld_data = omf2sld.get_output()

        #only to be done once - load in the position data of the atoms
        #verification ensures that this is the same across nuclear and magnetic datafiles
        if self.is_nuc:
            sld_data.vol_pix = self.nuc_sld_data.vol_pix
            sld_data.pos_x = self.nuc_sld_data.pos_x
            sld_data.pos_y = self.nuc_sld_data.pos_y
            sld_data.pos_z = self.nuc_sld_data.pos_z
        elif self.is_mag:
            sld_data.vol_pix = self.mag_sld_data.vol_pix
            sld_data.pos_x = self.mag_sld_data.pos_x
            sld_data.pos_y = self.mag_sld_data.pos_y
            sld_data.pos_z = self.mag_sld_data.pos_z

        #set the sld data from the required model file/GUI textbox
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
        #Provide data giving connections between atoms for 3D drawing
        #This SHOULD only occur in nuclear data files as it is a feature of
        #pdb files - however the option for it to be drawn from magnetic files
        #if present is given in case the sld file format is expanded to include them
        if self.is_nuc:
            if self.nuc_sld_data.has_conect:
                sld_data.has_conect=True
                sld_data.line_x = self.nuc_sld_data.line_x
                sld_data.line_y = self.nuc_sld_data.line_y
                sld_data.line_z = self.nuc_sld_data.line_z
            elif self.is_mag:
                if self.mag_sld_data.has_conect:
                    sld_data.has_conect=True
                    sld_data.line_x = self.mag_sld_data.line_x
                    sld_data.line_y = self.mag_sld_data.line_y
                    sld_data.line_z = self.mag_sld_data.line_z
        
        #take pixel data from nuclear sld as preference because may contatin atom types from pdb files
        if self.is_nuc:
            sld_data.pix_type = self.nuc_sld_data.pix_type
            sld_data.pix_symbol = self.nuc_sld_data.pix_symbol
        elif self.is_mag:
            sld_data.pix_type = self.mag_sld_data.pix_type
            sld_data.pix_symbol = self.mag_sld_data.pix_symbol

        return sld_data

    def onCompute(self):
        """Execute the computation of I(qx, qy)

        Copied from previous version
        """
        try:
            #create the combined sld data and update from gui
            sld_data = self.create_full_sld_data()
            self.model.set_sld_data(sld_data)
            self.write_new_values_from_gui()
            #create 2D or 1D data as appropriate
            if self.is_avg or self.is_avg is None:
                self._create_default_1d_data()
                inputs = [self.data.x, []]
            else:
                self._create_default_2d_data()
                inputs = [self.data.qx_data, self.data.qy_data]
            logging.info("Computation is in progress...")
            self.cmdCompute.setText('Wait...')
            self.cmdCompute.setEnabled(False)
            d = threads.deferToThread(self.complete, inputs, self._update)
            # Add deferred callback for call return
            #d.addCallback(self.plot_1_2d)
            d.addCallback(self.calculateComplete)
            d.addErrback(self.calculateFailed)
        except Exception:
            log_msg = "{}. stop".format(sys.exc_info()[1])
            logging.info(log_msg)
        return

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
        update_rate = 1.0 # seconds between updates
        next_update = timer() + update_rate if update is not None else numpy.inf
        nq = len(input[0])
        chunk_size = 32 if self.is_avg else 256
        out = []
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
        out = numpy.hstack(out)
        self.data_to_plot = out
        logging.info('Gen computation completed.')
        self.cmdCompute.setText('Compute')
        self.cmdCompute.setEnabled(True)
        return

    def onSaveFile(self):
        """Save data as .sld file"""
        path = os.path.dirname(str(self.datafile))
        default_name = os.path.join(path, 'sld_file')
        kwargs = {
            'parent': self,
            'directory': default_name,
            'filter': 'SLD file (*.sld)',
            'options': QtWidgets.QFileDialog.DontUseNativeDialog}
        # Query user for filename.
        filename_tuple = QtWidgets.QFileDialog.getSaveFileName(**kwargs)
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

    def plot3d(self, has_arrow=False):
        """ Generate 3D plot in real space with or without arrows
        
        :param has_arrow: Whether to plot arrows for the magnetic field on the plot.
            Defaults to `False`
        :type has_arrow: bool
        """
        sld_data = self.create_full_sld_data()
        self.write_new_values_from_gui()
        graph_title = " Graph {}: {} 3D SLD Profile".format(self.graph_num,
                                                            self.file_name)
        if has_arrow:
            graph_title += ' - Magnetic Vector as Arrow'

        plot3D = Plotter3D(self, graph_title)
        plot3D.plot(sld_data, has_arrow=has_arrow)
        plot3D.show()
        self.graph_num += 1

    def plot_1_2d(self):
        """ Generate 1D or 2D plot, called in Compute"""
        if self.is_avg or self.is_avg is None:
            data = Data1D(x=self.data.x, y=self.data_to_plot)
            data.title = "GenSAS {}  #{} 1D".format(self.file_name,
                                                    int(self.graph_num))
            data.xaxis('\\rm{Q_{x}}', '\AA^{-1}')
            data.yaxis('\\rm{Intensity}', 'cm^{-1}')

            self.graph_num += 1
        else:
            numpy.nan_to_num(self.data_to_plot)
            data = Data2D(image=self.data_to_plot,
                          qx_data=self.data.qx_data,
                          qy_data=self.data.qy_data,
                          q_data=self.data.q_data,
                          xmin=self.data.xmin, xmax=self.data.ymax,
                          ymin=self.data.ymin, ymax=self.data.ymax,
                          err_image=self.data.err_data)
            data.title = "GenSAS {}  #{} 2D".format(self.file_name,
                                                    int(self.graph_num))
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

class Plotter3DWidget(PlotterBase):
    """
    3D Plot widget for use with a QDialog
    """
    def __init__(self, parent=None, manager=None):
        super(Plotter3DWidget, self).__init__(parent,  manager=manager)

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
        #assert(self._data)
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
        pix_symbol = data.pix_symbol
        sld_tot = numpy.fabs(sld_mx) + numpy.fabs(sld_my) + \
                  numpy.fabs(sld_mz) + numpy.fabs(data.sld_n)
        is_nonzero = sld_tot > 0.0
        is_zero = sld_tot == 0.0

        if data.pix_type == 'atom':
            marker = 'o'
            m_size = 3.5

        self.figure.clear()
        self.figure.subplots_adjust(left=0.1, right=.8, bottom=.1)
        ax = Axes3D(self.figure)
        ax.set_xlabel('x ($\A{}$)'.format(data.pos_unit))
        ax.set_ylabel('z ($\A{}$)'.format(data.pos_unit))
        ax.set_zlabel('y ($\A{}$)'.format(data.pos_unit))

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
                other_color = other_color & (chosen_color!=True)
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
            im = ax.plot(pos_x[other_color], pos_z[other_color],
                         pos_y[other_color], marker, c="k", alpha=0.5,
                         markeredgecolor="k", markersize=m_size, label=a_name)
        if data.pix_type == 'atom':
            ax.legend(loc='upper left', prop={'size': 10})
        # IV. Draws atomic bond with grey lines if any
        if data.has_conect:
            for ind in range(len(data.line_x)):
                im = ax.plot(data.line_x[ind], data.line_z[ind],
                             data.line_y[ind], '-', lw=0.6, c="grey",
                             alpha=0.3)
        # V. Draws magnetic vectors
        if has_arrow and len(pos_x) > 0:
            def _draw_arrow(input=None, update=None):
                # import moved here for performance reasons
                from sas.qtgui.Plotting.Arrow3D import Arrow3D
                """
                draw magnetic vectors w/arrow
                """
                max_mx = max(numpy.fabs(sld_mx))
                max_my = max(numpy.fabs(sld_my))
                max_mz = max(numpy.fabs(sld_mz))
                max_m = max(max_mx, max_my, max_mz)
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
    def __init__(self, parent=None, graph_title=''):
        self.graph_title = graph_title
        QtWidgets.QDialog.__init__(self)
        Plotter3DWidget.__init__(self, manager=parent)
        self.setWindowTitle(self.graph_title)

