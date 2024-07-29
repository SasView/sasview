from PySide6.QtWidgets import QFileDialog, QLabel, QPushButton, QVBoxLayout, QWidget, QApplication
from PySide6.QtCore import Slot
from os import path

class AsciiDialog(QWidget):
    def __init__(self):
        super().__init__()

        self.raw_csv = None

        self.filename_label = QLabel("Click the button below to load a file.")

        self.load_button = QPushButton("Load File")
        self.load_button.clicked.connect(self.load)

        self.layout = QVBoxLayout(self)

        self.layout.addWidget(self.filename_label)
        self.layout.addWidget(self.load_button)

    @Slot()
    def load(self):
        filename = QFileDialog.getOpenFileName(self)[0]
        self.filename_label.setText(path.basename(filename))

        # TODO: Add error handling
        with open(filename) as file:
            self.raw_csv = file.read()


if __name__ == "__main__":
    app = QApplication([])

    widget = AsciiDialog()
    widget.show()


    exit(app.exec())
