"""Tests for the default settings and labels of the ASCII dialog (issue #4200)."""
import pytest

from sasdata.ascii_reader_metadata import AsciiReaderMetadata
from sasdata.dataset_types import angle_dim, one_dim, sesans, two_dim

from sas.ascii_dialog.dialog import AsciiDialog
from sas.metadata_filename_gui.metadata_filename_dialog import MetadataFilenameDialog


@pytest.fixture
def dialog(qapp):
    return AsciiDialog()


class AsciiDialogDefaultsTest:
    def testDatasetTypeOrder(self, dialog):
        # The options used to come from a set, so their order changed every time SasView was started.
        options = [dialog.dataset_combobox.itemText(i) for i in range(dialog.dataset_combobox.count())]
        assert options == [one_dim.name, two_dim.name, angle_dim.name, sesans.name]

    def testDefaultDatasetTypeIs1D(self, dialog):
        assert dialog.dataset_combobox.currentText() == one_dim.name
        assert dialog.currentDatasetType() == one_dim

    def testSeparatorsLabel(self, dialog):
        assert dialog.sep_label.text() == "Separators:"


class MetadataFilenameDialogLabelTest:
    def testSeparatorsLabel(self, qapp):
        filename = "1_33_1640_22.874115.csv"
        metadata = AsciiReaderMetadata()
        metadata.init_separator(filename)
        metadata.add_file(filename)
        metadata_dialog = MetadataFilenameDialog(filename, metadata)
        assert metadata_dialog.seperator_chars_label.text() == "Separators"
