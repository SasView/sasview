from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout

class MetadataCustomEntry(QWidget):
    def __init__(self):
        super().__init__()

        self.entry_box = QLineEdit()
        self.from_filename_button = QPushButton('From Filename')

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.entry_box)
        self.layout.addWidget(self.from_filename_button)
