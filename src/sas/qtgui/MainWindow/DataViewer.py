from PySide6.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QTableWidget

from sasdata.data import SasData


class DataViewer(QDialog):
    def __init__(self, to_view: SasData):
        super().__init__()
        self.to_view = to_view
        self.layout = QGridLayout(self)

        self.nameLabel = QLabel(f"Name: {self.to_view.name}")
        self.viewMetadataButton = QPushButton("View Metadata")
        self.dataTypeLabel = QLabel(
            f"Type: {self.to_view.dataset_type.name}"
        )  # TODO: Probably a better way of printing this
        self.dataTable = QTableWidget()  # TODO: Fill.

        self.layout.addWidget(self.nameLabel, 0, 0, 1, 1)
        self.layout.addWidget(self.viewMetadataButton, 0, 1, 1, 1)
        self.layout.addWidget(self.dataTypeLabel, 1, 0, 1, 1)
        self.layout.addWidget(self.dataTable, 2, 0, 1, 2)
