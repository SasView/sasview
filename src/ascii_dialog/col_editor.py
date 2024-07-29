from PySide6.QtWidgets import QComboBox, QHBoxLayout, QWidget


class ColEditor(QWidget):
    def __init__(self, cols: int):
        super().__init__()

        self.layout = QHBoxLayout()
        self.option_widgets = []
        for _ in range(cols):
            # TODO: This is placeholder data.
            placeholder_options = ["First", "Second", "Third"]
            new_combo_box = QComboBox()
            for option in placeholder_options:
                new_combo_box.addItem(option)
