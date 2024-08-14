#!/usr/bin/env python3

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from h5py import File as H5File
from h5py import Group as H5Group
from h5py import Dataset

class Hd5TreeWidget(QTreeWidget):
    def __init__(self, hd5_file: H5File):
        super().__init__()
        self.hd5_file: H5File = hd5_file

    def __add_to_tree__(self, root: QTreeWidgetItem, group: H5Group):
        for group_item in group.items():
            if group_item is H5Group:
                new_tree_item = QTreeWidgetItem(root, [group_item.name])
                self.__add_to_tree__(new_tree_item, group_item)
            elif group_item is Dataset:
                # TODO: Might be able to reduce code duplication here.
                new_tree_item = QTreeWidgetItem(root, [group_item.name])


    def update_tree(self):
        self.__add_to_tree__(self.invisibleRootItem(), self.hd5_file.parent)
