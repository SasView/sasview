from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal, Qt

class MetadataComponentSelector(QWidget):
    # Creating a separate signal for this because the custom button may be destroyed/recreated whenever the options are
    # redrawn.

    custom_button_pressed = Signal(Qt.MouseButton())

    def __init__(self, metadatum: str, metadata_dict: dict[str, str]):
        super().__init__()
        self.options: list[str]
        self.option_buttons: list[QPushButton]
        self.layout = QHBoxLayout(self)
        self.metadata_dict = metadata_dict
        self.metadatum = metadatum

    def clear_options(self):
        for i in reversed(range(self.layout.count() - 1)):
            self.layout.takeAt(i).widget().deleteLater()

    def draw_options(self, new_options: list[str], selected_option: str | None):
        self.clear_options()
        self.options = new_options
        self.option_buttons = []
        for option in self.options:
            option_button = QPushButton(option)
            option_button.setCheckable(True)
            option_button.clicked.connect(self.selection_changed)
            option_button.setChecked(option == selected_option)
            self.layout.addWidget(option_button)
            self.option_buttons.append(option_button)
        # This final button is to convert to use custom entry instead of this.
        self.custom_entry_button = QPushButton('Custom')
        self.custom_entry_button.clicked.connect(self.custom_entry_button)
        self.layout.addWidget(self.custom_entry_button)

    def selection_changed(self):
        selected_button: QPushButton = self.sender()
        selected_component = selected_button.text()
        for button in self.option_buttons:
            if button != selected_button:
                button.setChecked(False)
        if selected_button.isChecked():
            self.metadata_dict[self.metadatum] = selected_component
        else:
            del self.metadata_dict[self.metadatum]
