from PySide6.QtWidgets import QLabel

from sas.ascii_dialog.constants import TABLE_MAX_ROWS

# Maximum number of unreadable line numbers listed in the warning message.
MAX_LINES_LISTED = 10


class WarningLabel(QLabel):
    """Widget to display an appropriate warning message based on whether there
    exists columns that are missing, or there are columns that are duplicated.

    """
    def setFontRed(self):
        self.setStyleSheet("QLabel { color: red}")

    def setFontOrange(self):
        self.setStyleSheet("QLabel { color: orange}")

    def setFontNormal(self):
        self.setStyleSheet('')

    def updateWarning(
        self,
        missing_columns: list[str],
        duplicate_columns: list[str],
        lines: list[list[str]] | None = None,
        rows_is_included: list[bool] | None = None,
        starting_pos: int = 0,
        used_columns: list[int] | None = None,
    ):
        """Determine, and set the appropriate warning messages given how many
        columns are missing, how many columns are duplicated, and which lines
        can't be read.

        ``used_columns`` holds the indices of the columns that will actually be
        loaded (i.e. not ignored). Only the values in these columns are checked,
        so a line is only reported as unreadable if the loader would skip it.
        If it is None, every value in the line is checked.
        """
        unparsable_lines: list[int] = []
        if lines is not None and rows_is_included is not None:
            for i, line in enumerate(lines):
                # Right now, rows_is_included only includes a limited number of rows as there is a maximum that can be
                # shown in the table without it being really laggy. We're just going to assume the lines after it should
                # be included.
                if (i >= TABLE_MAX_ROWS or rows_is_included[i]) and i >= starting_pos:
                    if not self.isReadable(line, used_columns):
                        unparsable_lines.append(i)

        if len(missing_columns) != 0:
            self.setText(f'The following columns are missing: {missing_columns}')
            self.setFontRed()
        elif len(duplicate_columns) > 0:
            self.setText('There are columns which are repeated.')
            self.setFontRed()
        elif len(unparsable_lines) > 0:
            self.setText(self.unparsableMessage(unparsable_lines))
            self.setFontOrange()
        else:
            self.setText('')

    @staticmethod
    def isReadable(line: list[str], used_columns: list[int] | None) -> bool:
        """Whether all the values that will be loaded from this (already split)
        line can be read as numbers."""
        indices = range(len(line)) if used_columns is None else used_columns
        try:
            for index in indices:
                # An IndexError means the line has fewer values than the columns that will be loaded.
                _ = float(line[index])
        except (ValueError, IndexError):
            return False
        return True

    @staticmethod
    def unparsableMessage(unparsable_lines: list[int]) -> str:
        """Warning message for the lines that can't be read. Line numbers are
        shown starting from 1, as in the table."""
        shown = ', '.join(str(i + 1) for i in unparsable_lines[:MAX_LINES_LISTED])
        if len(unparsable_lines) > MAX_LINES_LISTED:
            shown += ', ...'
        if len(unparsable_lines) == 1:
            return f'Line {shown} could not be read. It will be ignored.'
        return f'{len(unparsable_lines)} lines could not be read (lines {shown}). They will be ignored.'

    def __init__(self, initial_missing_columns, initial_duplicate_classes):
        super().__init__()
        self.updateWarning(initial_missing_columns, initial_duplicate_classes)
