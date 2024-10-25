from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QLabel
from PySide6.QtCore import QAbstractItemModel
from metadata_component_selector import MetadataComponentSelector

class MetadataTreeWidget(QTreeWidget):
    def __init__(self, metadata_dict: dict[str, str]):
        super().__init__()
        self.setColumnCount(2)
        self.setHeaderLabels(['Name', 'Filename Components'])
        self.metadata_dict = metadata_dict


    def draw_tree(self, options: list[str]):
        self.clear()
        # TODO: This is placeholder data that'll need to be replaced by the real metadata.
        metadata = {'Instrument': ['Slit width', 'Other']}
        for top_level, items in metadata.items():
            top_level_item = QTreeWidgetItem([top_level])
            for metadatum in items:
                selector = MetadataComponentSelector(metadatum, self.metadata_dict)
                metadatum_item = QTreeWidgetItem([metadatum])
                selector.draw_options(options)
                top_level_item.addChild(metadatum_item)
                self.setItemWidget(metadatum_item, 1, selector)
            self.insertTopLevelItem(0, top_level_item)
        self.expandAll()
