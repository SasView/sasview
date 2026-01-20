"""
Unit tests for SASBDBDialog export functionality
"""
import os
import tempfile
from unittest.mock import MagicMock

import pytest
from PySide6 import QtWidgets

from sas.qtgui.Utilities.SASBDB.sasbdb_data import (
    SASBDBBuffer,
    SASBDBExportData,
    SASBDBInstrument,
    SASBDBMolecule,
    SASBDBProject,
    SASBDBSample,
)
from sas.qtgui.Utilities.SASBDB.SASBDBDialog import SASBDBDialog


class TestSASBDBDialog:
    """Test SASBDBDialog export functionality"""

    @pytest.fixture(autouse=True)
    def dialog(self, qapp):
        """Create/destroy the dialog with minimal export data"""
        export_data = SASBDBExportData()
        # Add minimal required data for validation
        project = SASBDBProject(project_title="Test Project")
        export_data.project = project

        sample = SASBDBSample(
            sample_title="Test Sample",
            angular_units="1/A",
            intensity_units="1/cm",
            curve_type="Single concentration"
        )
        molecule = SASBDBMolecule(
            long_name="Test Molecule",
            fasta_sequence="MKTAYIAKQR",
            monomer_mw_kda=10.5
        )
        sample.molecule = molecule

        buffer = SASBDBBuffer(description="PBS buffer", ph=7.4)
        sample.buffer = buffer

        instrument = SASBDBInstrument(
            source_type="X-ray synchrotron",
            beamline_name="BL12"
        )

        export_data.samples.append(sample)
        export_data.instruments.append(instrument)

        w = SASBDBDialog(export_data=export_data, parent=None)
        yield w
        w.close()

    def test_dialog_initialization(self, dialog):
        """Test dialog initializes correctly"""
        assert isinstance(dialog, QtWidgets.QDialog)
        assert dialog.export_data is not None
        assert len(dialog.export_data.samples) == 1

    def test_onExport_cancels_when_no_filename(self, dialog, mocker):
        """Test that onExport returns early when user cancels file dialog"""
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName',
                          return_value=("", ""))

        # Should return without error
        dialog.onExport()
        # Dialog should still be open (not closed)
        assert dialog.isVisible()

    def test_onExport_generates_correct_filenames(self, dialog, mocker):
        """Test that onExport generates correct PDF and project filenames"""
        test_json = "/tmp/test_export.json"
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName',
                          return_value=(test_json, "JSON file (*.json)"))

        # Mock all three save operations to succeed
        json_mock = mocker.patch(
            'sas.qtgui.Utilities.SASBDB.sasbdb_exporter.SASBDBExporter.export_to_json',
            return_value=True
        )
        pdf_mock = mocker.patch.object(dialog, '_generatePDFReport')
        project_mock = mocker.patch.object(dialog, '_saveProjectFile', return_value=True)
        close_mock = mocker.patch.object(dialog, 'close')
        msgbox_mock = mocker.patch.object(QtWidgets.QMessageBox, 'information')

        dialog.onExport()

        # Verify JSON was saved with correct filename
        json_mock.assert_called_once()
        call_args = json_mock.call_args[0]
        assert call_args[0] == test_json

        # Verify PDF filename was generated correctly
        pdf_mock.assert_called_once()
        pdf_args = pdf_mock.call_args[0]
        assert pdf_args[1] == "/tmp/test_export.pdf"

        # Verify project filename was generated correctly
        project_mock.assert_called_once()
        project_args = project_mock.call_args[0]
        assert project_args[0] == "/tmp/test_export_project.json"

    def test_onExport_handles_filename_without_extension(self, dialog, mocker):
        """Test that onExport adds .json extension if missing"""
        test_json = "/tmp/test_export"  # No extension
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName',
                          return_value=(test_json, "JSON file (*.json)"))

        json_mock = mocker.patch(
            'sas.qtgui.Utilities.SASBDB.sasbdb_exporter.SASBDBExporter.export_to_json',
            return_value=True
        )
        mocker.patch.object(dialog, '_generatePDFReport')
        mocker.patch.object(dialog, '_saveProjectFile', return_value=True)
        mocker.patch.object(QtWidgets.QMessageBox, 'information')
        mocker.patch.object(dialog, 'close')

        dialog.onExport()

        # Verify .json was added
        call_args = json_mock.call_args[0]
        assert call_args[0] == "/tmp/test_export.json"

    def test_onExport_all_files_succeed(self, dialog, mocker):
        """Test onExport when all three files save successfully"""
        test_json = "/tmp/test_export.json"
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName',
                          return_value=(test_json, "JSON file (*.json)"))

        mocker.patch(
            'sas.qtgui.Utilities.SASBDB.sasbdb_exporter.SASBDBExporter.export_to_json',
            return_value=True
        )
        mocker.patch.object(dialog, '_generatePDFReport')
        mocker.patch.object(dialog, '_saveProjectFile', return_value=True)
        close_mock = mocker.patch.object(dialog, 'close')
        msgbox_mock = mocker.patch.object(QtWidgets.QMessageBox, 'information')

        dialog.onExport()

        # Verify success message was shown
        msgbox_mock.assert_called_once()
        call_args = msgbox_mock.call_args
        assert call_args[0][1] == "Export Successful"

        # Verify dialog was closed
        close_mock.assert_called_once()

    def test_onExport_partial_failure(self, dialog, mocker):
        """Test onExport when some files fail"""
        test_json = "/tmp/test_export.json"
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName',
                          return_value=(test_json, "JSON file (*.json)"))

        # JSON succeeds, PDF fails, Project succeeds
        mocker.patch(
            'sas.qtgui.Utilities.SASBDB.sasbdb_exporter.SASBDBExporter.export_to_json',
            return_value=True
        )
        mocker.patch.object(dialog, '_generatePDFReport', side_effect=Exception("PDF error"))
        mocker.patch.object(dialog, '_saveProjectFile', return_value=True)
        msgbox_mock = mocker.patch.object(QtWidgets.QMessageBox, 'warning')

        dialog.onExport()

        # Verify warning message was shown (partial success)
        msgbox_mock.assert_called_once()
        call_args = msgbox_mock.call_args
        assert call_args[0][1] == "Partial Export Success"
        message = call_args[0][2]
        assert "2 of 3 files saved" in message or "2 of 3" in message

    def test_onExport_all_files_fail(self, dialog, mocker):
        """Test onExport when all files fail"""
        test_json = "/tmp/test_export.json"
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName',
                          return_value=(test_json, "JSON file (*.json)"))

        mocker.patch(
            'sas.qtgui.Utilities.SASBDB.sasbdb_exporter.SASBDBExporter.export_to_json',
            return_value=False
        )
        mocker.patch.object(dialog, '_generatePDFReport', side_effect=Exception("PDF error"))
        mocker.patch.object(dialog, '_saveProjectFile', return_value=False)
        msgbox_mock = mocker.patch.object(QtWidgets.QMessageBox, 'critical')

        dialog.onExport()

        # Verify error message was shown
        msgbox_mock.assert_called_once()
        call_args = msgbox_mock.call_args
        assert call_args[0][1] == "Export Failed"

    def test_onExport_json_failure(self, dialog, mocker):
        """Test onExport when JSON export fails"""
        test_json = "/tmp/test_export.json"
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName',
                          return_value=(test_json, "JSON file (*.json)"))

        mocker.patch(
            'sas.qtgui.Utilities.SASBDB.sasbdb_exporter.SASBDBExporter.export_to_json',
            side_effect=Exception("JSON export failed")
        )
        mocker.patch.object(dialog, '_generatePDFReport')
        mocker.patch.object(dialog, '_saveProjectFile', return_value=True)
        msgbox_mock = mocker.patch.object(QtWidgets.QMessageBox, 'warning')

        dialog.onExport()

        # Should show partial success message
        msgbox_mock.assert_called_once()
        message = msgbox_mock.call_args[0][2]
        assert "JSON" in message

    def test_saveProjectFile_no_parent(self, dialog):
        """Test _saveProjectFile when dialog has no parent"""
        dialog.setParent(None)
        result = dialog._saveProjectFile("/tmp/test_project.json")
        assert result is False

    def test_saveProjectFile_no_gui_manager(self, dialog):
        """Test _saveProjectFile when parent has no guiManager"""
        parent = MagicMock()
        parent.guiManager = None
        parent.gui_manager = None
        dialog.setParent(parent)

        result = dialog._saveProjectFile("/tmp/test_project.json")
        assert result is False

    def test_saveProjectFile_no_files_widget(self, dialog):
        """Test _saveProjectFile when guiManager has no filesWidget"""
        parent = MagicMock()
        gui_manager = MagicMock()
        gui_manager.filesWidget = None
        parent.guiManager = gui_manager
        dialog.setParent(parent)

        result = dialog._saveProjectFile("/tmp/test_project.json")
        assert result is False

    def test_saveProjectFile_success(self, dialog, mocker):
        """Test _saveProjectFile when all conditions are met"""
        parent = MagicMock()
        gui_manager = MagicMock()

        # Mock filesWidget
        files_widget = MagicMock()
        files_widget.getSerializedData.return_value = {'data1': 'test_data'}
        gui_manager.filesWidget = files_widget

        # Mock perspectives
        perspective = MagicMock()
        perspective.isSerializable.return_value = True
        perspective.serializeAll.return_value = {'data1': {'fit': 'result'}}
        gui_manager.loadedPerspectives = {'fitting': perspective}

        # Mock grid_window
        gui_manager.grid_window = MagicMock()
        gui_manager.grid_window.data_dict = {}

        # Mock current perspective
        current_perspective = MagicMock()
        current_perspective.name = "Fitting"
        gui_manager._current_perspective = current_perspective

        parent.guiManager = gui_manager
        dialog.setParent(parent)

        # Mock GuiUtils.saveData
        save_mock = mocker.patch('sas.qtgui.Utilities.GuiUtils.GuiUtils.saveData')

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            result = dialog._saveProjectFile(filepath)
            assert result is True
            save_mock.assert_called_once()
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_saveProjectFile_exception_handling(self, dialog, mocker):
        """Test _saveProjectFile handles exceptions gracefully"""
        parent = MagicMock()
        gui_manager = MagicMock()
        files_widget = MagicMock()
        files_widget.getSerializedData.side_effect = Exception("Test error")
        gui_manager.filesWidget = files_widget
        parent.guiManager = gui_manager
        dialog.setParent(parent)

        result = dialog._saveProjectFile("/tmp/test_project.json")
        assert result is False

    def test_onExport_validation_failure(self, dialog, mocker):
        """Test onExport when validation fails"""
        # Make validation fail by clearing required fields
        dialog.txtProjectTitle.setText("")
        dialog.txtSampleTitle.setText("")

        msgbox_mock = mocker.patch.object(QtWidgets.QMessageBox, 'warning')

        dialog.onExport()

        # Should show validation error, not file dialog
        msgbox_mock.assert_called_once()
        call_args = msgbox_mock.call_args
        assert call_args[0][1] == "Validation Error"

    def test_file_naming_with_complex_path(self, dialog, mocker):
        """Test file naming with complex directory path"""
        test_json = "/tmp/subfolder/test_export.json"
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName',
                          return_value=(test_json, "JSON file (*.json)"))

        json_mock = mocker.patch(
            'sas.qtgui.Utilities.SASBDB.sasbdb_exporter.SASBDBExporter.export_to_json',
            return_value=True
        )
        pdf_mock = mocker.patch.object(dialog, '_generatePDFReport')
        project_mock = mocker.patch.object(dialog, '_saveProjectFile', return_value=True)
        mocker.patch.object(QtWidgets.QMessageBox, 'information')
        mocker.patch.object(dialog, 'close')

        dialog.onExport()

        # Verify PDF filename uses same directory
        pdf_args = pdf_mock.call_args[0]
        assert pdf_args[1] == "/tmp/subfolder/test_export.pdf"

        # Verify project filename uses same directory
        project_args = project_mock.call_args[0]
        assert project_args[0] == "/tmp/subfolder/test_export_project.json"

    def test_onExport_updates_save_location(self, dialog, mocker):
        """Test that onExport updates the save_location"""
        test_json = "/tmp/new_location/test_export.json"
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName',
                          return_value=(test_json, "JSON file (*.json)"))

        mocker.patch(
            'sas.qtgui.Utilities.SASBDB.sasbdb_exporter.SASBDBExporter.export_to_json',
            return_value=True
        )
        mocker.patch.object(dialog, '_generatePDFReport')
        mocker.patch.object(dialog, '_saveProjectFile', return_value=True)
        mocker.patch.object(QtWidgets.QMessageBox, 'information')
        mocker.patch.object(dialog, 'close')

        dialog.onExport()

        # Verify save_location was updated
        assert dialog.save_location == "/tmp/new_location"

