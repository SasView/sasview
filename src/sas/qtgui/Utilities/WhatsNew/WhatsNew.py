from collections import defaultdict

from PySide6 import QtWidgets
from PySide6.QtWidgets import QDialog, QWidget, QTextBrowser, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox

from sas.system.version import __version__ as sasview_version
import importlib.resources as resources

from sas.system import config


from sas.qtgui.Utilities.WhatsNew.newer import strictly_newer_than, reduced_version

def whats_new_messages():
    """ Accumulate all files that are newer than the value in the config"""

    out = defaultdict(list)
    message_dir = resources.files("sas.qtgui.Utilities.WhatsNew.messages")
    for message_dir in message_dir.iterdir():
        # Get short filename
        if message_dir.is_dir():

            newer = False

            try:
                newer = strictly_newer_than(message_dir.name, config.LAST_WHATS_NEW_HIDDEN_VERSION)

            except ValueError:
                pass


            if newer:
                for file in message_dir.iterdir():
                    if file.name.endswith(".html"):
                        out[message_dir.name].append(file)


    return out


class WhatsNew(QDialog):
    """ What's New window: displays messages about what is new in this version of SasView

    It will find all files in messages.[version] if [version] is newer than the last time
    the "don't show me again" option was chosen

    To add new messages, just dump a (self-contained) html file into the appropriate folder

    """
    def __init__(self, parent=None):
        super().__init__()

        self.setWindowTitle(f"What's New in SasView {sasview_version}")

        self.browser = QTextBrowser()

        # Layout stuff
        self.mainLayout = QVBoxLayout()
        self.buttonBar = QWidget()
        self.buttonLayout = QHBoxLayout()


        # Buttons
        self.buttonBar.setLayout(self.buttonLayout)

        self.closeButton = QPushButton("Close")
        self.nextButton = QPushButton("Next")

        self.showAgain = QCheckBox("Show on Startup")
        self.showAgain.setChecked(True)

        self.buttonLayout.addWidget(self.showAgain)
        self.buttonLayout.addWidget(self.closeButton)
        self.buttonLayout.addWidget(self.nextButton)

        # Viewer
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.browser)
        self.mainLayout.addWidget(self.buttonBar)

        # Callbacks
        self.closeButton.clicked.connect(self.close_me)
        self.nextButton.clicked.connect(self.next_file)

        # # Gather new files
        new_messages = whats_new_messages()
        new_message_directories = [key for key in new_messages.keys()]
        new_message_directories.sort(key=reduced_version)

        self.all_messages = []

        for version in new_messages:
            self.all_messages += new_messages[version]

        self.max_index = len(self.all_messages)
        self.current_index = 0

        self.show_file()

        self.setModal(True)

    def next_file(self):
        self.current_index += 1
        self.current_index %= self.max_index
        self.show_file()

    def show_file(self):
        filename = self.all_messages[self.current_index]
        with open(filename, 'r') as fid:
            data = fid.read()
            self.browser.setText(data)

    def close_me(self):
        if not self.showAgain.isChecked():
            config.LAST_WHATS_NEW_HIDDEN_VERSION = sasview_version

        self.close()

    def has_new_messages(self) -> bool:
        """ Should the window be shown? """
        return bool(self.all_messages)



def maybe_show_whats_new():
    global whats_new_window
    """ Show the What's New dialogue if it is wanted """

    if whats_new_messages():
        whats_new_window = WhatsNew()
        whats_new_window.show()


def main():
    """ Demo/testing window"""

    from sas.qtgui.convertUI import main

    main()

    app = QtWidgets.QApplication([])

    maybe_show_whats_new()

    app.exec_()


if __name__ == "__main__":
    main()
