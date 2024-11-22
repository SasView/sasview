from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QLabel
from PySide6.QtCore import QAbstractItemModel
from metadata_filename_gui.metadata_component_selector import MetadataComponentSelector
from metadata_filename_gui.metadata_selector import MetadataSelector

class MetadataTreeWidget(QTreeWidget):
    def __init__(self, metadata_dict: dict[str, str]):
        super().__init__()
        self.setColumnCount(2)
        self.setHeaderLabels(['Name', 'Filename Components'])
        self.metadata_dict = metadata_dict


    def draw_tree(self, options: list[str], metadata_dict: dict[str, str]):
        self.clear()
        metadata = {
            'sasdata': ['aperture', 'collimation', 'detector', 'source'],
            'process': ['name', 'date', 'description', 'term', 'notes'],
            'sample': ['name', 'sample_id', 'thickness', 'transmission', 'temperature', 'position', 'orientation', 'details'],
            'transmission_spectrum': ['name', 'timestamp', 'transmission', 'transmission_deviation'],
            'other': ['title', 'run', 'definition']
        }
        for top_level, items in metadata.items():
            top_level_item = QTreeWidgetItem([top_level])
            for metadatum in items:
                # selector = MetadataComponentSelector(metadatum, self.metadata_dict)
                selector = MetadataSelector(metadatum, options, self.metadata_dict)
                metadatum_item = QTreeWidgetItem([metadatum])
                # selector.draw_options(options, metadata_dict.get(metadatum))
                top_level_item.addChild(metadatum_item)
                self.setItemWidget(metadatum_item, 1, selector)
            self.insertTopLevelItem(0, top_level_item)
        self.expandAll()
