#!/usr/bin/env python3

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from h5py import Dataset


class DatasetViewWidget(QWidget):
    def __init__(self, initial_dataset: Dataset):
        super().__init__()
        self._current_dataset = initial_dataset

        self.dataset_label = QLabel('Select a dataset on the left to view it.')

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.dataset_label)

    @property
    def current_dataset(self):
        return self.current_dataset

    @current_dataset.setter
    def current_dataset(self, value: Dataset):
        self._current_dataset = value
