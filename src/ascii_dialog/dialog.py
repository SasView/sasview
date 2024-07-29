from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget, QApplication
from PySide6.QtCore import Slot
from col_editor import ColEditor
from guess import guess_column_count, guess_seperator
from os import path

class AsciiDialog(QWidget):
    def __init__(self):
        super().__init__()

        self.raw_csv = None

        self.filename_label = QLabel("Click the button below to load a file.")

        self.load_button = QPushButton("Load File")
        self.load_button.clicked.connect(self.load)

        # Data parameters

        ## Seperator
        self.sep_layout = QHBoxLayout()
        self.sep_label = QLabel('Seperator')
        self.sep_entry = QLineEdit()
        self.sep_layout.addWidget(self.sep_label)
        self.sep_layout.addWidget(self.sep_entry)

        ## Starting Line
        self.startline_layout = QHBoxLayout()
        self.startline_label = QLabel('Starting Line')
        self.startline_entry = QSpinBox()
        self.startline_layout.addWidget(self.startline_label)
        self.startline_layout.addWidget(self.startline_entry)

        ## Column Count
        self.colcount_layout = QHBoxLayout()
        self.colcount_label = QLabel('Number of Columns')
        self.colcount_entry = QSpinBox()
        self.colcount_layout.addWidget(self.colcount_label)
        self.colcount_layout.addWidget(self.colcount_entry)

        ## Column Editor
        self.col_editor = ColEditor(4) ## TODO: 4 is just a placeholder. Use value from colcount

        self.layout = QVBoxLayout(self)

        self.layout.addWidget(self.filename_label)
        self.layout.addWidget(self.load_button)
        self.layout.addLayout(self.sep_layout)
        self.layout.addLayout(self.startline_layout)
        self.layout.addLayout(self.colcount_layout)
        self.layout.addWidget(self.col_editor)

    def attempt_guesses(self):
        guessed_seperator = guess_seperator(self.raw_csv)
        if guessed_seperator == None:
            # Seperator couldn't be guessed; just let the user fill that in.
            guessed_seperator = ''

        self.sep_entry.setText(guessed_seperator)

        guessed_colcount = guess_column_count(self.raw_csv, guessed_seperator, self.startline_entry.value())
        self.colcount_entry.setValue(guessed_colcount)

    @Slot()
    def load(self):
        filename = QFileDialog.getOpenFileName(self)[0]
        self.filename_label.setText(path.basename(filename))

        # TODO: Add error handling
        with open(filename) as file:
            self.raw_csv = file.readlines()

        self.attempt_guesses()


if __name__ == "__main__":
    app = QApplication([])

    widget = AsciiDialog()
    widget.show()


    exit(app.exec())
