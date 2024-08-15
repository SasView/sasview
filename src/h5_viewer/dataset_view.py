#!/usr/bin/env python3

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from h5py import Dataset


class DatasetViewWidget(QWidget):
    def __init__(self, initial_dataset: Dataset | None):
        super().__init__()
        self._current_dataset: Dataset | None = initial_dataset

        self.dataset_label = QLabel('Select a dataset on the left to view it.')

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.dataset_label)

    def update_view(self):
        if not self._current_dataset is None:
            self.dataset_label.setText(self._current_dataset.name)

    @property
    def current_dataset(self):
        return self.current_dataset

    @current_dataset.setter
    def current_dataset(self, value: Dataset):
        self._current_dataset = value
        self.update_view()
