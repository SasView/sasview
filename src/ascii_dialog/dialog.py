from PySide6.QtGui import QColor, QContextMenuEvent, QCursor, Qt
from PySide6.QtWidgets import QAbstractScrollArea, QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QHeaderView, QLabel, \
    QMessageBox, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QApplication, QDialog
from PySide6.QtCore import QModelIndex, QPoint, Slot
from selection_menu import SelectionMenu
from warning_label import WarningLabel
from col_editor import ColEditor
from row_status_widget import RowStatusWidget
from guess import guess_column_count, guess_columns, guess_starting_position
from os import path
from sasdata.dataset_types import DatasetType, dataset_types, one_dim, two_dim, sesans
from sasdata.temp_ascii_reader import load_data, AsciiReaderParams, split_line
from metadata_filename_gui.metadata_filename_dialog import MetadataFilenameDialog
from metadata_filename_gui.metadata_tree_data import initial_metadata_dict
from sasdata.ascii_reader_metadata import AsciiReaderMetadata
from constants import TABLE_MAX_ROWS, NOFILE_TEXT
import re

dataset_dictionary = dict([(dataset.name, dataset) for dataset in [one_dim, two_dim, sesans]])

class AsciiDialog(QDialog):
    """A dialog window allowing the user to adjust various properties regarding
    how an ASCII file should be interpreted. This widget allows the user to
    visualise what the data will look like with the parameter the user has
    selected.

    """
    def __init__(self):
        super().__init__()

        self.files: dict[str, list[str]] = {}
        self.files_full_path: dict[str, str] = {}
        self.files_is_included: dict[str, list[bool]] = {}
        # This is useful for whenever the user wants to reopen the metadata editor.
        self.internal_metadata: AsciiReaderMetadata = AsciiReaderMetadata()
        self.current_filename: str | None = None

        self.seperators: dict[str, bool] = {
            'Comma': True,
            'Whitespace': True,
            'Tab': True
        }

        self.setWindowTitle('ASCII File Reader')

        # Filename, unload button, and edit metadata button.

        self.filename_unload_layout = QHBoxLayout()
        self.filename_label = QLabel(NOFILE_TEXT)
        self.unloadButton = QPushButton("Unload")
        self.unloadButton.setDisabled(True)
        self.editMetadataButton = QPushButton("Edit Metadata")
        self.editMetadataButton.setDisabled(True)
        self.editMetadataButton.clicked.connect(self.editMetadata)
        self.unloadButton.clicked.connect(self.unload)
        self.filename_unload_layout.addWidget(self.filename_label)
        self.filename_unload_layout.addWidget(self.unloadButton)
        self.filename_unload_layout.addWidget(self.editMetadataButton)

        # Filename chooser
        self.filename_chooser = QComboBox()
        self.filename_chooser.currentTextChanged.connect(self.updateCurrentFile)

        self.load_button = QPushButton("Load File")
        self.load_button.clicked.connect(self.load_file)

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
            check_box.clicked.connect(self.seperatorToggle)
            self.sep_widgets.append(check_box)
            self.sep_layout.addWidget(check_box)

        ## Starting Line
        self.startline_layout = QHBoxLayout()
        self.startline_label = QLabel('Starting Line')
        self.startline_entry = QSpinBox()
        self.startline_entry.setMinimum(1)
        self.startline_entry.valueChanged.connect(self.updateStartpos)
        self.startline_layout.addWidget(self.startline_label)
        self.startline_layout.addWidget(self.startline_entry)

        ## Column Count
        self.colcount_layout = QHBoxLayout()
        self.colcount_label = QLabel('Number of Columns')
        self.colcount_entry = QSpinBox()
        self.colcount_entry.setMinimum(1)
        self.colcount_entry.valueChanged.connect(self.updateColcount)
        self.colcount_layout.addWidget(self.colcount_label)
        self.colcount_layout.addWidget(self.colcount_entry)

        ## Column Editor
        options =  self.datasetOptions()
        self.col_editor = ColEditor(self.colcount_entry.value(), options)
        self.dataset_combobox.currentTextChanged.connect(self.changeDatasetType)
        self.col_editor.column_changed.connect(self.updateColumn)

        ## Data Table

        self.table = QTableWidget()
        self.table.show()
        # Make the table readonly
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # The table's width will always resize to fit the amount of space it has.
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        # Add the context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.showContextMenu)

        # Warning Label
        self.warning_label: WarningLabel = WarningLabel(self.requiredMissing(), self.duplicateColumns())

        # Done button
        # TODO: Not entirely sure what to call/label this. Just going with 'done' for now.

        self.done_button = QPushButton('Done')
        self.done_button.clicked.connect(self.onDoneButton)

        self.layout = QVBoxLayout(self)

        self.layout.addLayout(self.filename_unload_layout)
        self.layout.addWidget(self.filename_chooser)
        self.layout.addWidget(self.load_button)
        self.layout.addLayout(self.dataset_layout)
        self.layout.addLayout(self.sep_layout)
        self.layout.addLayout(self.startline_layout)
        self.layout.addLayout(self.colcount_layout)
        self.layout.addWidget(self.col_editor)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.warning_label)
        self.layout.addWidget(self.done_button)

    @property
    def starting_pos(self) -> int:
        return self.startline_entry.value() - 1

    @starting_pos.setter
    def starting_pos(self, value: int):
        self.startline_entry.setValue(value + 1)

    @property
    def raw_csv(self) -> list[str] | None:
        if self.current_filename is None:
            return None
        return self.files[self.current_filename]

    @property
    def rows_is_included(self) -> list[bool] | None:
        if self.current_filename is None:
            return None
        return self.files_is_included[self.current_filename]

    @property
    def excluded_lines(self) -> set[int]:
        return set([i for i, included in enumerate(self.rows_is_included) if not included])

    def splitLine(self, line: str) -> list[str]:
        """Split a line in a CSV file based on which seperators the user has
        selected on the widget.

        """
        return split_line(self.seperators, line)

    def attemptGuesses(self) -> None:
        """Attempt to guess various parameters of the data to provide some
        default values. Uses the guess.py module

        """
        split_csv = [self.splitLine(line.strip()) for line in self.raw_csv]

        # TODO: I'm not sure if there is any point in holding this initial value. Can possibly be refactored.
        self.initial_starting_pos = guess_starting_position(split_csv)

        guessed_colcount = guess_column_count(split_csv, self.initial_starting_pos)
        self.col_editor.setCols(guessed_colcount)

        columns = guess_columns(guessed_colcount, self.currentDatasetType())
        self.col_editor.setColOrder(columns)
        self.colcount_entry.setValue(guessed_colcount)
        self.starting_pos = self.initial_starting_pos

    def fillTable(self) -> None:
        """Write the data to the table based on the parameters the user has
        selected.

        """

        # Don't try to fill the table if there's no data.
        if self.raw_csv is None:
            return

        self.table.clear()

        col_count = self.colcount_entry.value()

        self.table.setRowCount(min(len(self.raw_csv), TABLE_MAX_ROWS + 1))
        self.table.setColumnCount(col_count + 1)
        self.table.setHorizontalHeaderLabels(["Included"] + self.col_editor.colNames())
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Now fill the table with data
        for i, row in enumerate(self.raw_csv):
            if i == TABLE_MAX_ROWS:
                #  Fill with elipsis to indicate there is more data.
                for j in range(len(row_split)):
                    elipsis_item = QTableWidgetItem("...")
                    elipsis_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(i, j, elipsis_item)
                break

            if i < len(self.rows_is_included):
                initial_state = self.rows_is_included[i]
            else:
                initial_state = True
                self.rows_is_included.append(initial_state)
            if i >= self.starting_pos:
                row_status = RowStatusWidget(initial_state, i)
                row_status.status_changed.connect(self.updateRowStatus)
                self.table.setCellWidget(i, 0, row_status)
            row_split = self.splitLine(row)
            for j, col_value in enumerate(row_split):
                if j >= col_count:
                    continue # Ignore rows that have extra columns.
                item = QTableWidgetItem(col_value)
                self.table.setItem(i, j + 1, item)
            self.setRowTypesetting(i, self.rows_is_included[i])

        self.table.show()

    def currentDatasetType(self) -> DatasetType:
        """Get the dataset type that the user has currently selected."""
        return dataset_dictionary[self.dataset_combobox.currentText()]

    def setRowTypesetting(self, row: int, item_checked: bool) -> None:
        """Set the typesetting for the given role depending on whether it is to
        be included in the data being loaded, or not.

        """
        for column in range(1, self.table.columnCount() + 1):
            item = self.table.item(row, column)
            if item is None:
                continue
            item_font = item.font()
            if not item_checked or row < self.starting_pos:
                item.setForeground(QColor.fromString('grey'))
                item_font.setStrikeOut(True)
            else:
                item.setForeground(QColor.fromString('black'))
                item_font.setStrikeOut(False)
            item.setFont(item_font)

    def updateWarningLabel(self):
        required_missing = self.requiredMissing()
        duplicates = self.duplicateColumns()
        if self.raw_csv is None:
            # We don't have any actual data yet so we're just updating the warning based on the column.
            self.warning_label.update_warning(required_missing, duplicates)
        else:
            self.warning_label.update_warning(required_missing, duplicates, [self.splitLine(line) for line in self.raw_csv], self.rows_is_included, self.starting_pos)

    @Slot()
    def load_file(self) -> None:
        """Open the file loading dialog, and load the file the user selects."""
        filenames, result = QFileDialog.getOpenFileNames(self)
        # Happens when the user cancels without selecting a file. There isn't a
        # file to load in this case.
        if result == '':
            return
        for filename in filenames:

            basename = path.basename(filename)
            self.filename_label.setText(basename)

            try:
                with open(filename) as file:
                    file_csv = file.readlines()
                file_csv = [line.strip() for line in file_csv]
                # TODO: This assumes that no two files will be loaded with the same
                # name. This might not be a reasonable assumption.
                self.files[basename] = file_csv
                self.files_full_path[basename] = filename
                # Reset checkboxes
                self.files_is_included[basename] = []
                if len(self.files) == 1:
                    # Default behaviour is going to be to set this to the first file we load. This seems sensible but
                    # may provoke further discussion.
                    self.current_filename = basename
                # This will trigger the update current file event which will cause
                # the table to be drawn.
                self.internal_metadata.init_separator(basename)
                self.filename_chooser.addItem(basename)
                self.filename_chooser.setCurrentText(basename)
                self.internal_metadata.add_file(basename)

            except OSError:
                QMessageBox.critical(self, 'File Read Error', f'There was an error reading {basename}')
            except UnicodeDecodeError:
                QMessageBox.critical(self, 'File Read Error', f"""There was an error decoding {basename}.
This could potentially be because the file {basename} an ASCII format.""")
        # Attempt guesses on the first file that was loaded.
        self.attemptGuesses()

    @Slot()
    def unload(self) -> None:
        del self.files[self.current_filename]
        self.filename_chooser.removeItem(self.filename_chooser.currentIndex())
        # Filename chooser should now revert back to a different file.
        self.updateCurrentFile()

    @Slot()
    def updateColcount(self) -> None:
        """Triggered when the amount of columns the user has selected has
        changed.

        """
        self.col_editor.setCols(self.colcount_entry.value())
        self.fillTable()
        self.updateWarningLabel()

    @Slot()
    def updateStartpos(self) -> None:
        """Triggered when the starting position of the data has changed."""
        self.fillTable()
        self.updateWarningLabel()

    @Slot()
    def updateSeperator(self) -> None:
        """Changed when the user modifies the set of seperators being used."""
        self.fillTable()
        self.updateWarningLabel()

    @Slot()
    def updateColumn(self) -> None:
        """Triggered when any of the columns has been changed."""
        self.fillTable()
        self.updateWarningLabel()

    @Slot()
    def updateCurrentFile(self) -> None:
        """Triggered when the current file (choosen from the file chooser
        ComboBox) changes.

        """
        self.current_filename = self.filename_chooser.currentText()
        self.filename_label.setText(self.current_filename)
        if self.current_filename == '':
            self.table.clear()
            self.filename_label.setText(NOFILE_TEXT)
            self.table.setDisabled(True)
            self.unloadButton.setDisabled(True)
            self.editMetadataButton.setDisabled(True)
            # Set this to None because other methods are expecting this.
            self.current_filename = None
        else:
            self.table.setDisabled(False)
            self.unloadButton.setDisabled(False)
            self.editMetadataButton.setDisabled(False)
            self.fillTable()
            self.updateWarningLabel()

    @Slot()
    def seperatorToggle(self) -> None:
        """Triggered when one of the seperator check boxes has been toggled."""
        check_box = self.sender()
        self.seperators[check_box.text()] = check_box.isChecked()
        self.fillTable()
        self.updateWarningLabel()

    @Slot()
    def changeDatasetType(self) -> None:
        """Triggered when the selected dataset type has changed."""
        options = self.datasetOptions()
        self.col_editor.replaceOptions(options)

        # Update columns as they'll be different now.
        columns = guess_columns(self.colcount_entry.value(), self.currentDatasetType())
        self.col_editor.setColOrder(columns)

    @Slot()
    def updateRowStatus(self, row: int) -> None:
        """Triggered when the status of row has changed."""
        new_status = self.table.cellWidget(row, 0).isChecked()
        self.rows_is_included[row] = new_status
        self.setRowTypesetting(row, new_status)

    @Slot()
    def showContextMenu(self, point: QPoint) -> None:
        """Show the context menu for the table."""
        context_menu = SelectionMenu(self)
        context_menu.select_all_event.connect(self.selectItems)
        context_menu.deselect_all_event.connect(self.deselectItems)
        context_menu.exec(QCursor.pos())

    def changeInclusion(self, indexes: list[QModelIndex], new_value: bool):
        for index in indexes:
            # This will happen if the user has selected a point which exists before the starting line. To prevent an
            # error, this code will skip that position.
            row = index.row()
            if row < self.starting_pos:
                continue
            self.table.cellWidget(row, 0).setChecked(new_value)
            self.updateRowStatus(row)

    @Slot()
    def selectItems(self) -> None:
        """Include all of the items that have been selected in the table."""
        self.changeInclusion(self.table.selectedIndexes(), True)
        self.updateWarningLabel()

    @Slot()
    def deselectItems(self) -> None:
        """Don't include all of the items that have been selected in the table."""
        self.changeInclusion(self.table.selectedIndexes(), False)
        self.updateWarningLabel()

    def requiredMissing(self) -> list[str]:
        """Returns all the columns that are required by the dataset type but
        have not currently been selected.

        """
        dataset = self.currentDatasetType()
        missing_columns = [col for col in dataset.required if col not in self.col_editor.colNames()]
        return missing_columns

    def duplicateColumns(self) -> set[str]:
        """Returns all of the columns which have been selected multiple times."""
        col_names = self.col_editor.colNames()
        return set([col for col in col_names if not col == '<ignore>' and col_names.count(col) > 1])

    def datasetOptions(self) -> list[str]:
        current_dataset_type = self.currentDatasetType()
        return current_dataset_type.required + current_dataset_type.optional + ['<ignore>']

    # TODO: Only works for one single file at the moment
    def onDoneButton(self):
        params = AsciiReaderParams(
            self.files_full_path.values(),
            self.starting_pos,
            self.col_editor.columns,
            self.excluded_lines,
            self.seperators,
            self.internal_metadata
        )
        self.params = params
        self.accept()

    def editMetadata(self):
        dialog = MetadataFilenameDialog(self.current_filename, self.internal_metadata)
        status = dialog.exec()
        if status == 1:
            self.internal_metadata = dialog.internal_metadata


if __name__ == "__main__":
    app = QApplication([])

    dialog = AsciiDialog()
    status = dialog.exec()
    # 1 means the dialog was accepted.
    if status == 1:
        loaded = load_data(dialog.params)
        for datum in loaded:
            print(datum.summary())

    exit()
