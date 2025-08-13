from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from sasdata.ascii_reader_metadata import AsciiReaderMetadata, initial_metadata

from metadata_filename_gui.metadata_selector import MetadataSelector


class MetadataTreeWidget(QTreeWidget):
    def __init__(self, metadata: AsciiReaderMetadata):
        super().__init__()
        self.setColumnCount(2)
        self.setHeaderLabels(['Name', 'Filename Components'])
        self.metadata: AsciiReaderMetadata = metadata

    def draw_tree(self, full_filename: str):
        self.clear()
        for top_level, items in initial_metadata.items():
            top_level_item = QTreeWidgetItem([top_level])
            for metadatum in items:
                # selector = MetadataComponentSelector(metadatum, self.metadata_dict)
                selector = MetadataSelector(top_level, metadatum, self.metadata, full_filename)
                metadatum_item = QTreeWidgetItem([metadatum])
                # selector.draw_options(options, metadata_dict.get(metadatum))
                top_level_item.addChild(metadatum_item)
                self.setItemWidget(metadatum_item, 1, selector)
            self.insertTopLevelItem(0, top_level_item)
        self.expandAll()
