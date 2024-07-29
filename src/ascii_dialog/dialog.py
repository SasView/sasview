from PySide6 import QtGui
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QApplication
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
        self.colcount_entry.setMinimum(1)
        self.colcount_entry.valueChanged.connect(self.update_colcount)
        self.colcount_layout.addWidget(self.colcount_label)
        self.colcount_layout.addWidget(self.colcount_entry)

        ## Column Editor
        self.col_editor = ColEditor(self.colcount_entry.value())

        ## Data Table

        self.table = QTableWidget()
        self.table.show()
        # Make the table readonly
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.layout = QVBoxLayout(self)

        self.layout.addWidget(self.filename_label)
        self.layout.addWidget(self.load_button)
        self.layout.addLayout(self.sep_layout)
        self.layout.addLayout(self.startline_layout)
        self.layout.addLayout(self.colcount_layout)
        self.layout.addWidget(self.col_editor)
        self.layout.addWidget(self.table)


    def attempt_guesses(self):
        guessed_seperator = guess_seperator(self.raw_csv)
        if guessed_seperator == None:
            # Seperator couldn't be guessed; just let the user fill that in.
            guessed_seperator = ''

        self.sep_entry.setText(guessed_seperator)

        guessed_colcount = guess_column_count(self.raw_csv, guessed_seperator, self.startline_entry.value())
        self.colcount_entry.setValue(guessed_colcount)

    def fill_table(self):
        # At the moment, we're just going to start making the table from where
        # the user told us to start. Just trying this for now. We might want to
        # draw the full table later.

        # Don't try to fill the table if there's no data.
        if self.raw_csv is None:
            return

        starting_pos = self.startline_entry.value()

        self.table.setRowCount(len(self.raw_csv) - starting_pos)
        self.table.setColumnCount(self.colcount_entry.value())
        self.table.setHorizontalHeaderLabels(self.col_editor.col_names())

        # Now fill the table with data
        for i, row in enumerate(self.raw_csv[starting_pos::]):
            row_split = row.split(self.sep_entry.text())
            for j, col_value in enumerate(row_split):
                self.table.setItem(i, j, QTableWidgetItem(col_value))

        self.table.show()


    @Slot()
    def load(self):
        filename = QFileDialog.getOpenFileName(self)[0]
        self.filename_label.setText(path.basename(filename))

        # TODO: Add error handling
        with open(filename) as file:
            self.raw_csv = file.readlines()

        self.attempt_guesses()
        self.fill_table()

    @Slot()
    def update_colcount(self):
        self.col_editor.set_cols(self.colcount_entry.value())

if __name__ == "__main__":
    app = QApplication([])

    widget = AsciiDialog()
    widget.show()


    exit(app.exec())
