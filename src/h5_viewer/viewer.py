#!/usr/bin/env python3

from PySide6.QtCore import Slot
import h5py
from PySide6.QtWidgets import QApplication, QHBoxLayout, QSizePolicy, QWidget
from h5py._hl.dataset import Dataset
from h5_tree import Hd5TreeWidget
from h5py import File as H5File
from sys import argv

from dataset_view import DatasetViewWidget

class Hd5Viewer(QWidget):
    def __init__(self, hd5_file: H5File):
        super().__init__()
        self.hd5_file = hd5_file

        # Tree widget
        self.tree = Hd5TreeWidget(self.hd5_file)
        self.tree.update_tree()
        self.tree.selection_changed.connect(self.change_selection)
        self.tree.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        # Viewer widget
        self.dataset_viewer = DatasetViewWidget(None)

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.tree)
        self.layout.addWidget(self.dataset_viewer)

    @Slot()
    def change_selection(self):
        new_selection = self.tree.selected_item
        if isinstance(new_selection, Dataset):
            self.dataset_viewer.current_dataset = new_selection
        else:
            self.dataset_viewer.current_dataset = None

if __name__ == "__main__":
    if len(argv) < 2:
        print('Please enter a file to load as a command line argument.')
    else:
        app = QApplication([])
        to_load = H5File(argv[1], 'r')
        widget = Hd5Viewer(to_load)
        widget.show()
        exit(app.exec())