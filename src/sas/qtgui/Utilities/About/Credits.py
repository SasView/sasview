from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
)

from sas.system import SAS_RESOURCES


class Credits(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Credits and Licences for SasView")

        icon = QIcon()
        icon.addFile(":/res/ball.ico", QSize(), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        self.mainLayout = QVBoxLayout()
        self.creditsText = QTextBrowser()

        self.creditsText.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setText()

        self.mainLayout.addWidget(self.creditsText)

        self.setLayout(self.mainLayout)
        self.setModal(True)

        if parent is not None:
            # SasView doesn't set parents though?
            w = int(parent.width() * 0.33)
            h = int(parent.height() * 0.75)
            self.resize(w, h)
        else:
            w = 800
            h = 800
            self.resize(w, h)

    def setText(self):
        """
        Modify the labels so the text corresponds to the current version
        """
        with SAS_RESOURCES.resource("system/credits.html") as path:
            credits = path.read_text()
        self.creditsText.setText(credits)


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication([])

    credits = Credits()
    credits.show()

    sys.exit(app.exec())
