from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QWidget

from sas.data_manager import NewDataManager
from src.sas.refactored import Perspective

class DataExplorerMenu(QMenu):
    def __init__(self, parent: QWidget, data_manager: NewDataManager):
        super().__init__(parent)

        remove_data = QAction("Remove", parent)
        # TODO: There will be loads more

        send_to_menu = self.addMenu("Send To")

        for perspective in data_manager.all_perspectives:
            new_action = QAction(perspective.formatName, parent)
            send_to_menu.addAction(new_action)
        self.addAction(remove_data)

