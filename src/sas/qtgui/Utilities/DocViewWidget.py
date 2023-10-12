import sys
import os
from typing import Optional
import logging


from PySide6 import QtGui, QtWebEngineWidgets, QtCore, QtWidgets, QtWebEngineCore
from twisted.internet import threads

from .UI.DocViewWidgetUI import Ui_DocViewerWindow
from sas.qtgui.Utilities.TabbedModelEditor import TabbedModelEditor
from sas.qtgui.Utilities import GuiUtils
from sas.sascalc.fit import models

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

        # Necessary globals
        self.source = source
        self.regen_in_progress = False

        self.initializeSignals() # Connect signals

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

    def onShow(self):
        """
        Show window
        """
        self.show()
    
    def regenerateIfNeeded(self):
        """
        Determines whether or not a file needs to be regenerated.
        If it does, it will regenerate based off whether it is detected as SasView docs or a model.
        The documentation window will open after the process of regeneration is completed.
        Otherwise, simply triggers a load of the documentation window with loadHtml()
        """
        sas_path = os.path.abspath(os.path.dirname(sys.argv[0]))
        user_models = models.find_plugins_dir()
        html_path =  GuiUtils.HELP_DIRECTORY_LOCATION
        rst_py_path = GuiUtils.PY_SOURCE
        regen_string = ""

        if "models" in self.source:
            model_name = os.path.basename(self.source).replace("html", "py")
            regen_string = sas_path + "/" + rst_py_path + "/user/models/src/" + model_name
            user_model_name = user_models + model_name

            # Test if this is a user defined model, and if its HTML does not exist or is older than python source file
            if os.path.isfile(user_model_name):
                if self.newer(regen_string, user_model_name):
                    self.regenerateHtml(model_name)

            # Test to see if HTML does not exist or is older than python file
            elif self.newer(regen_string, self.source):
                self.regenerateHtml(model_name)
            # Regenerate RST then HTML if no model file found OR if HTML is older than equivalent .py    

        elif "index" in self.source:
            # Regenerate if HTML is older than RST -- for index.html, which gets passed in differently because it is located in a different folder
            regen_string = sas_path + "/" + rst_py_path + self.source.replace('.html', '.rst')
            html_path = sas_path + "/" + html_path + "/" + self.source
                # Test to see if HTML does not exist or is older than python file
            if self.newer(regen_string, html_path):
                self.regenerateHtml(regen_string)

        else:
            # Regenerate if HTML is older than RST
            from re import sub
            # Ensure that we are only using everything after and including /user/
            model_local_path = sub(r"^.*?(?=[\/\\]user)", "", self.source)
            html_path = sas_path + "/" + html_path + "/" + model_local_path.split('#')[0] # Remove jump links
            regen_string = sas_path + "/" + rst_py_path + model_local_path.replace('.html', '.rst').split('#')[0] #Remove jump links
                # Test to see if HTML does not exist or is older than python file
            if self.newer(regen_string, html_path):
                self.regenerateHtml(regen_string)
        
        if self.regen_in_progress is False:
            self.loadHtml() #loads the html file specified in the source url to the QWebViewer
    
    def newer(self, src, html):
        try:
            return not os.path.exists(html) or os.path.getmtime(src) > os.path.getmtime(html)
        except:
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

    def regenerateHtml(self, file_name):
        """
        Regenerate the documentation for the file
        """
        logging.info("Starting documentation regeneration...")
        sas_path = os.path.abspath(os.path.dirname(sys.argv[0]))
        recompile_path = GuiUtils.RECOMPILE_DOC_LOCATION
        regen_docs = sas_path + "/" + recompile_path + "/" + "makedocumentation.py"
        d = threads.deferToThread(self.regenerateDocs, regen_docs, target=file_name) # Regenerate specific documentation file
        d.addCallback(self.docRegenComplete, self.source)
        self.regen_in_progress = True
    
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
        self.onShow()
        self.loadHtml()
        self.parent.communicate.documentationRegeneratedSignal.emit()
        logging.info("Documentation regeneration completed.")
        self.regen_in_progress = False
