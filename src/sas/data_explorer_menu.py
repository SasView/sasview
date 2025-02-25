from typing import Literal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QWidget

from sas.data_manager import NewDataManager
from src.sas.refactored import Perspective
from dataclasses import dataclass

# TODO: Could we perhaps enforce that, if the action is send_to, the action_data
# should not be None?
@dataclass
class DataExplorerMenuAction():
    action: Literal['remove', 'send_to']
    action_data: Perspective | None = None

class DataExplorerMenu(QMenu):
    def __init__(self, parent: QWidget, data_manager: NewDataManager, send_to: bool):
        super().__init__(parent)

        remove_data = QAction("Remove", parent)
        # remove_data.setData('remove')
        remove_data.setData(DataExplorerMenuAction('remove'))
        # TODO: There will be loads more

        if send_to:
            send_to_menu = self.addMenu("Send To")

            for perspective in data_manager.all_perspectives:
                new_action = QAction(perspective.formatName, parent)
                new_action.setData(DataExplorerMenuAction('send_to', perspective))
                send_to_menu.addAction(new_action)
        self.addAction(remove_data)
