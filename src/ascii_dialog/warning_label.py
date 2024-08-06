

from PySide6.QtWidgets import QLabel


class WarningLabel(QLabel):
    """Widget to display an appropriate warning message based whether there
    exists columns that are missing, or there are columns that are duplicated."""
    def set_font_red(self):
        self.setStyleSheet("QLabel { color: red}")

    def set_font_normal(self):
        self.setStyleSheet('')

    def update(self, missing_columns, duplicate_classes):
        """Determine, and set the appropriate warning messages given how many
        columns are missing, and how many columns are duplicated."""
        if len(missing_columns) != 0:
            self.setText(f'The following columns are missing: {missing_columns}')
            self.set_font_red()
        elif len(duplicate_classes) > 0:
            self.setText(f'There are duplicate columns.')
            self.set_font_red()
        else:
            self.setText('All is fine') # TODO: Probably want to find a more appropriate message.
            self.set_font_normal()

    def __init__(self, initial_missing_columns, initial_duplicate_classes):
        super().__init__()
        self.update(initial_missing_columns, initial_duplicate_classes)
