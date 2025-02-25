from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QWidget

from sas.data_manager import NewDataManager
from src.sas.refactored import Perspective

class DataExplorerMenu(QMenu):
    def __init__(self, parent: QWidget, data_manager: NewDataManager):
        super().__init__(parent)

        remove_data = QAction("Remove", parent)
        # TODO: There will be loads more

        send_to_menu = SendToMenu(self, data_manager.all_perspectives)

        self.addAction(remove_data)
        self.addMenu(send_to_menu)

class SendToMenu(QMenu):
    def __init__(self, parent: QMenu, perspectives: list[Perspective]):
        super().__init__(parent)

        # TODO: May need a way of identifying the perspective other than the name.
        self.menu_items: list[QAction] = []

        for perspective in perspectives:
            new_action = QAction(perspective.formatName, parent)
            self.menu_items.append(new_action)
