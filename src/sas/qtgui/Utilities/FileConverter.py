# pylint: disable=C0103, I1101
"""
File Converter Widget
"""
import logging
import os

import numpy as np
from PySide6 import QtWidgets
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

import sasdata.file_converter.FileConverterUtilities as Utilities
from sasdata.dataloader.data_info import Data1D, Detector, Sample, Source, Vector
from sasdata.file_converter.ascii2d_loader import ASCII2DLoader
from sasdata.file_converter.nxcansas_writer import NXcanSASWriter

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.FrameSelect import FrameSelect
from sas.system import version

from .UI.FileConverterUI import Ui_FileConverterUI


class FileConverterWidget(QtWidgets.QDialog, Ui_FileConverterUI):
    """
    Class to describe the behaviour of the File Converter widget
    """
    def __init__(self, parent=None):
        """
        Parent here is the GUI Manager. Required for access to
        the help location and to the file loader.
        """
        super(FileConverterWidget, self).__init__()


        self.parent = parent
        self.setupUi(self)

        self.setWindowTitle("File Converter")

        icon = QIcon()
        icon.addFile(":/res/ball.ico", QSize(), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)


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
        self.metadata = {}
        self.setValidators()

        self.addSlots()

    def setValidators(self):
        """
        Apply validators for double precision numbers to numerical fields
        """
        #self.txtMG_RunNumber.setValidator(QtGui.QIntValidator())

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
        self.cmdClose.clicked.connect(self.accept)
        self.cmdHelp.clicked.connect(self.onHelp)

        self.btnQFile.clicked.connect(self.onQFileOpen)
        self.btnIFile.clicked.connect(self.onIFileOpen)
        self.btnOutputFile.clicked.connect(self.onNewFile)

        self.txtOutputFile.editingFinished.connect(self.onNewFileEdited)

        self.cbInputFormat.currentIndexChanged.connect(self.onInputFormat)

    def onConvert(self):
        """
        Call the conversion method (and update DataExplorer with converted data)?
        """
        self.readMetadata()

        try:
            if not self.isBSL and self.is1D:
                qdata = Utilities.extract_ascii_data(self.qfile)
                iqdata = np.array([Utilities.extract_ascii_data(self.ifile)])
                self.convert1Ddata(qdata, iqdata, self.ofile, self.getMetadata())
            elif self.isBSL and self.is1D:
                qdata, iqdata = Utilities.extract_otoko_data(self.qfile, self.ifile)
                self.convert1Ddata(qdata, iqdata, self.ofile, self.getMetadata())
            elif not self.isBSL and not self.is1D:
                loader = ASCII2DLoader(self.ifile)
                data = loader.load()
                dataset = [data] # ASCII 2D only ever contains 1 frame
                Utilities.convert_2d_data(dataset, self.ofile, self.getMetadata())
            else: # self.data_type == 'bsl'
                #dataset = Utilities.extract_bsl_data(self.ifile)
                dataset = self.extractBSLdata(self.ifile)

                if dataset is None:
                    return
                Utilities.convert_2d_data(dataset, self.ofile, self.getMetadata())

        except (OSError, ValueError) as ex:
            msg = str(ex)
            logging.error(msg)
            return
        # everything converted, notify the user
        logging.info("File successfully converted.")
        self.parent.communicate.statusBarUpdateSignal.emit("File converted successfully.")

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
        except (OSError, RuntimeError) as ex:
            log_msg = f"File Converter failed with: {ex}"
            logging.error(log_msg)
            raise
        return datafile

    def getDetectorMetadata(self):
        """
        Read the detector metadata fields and put them in the dictionary
        """
        detector = Detector()
        detector.name = self.txtMD_Name.text()
        detector.distance = Utilities.toFloat(self.txtMD_Distance.text())
        detector.offset = Vector(x=Utilities.toFloat(self.txtMD_OffsetX.text()),
                                 y=Utilities.toFloat(self.txtMD_OffsetY.text()))
        detector.orientation = Vector(x=Utilities.toFloat(self.txtMD_OrientRoll.text()),
                                      y=Utilities.toFloat(self.txtMD_OrientPitch.text()),
                                      z=Utilities.toFloat(self.txtMD_OrientYaw.text()))
        detector.beam_center = Vector(x=Utilities.toFloat(self.txtMD_BeamX.text()),
                                      y=Utilities.toFloat(self.txtMD_BeamY.text()))
        detector.pixel_size = Vector(x=Utilities.toFloat(self.txtMD_PixelX.text()),
                                     y=Utilities.toFloat(self.txtMD_PixelY.text()))
        detector.slit_length = Utilities.toFloat(self.txtMD_Distance.text())
        return detector

    def getSourceMetadata(self):
        """
        Read the source metadata fields and put them in the dictionary
        """
        source = Source()
        # radiation is on the front panel
        source.radiation = self.cbRadiation.currentText().lower()
        # the rest is in the 'Source' tab of the Metadata tab
        source.name = self.txtMSo_Name.text()
        source.beam_size = Vector(x=Utilities.toFloat(self.txtMSo_BeamSizeX.text()),
                                  y=Utilities.toFloat(self.txtMSo_BeamSizeY.text()))
        source.beam_shape = self.txtMSo_BeamShape.text()
        source.wavelength = Utilities.toFloat(self.txtMSo_BeamWavelength.text())
        source.wavelength_min = Utilities.toFloat(self.txtMSo_MinWavelength.text())
        source.wavelength_max = Utilities.toFloat(self.txtMSo_MaxWavelength.text())
        source.wavelength_spread = Utilities.toFloat(self.txtMSo_Spread.text())
        return source

    def getSampleMetadata(self):
        """
        Read the sample metadata fields and put them in the dictionary
        """
        sample = Sample()
        sample.name = self.txtMSa_Name.text()
        sample.thickness = Utilities.toFloat(self.txtMSa_Thickness.text())
        sample.transmission = Utilities.toFloat(self.txtMSa_Transmission.text())
        sample.temperature = Utilities.toFloat(self.txtMSa_Temperature.text())
        sample.temperature_unit = self.txtMSa_TempUnit.text()
        sample.position = Vector(x=Utilities.toFloat(self.txtMSa_PositionX.text()),
                                 y=Utilities.toFloat(self.txtMSa_PositionY.text()))
        sample.orientation = Vector(x=Utilities.toFloat(self.txtMSa_OrientR.text()),
                                    y=Utilities.toFloat(self.txtMSa_OrientP.text()),
                                    z=Utilities.toFloat(self.txtMSa_OrientY.text()))

        details = self.txtMSa_Details.toPlainText()
        sample.details = [details] if details else []

        return sample

    def getMetadata(self):
        ''' metadata getter '''
        return self.metadata

    def readMetadata(self):
        """
        Read the metadata fields and put them in the dictionary

        This reads the UI elements directly, but we don't
        have a clear MVP distinction in this widgets, so there.
        """

        run_title = self.txtMG_RunName.text()
        run = self.txtMG_RunNumber.text()
        run = run.split(",")

        run_name = None
        if run:
            run_number = run[0]
            run_name = { run_number: run_title }

        metadata = {
            'title': self.txtMG_Title.text(),
            'run': run,
            'run_name': run_name, # if run_name != "" else "None" ,
            'instrument': self.txtMG_Instrument.text(),
            'detector': [self.getDetectorMetadata()],
            'sample': self.getSampleMetadata(),
            'source': self.getSourceMetadata(),
            'notes': [f'Data file generated by SasView v{version.__version__}'],
        }
        self.metadata = metadata

    def onNewFile(self):
        """
        show the save new file widget
        """
        wildcard1d = "CanSAS 1D files(*.xml);;" if self.is1D else ""
        wildcard = wildcard1d + "NXcanSAS files (*.h5)"
        caption = 'Save As'
        filter = wildcard
        parent = None
        # Query user for filename.
        filename_tuple = QtWidgets.QFileDialog.getSaveFileName(parent, caption, "", filter, "")
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
            else:
                filename += '.h5' # default for user entered filenames

        self.ofile = filename
        self.txtOutputFile.setText(filename)
        self.updateConvertState()

    def onNewFileEdited(self):
        """
        Update the output file state on direct field edit
        """
        text = self.txtOutputFile.text()
        if not text:
            return
        # Check/add extension
        filename_tuple = os.path.splitext(text)
        ext = filename_tuple[1]
        if ext.lower() not in ('.xml', '.h5'):
            text += '.h5'
        if not self.is1D and '.h5' not in ext.lower():
            # quietly add .h5 as extension
            text += '.h5'

        self.ofile = text
        self.updateConvertState()

    def updateConvertState(self):
        """
        Asserts presece of files for coversion.
        If all present -> enable the Convert button.
        """
        enabled = self.ifile != "" and os.path.exists(self.ifile) and self.ofile != ""
        if self.is1D:
            enabled = enabled and self.qfile != "" and os.path.exists(self.qfile)

        self.cmdConvert.setEnabled(enabled)

    def onInputFormat(self):
        """
        Enable/disable UI items based on input format spec
        """
        # ASCII 2D allows for one file only
        self.is1D = '2D' not in self.cbInputFormat.currentText()
        self.label_7.setVisible(self.is1D)
        self.txtQFile.setVisible(self.is1D)
        self.btnQFile.setVisible(self.is1D)
        self.isBSL = 'BSL' in self.cbInputFormat.currentText()

        # clear out filename fields
        self.txtQFile.setText("")
        self.txtIFile.setText("")
        # No need to clear the output field.

    def extractBSLdata(self, filename):
        """
        Extracts data from a 2D BSL file

        :param filename: The header file to extract the data from
        :return x_data: A 1D array containing all the x coordinates of the data
        :return y_data: A 1D array containing all the y coordinates of the data
        :return frame_data: A dictionary of the form *{frame_number: data}*,
            where data is a 2D numpy array containing the intensity data
        """
        loader = Utilities.BSLLoader(filename)
        frames = [0]
        should_continue = True

        if loader.n_frames > 1:
            params = self.askFrameRange(loader.n_frames)
            frames = params['frames']
            if len(frames) == 0:
                should_continue = False
        elif loader.n_rasters == 1 and loader.n_frames == 1:
            message = ("The selected file is an OTOKO file. Please select the "
                       "'OTOKO 1D' option if you wish to convert it.")
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)
            msgbox.setText(message)
            msgbox.setWindowTitle("File Conversion")
            msgbox.exec_()
            return
        else:
            msg = ("The selected data file only has 1 frame, it might be"
                       " a multi-frame OTOKO file.\nContinue conversion?")
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)
            msgbox.setText(msg)
            msgbox.setWindowTitle("File Conversion")
            # custom buttons
            button_yes = QtWidgets.QPushButton("Yes")
            msgbox.addButton(button_yes, QtWidgets.QMessageBox.YesRole)
            button_no = QtWidgets.QPushButton("No")
            msgbox.addButton(button_no, QtWidgets.QMessageBox.RejectRole)
            retval = msgbox.exec_()
            if retval == QtWidgets.QMessageBox.RejectRole:
                # cancel fit
                return

        if not should_continue:
            return None
        frame_data = loader.load_frames(frames)

        return frame_data

    def convert1Ddata(self, qdata, iqdata, ofile, metadata):
        """
        Formats a 1D array of q_axis data and a 2D array of I axis data (where
        each row of iqdata is a separate row), into an array of Data1D objects
        """
        frames = []
        increment = 1
        single_file = True
        n_frames = iqdata.shape[0]

        # Standard file has 3 frames: SAS, calibration and WAS
        if n_frames > 3:
            # File has multiple frames - ask the user which ones they want to
            # export
            params = self.askFrameRange(n_frames)
            frames = params['frames']
            increment = params['inc']
            single_file = params['file']
            if frames == []:
                return
        else: # Only interested in SAS data
            frames = [0]

        output_path = ofile

        frame_data = {}
        for i in frames:
            data = Data1D(x=qdata, y=iqdata[i])
            frame_data[i] = data
        if single_file:
            # Only need to set metadata on first Data1D object
            frame_data = list(frame_data.values()) # Don't need to know frame numbers
            frame_data[0].filename = output_path.split('\\')[-1]
            for key, value in metadata.items():
                setattr(frame_data[0], key, value)
        else:
            # Need to set metadata for all Data1D objects
            for datainfo in list(frame_data.values()):
                datainfo.filename = output_path.split('\\')[-1]
                for key, value in metadata.items():
                    setattr(datainfo, key, value)

        _, ext = os.path.splitext(output_path)
        if ext == '.xml':
            run_name = metadata['title']
            Utilities.convert_to_cansas(frame_data, output_path, run_name, single_file)
        else: # ext == '.h5'
            w = NXcanSASWriter()
            w.write(frame_data, output_path)

    def askFrameRange(self, n_frames=1):
        """
        Display a dialog asking the user to input the range of frames they
        would like to export

        :param n_frames: How many frames the loaded data file has
        :return: A dictionary containing the parameters input by the user
        """
        output_path = self.txtOutputFile.text()
        if not output_path:
            return
        _, ext = os.path.splitext(output_path)
        show_single_btn = (ext == '.h5')
        frames = None
        increment = None
        single_file = True

        dlg = FrameSelect(self, n_frames, show_single_btn)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return

        (first_frame, last_frame, increment) = dlg.getFrames()
        frames = list(range(first_frame, last_frame + 1, increment))
        return { 'frames': frames, 'inc': increment, 'file': single_file }

