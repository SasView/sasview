import sys
import os
import logging
from pathlib import Path

from PySide6 import QtCore, QtWidgets, QtWebEngineCore
from twisted.internet import threads

from .UI.DocViewWidgetUI import Ui_DocViewerWindow
from sas.qtgui.Utilities.TabbedModelEditor import TabbedModelEditor
from sas.sascalc.fit import models
from sas.sascalc.doc_regen.makedocumentation import make_documentation, HELP_DIRECTORY_LOCATION, MAIN_PY_SRC, MAIN_DOC_SRC


class DocViewWindow(QtWidgets.QDialog, Ui_DocViewerWindow):
    """
    Instantiates a window to view documentation using a QWebEngineViewer widget
    """

    def __init__(self, parent=None, source: Path = None):
        super(DocViewWindow, self).__init__(parent._parent)
        self.parent = parent
        self.setupUi(self)
        self.setWindowTitle("Documentation Viewer")

        # Necessary globals
        self.source: Path = Path(source)
        self.regen_in_progress: bool = False

        self.initializeSignals()  # Connect signals

        self.regenerateIfNeeded()

    def initializeSignals(self):
        """
        Initialize Signals 
        """
        self.editButton.clicked.connect(self.onEdit)
        self.closeButton.clicked.connect(self.onClose)
        self.parent.communicate.documentationRegeneratedSignal.connect(self.refresh)

    def onEdit(self):
        """
        Open editor (TabbedModelEditor) window.
        """
        # Convert QUrl to pathname:
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

    def onClose(self):
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
    
    def regenerateIfNeeded(self):
        """
        Determines whether a file needs to be regenerated.
        If it does, it will regenerate based off whether it is detected as SasView docs or a model.
        The documentation window will open after the process of regeneration is completed.
        Otherwise, simply triggers a load of the documentation window with loadHtml()
        """
        user_models = Path(models.find_plugins_dir())
        html_path = HELP_DIRECTORY_LOCATION
        rst_path = MAIN_DOC_SRC
        rst_py_path = MAIN_PY_SRC
        base_path = self.source.parent.parts
        url_str = "/".join(base_path) + self.source.name

        if "models" in base_path:
            model_name = self.source.name.replace("html", "py")
            regen_string = rst_py_path / "user" / "models" / "src" / model_name
            user_model_name = user_models / model_name

            # Test if this is a user defined model, and if its HTML does not exist or is older than python source file
            if os.path.isfile(user_model_name):
                if self.newer(regen_string, user_model_name):
                    self.regenerateHtml(model_name)

            # Test to see if HTML does not exist or is older than python file
            elif self.newer(regen_string, self.source):
                self.regenerateHtml(model_name)
            # Regenerate RST then HTML if no model file found OR if HTML is older than equivalent .py    

        elif "index" in base_path:
            # Regenerate if HTML is older than RST -- for index.html, which gets passed in differently because it is located in a different folder
            regen_string = rst_py_path / url_str.replace('.html', '.rst')
            html_path = html_path / self.source
                # Test to see if HTML does not exist or is older than python file
            if self.newer(regen_string, html_path):
                self.regenerateHtml(regen_string)

        else:
            # Regenerate if HTML is older than RST
            from re import sub
            # Ensure that we are only using everything after and including /user/
            model_local_path = sub(r"^.*?user", "user", url_str)
            html_path = html_path / model_local_path.split('#')[0]  # Remove jump links
            regen_string = rst_path / model_local_path.replace('.html', '.rst').split('#')[0] #Remove jump links
                # Test to see if HTML does not exist or is older than python file
            if self.newer(regen_string, html_path):
                self.regenerateHtml(regen_string)
        
        if self.regen_in_progress is False:
            self.loadHtml() #loads the html file specified in the source url to the QWebViewer

    @staticmethod
    def newer(src, html):
        try:
            return not os.path.exists(html) or os.path.getmtime(src) > os.path.getmtime(html)
        except Exception:
            return True

    def loadHtml(self):
        """
        Loads the HTML file specified when this python is called from another part of the program.
        """
        # Ensure urls are properly processed before passing into widget
        url = self.processUrl()
        settings = self.webEngineViewer.settings()
        # Allows QtWebEngine to access MathJax and code highlighting APIs
        settings.setAttribute(QtWebEngineCore.QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QtWebEngineCore.QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        self.webEngineViewer.load(url)

        # Show widget
        self.onShow()
    
    def refresh(self):
        self.webEngineViewer.reload()

    def processUrl(self):
        """
        Process path into proper QUrl for use in QWebViewer
        """
        url = self.source
        # Check to see if path is absolute or relative, accommodating urls from many different places
        if not os.path.exists(url):
            location = HELP_DIRECTORY_LOCATION / url
            sas_path = Path(os.path.dirname(sys.argv[0]))
            url = sas_path / location

        # Check if the URL string contains a fragment (jump link)
        if '#' in url.name:
            url, fragment = url.name.split('#', 1)
            # Convert path to a QUrl needed for QWebViewerEngine
            abs_url = QtCore.QUrl.fromLocalFile(url)
            abs_url.setFragment(fragment)
        else:
            # Convert path to a QUrl needed for QWebViewerEngine
            abs_url = QtCore.QUrl.fromLocalFile(url)
        return abs_url

    def regenerateHtml(self, file_name):
        """
        Regenerate the documentation for the file
        """
        logging.info("Starting documentation regeneration...")
        d = threads.deferToThread(self.regenerateDocs, target=file_name)
        d.addCallback(self.docRegenComplete, self.source)
        self.regen_in_progress = True

    @staticmethod
    def regenerateDocs(target=None):
        """
        Regenerates documentation for a specific file (target) in a subprocess
        """
        make_documentation(target)
    
    def docRegenComplete(self):
        """
        Tells Qt that regeneration of docs is done and emits signal tied to opening
        documentation viewer window
        """
        self.onShow()
        self.loadHtml()
        self.parent.communicate.documentationRegeneratedSignal.emit()
        logging.info("Documentation regeneration completed.")
        self.regen_in_progress = False
