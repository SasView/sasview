from PySide6.QtWidgets import QLabel
from ascii_dialog.constants import TABLE_MAX_ROWS


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

    def update_warning(self, missing_columns: list[str], duplicate_columns: list[str], lines: list[list[str]] | None = None, rows_is_included: list[bool] | None = None, starting_pos: int = 0):
        """Determine, and set the appropriate warning messages given how many
        columns are missing, and how many columns are duplicated."""
        unparsable = 0
        if lines is not None and rows_is_included is not None:
            # FIXME: I feel like I am repeating a lot of logic from the table filling. Is there a way I can abstract
            # this?
            for i, line in enumerate(lines):
                # Right now, rows_is_included only includes a limited number of rows as there is a maximum that can be
                # shown in the table without it being really laggy. We're just going to assume the lines after it should
                # be included.
                if (i >= TABLE_MAX_ROWS or rows_is_included[i]) and i >= starting_pos:
                    # TODO: Is there really no builtin function for this? I don't like using try/except like this.
                    try:
                        for item in line:
                            _ = float(item)
                    except:
                        unparsable += 1

        if len(missing_columns) != 0:
            self.setText(f'The following columns are missing: {missing_columns}')
            self.setFontRed()
        elif len(duplicate_columns) > 0:
            self.setText(f'There are columns which are repeated.')
            self.setFontRed()
        elif unparsable > 0:
            # FIXME: This error message could perhaps be a bit clearer.
            self.setText(f'{unparsable} lines cannot be parsed. They will be ignored.')
            self.setFontOrange()
        else:
            self.setText('')

    def __init__(self, initial_missing_columns, initial_duplicate_classes):
        super().__init__()
        self.update_warning(initial_missing_columns, initial_duplicate_classes)
