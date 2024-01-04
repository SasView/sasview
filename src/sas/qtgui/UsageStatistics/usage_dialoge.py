from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QTextBrowser, QPushButton, QSizePolicy
import importlib.resources as resources

from sas.system import config
from sas.system.version import __version__ as version

from sas.qtgui.Utilities.WhatsNew.newer import strictly_newer_than


class UsageStatisticsDialog(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        message_text = resources.read_text("sas.qtgui.UsageStatistics", "usage_dialog_message.html")
        webview = QTextBrowser()
        webview.setText(message_text)
        main_layout.addWidget(webview, stretch=1)


        button_panel = QWidget()
        button_layout = QHBoxLayout()
        button_panel.setLayout(button_layout)

        yes_button = QPushButton("Yes, I'd love to help!")
        yes_button.setStyleSheet("QPushButton {font-size: 18pt; font-weight: bold }")

        no_button = QPushButton("No")

        button_layout.addWidget(no_button)
        button_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Expanding, QSizePolicy.Expanding))
        button_layout.addWidget(yes_button)

        main_layout.addWidget(button_panel)

    def onSelectNo(self):
        config.DO_USAGE_REPORT = False

    def onSelectYes(self):
        config.DO_USAGE_REPORT = True

def maybe_show_dialog():
    strictly_newer_than(version, config.LAST_WHATS_NEW_HIDDEN_VERSION)

def demo_dialog():

    import os
    from PySide6 import QtWidgets
    from PySide6.QtCore import Qt

    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    app = QtWidgets.QApplication([])

    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_ShareOpenGLContexts)


    mainWindow = QtWidgets.QMainWindow()
    viewer = UsageStatisticsDialog(mainWindow)

    mainWindow.setCentralWidget(viewer)

    mainWindow.show()

    mainWindow.resize(600, 600)
    app.exec_()


if __name__ == "__main__":
    demo_dialog()