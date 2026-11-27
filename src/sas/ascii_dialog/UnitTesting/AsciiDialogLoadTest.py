"""Tests for what the ASCII dialog passes to the loader (issue #4215)."""
from unittest import mock

import pytest
from PySide6.QtWidgets import QFileDialog

from sasdata.data_io.importers.import_ascii import load_data
from sasdata.dataset_types import angle_dim, one_dim, two_dim

from sas.ascii_dialog.dialog import AsciiDialog

DATA_1D = "0.01 100 1\n0.02 90 2\n0.03 80 3\n"
DATA_2D = "0.01 0.02 100 1\n0.02 0.03 90 2\n0.03 0.04 80 3\n"
DATA_PHI = "10 100 1\n20 90 2\n30 80 3\n"


def load_files(dialog: AsciiDialog, filenames: list[str]):
    with mock.patch.object(QFileDialog, "getOpenFileNames", return_value=(filenames, "All (*)")):
        dialog.loadFile()


@pytest.fixture
def dialog(qapp):
    return AsciiDialog()


class AsciiDialogDatasetTypeTest:
    @pytest.mark.parametrize(
        "dataset_type, text, columns",
        [(one_dim, DATA_1D, {"Q", "I"}), (two_dim, DATA_2D, {"Qx", "Qy", "I"}), (angle_dim, DATA_PHI, {"Phi", "I"})],
    )
    def testDatasetTypePassedToLoader(self, dialog, tmp_path, dataset_type, text, columns):
        filename = tmp_path / "data.txt"
        filename.write_text(text)
        dialog.dataset_combobox.setCurrentText(dataset_type.name)
        load_files(dialog, [str(filename)])

        dialog.onDoneButton()

        assert dialog.params.dataset_type == dataset_type
        # Used to fail for 2D data with "Columns don't match the dataset type", and for I vs Phi data with
        # "Current unit doesn't seem to exist" as the I column was given the unit of the previous column
        data = load_data(dialog.params)[0]
        assert set(data._data_contents) == columns


class AsciiDialogUnloadTest:
    def testUnloadedFileIsNotLoaded(self, dialog, tmp_path):
        filenames = []
        for name in ["first.txt", "second.txt"]:
            filename = tmp_path / name
            filename.write_text(DATA_1D)
            filenames.append(str(filename))
        load_files(dialog, filenames)
        dialog.filename_chooser.setCurrentText("second.txt")

        dialog.unload()

        assert dialog.current_filename == "first.txt"
        assert dialog.filename_chooser.count() == 1
        assert list(dialog.files) == ["first.txt"]
        assert list(dialog.files_is_included) == ["first.txt"]
        assert "second.txt" not in dialog.internal_metadata.filename_specific_metadata
        dialog.onDoneButton()
        assert dialog.params.filenames == [filenames[0]]

    def testUnloadLastFile(self, dialog, tmp_path):
        filename = tmp_path / "data.txt"
        filename.write_text(DATA_1D)
        load_files(dialog, [str(filename)])

        dialog.unload()

        assert dialog.current_filename is None
        assert dialog.filename_chooser.count() == 0
        assert not dialog.unloadButton.isEnabled()
        dialog.onDoneButton()
        assert dialog.params.filenames == []
