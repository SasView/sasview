from PySide6.QtWidgets import QPushButton, QWidget, QApplication

class AsciiDialog(QWidget):
    def __init__(self):
        super().__init__()



if __name__ == "__main__":
    app = QApplication([])

    widget = AsciiDialog()
    widget.show()


    exit(app.exec())
