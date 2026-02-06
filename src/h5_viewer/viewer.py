#!/usr/bin/env python3

from json import loads
from re import search
from sys import argv

from h5py import File as H5File
from h5py._hl.dataset import Dataset
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QHBoxLayout, QSizePolicy, QStackedWidget, QWidget

from h5_viewer.dataset_view import DatasetViewWidget
from h5_viewer.h5_tree import Hd5TreeWidget
from h5_viewer.json_view import JsonViewWidget
from h5_viewer.str_view import StrViewWidget


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
        self.str_viewer = StrViewWidget(None)
        self.json_viewer = JsonViewWidget(None)
        self.stacked_viewers = QStackedWidget()
        self.stacked_viewers.addWidget(self.dataset_viewer)
        self.stacked_viewers.addWidget(self.str_viewer)
        self.stacked_viewers.addWidget(self.json_viewer)

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.tree)
        self.layout.addWidget(self.stacked_viewers)

    @Slot()
    def change_selection(self):
        new_selection = self.tree.selected_item
        if isinstance(new_selection, Dataset):
            if new_selection.shape == (1,):
                try:
                    new_selection_str = str(new_selection[0], 'utf8')
                    if search(r'{|}|\[|\]', new_selection_str) is not None:
                        self.json_viewer.current_json_dict = loads(new_selection_str)
                        self.stacked_viewers.setCurrentIndex(2)
                    else:
                        self.str_viewer.current_str = new_selection_str
                        self.stacked_viewers.setCurrentIndex(1)
                except UnicodeDecodeError:
                    # Doesn't appear to be a unicode string. It may be a float et cetera. Convert it some other way
                    new_selection_str = str(new_selection[0])
                    self.str_viewer.current_str = new_selection_str
                    self.stacked_viewers.setCurrentIndex(1)
            else:
                self.dataset_viewer.current_dataset = new_selection
                self.stacked_viewers.setCurrentIndex(0)
        elif isinstance(new_selection, str):
            # Do an incredibly simple check to guess whether the text is a JSON
            # file.
            self.str_viewer.current_str = new_selection
            self.stacked_viewers.setCurrentIndex(1)
        else:
            self.dataset_viewer.current_dataset = None
            self.stacked_viewers.setCurrentIndex(0)

if __name__ == "__main__":
    if len(argv) < 2:
        print('Please enter a file to load as a command line argument.')
    else:
        app = QApplication([])
        to_load = H5File(argv[1], 'r')
        widget = Hd5Viewer(to_load)
        widget.show()
        exit(app.exec())
