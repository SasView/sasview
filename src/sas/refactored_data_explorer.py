from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

# TODO: Just using the word 'new' to avoid conflicts. The final version
# shouldn't have that name.
class NewDataExplorer(QWidget):
    def __init__(self, parent: QWidget | None = ...) -> None:
        super().__init__(parent)

        self.layout = QVBoxLayout(self)

        test_label = QLabel('Test')
        self.layout.addWidget(test_label)
