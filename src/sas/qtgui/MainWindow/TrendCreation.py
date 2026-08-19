from sasdata.data import SasData
from sas.qtgui.MainWindow.MetadataExplorer import MetadataExplorer
from dataclasses import dataclass
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QHBoxLayout, QPushButton, QTableWidgetItem


@dataclass
class ProposedTrendAxis:
    axis_name: str
    axis_path: list[str]


class TrendCreation(QDialog):
    def __init__(self, target_data: list[SasData]):
        super().__init__()

        self.proposed_trend_axes: list[ProposedTrendAxis] = []
        self.target_data = target_data

        self.setWindowTitle("Trend Creation")

        self.layout = QVBoxLayout(self)

        self.header_label = QLabel("The below table shows the axes that are selected for this trend.")
        self.table = QTableWidget()
        self.update_table()
        self.add_axes_button = QPushButton("Add Axes")

        self.button_row = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.make_button = QPushButton("Make Trend")
        self.make_button.clicked.connect(self.accept)
        self.button_row.addWidget(self.cancel_button)
        self.button_row.addWidget(self.make_button)

        self.layout.addWidget(self.header_label)
        self.layout.addWidget(self.add_axes_button)
        self.layout.addWidget(self.table)
        self.layout.addLayout(self.button_row)

    def update_table(self):
        self.table.clear()

        self.table.setRowCount(len(self.proposed_trend_axes))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Axis Name", "Axis Metadata"])

        row_index = 0
        for axis in self.proposed_trend_axes:
            name_item = QTableWidgetItem(axis.axis_name)
            path_item = QTableWidgetItem(", ".join(axis.axis_path))
            self.table.setItem(row_index, 0, name_item)
            self.table.setItem(row_index, 1, path_item)
            row_index += 1

        self.table.show()

    def handle_add_axes(self):
        # TODO: This is assuming all the data in target data has the same
        # metadata, but this of course is not guaranteed. I see two ways of
        # resolving this:
        #
        # 1. Validate that the objects do share all the same metadata.
        # 2. Only show metadata in the explorer which the data objects share.
        # This is probably trickier to implement but would also be the most
        # flexible.
        metadata_dialog = MetadataExplorer(self.target_data[0].metadata, "New Trend", True)
        result = metadata_dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            pass  # TODO: Update proposed axes.
