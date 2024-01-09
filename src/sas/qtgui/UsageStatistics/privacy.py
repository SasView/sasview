from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QTextBrowser, QPushButton, QSizePolicy, QDialog

import importlib.resources as resources



class PrivacyDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("SasView Privacy Policy")

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        message_text = resources.read_text("sas.qtgui.UsageStatistics", "privacy_policy.html")
        webview = QTextBrowser()
        webview.setText(message_text)

        main_layout.addWidget(webview, stretch=1)


        button_panel = QWidget()
        button_layout = QHBoxLayout()
        button_panel.setLayout(button_layout)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.onOK)

        button_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Expanding, QSizePolicy.Expanding))
        button_layout.addWidget(ok_button)
        button_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Expanding, QSizePolicy.Expanding))

        main_layout.addWidget(button_panel)

    def onOK(self):
        """ Called when no button is clicked."""
        self.close()

_privacy_dialog = None
def show_privacy_dialog():

    global _privacy_dialog

    _privacy_dialog = PrivacyDialog()
    _privacy_dialog.setFixedSize(600, 400)
    _privacy_dialog.setModal(True)
    _privacy_dialog.show()

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

    show_privacy_dialog()
    app.exec_()


if __name__ == "__main__":
    demo_dialog()