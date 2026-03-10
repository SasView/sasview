import logging

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QPalette
from PySide6.QtWidgets import QApplication, QDialog, QSizePolicy, QTextBrowser, QVBoxLayout

from sas.system import SAS_RESOURCES

logger = logging.getLogger(__name__)


def is_dark_mode() -> bool:
    """Returns True if the application is in dark mode (window color is dark)."""
    app = QApplication.instance()
    if not app:
        return False
    window_color = app.palette().color(QPalette.Window)
    # QColor.lightness() returns 0 (dark) to 255 (light)
    return window_color.lightness() < 128


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

        if is_dark_mode():
            # Inject dark mode CSS into the credits HTML
            dark_css = """
            <style>
            body { background-color: #000000; color: #e0e0e0; }
            pre { background-color: #2b2b2b; color: #f4f4f4; }
            a { color: #4da3ff; }
            </style>
            """
            if "</head>" in credits:
                credits = credits.replace("</head>", dark_css + "</head>", 1)
            else:
                logger.error("Could not find </head> in credits.html.")

        self.creditsText.setHtml(credits)


if __name__ == "__main__":
    import sys

    app = QApplication([])

    credits = Credits()
    credits.show()

    sys.exit(app.exec())
