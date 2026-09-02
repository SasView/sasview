from sas.refactored import NamedTrend
from sasdata.data import SasData
from sasdata.trend import Trend
from sas.qtgui.MainWindow.MetadataExplorer import MetadataExplorer
from dataclasses import dataclass
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QHBoxLayout, QPushButton, QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit


@dataclass
class ProposedTrendAxis:
    axis_name: str
    axis_path: list[str]


def proposed_axes_as_dict(proposed_axes: list[ProposedTrendAxis]) -> dict[str, list[str]]:
    return {axis.axis_name: axis.axis_path for axis in proposed_axes}

class TrendCreation(QDialog):
    def __init__(self, target_data: list[SasData], default_name: str):
        super().__init__()

        self.proposed_trend_axes: list[ProposedTrendAxis] = []
        self.proposed_name = default_name
        self.target_data = target_data

        self.setWindowTitle("Trend Creation")

        self.layout = QVBoxLayout(self)

        self.trend_name_label = QLabel("Trend Name:")
        self.trend_name_entry = QLineEdit(self.proposed_name)
        self.trend_name_entry.textChanged.connect(self.on_new_proposed_name)

        self.header_label = QLabel("The below table shows the axes that are selected for this trend.")
        self.table = QTableWidget()
        self.update_table()
        self.add_axes_button = QPushButton("Add Axes")
        self.add_axes_button.clicked.connect(self.handle_add_axes)

        self.button_row = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.make_button = QPushButton("Make Trend")
        self.make_button.clicked.connect(self.make_trend)
        self.button_row.addWidget(self.cancel_button)
        self.button_row.addWidget(self.make_button)

        self.layout.addWidget(self.trend_name_label)
        self.layout.addWidget(self.trend_name_entry)
        self.layout.addWidget(self.header_label)
        self.layout.addWidget(self.add_axes_button)
        self.layout.addWidget(self.table)
        self.layout.addLayout(self.button_row)

    def on_new_proposed_name(self):
        self.proposed_name = self.trend_name_entry.text()

    def update_table(self):
        self.table.clear()

        self.table.setRowCount(len(self.proposed_trend_axes))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Axis Name", "Metadata Path"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

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
            for axis_path in metadata_dialog.getSelectedPaths:
                # TODO: perhaps have a better way of choosing names. Maybe make them customisable?
                self.proposed_trend_axes.append(ProposedTrendAxis(axis_name=axis_path[-1], axis_path=axis_path))
                self.update_table()

    @property
    def selected_proposed_trend_axes_as_dict(self) -> dict[str, list[str]]:
        return proposed_axes_as_dict(self.proposed_trend_axes)

    @property
    def proposed_trend(self) -> NamedTrend:
        return NamedTrend(self.target_data, self.selected_proposed_trend_axes_as_dict, self.proposed_name)

    def make_trend(self):
        """Try to make the proposed Trend, and error if it fails."""
        try:
            _ = self.proposed_trend
            self.accept()
        except ValueError as e:
            QMessageBox.critical(None, "Trend cannot be created", str(e))
                
