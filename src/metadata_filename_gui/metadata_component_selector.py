from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal, Qt, Slot

from metadata_filename_gui.internal_metadata import InternalMetadata

class MetadataComponentSelector(QWidget):
    # Creating a separate signal for this because the custom button may be destroyed/recreated whenever the options are
    # redrawn.

    custom_button_pressed = Signal(Qt.MouseButton())

    def __init__(self, category: str, metadatum: str, filename: str, internal_metadata: InternalMetadata):
        super().__init__()
        self.options: list[str]
        self.option_buttons: list[QPushButton]
        self.layout = QHBoxLayout(self)
        self.internal_metadata = internal_metadata
        self.metadatum = metadatum
        self.category = category
        self.filename = filename

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
        # self.custom_entry_button.clicked.connect(self.custom_button_pressed)
        self.custom_entry_button.clicked.connect(self.handle_custom_button)
        self.layout.addWidget(self.custom_entry_button)

    def handle_custom_button(self):
        self.custom_button_pressed.emit()

    def selection_changed(self):
        selected_button: QPushButton = self.sender()
        button_index = -1
        for i, button in enumerate(self.option_buttons):
            if button != selected_button:
                button.setChecked(False)
            else:
                button_index = i
        if selected_button.isChecked():
            self.internal_metadata.update_metadata(self.category, self.metadatum, self.filename, button_index)
        else:
            self.internal_metadata.clear_metadata(self.category, self.metadatum, self.filename)
