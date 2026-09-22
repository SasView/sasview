from dataclasses import dataclass
from typing import Literal

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QWidget

from sas.data_manager import NewDataManager
from sas.refactored import Perspective


# TODO: Could we perhaps enforce that, if the action is send_to, the action_data
# should not be None?
@dataclass
class DataExplorerMenuAction:
    action: Literal["remove", "send_to", "view_data"]
    action_data: Perspective | None = None


class DataExplorerMenu(QMenu):
    def __init__(self, parent: QWidget, data_manager: NewDataManager, send_to: bool, view_data: bool):
        super().__init__(parent)

        remove_action = QAction("Remove", parent)
        remove_action.setData(DataExplorerMenuAction("remove"))
        self.addAction(remove_action)

        # TODO: There will be loads more

        if send_to:
            send_to_menu = self.addMenu("Send To")

            for perspective in data_manager.all_perspectives:
                new_action = QAction(perspective.formatName, parent)
                new_action.setData(DataExplorerMenuAction("send_to", perspective))
                send_to_menu.addAction(new_action)

        if view_data:
            view_data_action = QAction("View Data", parent)
            view_data_action.setData(DataExplorerMenuAction("view_data"))
            self.addAction(view_data_action)
