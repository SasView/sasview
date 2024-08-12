#!/usr/bin/env python3

from PySide6.QtWidgets import QApplication, QWidget

class UnitPreferences(QWidget):
    def __init__(self):
        super().__init__()

if __name__ == "__main__":
    app = QApplication([])

    widget = UnitPreferences()
    widget.show()

    exit(app.exec())
