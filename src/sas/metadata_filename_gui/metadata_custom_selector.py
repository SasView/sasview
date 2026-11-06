from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget

from sasdata.ascii_reader_metadata import AsciiReaderMetadata


class MetadataCustomSelector(QWidget):
    def __init__(self, category:str, metadatum: str, internal_metadata: AsciiReaderMetadata, filename: str):
        super().__init__()
        self.internal_metadata = internal_metadata
        self.metadatum = metadatum
        self.category = category
        self.filename = filename

        prexisting_value = self.internal_metadata.get_metadata(category, metadatum, filename)
        initial_value = prexisting_value if prexisting_value is not None else ''
        self.entry_box = QLineEdit(initial_value)
        self.entry_box.textChanged.connect(self.selection_changed)
        self.from_filename_button = QPushButton('From Filename')

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.entry_box)
        self.layout.addWidget(self.from_filename_button)

    def selection_changed(self):
        new_value = self.entry_box.text()
        if new_value != '':
            self.internal_metadata.update_metadata(self.category, self.metadatum, self.filename, new_value)
        else:
            self.internal_metadata.clear_metadata(self.category, self.metadatum, self.filename)
