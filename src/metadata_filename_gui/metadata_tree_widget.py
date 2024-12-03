from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QLabel
from PySide6.QtCore import QAbstractItemModel
from metadata_filename_gui.metadata_component_selector import MetadataComponentSelector
from metadata_filename_gui.metadata_selector import MetadataSelector
from metadata_filename_gui.internal_metadata import InternalMetadata
from metadata_filename_gui.metadata_tree_data import metadata as metadata_categories

class MetadataTreeWidget(QTreeWidget):
    def __init__(self, metadata: InternalMetadata):
        super().__init__()
        self.setColumnCount(2)
        self.setHeaderLabels(['Name', 'Filename Components'])
        self.metadata: InternalMetadata = metadata

    def draw_tree(self, options: list[str], full_filename: str):
        self.clear()
        for top_level, items in metadata_categories.items():
            top_level_item = QTreeWidgetItem([top_level])
            for metadatum in items:
                # selector = MetadataComponentSelector(metadatum, self.metadata_dict)
                selector = MetadataSelector(top_level, metadatum, options, self.metadata, full_filename)
                metadatum_item = QTreeWidgetItem([metadatum])
                # selector.draw_options(options, metadata_dict.get(metadatum))
                top_level_item.addChild(metadatum_item)
                self.setItemWidget(metadatum_item, 1, selector)
            self.insertTopLevelItem(0, top_level_item)
        self.expandAll()
