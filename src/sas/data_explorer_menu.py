from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QWidget


class DataExplorerMenu(QMenu):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        remove_data = QAction("Remove", parent)
        # TODO: There will be loads more

        self.addAction(remove_data)
