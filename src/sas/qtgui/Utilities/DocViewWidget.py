import logging
import os
import sys
from pathlib import Path

from PySide6 import QtCore, QtWebEngineCore, QtWidgets
from PySide6.QtGui import QCloseEvent

from sas.system import HELP_SYSTEM

from .UI.DocViewWidgetUI import Ui_DocViewerWindow

HTML_404 = '''
<html>
<body>
<p>Unable to find documentation.</p>
<p>Developers: please build the documentation and try again.</p>
</body>
</html>
'''

logger = logging.getLogger(__name__)


class DocViewWindow(QtWidgets.QDialog, Ui_DocViewerWindow):
    """
    Instantiates a window to view documentation using a QWebEngineViewer widget
    """

    def __init__(self, source: Path):
        """The DocViewWindow class is an HTML viewer built into SasView.

        :param parent: Any Qt object with a communicator that can trigger events.
        :param source: The Path to the html file.
        """
        super(DocViewWindow, self).__init__(None)
        self.setupUi(self)
        self.setWindowTitle("Documentation Viewer")

        # Necessary globals
        self.source: Path = Path(source)

        from sas.qtgui.Utilities.GuiUtils import communicator
        self.communicator = communicator
        self.initializeSignals()  # Connect signals

        self.initialLoadHtml()

    def initializeSignals(self):
        """Initialize all external signals that will trigger events for the window."""
        self.closeButton.clicked.connect(self.onCloseButtonClicked)
        self.communicator.closeSignal.connect(self.onCloseButtonClicked)
        self.webEngineViewer.urlChanged.connect(self.updateTitle)
        self.webEngineViewer.page().profile().downloadRequested.connect(self.onDownload)

    def closeEvent(self, event: QCloseEvent):
        """
        Close window
        Keep as a separate method to allow for additional functionality when closing
        """
        self.accept()

    def onCloseButtonClicked(self):
        """
        Close window
        Keep as a separate method to allow for additional functionality when closing
        """
        self.close()

    def onShow(self):
        """
        Show window
        Keep as a separate method to allow for additional functionality when opening
        """
        self.show()

    def onDownload(self, download_item):
        # There may be several active webEngineViewers. Only process the
        # actual caller
        if download_item.page() == self.webEngineViewer.page():
            download_item.accept()
            download_item.isFinishedChanged.connect(lambda: self.onDownloadFinished(download_item))

    def onDownloadFinished(self, item):
        _filename = item.downloadFileName()
        if item.state() == item.DownloadState.DownloadCompleted:
            logger.warning(f"your file: {_filename} was downloaded to your default download directory")
        else:
            logger.error(f"FAILED TO DOWNLOAD: {_filename} is unavailable")

    def initialLoadHtml(self):
        """
        Undertake preflight checks and if OK, load the requested page
        """
        if not HELP_SYSTEM.path.exists():
            # The docs can't be found - display a 404 message
            logger.error("Documentation could not be found at configured location: %s", HELP_SYSTEM.path)
            self.load404()
            return

        self.loadHtml()  # loads the html file specified in the source url to the QWebViewer

    def loadHtml(self):
        """Loads the HTML file specified when this python is called from another part of the program."""
        # Ensure urls are properly processed before passing into widget
        url = self.processUrl()
        settings = self.webEngineViewer.settings()
        # Allows QtWebEngine to access MathJax and code highlighting APIs
        settings.setAttribute(QtWebEngineCore.QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QtWebEngineCore.QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        self.webEngineViewer.load(url)

        # Show widget
        self.onShow()

    def updateTitle(self):
        """
        Set the title of the window to include the name of the document,
        found in the first <h1> tags.
        """
        # Convert QUrl to pathlib path
        try:
            current_path = self.webEngineViewer.url().toLocalFile()
            self.setWindowTitle(f"Documentation—{current_path.strip()}") # Try to add the filepath to the window title
        except (AttributeError, TypeError, ValueError) as ex:
            self.setWindowTitle("Documentation")
            logger.warning(f"Error updating documentation window title: {ex}")

    def load404(self):
        self.webEngineViewer.setHtml(HTML_404)
        self.onShow()

    def refresh(self):
        self.webEngineViewer.reload()

    def processUrl(self) -> QtCore.QUrl:
        """Process path into proper QUrl for use in QWebViewer.

        :return: A QtCore.QUrl object built using self.source.
        """
        url = self.source
        # Check to see if path is absolute or relative, accommodating urls from many different places
        if not os.path.exists(url):
            location = HELP_SYSTEM.path / url
            sas_path = Path(os.path.dirname(sys.argv[0]))
            url = sas_path / location

        # Check if the URL string contains a fragment (jump link)
        if '#' in url.name:
            url_str, fragment = str(url.absolute()).split('#', 1)
            # Convert path to a QUrl needed for QWebViewerEngine
            abs_url = QtCore.QUrl.fromLocalFile(url_str)
            abs_url.setFragment(fragment)
        else:
            # Convert path to a QUrl needed for QWebViewerEngine
            abs_url = QtCore.QUrl.fromLocalFile(url)
        return abs_url
