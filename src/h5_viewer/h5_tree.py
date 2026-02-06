#!/usr/bin/env python3

from importlib import resources

from h5py import Dataset, HLObject
from h5py import File as H5File
from h5py import Group as H5Group
from h5py._hl.attrs import AttributeManager
from h5py._hl.group import Group
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem


class Hd5TreeWidget(QTreeWidget):
    selection_changed = Signal()

    def __init__(self, hd5_file: H5File):
        super().__init__()
        self.header().setVisible(False)
        self.hd5_file: H5File = hd5_file

        with resources.path('sas.qtgui.images.icons', 'folder.svg') as r:
            self.folder_icon = QIcon(str(r))
        with resources.path('sas.qtgui.images.icons', 'empty-page.svg') as r:
            self.empty_page_icon = QIcon(str(r))
        with resources.path('sas.qtgui.images.icons', 'info-circle.svg') as r:
            self.info_circle_icon = QIcon(str(r))

        self.currentItemChanged.connect(self.selection_changed)

    def __add_to_tree__(self, root: QTreeWidgetItem, group: H5Group | AttributeManager):
        for name, group_item in group.items():
            new_tree_item = QTreeWidgetItem(root, [name])
            new_tree_item.setData(0, Qt.ItemDataRole.UserRole, group_item)
            if isinstance(group_item, Group):
                new_tree_item.setIcon(0, self.folder_icon)
                self.__add_to_tree__(new_tree_item, group_item)
            elif isinstance(group_item, Dataset):
                new_tree_item.setIcon(0, self.empty_page_icon)
                self.__add_to_tree__(new_tree_item, group_item.attrs)
            elif isinstance(group_item, str):
                new_tree_item.setIcon(0, self.info_circle_icon)

    @property
    def selected_item(self) -> HLObject:
        return self.currentItem().data(0, Qt.ItemDataRole.UserRole)

    def update_tree(self):
        self.h5_items = []
        self.__add_to_tree__(self.invisibleRootItem(), self.hd5_file.parent)
