import logging
import webbrowser
from copy import copy

import requests
from packaging.version import Version, parse
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from sas import config
from sas.system import web
from sas.system.version import __version__ as current_version_string

logger = logging.getLogger("NewVersionAvailable")

class NewVersionAvailable(QDialog):
    """
    Dialog to say that a new version is available

    """
    def __init__(self, current_version: str, latest_version: str, url: str = 'http://www.sasview.org/#downloadsection', parent=None):
        super().__init__(parent)

        self.latest_version = latest_version
        self.url = url

        self.setWindowTitle(f"SasView {latest_version} Is Out!")

        icon = QIcon()
        icon.addFile(":/res/ball.ico", QSize(), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        vertical_layout = QVBoxLayout()

        self.setLayout(vertical_layout)

        text = QLabel("<p>A new version of sasview is available.</p>"
                       ""
                       "<p><center>Visit the download page?</centre></p><p/>")

        vertical_layout.addWidget(text)

        # Buttons

        button_panel = QWidget()
        button_layout = QHBoxLayout()
        button_panel.setLayout(button_layout)

        vertical_layout.addWidget(button_panel)

        cancel = QPushButton("Close")
        cancel.clicked.connect(self.cancel)

        self.dont_show = QCheckBox("Keep reminding me")
        self.dont_show.setChecked(True)

        accept = QPushButton("Take Me There", parent=button_panel)
        accept.clicked.connect(self.go)
        accept.setFocus()

        button_layout.addWidget(cancel)
        button_layout.addWidget(self.dont_show)
        button_layout.addSpacerItem(QSpacerItem(50,10))
        button_layout.addWidget(accept)

    def go(self):
        webbrowser.open(self.url, new=2)

    def cancel(self):
        if not self.dont_show.isChecked():
            config.LAST_UPDATE_DISMISSED_VERSION = self.latest_version
        self.close()


def get_current_release_version() -> tuple[str, str, Version] | None:
    """ Get the current version from the server """
    try:
        response = requests.get(web.update_url, timeout=config.UPDATE_TIMEOUT)
        # Will throw Exception if the HTTP status code returned isn't success
        # (2xx)
        response.raise_for_status()
        version_info = response.json()
        logger.info("Connected to www.sasview.org. Received: %s", version_info)

        version_string = version_info["version"]
        url = version_info["download_url"]

        return version_string, url, parse(version_string)

    except Exception as ex:
        logging.info("Failed to get version number %s", ex)
        return None



def maybe_prompt_new_version_download() -> QDialog | None:
    """ If a new version is available, and Show a dialog prompting the user to download """

    try:

        # Check the config to see if we should show
        # The last dismissed version needs to be at least as old as this version
        last_dismissed_string = config.LAST_UPDATE_DISMISSED_VERSION

        last_dismissed = parse(last_dismissed_string)
        current = parse(current_version_string)

        # Set the latest version in the config, if it is newer, this way, the prompt only
        # shows when a new version isn't installed - even if its not the version you're running right now

        if current > last_dismissed:
            config.LAST_UPDATE_DISMISSED_VERSION = copy(current_version_string)
            comparison = current

            # Uncomment this to check:
            # comparison = (5, 0, 0)

        else:
            comparison = last_dismissed

        # Get the newest version and compare

        latest_string_and_tuple = get_current_release_version()

        # If we can't check for whatever reason, just don't show
        if latest_string_and_tuple is None:
            return

        latest_string, url, latest = latest_string_and_tuple

        if latest > comparison:

            app = QApplication([])
            new_version = NewVersionAvailable(current_version_string, latest_string, url)
            new_version.show()

            app.exec()
            app.shutdown() # Of course!





    except Exception as ex:
        logger.info("Error getting latest sasview version %s", ex)
        return None

def main():
    """ Demo/testing window"""

    maybe_prompt_new_version_download()


if __name__ == "__main__":
    main()
