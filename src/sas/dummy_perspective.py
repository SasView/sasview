from typing import override
from PySide6.QtWidgets import QDialog, QWidget
from sas.refactored import Perspective

class DummyPerspective(QDialog, Perspective):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    @property
    @override
    def title(self) -> str:
        return "Dummy"

    @property
    @override
    def title(self) -> str:
        return "Dummy Perspective"
