from PySide6.QtWidgets import QMessageBox, QWidget


class DataExplorerErrorMessage(QMessageBox):
    def __init__(self, parent: QWidget, error: ValueError):
        super().__init__(parent)
        self.setIcon(QMessageBox.Icon.Critical)
        self.setText(str(error))
        self.setWindowTitle('Data Error')
