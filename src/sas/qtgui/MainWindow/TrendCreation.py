from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QHBoxLayout, QPushButton


class TrendCreation(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Trend Creation")

        self.layout = QVBoxLayout(self)

        self.header_label = QLabel("The below table shows the axes that are selected for this trend.")
        self.table = QTableWidget()
        self.table.setHorizontalHeaderLabels(["Axis Name", "Axis Metadata"])

        self.button_row = QHBoxLayout()
        self.cancel_button = QPushButton("Cance ")
        self.make_button = QPushButton("Make Trend")
        self.button_row.addWidget(self.cancel_button)
        self.button_row.addWidget(self.make_button)

        self.layout.addWidget(self.header_label)
        self.layout.addWidget(self.table)
        self.layout.addLayout(self.button_row)
