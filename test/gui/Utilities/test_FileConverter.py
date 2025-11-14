import os
import tempfile
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from sas.qtgui.Utilities.FileConverter import FileConverterWidget


@pytest.fixture(scope="session", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestFileConverterWidget:
    def setup_method(self):
        self.parent = MagicMock()
        self.widget = FileConverterWidget(parent=self.parent)

    def test_initialization(self):
        """Test that the widget initializes correctly."""
        assert self.widget.windowTitle() == "File Converter"
        assert self.widget.parent == self.parent
        assert self.widget.is1D is True
        assert self.widget.isBSL is False
        assert self.widget.ifile == ""
        assert self.widget.qfile == ""
        assert self.widget.ofile == ""
        assert isinstance(self.widget.metadata, dict)
        assert not self.widget.txtIFile.isEnabled()
        assert not self.widget.txtQFile.isEnabled()
        assert not self.widget.cmdConvert.isEnabled()

    def test_set_validators(self):
        """Test that validators are set on numerical fields."""
        # Check that validators are set (can't easily test the exact validator)
        assert self.widget.txtMD_Distance.validator() is not None
        assert self.widget.txtMSa_Thickness.validator() is not None
        assert self.widget.txtMSo_BeamWavelength.validator() is not None

    def test_add_slots(self):
        """Test that slots are connected (hard to test directly, but ensure no errors)."""
        # Just ensure the widget was created without errors
        assert self.widget is not None

    def test_update_convert_state(self):
        """Test the updateConvertState method."""
        # Initially disabled
        assert not self.widget.cmdConvert.isEnabled()

        # Set files for 1D
        self.widget.ifile = "/fake/path/i.txt"
        self.widget.qfile = "/fake/path/q.txt"
        self.widget.ofile = "/fake/path/out.xml"
        with patch('os.path.exists', return_value=True):
            self.widget.updateConvertState()
        assert self.widget.cmdConvert.isEnabled()

        # For 2D, qfile not needed
        self.widget.is1D = False
        self.widget.qfile = ""
        with patch('os.path.exists', return_value=True):
            self.widget.updateConvertState()
        assert self.widget.cmdConvert.isEnabled()

    def test_on_input_format(self):
        """Test changing input format."""
        # Initially 1D
        assert self.widget.is1D is True

        # Change to 2D
        self.widget.cbInputFormat.setCurrentText("ASCII 2D")
        self.widget.onInputFormat()
        assert self.widget.is1D is False

        # Change to BSL
        self.widget.cbInputFormat.setCurrentText("BSL 2D")
        self.widget.onInputFormat()
        assert self.widget.isBSL is True

    def test_on_new_file_edited(self):
        """Test editing output file directly."""
        self.widget.txtOutputFile.setText("test")
        self.widget.onNewFileEdited()
        assert self.widget.ofile == "test.h5"
        assert self.widget.txtOutputFile.text() == "test"

        # With extension
        self.widget.txtOutputFile.setText("test.xml")
        self.widget.onNewFileEdited()
        assert self.widget.ofile == "test.xml"

    def test_get_detector_metadata(self):
        """Test reading detector metadata."""
        self.widget.txtMD_Name.setText("Test Detector")
        self.widget.txtMD_Distance.setText("1.0")
        detector = self.widget.getDetectorMetadata()
        assert detector.name == "Test Detector"
        assert detector.distance == 1.0

    def test_get_source_metadata(self):
        """Test reading source metadata."""
        self.widget.cbRadiation.setCurrentText("Neutron")
        self.widget.txtMSo_Name.setText("Test Source")
        self.widget.txtMSo_BeamWavelength.setText("5.0")
        source = self.widget.getSourceMetadata()
        assert source.radiation == "neutron"
        assert source.name == "Test Source"
        assert source.wavelength == 5.0

    def test_get_sample_metadata(self):
        """Test reading sample metadata."""
        self.widget.txtMSa_Name.setText("Test Sample")
        self.widget.txtMSa_Thickness.setText("2.0")
        sample = self.widget.getSampleMetadata()
        assert sample.name == "Test Sample"
        assert sample.thickness == 2.0

    def test_read_metadata(self):
        """Test reading all metadata."""
        self.widget.txtMG_Title.setText("Test Title")
        self.widget.txtMG_RunNumber.setText("123")
        self.widget.txtMG_RunName.setText("Test Run")
        self.widget.txtMG_Instrument.setText("Test Instrument")
        self.widget.readMetadata()
        metadata = self.widget.getMetadata()
        assert metadata['title'] == "Test Title"
        assert metadata['run'] == ["123"]
        assert metadata['instrument'] == "Test Instrument"

    @patch('sas.qtgui.Utilities.FileConverter.QtWidgets.QFileDialog.getOpenFileName')
    def test_open_file(self, mock_dialog):
        """Test opening a file."""
        mock_dialog.return_value = ("/path/to/file.txt", "")
        result = self.widget.openFile()
        assert result == "/path/to/file.txt"

    @patch('sas.qtgui.Utilities.FileConverter.QtWidgets.QFileDialog.getSaveFileName')
    def test_on_new_file(self, mock_dialog):
        """Test selecting output file."""
        mock_dialog.return_value = ("/path/to/output", "NXcanSAS files (*.h5)")
        self.widget.onNewFile()
        assert self.widget.ofile == "/path/to/output.h5"
        assert self.widget.txtOutputFile.text() == "/path/to/output.h5"

    @patch('sas.qtgui.Utilities.FileConverter.Utilities.extract_ascii_data')
    @patch('sas.qtgui.Utilities.FileConverter.Utilities.convert_to_cansas')
    def test_convert1Ddata_cansas(self, mock_convert, mock_extract):
        """Test converting 1D data to CanSAS."""
        mock_extract.return_value = [1, 2, 3]
        qdata = [0.1, 0.2, 0.3]
        iqdata = np.array([[10, 20, 30]])
        metadata = {'title': 'Test'}
        self.widget.convert1Ddata(qdata, iqdata, "/output.xml", metadata)
        mock_convert.assert_called_once()

    @patch('sas.qtgui.Utilities.FileConverter.NXcanSASWriter')
    def test_convert1Ddata_nxcansas(self, mock_writer):
        """Test converting 1D data to NXcanSAS."""
        mock_writer.return_value.write = MagicMock()
        qdata = [0.1, 0.2, 0.3]
        iqdata = np.array([[10, 20, 30]])
        metadata = {'title': 'Test'}
        self.widget.convert1Ddata(qdata, iqdata, "/output.h5", metadata)
        mock_writer.return_value.write.assert_called_once()

    @patch('sas.qtgui.Utilities.FileConverter.FrameSelect')
    def test_ask_frame_range(self, mock_frame_select):
        """Test asking for frame range."""
        mock_dlg = MagicMock()
        mock_dlg.exec_.return_value = 1  # QDialog.Accepted
        mock_dlg.getFrames.return_value = (0, 2, 1)
        mock_frame_select.return_value = mock_dlg
        self.widget.txtOutputFile.setText("/output.h5")
        result = self.widget.askFrameRange(3)
        assert result == {'frames': [0, 1, 2], 'inc': 1, 'file': True}

    # @patch('sas.qtgui.Utilities.FileConverter.Utilities.BSLLoader')
    # @patch('sas.qtgui.Utilities.FileConverter.QtWidgets.QMessageBox')
    # def test_extract_bsl_data_single_frame(self, mock_msgbox, mock_loader):
    #     """Test extracting BSL data with single frame."""
    #     mock_loader.return_value.n_frames = 1
    #     mock_loader.return_value.n_rasters = 2
    #     mock_loader.return_value.load_frames.return_value = "data"
    #     mock_msgbox.return_value.exec_.return_value = 5  # QMessageBox.YesRole
    #     result = self.widget.extractBSLdata("/file.bsl")
    #     assert result == "data"

    def test_on_help(self):
        """Test help display."""
        self.widget.onHelp()
        self.parent.showHelp.assert_called_with("/user/qtgui/Calculators/file_converter_help.html")

    def test_on_close(self):
        """Test closing the dialog."""
        with patch.object(self.widget, 'accept') as mock_accept:
            self.widget.cmdClose.clicked.emit()
            mock_accept.assert_called_once()