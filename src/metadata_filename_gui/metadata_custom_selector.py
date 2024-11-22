from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout

class MetadataCustomSelector(QWidget):
    def __init__(self, metadatum: str, metadata_dict: dict[str, str]):
        super().__init__()
        self.metadata_dict = metadata_dict
        self.metadatum = metadatum

        prexisting_value = metadata_dict.get(metadatum)
        initial_value = prexisting_value if prexisting_value is not None else ''
        self.entry_box = QLineEdit(initial_value)
        self.entry_box.textChanged.connect(self.selection_changed)
        self.from_filename_button = QPushButton('From Filename')

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.entry_box)
        self.layout.addWidget(self.from_filename_button)

    def selection_changed(self):
        new_value = self.from_filename_button.text()
        if new_value != '':
            self.metadata_dict[self.metadatum] = new_value
        elif self.metadatum in self.metadata_dict:
            del self.metadata_dict[self.metadatum]
