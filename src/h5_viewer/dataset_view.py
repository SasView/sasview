#!/usr/bin/env python3

from PySide6.QtWidgets import QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from h5py import Dataset
from numpy import ndarray


class DatasetViewWidget(QWidget):
    def __init__(self, initial_dataset: Dataset | None):
        super().__init__()
        self._current_dataset: Dataset | None = initial_dataset

        self.dataset_label = QLabel()
        self.table = QTableWidget()
        # Make the table readonly
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.dataset_label)
        self.layout.addWidget(self.table)

        self.update_view()

    def update_view(self):
        if self._current_dataset is None:
            self.dataset_label.setText('Select a dataset on the left to view it.')
        else:
            self.dataset_label.setText(self._current_dataset.name)
        self.fill_table()

    def fill_table(self):
        self.table.clear()
        if self._current_dataset is None:
            self.table.setDisabled(True)
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
        else:
            self.table.setDisabled(False)
            self.table.setColumnCount(self._current_dataset.ndim)
            self.table.setRowCount(self._current_dataset.shape[0])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            for i, row in enumerate(self._current_dataset):
                # If the dataset is 1 dimensional then 'row' is just the value
                # itself but otherwise it'll be an array of values.
                if isinstance(row, ndarray):
                    columns = row
                else:
                    columns = [row]
                for j, col in enumerate(columns):
                    item = QTableWidgetItem(str(col))
                    self.table.setItem(i, j, item)
        self.table.show()


    @property
    def current_dataset(self):
        return self.current_dataset

    @current_dataset.setter
    def current_dataset(self, value: Dataset | None):
        self._current_dataset = value
        self.update_view()
