import os
import logging

import numpy as np

from PyQt5 import QtWidgets, QtCore, QtGui

from sas.sascalc.file_converter.ascii2d_loader import ASCII2DLoader
from sas.sascalc.dataloader.data_info import Detector
from sas.sascalc.dataloader.data_info import Sample
from sas.sascalc.dataloader.data_info import Source
from sas.sascalc.dataloader.data_info import Vector

import sas.sascalc.file_converter.FileConverterUtilities as Utilities

import sas.qtgui.Utilities.GuiUtils as GuiUtils

from .UI.FileConverterUI import Ui_FileConverterUI

class FileConverterWidget(QtWidgets.QDialog, Ui_FileConverterUI):
    def __init__(self, parent=None):
        super(FileConverterWidget, self).__init__(parent._parent)

        self.parent = parent
        self.setupUi(self)

        # disable the context help icon
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        self.setWindowTitle("File Converter")

        # i,q file fields are not editable
        self.txtIFile.setEnabled(False)
        self.txtQFile.setEnabled(False)
        self.cmdConvert.setEnabled(False)

        # globals
        self.is1D = True
        self.isBSL = False
        self.ifile = ""
        self.qfile = ""
        self.ofile = ""
        self.setValidators()

        self.addSlots()

    def setValidators(self):
        """
        Apply validators for double precision numbers to numerical fields
        """
        self.txtMG_RunNumber.setValidator(QtGui.QIntValidator(0, 10000))

        self.txtMD_Distance.setValidator(GuiUtils.DoubleValidator())
        self.txtMD_OffsetX.setValidator(GuiUtils.DoubleValidator())
        self.txtMD_OffsetY.setValidator(GuiUtils.DoubleValidator())
        self.txtMD_OrientRoll.setValidator(GuiUtils.DoubleValidator())
        self.txtMD_OrientPitch.setValidator(GuiUtils.DoubleValidator())
        self.txtMD_OrientYaw.setValidator(GuiUtils.DoubleValidator())
        self.txtMD_PixelX.setValidator(GuiUtils.DoubleValidator())
        self.txtMD_PixelY.setValidator(GuiUtils.DoubleValidator())
        self.txtMD_BeamX.setValidator(GuiUtils.DoubleValidator())
        self.txtMD_BeamY.setValidator(GuiUtils.DoubleValidator())
        self.txtMD_SlitLength.setValidator(GuiUtils.DoubleValidator())

        self.txtMSa_Thickness.setValidator(GuiUtils.DoubleValidator())
        self.txtMSa_Transmission.setValidator(GuiUtils.DoubleValidator())
        self.txtMSa_Temperature.setValidator(GuiUtils.DoubleValidator())
        self.txtMSa_PositionX.setValidator(GuiUtils.DoubleValidator())
        self.txtMSa_PositionY.setValidator(GuiUtils.DoubleValidator())
        self.txtMSa_OrientR.setValidator(GuiUtils.DoubleValidator())
        self.txtMSa_OrientY.setValidator(GuiUtils.DoubleValidator())
        self.txtMSa_OrientP.setValidator(GuiUtils.DoubleValidator())

        self.txtMSo_BeamSizeX.setValidator(GuiUtils.DoubleValidator())
        self.txtMSo_BeamSizeY.setValidator(GuiUtils.DoubleValidator())
        self.txtMSo_BeamWavelength.setValidator(GuiUtils.DoubleValidator())
        self.txtMSo_MinWavelength.setValidator(GuiUtils.DoubleValidator())
        self.txtMSo_MaxWavelength.setValidator(GuiUtils.DoubleValidator())
        self.txtMSo_Spread.setValidator(GuiUtils.DoubleValidator())

    def addSlots(self):
        """
        Create callbacks for UI elements and outside signals
        """
        self.cmdConvert.clicked.connect(self.onConvert)
        self.cmdHelp.clicked.connect(self.onHelp)

        self.btnQFile.clicked.connect(self.onQFileOpen)
        self.btnIFile.clicked.connect(self.onIFileOpen)
        self.btnOutputFile.clicked.connect(self.onNewFile)

        self.txtOutputFile.textEdited.connect(self.onNewFileEdited)

        self.cbInputFormat.currentIndexChanged.connect(self.onInputFormat)

    def onConvert(self):
        """
        Call the conversion method (*and update DataExplorer with converted data)?
        """
        self.readMetadata()

        try:
            if not self.isBSL and self.is1D:
                qdata = Utilities.extract_ascii_data(self.qfile)
                iqdata = np.array([Utilities.extract_ascii_data(self.ifile)])
                Utilities.convert_1d_data(qdata, iqdata, self.ofile, self.getMetadata())
            elif self.isBSL and self.is1D:
                qdata, iqdata = Utilities.extract_otoko_data(self.qfile, self.ifile)
                Utilities.convert_1d_data(qdata, iqdata, self.ofile, self.getMetadata())
            elif not self.isBSL and not self.is1D:
                loader = ASCII2DLoader(self.ifile)
                data = loader.load()
                dataset = [data] # ASCII 2D only ever contains 1 frame
                Utilities.convert_2d_data(dataset, self.ofile, self.getMetadata())
            else: # self.data_type == 'bsl'
                dataset = Utilities.extract_bsl_data(self.ifile)
                if dataset is None:
                    return
                Utilities.convert_2d_data(dataset, self.ofile, self.getMetadata())

        except Exception as ex:
            msg = str(ex)
            logging.error(msg)
            return
        # everything converted, notify the user
        logging.info("File successfully converted.")

        # Optionally, load the freshly converted file into Data Explorer
        if self.chkLoadFile.isChecked():
            # awful climbing up the hierarchy... don't do that. please.
            self.parent.filesWidget.loadFromURL([self.ofile])

    def onHelp(self):
        """
        Display online help related to the file converter
        """
        location = "/user/qtgui/Calculators/file_converter_help.html"
        self.parent.showHelp(location)

    def onIFileOpen(self):
        """
        Show the path chooser for file with I
        """
        file_candidate = self.openFile()
        if not file_candidate:
            return
        self.ifile = file_candidate
        self.txtIFile.setText(os.path.basename(str(file_candidate)))
        self.updateConvertState()

    def onQFileOpen(self):
        """
        Show the path chooser for file with Q
        """
        file_candidate = self.openFile()
        if not file_candidate:
            return
        self.qfile = file_candidate
        self.txtQFile.setText(os.path.basename(str(file_candidate)))
        self.updateConvertState()

    def openFile(self):
        """
        Show the path chooser for existent file
        """
        datafile = None
        try:
            datafile = QtWidgets.QFileDialog.getOpenFileName(
                self, "Choose a file", "", "All files (*.*)")[0]
        except (RuntimeError, IOError) as ex:
            log_msg = "File Converter failed with: {}".format(ex)
            logging.error(log_msg)
            raise
        return datafile

    def toFloat(self, text):
        """
        Dumb string->float converter
        """
        value = None
        try:
            value = float(text) if text is not "" else None
        except ValueError:
            pass
        return value

    def getDetectorMetadata(self):
        """
        Read the detector metadata fields and put them in the dictionary
        """
        detector = Detector()
        detector.name = self.txtMD_Name.text()
        detector.distance = self.toFloat(self.txtMD_Distance.text())
        detector.offset = Vector(x=self.toFloat(self.txtMD_OffsetX.text()),
                                 y=self.toFloat(self.txtMD_OffsetY.text()))
        detector.orientation = Vector(x=self.toFloat(self.txtMD_OrientRoll.text()),
                                      y=self.toFloat(self.txtMD_OrientPitch.text()),
                                      z=self.toFloat(self.txtMD_OrientYaw.text()))
        detector.beam_center = Vector(x=self.toFloat(self.txtMD_BeamX.text()),
                                      y=self.toFloat(self.txtMD_BeamY.text()))
        detector.pixel_size = Vector(x=self.toFloat(self.txtMD_PixelX.text()),
                                     y=self.toFloat(self.txtMD_PixelY.text()))
        detector.slit_length = self.toFloat(self.txtMD_Distance.text())
        return detector

    def getSampleMetadata(self):
        """
        Read the sample metadata fields and put them in the dictionary
        """
        sample = Sample()
        sample.name = self.txtMSa_Name.text()
        sample.beam_size = Vector(x=self.toFloat(self.txtMSo_BeamSizeX.text()),
                                  y=self.toFloat(self.txtMSo_BeamSizeY.text()))
        sample.beam_shape = self.txtMSo_BeamShape.text()
        sample.wavelength = self.toFloat(self.txtMSo_BeamWavelength.text())
        sample.wavelength_min = self.toFloat(self.txtMSo_MinWavelength.text())
        sample.wavelength_max = self.toFloat(self.txtMSo_MaxWavelength.text())
        sample.wavelength_spread = self.toFloat(self.txtMSo_Spread.text())
        return sample

    def getSourceMetadata(self):
        """
        Read the source metadata fields and put them in the dictionary
        """
        source = Source()
        # radiation is on the front panel
        source.radiation = self.cbRadiation.currentText().lower()
        # the rest is in the 'Source' tab of the Metadata tab
        source.name = self.txtMSo_Name.text()
        source.thickness = self.toFloat(self.txtMSa_Thickness.text())
        source.transmission = self.toFloat(self.txtMSa_Transmission.text())
        source.temperature = self.toFloat(self.txtMSa_Temperature.text())
        source.position = Vector(x=self.toFloat(self.txtMSa_PositionX.text()),
                                 y=self.toFloat(self.txtMSa_PositionY.text()))
        source.orientation = Vector(x=self.toFloat(self.txtMSa_OrientR.text()),
                                    y=self.toFloat(self.txtMSa_OrientP.text()),
                                    z=self.toFloat(self.txtMSa_OrientY.text()))

        source.details = self.txtMSa_Details.toPlainText()

        return source

    def getMetadata(self):
        return self.metadata

    def readMetadata(self):
        """
        Read the metadata fields and put them in the dictionary

        This reads the UI elements directly, but we don't
        have a clear MVP distinction in this widgets, so there.
        """
        metadata = {
            'title': self.txtMG_Title.text(),
            'run': self.txtMG_RunNumber.text(),
            'run_name': self.txtMG_RunName.text(),
            'instrument': self.txtMG_Instrument.text(),
            'detector': [self.getDetectorMetadata()],
            'sample': self.getSampleMetadata(),
            'source': self.getSourceMetadata()
        }
        self.metadata = metadata

    def onNewFile(self):
        """
        show the save new file widget
        """
        wildcard1d = "CanSAS 1D files(*.xml);;" if self.is1D else ""
        wildcard = wildcard1d + "NXcanSAS files (*.h5)"
        kwargs = {
            'caption'   : 'Save As',
            'filter'    : wildcard,
            'parent'    : None,
            'options'   : QtWidgets.QFileDialog.DontUseNativeDialog
        }
        # Query user for filename.
        filename_tuple = QtWidgets.QFileDialog.getSaveFileName(**kwargs)
        filename = filename_tuple[0]

        # User cancelled.
        if not filename:
            return
        # Check/add extension
        if not os.path.splitext(filename)[1]:
            ext = filename_tuple[1]
            if 'CanSAS' in ext:
                filename += '.xml'
            elif 'NXcanSAS' in ext:
                filename += '.h5'

        self.ofile = filename
        self.txtOutputFile.setText(filename)
        self.updateConvertState()

    def onNewFileEdited(self, text):
        """
        Update the output file state on direct field edit
        """
        self.ofile = text
        self.updateConvertState()

    def updateConvertState(self):
        """
        Asserts presece of files for coversion.
        If all present -> enable the Convert button.
        """
        enabled = self.ifile!="" and os.path.exists(self.ifile) and self.ofile!=""
        if self.is1D:
            enabled = enabled and self.qfile!="" and os.path.exists(self.qfile)

        self.cmdConvert.setEnabled(enabled)

    def onInputFormat(self):
        """
        Enable/disable UI items based on input format spec
        """
        # ASCII 2D allows for one file only
        self.is1D = not '2D' in self.cbInputFormat.currentText()
        self.label_7.setVisible(self.is1D)
        self.txtQFile.setVisible(self.is1D)
        self.btnQFile.setVisible(self.is1D)
        self.isBSL = 'BSL' in self.cbInputFormat.currentText()

        # clear out filename fields
        self.txtQFile.setText("")
        self.txtIFile.setText("")
        # No need to clear the output field.





