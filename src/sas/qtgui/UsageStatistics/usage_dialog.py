from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QTextBrowser, QPushButton, QSizePolicy, QDialog
from PySide6.QtCore import QUrl
import importlib.resources as resources

from sas.system import config
from sas.system.version import __version__ as version


from sas.qtgui.Utilities.WhatsNew.newer import strictly_newer_than

from sas.qtgui.UsageStatistics.privacy import show_privacy_dialog

class UsageStatisticsDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Gather Usage Statistics?")

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.message_text = resources.read_text("sas.qtgui.UsageStatistics", "usage_dialog_message.html")
        self.webview = QTextBrowser()
        self.webview.setText(self.message_text)
        self.webview.anchorClicked.connect(self.linkClicked)
        main_layout.addWidget(self.webview, stretch=1)


        button_panel = QWidget()
        button_layout = QHBoxLayout()
        button_panel.setLayout(button_layout)

        yes_button = QPushButton("Yes, I'd love to help!")
        yes_button.setStyleSheet("QPushButton {font-size: 18pt; font-weight: bold }")
        yes_button.clicked.connect(self.onSelectYes)

        no_button = QPushButton("No")
        no_button.clicked.connect(self.onSelectNo)

        button_layout.addWidget(no_button)
        button_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Expanding, QSizePolicy.Expanding))
        button_layout.addWidget(yes_button)

        main_layout.addWidget(button_panel)

    def onSelectNo(self):
        """ Called when no button is clicked."""
        config.DO_USAGE_REPORT = False
        self.close()

    def onSelectYes(self):
        """ Called when yes button is clicked."""
        config.DO_USAGE_REPORT = True
        self.close()

    def linkClicked(self, url: QUrl):
        if url.url() == "privacy_policy":
            show_privacy_dialog()
            self.webview.setText(self.message_text)
        else:
            raise NotImplementedError("Links to other places than the privacy policy not implemented")


_usage_dialog = None
def show_usage_dialog():

    global _usage_dialog

    _usage_dialog = UsageStatisticsDialog()
    _usage_dialog.setFixedSize(600, 400)
    _usage_dialog.setModal(True)
    _usage_dialog.show()

def maybe_show_dialog():
    if strictly_newer_than(version, config.LAST_WHATS_NEW_HIDDEN_VERSION):
        if config.ASK_USAGE_REPORT:
            show_usage_dialog()

def demo_dialog():

    import os
    from PySide6 import QtWidgets
    from PySide6.QtCore import Qt

    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    app = QtWidgets.QApplication([])

    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_ShareOpenGLContexts)

    # mainWindow = QtWidgets.QMainWindow()
    # viewer = UsageStatisticsDialog(mainWindow)
    #
    # mainWindow.setCentralWidget(viewer)
    #
    # mainWindow.show()

    # mainWindow.resize(600, 600)

    show_usage_dialog()
    app.exec_()


if __name__ == "__main__":
    demo_dialog()