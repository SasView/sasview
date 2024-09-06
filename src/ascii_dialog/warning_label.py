

from PySide6.QtWidgets import QLabel


class WarningLabel(QLabel):
    """Widget to display an appropriate warning message based on whether there
    exists columns that are missing, or there are columns that are duplicated.

    """
    def setFontRed(self):
        self.setStyleSheet("QLabel { color: red}")

    def setFontNormal(self):
        self.setStyleSheet('')

    def update(self, missing_columns, duplicate_columns):
        """Determine, and set the appropriate warning messages given how many
        columns are missing, and how many columns are duplicated."""
        if len(missing_columns) != 0:
            self.setText(f'The following columns are missing: {missing_columns}')
            self.setFontRed()
        elif len(duplicate_columns) > 0:
            self.setText(f'There are duplicate columns.')
            self.setFontRed()
        else:
            self.setText('All is fine') # TODO: Probably want to find a more appropriate message.
            self.setFontNormal()

    def __init__(self, initial_missing_columns, initial_duplicate_classes):
        super().__init__()
        self.update(initial_missing_columns, initial_duplicate_classes)
