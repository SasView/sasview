#!/usr/bin/env python3

import h5py
from PySide6.QtWidgets import QApplication, QWidget

class Hd5Viewer(QWidget):
    def __init__(self):
        super().__init__()

if __name__ == "__main__":
    app = QApplication([])

    widget = Hd5Viewer()
    widget.show()

    exit(app.exec())
