

from PySide6.QtWidgets import QLabel


class WarningLabel(QLabel):
    def update(self, missing_columns):
        if len(missing_columns) == 0:
            self.setText('All is fine') # TODO: Probably want to find a more appropriate message.
            self.setStyleSheet('')
        else:
            self.setText(f'The following columns are missing: {missing_columns}')
            self.setStyleSheet("QLabel { color: red}")


    def __init__(self, initial_missing_columns):
        super().__init__()
        self.update(initial_missing_columns)
