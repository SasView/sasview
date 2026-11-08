"""Tests for the warning shown in the ASCII dialog about lines that can't be read."""
from unittest import mock

import pytest
from PySide6.QtWidgets import QFileDialog

from sas.ascii_dialog.dialog import AsciiDialog
from sas.ascii_dialog.warning_label import WarningLabel

# Q, I, dI data with some lines that can't be read. Line numbers (from 1) are in the comments.
TEST_FILE = (
    "0.01\t100\t1\n"  # 1
    "wrong line\n"  # 2: not numbers -> skipped
    "0.02\t90\t2\n"  # 3
    "1 2 3 4\n"  # 4: extra numeric column -> loaded (4 is ignored)
    "8 9 10 a\n"  # 5: extra non-numeric column -> loaded (a is ignored)
    "11 12 b\n"  # 6: non-numeric value in dI -> skipped
    "5 6\n"  # 7: too few columns -> skipped
    "0.03\t80\t3\n"  # 8
)


def split(text: str) -> list[list[str]]:
    return [line.split() for line in text.splitlines()]


@pytest.fixture
def label(qapp):
    return WarningLabel([], [])


class WarningLabelTest:
    def testOnlyUsedColumnsChecked(self, label):
        lines = split(TEST_FILE)
        label.updateWarning([], [], lines, [True] * len(lines), 0, used_columns=[0, 1, 2])
        assert label.text() == "3 lines could not be read (lines 2, 6, 7). They will be ignored."

    def testIgnoredColumnNotChecked(self, label):
        # The third column is ignored, so "11 12 b" can be read, but "5 6" still can't.
        lines = split(TEST_FILE)
        label.updateWarning([], [], lines, [True] * len(lines), 0, used_columns=[0, 1])
        assert label.text() == "Line 2 could not be read. It will be ignored."

    def testAllColumnsCheckedWithoutUsedColumns(self, label):
        # Previous behaviour, kept when the used columns aren't given.
        lines = split(TEST_FILE)
        label.updateWarning([], [], lines, [True] * len(lines), 0)
        assert label.text().startswith("3 lines could not be read (lines 2, 5, 6)")

    def testExcludedAndHeaderLinesNotCounted(self, label):
        lines = split(TEST_FILE)
        included = [True] * len(lines)
        included[5] = False  # "11 12 b" is excluded by the user.
        label.updateWarning([], [], lines, included, 2, used_columns=[0, 1, 2])  # "wrong line" is before the start.
        assert label.text() == "Line 7 could not be read. It will be ignored."

    def testNoWarningWhenAllLinesReadable(self, label):
        lines = split("0.01 100 1\n0.02 90 2\n")
        label.updateWarning([], [], lines, [True, True], 0, used_columns=[0, 1, 2])
        assert label.text() == ""

    def testLongListOfLinesIsShortened(self, label):
        lines = split("x\n" * 15)
        label.updateWarning([], [], lines, [True] * 15, 0, used_columns=[0])
        assert label.text() == (
            "15 lines could not be read (lines 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, ...). They will be ignored."
        )

    def testMissingColumnsTakePriority(self, label):
        lines = split(TEST_FILE)
        label.updateWarning(["dI"], [], lines, [True] * len(lines), 0, used_columns=[0, 1, 2])
        assert label.text() == "The following columns are missing: ['dI']"


class AsciiDialogWarningTest:
    def testWarningMatchesFile(self, qapp, tmp_path):
        filename = tmp_path / "test_data.txt"
        filename.write_text(TEST_FILE)
        dialog = AsciiDialog()
        dialog.dataset_combobox.setCurrentText("1D I vs Q")
        with mock.patch.object(QFileDialog, "getOpenFileNames", return_value=([str(filename)], "All (*)")):
            dialog.loadFile()
        assert dialog.col_editor.colNames() == ["Q", "I", "dI"]
        assert dialog.warning_label.text() == "3 lines could not be read (lines 2, 6, 7). They will be ignored."
