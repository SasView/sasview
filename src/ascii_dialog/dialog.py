from PySide6 import QtGui
from PySide6.QtGui import QColor, QIntValidator, QPalette, Qt
from PySide6.QtWidgets import QAbstractScrollArea, QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QSizePolicy, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QApplication
from PySide6.QtCore import Slot
from warning_label import WarningLabel
from col_editor import ColEditor
from row_status_widget import RowStatusWidget
from guess import guess_column_count, guess_columns, guess_starting_position
from os import path
from dataset_types import DatasetType, dataset_types, one_dim, two_dim, sesans
import re

TABLE_MAX_ROWS = 1000

class AsciiDialog(QWidget):
    def __init__(self):
        super().__init__()

        self.raw_csv: str | None = None

        self.seperators: dict[str, bool] = {
            'Comma': True,
            'Whitespace': True,
            'Tab': True
        }

        self.filename_label = QLabel("Click the button below to load a file.")

        self.load_button = QPushButton("Load File")
        self.load_button.clicked.connect(self.load)

        ## Dataset type selection
        self.dataset_layout = QHBoxLayout()
        self.dataset_label = QLabel("Dataset Type")
        self.dataset_combobox = QComboBox()
        for name in dataset_types:
            self.dataset_combobox.addItem(name)
        self.dataset_layout.addWidget(self.dataset_label)
        self.dataset_layout.addWidget(self.dataset_combobox)

        ## Seperator
        self.sep_layout = QHBoxLayout()

        self.sep_widgets: list[QWidget] = []
        self.sep_label = QLabel('Seperators:')
        self.sep_layout.addWidget(self.sep_label)
        for seperator_name, value in self.seperators.items():
            check_box = QCheckBox(seperator_name)
            check_box.setChecked(value)
            check_box.clicked.connect(self.seperator_toggle)
            self.sep_widgets.append(check_box)
            self.sep_layout.addWidget(check_box)

        ## Starting Line
        self.startline_layout = QHBoxLayout()
        self.startline_label = QLabel('Starting Line')
        self.startline_entry = QSpinBox()
        self.startline_entry.valueChanged.connect(self.update_startpos)
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
        current_dataset_type = self.current_dataset_type()
        options =  current_dataset_type.required + current_dataset_type.optional
        self.col_editor = ColEditor(self.colcount_entry.value(), options)
        self.dataset_combobox.currentTextChanged.connect(self.change_dataset_type)
        self.col_editor.column_changed.connect(self.update_column)

        ## Data Table

        self.table = QTableWidget()
        self.table.show()
        # Make the table readonly
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # The table's width will always resize to fit the amount of space it has.
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        # Warning Label
        self.warning_label = WarningLabel(self.required_missing(), self.duplicate_columns())

        self.layout = QVBoxLayout(self)

        self.layout.addWidget(self.filename_label)
        self.layout.addWidget(self.load_button)
        self.layout.addLayout(self.dataset_layout)
        self.layout.addLayout(self.sep_layout)
        self.layout.addLayout(self.startline_layout)
        self.layout.addLayout(self.colcount_layout)
        self.layout.addWidget(self.col_editor)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.warning_label)

        self.rows_is_included: list[bool] = []

    def split_line(self, line: str) -> list[str]:
        expr = ''
        for seperator, isenabled in self.seperators.items():
            if isenabled:
                if expr != r'':
                    expr += r'|'
                match seperator:
                    case 'Comma':
                        seperator_text = r','
                    case 'Whitespace':
                        seperator_text = r'\s+'
                    case 'Tab':
                        seperator_text = r'\t'
                expr += seperator_text

        return re.split(expr, line)

    def attempt_guesses(self) -> None:
        split_csv = [self.split_line(line.strip()) for line in self.raw_csv]

        self.initial_starting_pos = guess_starting_position(split_csv)

        guessed_colcount = guess_column_count(split_csv,
                                              self.initial_starting_pos)
        self.col_editor.set_cols(guessed_colcount)

        columns = guess_columns(guessed_colcount, self.current_dataset_type())
        self.col_editor.set_col_order(columns)
        self.colcount_entry.setValue(guessed_colcount)
        self.startline_entry.setValue(self.initial_starting_pos)

    def fill_table(self) -> None:
        # Don't try to fill the table if there's no data.
        if self.raw_csv is None:
            return

        self.table.clear()

        starting_pos = self.startline_entry.value()
        col_count = self.colcount_entry.value()

        self.table.setRowCount(min(len(self.raw_csv), TABLE_MAX_ROWS))
        self.table.setColumnCount(col_count + 1)
        self.table.setHorizontalHeaderLabels(["Included"] + self.col_editor.col_names())
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Now fill the table with data
        for i, row in enumerate(self.raw_csv):
            if i < len(self.rows_is_included):
                initial_state = self.rows_is_included[i]
            else:
                initial_state = True
                self.rows_is_included.append(initial_state)
            if i >= starting_pos:
                row_status = RowStatusWidget(initial_state, i)
                row_status.status_changed.connect(self.update_row_status)
                self.table.setCellWidget(i, 0, row_status)
            row_split = self.split_line(row)
            for j, col_value in enumerate(row_split):
                if j >= col_count:
                    continue # Ignore rows that have extra columns.
                item = QTableWidgetItem(col_value)
                self.table.setItem(i, j + 1, item)
            if i == TABLE_MAX_ROWS:
                break

        self.table.show()
        for row in range(self.table.rowCount()):
            self.set_row_typesetting(row, self.rows_is_included[row])

    def current_dataset_type(self) -> DatasetType:
        # TODO: Using linear search but should probably just use a dictionary
        # later.
        for type in [one_dim, two_dim, sesans]:
            if type.name == self.dataset_combobox.currentText():
                return type
        return one_dim

    def set_row_typesetting(self, row: int, item_checked: bool) -> None:
        starting_pos = self.startline_entry.value()
        for column in range(1, self.table.columnCount() + 1):
            item = self.table.item(row, column)
            if item is None:
                continue
            item_font = item.font()
            if not item_checked or row < starting_pos:
                item.setForeground(QColor.fromString('grey'))
                item_font.setStrikeOut(True)
            else:
                item.setForeground(QColor.fromString('black'))
                item_font.setStrikeOut(False)
            item.setFont(item_font)


    @Slot()
    def load(self) -> None:
        result = QFileDialog.getOpenFileName(self)
        # Happens when the user cancels without selecting a file. There isn't a
        # file to load in this case.
        if result[1] == '':
            return
        filename = result[0]
        self.filename_label.setText(path.basename(filename))

        # TODO: Add error handling
        with open(filename) as file:
            self.raw_csv = file.readlines()

        # Reset checkboxes
        self.rows_is_included = []
        self.attempt_guesses()
        self.fill_table()

    @Slot()
    def update_colcount(self) -> None:
        self.col_editor.set_cols(self.colcount_entry.value())
        self.fill_table()

    @Slot()
    def update_startpos(self) -> None:
        self.fill_table()

    @Slot()
    def update_seperator(self) -> None:
        self.fill_table()

    @Slot()
    def update_column(self) -> None:
        self.fill_table()
        required_missing = self.required_missing()
        duplicates = self.duplicate_columns()
        self.warning_label.update(required_missing, duplicates)

    @Slot()
    def seperator_toggle(self) -> None:
        check_box = self.sender()
        self.seperators[check_box.text()] = check_box.isChecked()
        self.fill_table()

    @Slot()
    def change_dataset_type(self) -> None:
        new_dataset = self.current_dataset_type()
        self.col_editor.replace_options(new_dataset.required + new_dataset.optional)

        # Update columns as they'll be different now.
        columns = guess_columns(self.colcount_entry.value(), self.current_dataset_type())
        self.col_editor.set_col_order(columns)

    @Slot()
    def update_row_status(self, row: int) -> None:
        new_status = self.table.cellWidget(row, 0).isChecked()
        self.rows_is_included[row] = new_status
        self.set_row_typesetting(row, new_status)

    def required_missing(self) -> list[str]:
        dataset = self.current_dataset_type()
        missing_columns = [col for col in dataset.required if col not in self.col_editor.col_names()]
        return missing_columns

    def duplicate_columns(self) -> list[str]:
        col_names = self.col_editor.col_names()
        return [col for col in col_names if col_names.count(col) > 1]

if __name__ == "__main__":
    app = QApplication([])

    widget = AsciiDialog()
    widget.show()


    exit(app.exec())
