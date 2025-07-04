from PySide6.QtWidgets import (
    QDialog, QGridLayout, QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

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
        self.dataTable = QTableWidget()
        self.buildTable()
        self.closeButton = QPushButton("Close")
        self.closeButton.clicked.connect(self.close)

        self.layout.addWidget(self.nameLabel, 0, 0, 1, 1)
        self.layout.addWidget(self.viewMetadataButton, 0, 1, 1, 1)
        self.layout.addWidget(self.dataTypeLabel, 1, 0, 1, 1)
        self.layout.addWidget(self.dataTable, 2, 0, 1, 2)
        self.layout.addWidget(self.closeButton, 3, 0, 1, 2)

    def buildTable(self):
        self.dataTable.setHorizontalHeaderLabels(self.to_view._data_contents.keys())
        for i, data in enumerate(self.to_view._data_contents.values()):
            for j, datum in enumerate(data.value):
                self.dataTable.setItem(j, i, QTableWidgetItem(datum))
