from PySide6.QtWidgets import QDialog
from sasdata.data import SasData


class DataViewer(QDialog):
    def __init__(self, to_view: SasData):
        super().__init__()
        self.to_view = to_view
