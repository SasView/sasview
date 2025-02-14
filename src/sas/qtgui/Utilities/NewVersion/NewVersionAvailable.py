import webbrowser
from copy import copy
from typing import Optional

import json
import logging
import re

from PySide6 import QtWidgets
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QCheckBox, QPushButton, QSpacerItem

import logging

from sas import config, system
from sas.qtgui.Utilities.ConnectionProxy import ConnectionProxy
from sas.system import web

from sas.system.version import __version__ as current_version_string

logger = logging.getLogger("NewVersionAvailable")
class DummyLogger:
    def info(self, *stuff):
        print(stuff)

logger = DummyLogger()

class NewVersionAvailable(QDialog):
    """
    Dialog to say that a new version is available

    """
    def __init__(self, current_version: str, latest_version: str, parent=None):
        super().__init__(parent)

        self.latest_version = latest_version

        self.setWindowTitle(f"A new version is available")

        icon = QIcon()
        icon.addFile(u":/res/ball.ico", QSize(), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        vertical_layout = QVBoxLayout()

        self.setLayout(vertical_layout)

        text1 = QLabel(f"A new version of sasview is available.")
        text2 = QLabel(f"You are running {current_version}, would you like to go to the {latest_version} download?")

        vertical_layout.addWidget(text1)
        vertical_layout.addWidget(text2)

        # Buttons

        button_panel = QWidget()
        button_layout = QHBoxLayout()
        button_panel.setLayout(button_layout)

        vertical_layout.addWidget(button_panel)

        cancel = QPushButton("Close")
        cancel.clicked.connect(self.cancel)

        self.dont_show = QCheckBox("Keep reminding me")

        accept = QPushButton("Take Me There", parent=button_panel)
        accept.clicked.connect(self.go)
        accept.setFocus()

        button_layout.addWidget(cancel)
        button_layout.addWidget(self.dont_show)
        button_layout.addSpacerItem(QSpacerItem(10,10))
        button_layout.addWidget(accept)

    def go(self):
        webbrowser.open('http://www.sasview.org', new=2)

    def cancel(self):
        if not self.dont_show.isChecked():
            config.LAST_UPDATE_DISMISSED_VERSION = self.latest_version
        self.close()

def parse_version(version_string: str) -> tuple[int, int, int]:
    """ Convert a string into numerical version"""
    # get parts, scrub non numerical stuff
    parts = [int(re.sub("[^0-9.]", "", part)) for part in version_string.split(".")]

    if len(parts) != 3:
        raise ValueError("Expected three parts to version")

    return parts[0], parts[1], parts[2]

def get_current_release_version() -> Optional[tuple[str, tuple[int, int, int]]]:
    """ Get the current version from the server """

    c = ConnectionProxy(web.update_url, config.UPDATE_TIMEOUT)
    response = c.connect()

    # Don't do anything if we can't reach the server
    if response is None:
        return None

    try:
        content = response.read().strip()
        logger.info(f"Connected to www.sasview.org. Received: {content}")

        version_info = json.loads(content)

        version_string = version_info["version"]

        return version_string, parse_version(version_string)


    except Exception as ex:
        logging.info("Failed to get version number", ex)


def a_newer_than_b(version_a: tuple[int, int, int], version_b: tuple[int, int, int]) -> bool:
    """ Check if version_a is strictly newer than version_b"""
    return version_a[0] > version_b[0] \
        or version_a[1] > version_b[1] \
        or version_a[2] > version_b[2]

def maybe_prompt_new_version_download() -> Optional[QDialog]:
    """ If a new version is available, and Show a dialog prompting the user to download """

    try:

        # Check the config to see if we should show
        # The last dismissed version needs to be at least as old as this version
        last_dismissed_string = config.LAST_UPDATE_DISMISSED_VERSION

        last_dismissed = parse_version(last_dismissed_string)
        current = parse_version(current_version_string)

        # Set the latest version in the config, if it is newer, this way, the prompt only
        # shows when a new version isn't installed - even if its not the version you're running right now

        if a_newer_than_b(version_a=current, version_b=last_dismissed):
            config.LAST_UPDATE_DISMISSED_VERSION = copy(current_version_string)
            comparison = current

            # check
            comparison = (5,0,0)

        else:
            comparison = last_dismissed

        # Get the newest version and compare

        latest_string_and_tuple = get_current_release_version()

        # If we can't check for whatever reason, just don't show
        if latest_string_and_tuple is None:
            return

        latest_string, latest = latest_string_and_tuple

        print(comparison)
        print(latest)

        if a_newer_than_b(latest, comparison):

            whats_new_window = NewVersionAvailable(current_version_string, latest_string)
            whats_new_window.show()

            return whats_new_window

        else:

            return None

    except Exception as ex:
        logger.info("Error getting latest sasview version", ex)
        return None
def main():
    """ Demo/testing window"""

    app = QtWidgets.QApplication([])

    window = maybe_prompt_new_version_download()

    app.exec_()


if __name__ == "__main__":
    main()