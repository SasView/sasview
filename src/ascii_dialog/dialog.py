from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QApplication
from PySide6.QtCore import Slot
from guess import guess_seperator
from os import path

class AsciiDialog(QWidget):
    def __init__(self):
        super().__init__()

        self.raw_csv = None

        self.filename_label = QLabel("Click the button below to load a file.")

        self.load_button = QPushButton("Load File")
        self.load_button.clicked.connect(self.load)

        # Data parameters
        self.sep_layout = QHBoxLayout()
        self.sep_label = QLabel('Seperator')
        self.sep_entry = QLineEdit()
        self.sep_layout.addWidget(self.sep_label)
        self.sep_layout.addWidget(self.sep_entry)

        self.layout = QVBoxLayout(self)

        self.layout.addWidget(self.filename_label)
        self.layout.addWidget(self.load_button)
        self.layout.addLayout(self.sep_layout)

    def attempt_guesses(self):
        guessed_seperator = guess_seperator(self.raw_csv)
        if guessed_seperator == None:
            # Seperator couldn't be guessed; just let the user fill that in.
            guessed_seperator = ''

        self.sep_entry.setText(guessed_seperator)

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
