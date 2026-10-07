from typing import override
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout
from sas.data_manager import NewDataManager
from sas.refactored import Perspective


# This perspective was made as a worked example for the perspective creation
# tutorial. It is for demonstrations purposes only. It is not intended to do
# anything useful for small angle scattering, but is merely just an example of
# what can be done with a perspective.
#
# IF YOU WANT TO MAKE CHANGES: the code is referred to in the perspective
# tutorial. After making changes, you should check the tutorial to make sure it
# matches what is here.
class StatisticsPerspective(Perspective):
    def __init__(self, data_manager: NewDataManager, parent: QWidget | None = None):
        super().__init__(data_manager, parent)

        self.data_loaded_label = QLabel("No data loaded.")
        self.std_label = QLabel("")
        self.calculate_button = QPushButton("Calculate")
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.data_loaded_label)
        self.layout.addWidget(self.std_label)
        self.layout.addWidget(self.calculate_button)

    @property
    @override
    def title(self) -> str:
        return "Statistics Perspective"
