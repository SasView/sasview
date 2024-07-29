from PySide6.QtWidgets import QFileDialog, QLabel, QPushButton, QVBoxLayout, QWidget, QApplication
from PySide6.QtCore import Slot

class AsciiDialog(QWidget):
    def __init__(self):
        super().__init__()

        self.load_button = QPushButton("Load File")
        self.load_button.clicked.connect(self.load)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.load_button)

    @Slot()
    def load(self):
        filename = QFileDialog.getOpenFileName(self)
        print(filename)


if __name__ == "__main__":
    app = QApplication([])

    widget = AsciiDialog()
    widget.show()


    exit(app.exec())
