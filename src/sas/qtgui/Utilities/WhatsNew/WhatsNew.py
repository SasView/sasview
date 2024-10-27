from collections import defaultdict

from PySide6 import QtWidgets
from PySide6.QtGui import QImage, QPixmap, QIcon
from PySide6.QtWidgets import QDialog, QWidget, QTextBrowser, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox
from PySide6.QtCore import QUrl, QSize

from sas.system.version import __version__ as sasview_version
import importlib.resources as resources

from sas.system import config


from sas.qtgui.Utilities.WhatsNew.newer import strictly_newer_than, reduced_version, newest



def whats_new_messages(strictly_newer=True):
    """ Accumulate all files that are newer than the value in the config

    :param strictly_newer: require strictly newer stuff, strictness is needed for showing new things
                           when there is an update, non-strictness is needed for the menu access.
    """

    out = defaultdict(list)
    message_dir = resources.files("sas.qtgui.Utilities.WhatsNew.messages")
    for message_dir in message_dir.iterdir():
        # Get short filename
        if message_dir.is_dir():

            newer = False

            try:
                if strictly_newer:
                    newer = strictly_newer_than(message_dir.name, config.LAST_WHATS_NEW_HIDDEN_VERSION)
                else:
                    # Include current version
                    newer = not strictly_newer_than(config.LAST_WHATS_NEW_HIDDEN_VERSION, message_dir.name)

            except ValueError:
                pass

            if newer:
                for file in message_dir.iterdir():
                    if file.name.endswith(".html"):
                        out[message_dir.name].append(file)


    return out

class WhatsNewBrowser(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)

        css = resources.read_text("sas.qtgui.Utilities.WhatsNew.css", "style.css")
        self.css_data = "<style>\n" + css + "</style>"

    def setHtml(self, text: str) -> None:
        """ Overriden to inject CSS into HTML files - very, very ugly"""
        super().setHtml(text.replace("<!-- INJECT CSS HERE -->", self.css_data))

    def loadResource(self, kind: int, url: QUrl | str):

        """ Override the resource discovery to get the images we need """

        if isinstance(url, QUrl):
            name = url.toString()
        else:
            name = url

        if kind == 2:

            # This is pretty nasty, there's probably a better way
            if name.startswith("whatsnew/"):
                parts = name.split("/")[1:]

                location = resources.files("sas.qtgui.Utilities.WhatsNew.messages")

                for part in parts:
                    location = location.joinpath(part)

                im = QPixmap(str(location))

                return im

        return super().loadResource(kind, url)



class WhatsNew(QDialog):
    """ What's New window: displays messages about what is new in this version of SasView

    It will find all files in messages.[version] if [version] is newer than the last time
    the "don't show me again" option was chosen

    To add new messages, just dump a (self-contained) html file into the appropriate folder

    """
    def __init__(self, parent=None, strictly_newer=True):
        super().__init__(parent)

        self.setWindowTitle(f"What's New in SasView {sasview_version}")

        icon = QIcon()
        icon.addFile(u":/res/ball.ico", QSize(), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        self.browser = WhatsNewBrowser()
        self.browser.setOpenLinks(True)
        self.browser.setOpenExternalLinks(True)

        # Layout stuff
        self.mainLayout = QVBoxLayout()
        self.buttonBar = QWidget()
        self.buttonLayout = QHBoxLayout()


        # Buttons
        self.buttonBar.setLayout(self.buttonLayout)

        self.closeButton = QPushButton("Close")
        self.nextButton = QPushButton("Next")

        # Only show the show on startup checkbox if we're not up-to-date
        self.buttonLayout.addWidget(self.closeButton)

        if strictly_newer_than(sasview_version, config.LAST_WHATS_NEW_HIDDEN_VERSION):

            self.showAgain = QCheckBox("Show on Startup")
            self.showAgain.setChecked(True)
            self.buttonLayout.addWidget(self.showAgain)

        else:
            self.showAgain = None

        # other buttons
        self.buttonLayout.addSpacerItem(QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        self.buttonLayout.addWidget(self.nextButton)


        # Viewer
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.browser)
        self.mainLayout.addWidget(self.buttonBar)

        # Callbacks
        self.closeButton.clicked.connect(self.close_me)
        self.nextButton.clicked.connect(self.next_file)

        # # Gather new files
        new_messages = whats_new_messages(strictly_newer=strictly_newer)
        new_message_directories = [key for key in new_messages.keys()]
        new_message_directories.sort(key=reduced_version)

        self.all_messages = []

        for version in new_messages:
            self.all_messages += new_messages[version]

        self.max_index = len(self.all_messages)
        self.current_index = 0

        self.show_file()

        self.setFixedSize(800, 600)
        self.setModal(True)

    def next_file(self):
        self.current_index += 1
        self.current_index %= self.max_index
        self.show_file()

    def show_file(self):
        if len(self.all_messages) > 0:
            filename = self.all_messages[self.current_index]
            with open(filename, 'r') as fid:
                data = fid.read()
                self.browser.setHtml(data)
        else:
            self.browser.setHtml("<html><body><h1>You should not see this!!!</h1></body></html>")

    def close_me(self):
        if self.showAgain is not None:
            if not self.showAgain.isChecked():
                # We choose the newest, for backwards compatability, i.e. we never reduce the last version
                config.LAST_WHATS_NEW_HIDDEN_VERSION = newest(sasview_version, config.LAST_WHATS_NEW_HIDDEN_VERSION)

        self.close()

    def has_new_messages(self) -> bool:
        """ Should the window be shown? """
        return bool(self.all_messages)




def main():
    """ Demo/testing window"""

    from sas.qtgui.convertUI import main

    app = QtWidgets.QApplication([])

    whats_new_window = WhatsNew()
    whats_new_window.show()

    app.exec_()


if __name__ == "__main__":
    main()
