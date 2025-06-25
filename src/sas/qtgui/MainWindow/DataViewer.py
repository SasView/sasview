from PySide6.QtWidgets import QDialog, QLabel, QGridLayout
from sasdata.data import SasData


class DataViewer(QDialog):
    def __init__(self, to_view: SasData):
        super().__init__()
        self.to_view = to_view
        self.layout = QGridLayout(self)

        self.nameLabel = QLabel(f"Name: {self.to_view.name}")
        self.layout.addWidget(self.nameLabel, 0, 0, 1, 1)
