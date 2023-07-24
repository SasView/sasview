import sys
import os
from typing import Optional


from PySide6 import QtGui, QtWebEngineWidgets, QtCore, QtWidgets, QtWebEngineCore
from twisted.internet import threads

from .UI.DocViewWidgetUI import Ui_DocViewerWindow
from sas.qtgui.Utilities.TabbedModelEditor import TabbedModelEditor
from sas.qtgui.Utilities import GuiUtils


class DocViewWindow(QtWidgets.QDialog, Ui_DocViewerWindow):
    """
    Instantiates a window to view documentation using a QWebEngineViewer widget
    """
    def __init__(self, parent=None, source=None):
        super(DocViewWindow, self).__init__(parent._parent)
        self.parent = parent
        self.setupUi(self)
        # Disable the context help icon
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Documentation Viewer")

        # Necessary global
        self.source = source

        self.initializeSignals() # Connect signals

        self.regenerateNeeded() #loads the html file specified in the source url to the QWebViewer

    def initializeSignals(self):
        """
        Initialize Signals 
        """
        self.parent.communicate.docsRegeneratedSignal.connect(self.loadHtml)

        self.editButton.clicked.connect(self.onEdit)
        self.closeButton.clicked.connect(self.onClose)

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
            self.editorWindow =  TabbedModelEditor(parent=self.parent,
                                                   edit_only=True,
                                                   load_file=py_base_file_name,
                                                   model=True)
        else:
            # Remove everything before /user/ (or \user\)
            file = sub(r"^.*?(?=[\/\\]user)", "", path[0])

            # index.html is the only rst file outside of /user/ folder-- set it manually
            if "index.html" in file:
                file = "/index.html"
            self.editorWindow =  TabbedModelEditor(parent=self.parent,
                                                   edit_only=True,
                                                   load_file=file,
                                                   model=False)
        self.editorWindow.show()

    def onClose(self):
        """
        Close window
        """
        self.close()
    
    def regenerateNeeded(self):
        """
        Determine what processes are needed in order to display updated docs
        """
        # Define a lot of path variables
        rst_path = self.findRstEquivalent()

        self.loadHtml() #loads the html file specified in the source url to the QWebViewer
    
    def findRstEquivalent(self):
        """
        Returns path of equivalent Python file to a specified HTML file. If the specified HTML file is not from a model, then return the path to its RST.
        is_python variable determines whether of not we will have to generate a RST from the python file before running it through sphinx.
        """
        is_python = False
        sas_path = os.path.abspath(os.path.dirname(sys.argv[0]))
        html_path =  GuiUtils.HELP_DIRECTORY_LOCATION
        regen_string = ""

        if "models" in self.source:
            pass
        if "index" in self.source:
            pass
        else:
            pass
        
        return regen_string, is_python

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

    def processUrl(self):
        url = self.source
        # Check to see if path is absolute or relative, accomodating urls from many different places
        if not os.path.exists(url):
            from sas.qtgui.Utilities.GuiUtils import HELP_DIRECTORY_LOCATION
            location = HELP_DIRECTORY_LOCATION + url
            sas_path = os.path.abspath(os.path.dirname(sys.argv[0]))
            url = sas_path+"/"+location

        # Check if the URL string contains a fragment (jump link)
        if '#' in url:
            fragment = url.split('#', 1)[1]
            url = url.split('#', 1)[0]
            # Convert path to a QUrl needed for QWebViewerEngine
            abs_url = QtCore.QUrl.fromLocalFile(url)
            abs_url.setFragment(fragment)
        else:
            # Convert path to a QUrl needed for QWebViewerEngine
            abs_url = QtCore.QUrl.fromLocalFile(url)
        return abs_url

    def regenerateHtml(self):
        """
        Regenerate the documentation for the file
        """
        regen_in_progress = False
        sas_path = os.path.abspath(os.path.dirname(sys.argv[0]))
        html_path =  GuiUtils.HELP_DIRECTORY_LOCATION
        recompile_path = GuiUtils.RECOMPILE_DOC_LOCATION
        regen_docs = sas_path + "/" + recompile_path + "/" + "makedocumentation.py"
        py_target = self.kernel_module.id + ".py"
        tree_location = sas_path + "/" + html_path + "/user/models/"
        helpfile = self.kernel_module.id + ".html"
        help_location = tree_location + helpfile
        d = threads.deferToThread(self.regenerateDocs, regen_docs, target=py_target) # Regenerate specific documentation file
        d.addCallback(self.docRegenComplete, help_location)
        regen_in_progress = True
    
    def regenerateDocs(self, regen_docs, target=None):
        """
        Regenerates documentation for a specific file (target) in a subprocess
        """
        import subprocess
        command = [
            sys.executable,
            regen_docs,
            target,
        ]
        doc_regen_dir = os.path.dirname(regen_docs)
        subprocess.run(command, cwd=doc_regen_dir) # cwd parameter tells subprocess to open from a specific directory
    
    def docRegenComplete(self, d, help_location):
        """
        Tells Qt that regeneration of docs is done and emits signal tied to opening
        documentation viewer window
        """
        self.parent.communicate.docsRegeneratedSignal.emit(help_location)
