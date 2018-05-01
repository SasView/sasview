import sys
import os
import numpy
import logging
import time

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

    def __init__(self, parent=None):
        super(GenericScatteringCalculator, self).__init__()
        self.setupUi(self)
        self.manager = parent
        self.communicator = self.manager.communicator()
        self.model = sas_gen.GenSAS()
        self.omf_reader = sas_gen.OMFReader()
        self.sld_reader = sas_gen.SLDReader()
        self.pdb_reader = sas_gen.PDBReader()
        self.reader = None
        self.sld_data = None

        self.parameters = []
        self.data = None
        self.datafile = None
        self.file_name = ''
        self.ext = None
        self.default_shape = str(self.cbShape.currentText())
        self.is_avg = False
        self.data_to_plot = None
        self.graph_num = 1  # index for name of graph

        # combox box
        self.cbOptionsCalc.setVisible(False)

        # push buttons
        self.cmdClose.clicked.connect(self.accept)
        self.cmdHelp.clicked.connect(self.onHelp)

        self.cmdLoad.clicked.connect(self.loadFile)
        self.cmdCompute.clicked.connect(self.onCompute)
        self.cmdReset.clicked.connect(self.onReset)
        self.cmdSave.clicked.connect(self.onSaveFile)

        self.cmdDraw.clicked.connect(lambda: self.plot3d(has_arrow=True))
        self.cmdDrawpoints.clicked.connect(lambda: self.plot3d(has_arrow=False))

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

        # 0 < Qmax <= 1000
        validat_regex_q = QtCore.QRegExp('^1000$|^[+]?(\d{1,3}([.]\d+)?)$')
        self.txtQxMax.setValidator(QtGui.QRegExpValidator(validat_regex_q,
                                                          self.txtQxMax))
        self.txtQxMax.textChanged.connect(self.check_value)

        # 2 <= Qbin <= 1000
        self.txtNoQBins.setValidator(QtGui.QRegExpValidator(validat_regex_q,
                                                            self.txtNoQBins))
        self.txtNoQBins.textChanged.connect(self.check_value)

        # plots - 3D in real space
        self.trigger_plot_3d.connect(lambda: self.plot3d(has_arrow=False))

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

    def loadFile(self):
        """
        Open menu to choose the datafile to load
        Only extensions .SLD, .PDB, .OMF, .sld, .pdb, .omf
        """
        try:
            self.datafile = QtWidgets.QFileDialog.getOpenFileName(
                self, "Choose a file", "", "All Gen files (*.OMF *.omf) ;;"
                                          "SLD files (*.SLD *.sld);;PDB files (*.pdb *.PDB);; "
                                          "OMF files (*.OMF *.omf);; "
                                          "All files (*.*)")[0]
            if self.datafile:
                self.default_shape = str(self.cbShape.currentText())
                self.file_name = os.path.basename(str(self.datafile))
                self.ext = os.path.splitext(str(self.datafile))[1]
                if self.ext in self.omf_reader.ext:
                    loader = self.omf_reader
                elif self.ext in self.sld_reader.ext:
                    loader = self.sld_reader
                elif self.ext in self.pdb_reader.ext:
                    loader = self.pdb_reader
                else:
                    loader = None
                # disable some entries depending on type of loaded file
                # (according to documentation)
                if self.ext.lower() in ['.sld', '.omf', '.pdb']:
                    self.txtUpFracIn.setEnabled(False)
                    self.txtUpFracOut.setEnabled(False)
                    self.txtUpTheta.setEnabled(False)

                if self.reader is not None and self.reader.isrunning():
                    self.reader.stop()
                self.cmdLoad.setEnabled(False)
                self.cmdLoad.setText('Loading...')
                self.communicator.statusBarUpdateSignal.emit(
                    "Loading File {}".format(os.path.basename(
                        str(self.datafile))))
                self.reader = GenReader(path=str(self.datafile), loader=loader,
                                        completefn=self.complete_loading,
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

    def complete_loading(self, data=None):
        """ Function used in GenRead"""
        self.cbShape.setEnabled(False)
        try:
            is_pdbdata = False
            self.txtData.setText(os.path.basename(str(self.datafile)))
            self.is_avg = False
            if self.ext in self.omf_reader.ext:
                gen = sas_gen.OMF2SLD()
                gen.set_data(data)
                self.sld_data = gen.get_magsld()
                self.check_units()
            elif self.ext in self.sld_reader.ext:
                self.sld_data = data
            elif self.ext in self.pdb_reader.ext:
                self.sld_data = data
                is_pdbdata = True
            # Display combobox of orientation only for pdb data
            self.cbOptionsCalc.setVisible(is_pdbdata)
            self.update_gui()
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
        self.cmdLoad.setEnabled(True)
        self.cmdLoad.setText('Load')
        self.trigger_plot_3d.emit()

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

    def check_value(self):
        """Check range of text edits for QMax and Number of Qbins """
        text_edit = self.sender()
        text_edit.setStyleSheet('background-color: rgb(255, 255, 255);')
        if text_edit.text():
            value = float(str(text_edit.text()))
            if text_edit == self.txtQxMax:
                if value <= 0 or value > 1000:
                    text_edit.setStyleSheet('background-color: rgb(255, 182, 193);')
                else:
                    text_edit.setStyleSheet('background-color: rgb(255, 255, 255);')
            elif text_edit == self.txtNoQBins:
                if value < 2 or value > 1000:
                    self.txtNoQBins.setStyleSheet('background-color: rgb(255, 182, 193);')
                else:
                    self.txtNoQBins.setStyleSheet('background-color: rgb(255, 255, 255);')

    def update_gui(self):
        """ Update the interface with values from loaded data """
        self.model.set_is_avg(self.is_avg)
        self.model.set_sld_data(self.sld_data)
        self.model.params['total_volume'] = len(self.sld_data.sld_n)*self.sld_data.vol_pix[0]

        # add condition for activation of save button
        self.cmdSave.setEnabled(True)

        # activation of 3D plots' buttons (with and without arrows)
        self.cmdDraw.setEnabled(self.sld_data is not None)
        self.cmdDrawpoints.setEnabled(self.sld_data is not None)

        self.txtScale.setText(str(self.model.params['scale']))
        self.txtBackground.setText(str(self.model.params['background']))
        self.txtSolventSLD.setText(str(self.model.params['solvent_SLD']))

        # Volume to write to interface: npts x volume of first pixel
        self.txtTotalVolume.setText(str(len(self.sld_data.sld_n)*self.sld_data.vol_pix[0]))

        self.txtUpFracIn.setText(str(self.model.params['Up_frac_in']))
        self.txtUpFracOut.setText(str(self.model.params['Up_frac_out']))
        self.txtUpTheta.setText(str(self.model.params['Up_theta']))

        self.txtNoPixels.setText(str(len(self.sld_data.sld_n)))
        self.txtNoPixels.setEnabled(False)

        list_parameters = ['sld_mx', 'sld_my', 'sld_mz', 'sld_n', 'xnodes',
                           'ynodes', 'znodes', 'xstepsize', 'ystepsize',
                           'zstepsize']
        list_gui_button = [self.txtMx, self.txtMy, self.txtMz, self.txtNucl,
                           self.txtXnodes, self.txtYnodes, self.txtZnodes,
                           self.txtXstepsize, self.txtYstepsize,
                           self.txtZstepsize]

        # Fill right hand side of GUI
        for indx, item in enumerate(list_parameters):
            if getattr(self.sld_data, item) is None:
                list_gui_button[indx].setText('NaN')
            else:
                value = getattr(self.sld_data, item)
                if isinstance(value, numpy.ndarray):
                    item_for_gui = str(GuiUtils.formatNumber(numpy.average(value), True))
                else:
                    item_for_gui = str(GuiUtils.formatNumber(value, True))
                list_gui_button[indx].setText(item_for_gui)

        # Enable / disable editing of right hand side of GUI
        for indx, item in enumerate(list_parameters):
            if indx < 4:
                # this condition only applies to Mx,y,z and Nucl
                value = getattr(self.sld_data, item)
                enable = self.sld_data.pix_type == 'pixel' \
                         and numpy.min(value) == numpy.max(value)
            else:
                enable = not self.sld_data.is_data
            list_gui_button[indx].setEnabled(enable)

    def write_new_values_from_gui(self):
        """
        update parameters using modified inputs from GUI
        used before computing
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

        if self.txtMx.isModified():
            self.sld_data.sld_mx = float(self.txtMx.text())*\
                                   numpy.ones(len(self.sld_data.sld_mx))

        if self.txtMy.isModified():
            self.sld_data.sld_my = float(self.txtMy.text())*\
                                   numpy.ones(len(self.sld_data.sld_my))

        if self.txtMz.isModified():
            self.sld_data.sld_mz = float(self.txtMz.text())*\
                                   numpy.ones(len(self.sld_data.sld_mz))

        if self.txtNucl.isModified():
            self.sld_data.sld_n = float(self.txtNucl.text())*\
                                  numpy.ones(len(self.sld_data.sld_n))

        if self.txtXnodes.isModified():
            self.sld_data.xnodes = int(self.txtXnodes.text())

        if self.txtYnodes.isModified():
            self.sld_data.ynodes = int(self.txtYnodes.text())

        if self.txtZnodes.isModified():
            self.sld_data.znodes = int(self.txtZnodes.text())

        if self.txtXstepsize.isModified():
            self.sld_data.xstepsize = float(self.txtXstepsize.text())

        if self.txtYstepsize.isModified():
            self.sld_data.ystepsize = float(self.txtYstepsize.text())

        if self.txtZstepsize.isModified():
            self.sld_data.zstepsize = float(self.txtZstepsize.text())

        if self.cbOptionsCalc.isVisible():
            self.is_avg = (self.cbOptionsCalc.currentIndex() == 1)

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
        """ Reset the inputs of textEdit to default values """
        try:
            # reset values in textedits
            self.txtUpFracIn.setText("1.0")
            self.txtUpFracOut.setText("1.0")
            self.txtUpTheta.setText("0.0")
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
            # reset Load button and textedit
            self.txtData.setText('Default SLD Profile')
            self.cmdLoad.setEnabled(True)
            self.cmdLoad.setText('Load')
            # reset option for calculation
            self.cbOptionsCalc.setCurrentIndex(0)
            self.cbOptionsCalc.setVisible(False)
            # reset shape button
            self.cbShape.setCurrentIndex(0)
            self.cbShape.setEnabled(True)
            # reset compute button
            self.cmdCompute.setText('Compute')
            self.cmdCompute.setEnabled(True)
            # TODO reload default data set
            self._create_default_sld_data()

        finally:
            pass

    def _create_default_2d_data(self):
        """
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
        """
        Copied from previous version
        Making default sld-data
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
        """
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

    def onCompute(self):
        """
        Copied from previous version
        Execute the computation of I(qx, qy)
        """
        # Set default data when nothing loaded yet
        if self.sld_data is None:
            self._create_default_sld_data()
        try:
            self.model.set_sld_data(self.sld_data)
            self.write_new_values_from_gui()
            if self.is_avg or self.is_avg is None:
                self._create_default_1d_data()
                i_out = numpy.zeros(len(self.data.y))
                inputs = [self.data.x, [], i_out]
            else:
                self._create_default_2d_data()
                i_out = numpy.zeros(len(self.data.data))
                inputs = [self.data.qx_data, self.data.qy_data, i_out]
            logging.info("Computation is in progress...")
            self.cmdCompute.setText('Wait...')
            self.cmdCompute.setEnabled(False)
            d = threads.deferToThread(self.complete, inputs, self._update)
            # Add deferred callback for call return
            d.addCallback(self.plot_1_2d)
            d.addErrback(self.calculateFailed)
        except:
            log_msg = "{}. stop".format(sys.exc_info()[1])
            logging.info(log_msg)
        return

    def _update(self, value):
        """
        Copied from previous version
        """
        pass

    def calculateFailed(self, reason):
        """
        """
        print("Calculate Failed with:\n", reason)
        pass

    def complete(self, input, update=None):
        """
        Gen compute complete function
        :Param input: input list [qx_data, qy_data, i_out]
        """
        out = numpy.empty(0)
        for ind in range(len(input[0])):
            if self.is_avg:
                if ind % 1 == 0 and update is not None:
                    # update()
                    percentage = int(100.0 * float(ind) / len(input[0]))
                    update(percentage)
                    time.sleep(0.001)  # 0.1
                inputi = [input[0][ind:ind + 1], [], input[2][ind:ind + 1]]
                outi = self.model.run(inputi)
                out = numpy.append(out, outi)
            else:
                if ind % 50 == 0 and update is not None:
                    percentage = int(100.0 * float(ind) / len(input[0]))
                    update(percentage)
                    time.sleep(0.001)
                inputi = [input[0][ind:ind + 1], input[1][ind:ind + 1],
                          input[2][ind:ind + 1]]
                outi = self.model.runXY(inputi)
                out = numpy.append(out, outi)
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
                sas_gen.SLDReader().write(filename, self.sld_data)
            except:
                raise

    def plot3d(self, has_arrow=False):
        """ Generate 3D plot in real space with or without arrows """
        self.write_new_values_from_gui()
        graph_title = " Graph {}: {} 3D SLD Profile".format(self.graph_num,
                                                            self.file_name)
        if has_arrow:
            graph_title += ' - Magnetic Vector as Arrow'

        plot3D = Plotter3D(self, graph_title)
        plot3D.plot(self.sld_data, has_arrow=has_arrow)
        plot3D.show()
        self.graph_num += 1

    def plot_1_2d(self, d):
        """ Generate 1D or 2D plot, called in Compute"""
        if self.is_avg or self.is_avg is None:
            data = Data1D(x=self.data.x, y=self.data_to_plot)
            data.title = "GenSAS {}  #{} 1D".format(self.file_name,
                                                    int(self.graph_num))
            data.xaxis('\\rm{Q_{x}}', '\AA^{-1}')
            data.yaxis('\\rm{Intensity}', 'cm^{-1}')
            plot1D = Plotter(self)
            plot1D.plot(data)
            plot1D.show()
            self.graph_num += 1
            # TODO
            print('TRANSFER OF DATA TO MAIN PANEL TO BE IMPLEMENTED')
            return plot1D
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
            plot2D = Plotter2D(self)
            plot2D.plot(data)
            plot2D.show()
            self.graph_num += 1
            # TODO
            print('TRANSFER OF DATA TO MAIN PANEL TO BE IMPLEMENTED')
            return plot2D


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
                try:
                    max_step = max(data.xstepsize, data.ystepsize, data.zstepsize)
                except:
                    max_step = 0
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
                except:
                    pass
                log_msg = "Arrow Drawing completed.\n"
                logging.info(log_msg)
            log_msg = "Arrow Drawing is in progress..."
            logging.info(log_msg)

            # Defer the drawing of arrows to another thread
            d = threads.deferToThread(_draw_arrow, ax)

        self.figure.canvas.resizing = False
        self.figure.canvas.draw()


class Plotter3D(QtWidgets.QDialog, Plotter3DWidget):
    def __init__(self, parent=None, graph_title=''):
        self.graph_title = graph_title
        QtWidgets.QDialog.__init__(self)
        Plotter3DWidget.__init__(self, manager=parent)
        self.setWindowTitle(self.graph_title)

