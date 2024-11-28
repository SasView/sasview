from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QLabel
from PySide6.QtCore import QAbstractItemModel
from metadata_filename_gui.metadata_component_selector import MetadataComponentSelector
from metadata_filename_gui.metadata_selector import MetadataSelector

class MetadataTreeWidget(QTreeWidget):
    def __init__(self, metadata_dict: dict[str, str], master_metadata: dict[str, dict[str, int]]):
        super().__init__()
        self.setColumnCount(2)
        self.setHeaderLabels(['Name', 'Filename Components'])
        self.metadata_dict = metadata_dict
        self.master_metadata = master_metadata


    def draw_tree(self, options: list[str], metadata_dict: dict[str, str]):
        self.clear()
        # TODO: I'm not sure whether I like this approach. Maybe use some reflection from the Metadata class instead.
        metadata = {
            'source': ['name', 'radiation', 'type', 'probe_particle', 'beam_size_name', 'beam_size', 'beam_shape', 'wavelength', 'wavelength_min', 'wavelength_max', 'wavelength_spread'],
            'detector': ['name', 'distance', 'offset', 'orientation', 'beam_center', 'pixel_size', 'slit_length'],
            'aperture': ['name', 'type', 'size_name', 'size', 'distance'],
            'collimation': ['name', 'lengths'],
            'process': ['name', 'date', 'description', 'term', 'notes'],
            'sample': ['name', 'sample_id', 'thickness', 'transmission', 'temperature', 'position', 'orientation', 'details'],
            'transmission_spectrum': ['name', 'timestamp', 'transmission', 'transmission_deviation'],
            'other': ['title', 'run', 'definition']
        }
        for top_level, items in metadata.items():
            top_level_item = QTreeWidgetItem([top_level])
            for metadatum in items:
                # selector = MetadataComponentSelector(metadatum, self.metadata_dict)
                selector = MetadataSelector(metadatum, options, self.metadata_dict[top_level], self.master_metadata[top_level])
                metadatum_item = QTreeWidgetItem([metadatum])
                # selector.draw_options(options, metadata_dict.get(metadatum))
                top_level_item.addChild(metadatum_item)
                self.setItemWidget(metadatum_item, 1, selector)
            self.insertTopLevelItem(0, top_level_item)
        self.expandAll()
