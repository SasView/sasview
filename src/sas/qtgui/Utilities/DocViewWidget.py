import logging
import os
import sys
import time
from pathlib import Path

from PySide6 import QtCore, QtWebEngineCore, QtWidgets
from PySide6.QtGui import QCloseEvent
from twisted.internet import threads

from sas.qtgui.Utilities.ModelEditors.TabbedEditor.TabbedModelEditor import TabbedModelEditor
from sas.sascalc.data_util.calcthread import CalcThread
from sas.sascalc.doc_regen.makedocumentation import make_documentation
from sas.system.user import (
    HELP_DIRECTORY_LOCATION,
    MAIN_DOC_SRC,
    PATH_LIKE,
    create_user_files_if_needed,
    get_plugin_dir,
)

from .UI.DocViewWidgetUI import Ui_DocViewerWindow

HTML_404 = '''
<html>
<body>
<p>Unable to find documentation.</p>
<p>Developers: please build the documentation and try again.</p>
</body>
</html>
'''


class DocGenThread(CalcThread):
    """Thread performing the fit """

    def __init__(self,
                 completefn=None,
                 updatefn=None,
                 yieldtime=0.03,
                 worktime=0.03,
                 reset_flag=False):
        CalcThread.__init__(self,
                            completefn,
                            updatefn,
                            yieldtime,
                            worktime)
        self.starttime = time.time()
        self.updatefn = updatefn
        self.reset_flag = reset_flag
        self.target = None
        self.runner = None
        self._running = False
        from sas.qtgui.Utilities.GuiUtils import communicate
        self.communicate = communicate

    def compute(self, target=None):
        """
        Regen the docs in a separate thread
        """
        self.target = Path(target)
        try:
            # Start a try/finally block to ensure that the lock is released if an exception is thrown
            if not self.target.exists():
                self.runner = make_documentation(self.target)
                while self.runner and self.runner.poll() is None:
                    time.sleep(0.5)
                    self.communicate.documentationUpdateLogSignal.emit()
        except KeyboardInterrupt as msg:
            logging.log(0, msg)
        finally:
            self.close()

    def close(self):
        # Ensure the runner and locks are fully released when closing the main application
        if self.runner:
            self.runner.kill()
            self.runner = None
        self.stop()


class DocViewWindow(QtWidgets.QDialog, Ui_DocViewerWindow):
    """
    Instantiates a window to view documentation using a QWebEngineViewer widget
    """

    def __init__(self, source: Path = None):
        """The DocViewWindow class is an HTML viewer built into SasView.

        :param parent: Any Qt object with a communicator that can trigger events.
        :param source: The Path to the html file.
        """
        super(DocViewWindow, self).__init__(None)
        self.setupUi(self)
        self.setWindowTitle("Documentation Viewer")

        # Necessary globals
        self.source: Path = Path(source)
        self.regen_in_progress: bool = False
        self.thread: CalcThread | None = None

        from sas.qtgui.Utilities.GuiUtils import communicate
        self.communicate = communicate
        self.initializeSignals()  # Connect signals

        # Hide editing button for 6.0.0 release
        self.editButton.setVisible(False)

        self.regenerateIfNeeded()

    def initializeSignals(self):
        """Initialize all external signals that will trigger events for the window."""
        self.editButton.clicked.connect(self.onEdit)
        self.closeButton.clicked.connect(self.closeEvent)
        self.communicate.documentationRegeneratedSignal.connect(self.refresh)
        self.communicate.closeSignal.connect(self.closeEvent)
        self.webEngineViewer.urlChanged.connect(self.updateTitle)
        self.webEngineViewer.page().profile().downloadRequested.connect(self.onDownload)

    def onEdit(self):
        """Open editor (TabbedModelEditor) window."""
        from re import findall, sub
        # Extract path from QUrl
        path = findall(r"(?<=file:\/\/\/).+\.html", str(self.webEngineViewer.url()))
        # Test to see if we're dealing with a model html file or other html file
        if "models" in path[0]:
            py_base_file_name = os.path.splitext(os.path.basename(path[0]))[0]
            self.editorWindow = TabbedModelEditor(parent=self.parent,
                                                  edit_only=True,
                                                  load_file=py_base_file_name,
                                                  model=True)
        else:
            # Remove everything before /user/ (or \user\)
            file = sub(r"^.*?(?=[\/\\]user)", "", path[0])

            # index.html is the only rst file outside the /user/ folder-- set it manually
            if "index.html" in file:
                file = "/index.html"
            self.editorWindow = TabbedModelEditor(parent=self.parent,
                                                  edit_only=True,
                                                  load_file=file,
                                                  model=False)
        self.editorWindow.show()

    def closeEvent(self, event: QCloseEvent):
        """
        Close window
        Keep as a separate method to allow for additional functionality when closing
        """
        if self.thread:
            self.thread.close()
        self.accept()

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
            logging.warning(f"your file: {_filename} was downloaded to your default download directory")
        else:
            logging.error(f"FAILED TO DOWNLOAD: {_filename} is unavailable")

    def regenerateIfNeeded(self):
        """
        Determines whether a file needs to be regenerated.
        If it does, it will regenerate based off whether it is detected as SasView docs or a model.
        The documentation window will open after the process of regeneration is completed.
        Otherwise, simply triggers a load of the documentation window with loadHtml()
        """
        user_models = Path(get_plugin_dir())
        html_path = HELP_DIRECTORY_LOCATION
        rst_path = MAIN_DOC_SRC
        base_path = self.source.parent.parts
        url_str = str(self.source)
        create_user_files_if_needed()

        if not MAIN_DOC_SRC.exists() and not HELP_DIRECTORY_LOCATION.exists():
            # The user docs were never built - disable edit button and do not attempt doc regen
            self.editButton.setEnabled(False)
            self.load404()
            return

        if "models" in base_path:
            user_model_name = user_models / self.source.name.replace("html", "py")

            # Test if this is a user defined model, and if its HTML does not exist or is older than python source file
            if os.path.isfile(user_model_name):
                if self.newer(user_model_name, url_str):
                    self.regenerateHtml(self.source.name)

            # Test to see if HTML does not exist or is older than python file
            elif not os.path.exists(url_str):
                self.load404()
            # Regenerate RST then HTML if no model file found OR if HTML is older than equivalent .py

        elif "index" in url_str:
            # Regenerate if HTML is older than RST -- for index.html, which gets passed in differently because it is located in a different folder
            regen_string = rst_path / str(self.source.name).replace(".html", ".rst")
                # Test to see if HTML does not exist or is older than python file
            if not os.path.exists(self.source.absolute()):
                self.load404()

        else:
            # Regenerate if HTML is older than RST
            from re import sub
            # Ensure that we are only using everything after and including /user/
            model_local_path = sub(r"^.*?user", "user", url_str)
            html_path = html_path / model_local_path.split('#')[0]  # Remove jump links
            regen_string = rst_path / model_local_path.replace('.html', '.rst').split('#')[0] #Remove jump links
                # Test to see if HTML does not exist or is older than python file
            if not os.path.exists(html_path):
                self.load404()

        if self.regen_in_progress is False:
            self.loadHtml() #loads the html file specified in the source url to the QWebViewer

    @staticmethod
    def newer(src: PATH_LIKE, html: PATH_LIKE) -> bool:
        """Compare two files to determine if a file regeneration is required.

        :param src: The ReST file that might need regeneration.
        :param html: The HTML file built from the ReST file.
        :return: Is the ReST file newer than the HTML file? Returned as a boolean.
        """
        try:
            html_exists = os.path.exists(html)
            rst_time = os.path.getmtime(src)
            html_time = os.path.getmtime(html)
            return not html_exists or rst_time > html_time
        except Exception:
            # Catch exception for debugging
            return True

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
            logging.warning(f"Error updating documentation window title: {ex}")

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
            location = HELP_DIRECTORY_LOCATION / url
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

    def regenerateHtml(self, file_name: PATH_LIKE):
        """Regenerate the documentation for the file passed to the method

        :param file_name: A file-path like object that needs regeneration.
        """
        logging.info("Starting documentation regeneration...")
        self.communicate.documentationRegenInProgressSignal.emit()
        d = threads.deferToThread(self.regenerateDocs, target=file_name)
        d.addCallback(self.docRegenComplete)
        self.regen_in_progress = True

    def regenerateDocs(self, target: PATH_LIKE = None):
        """Regenerates documentation for a specific file (target) in a subprocess

        :param target: A file-path like object that needs regeneration.
        """
        self.thread = DocGenThread()
        self.thread.queue(target=target)
        self.thread.ready(2.5)
        while not self.thread.isrunning():
            time.sleep(0.1)
        while self.thread.isrunning():
            time.sleep(0.1)

    def docRegenComplete(self, *args):
        """Tells Qt that regeneration of docs is done and emits signal tied to opening documentation viewer window.
        This method is likely called as a thread call back, but no value is used from that callback return.
        """
        self.loadHtml()
        self.communicate.documentationRegeneratedSignal.emit()
        logging.info("Documentation regeneration completed.")
        self.regen_in_progress = False
