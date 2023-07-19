import sys
from os.path import abspath, dirname, splitext, basename
from PySide6 import QtGui, QtWebEngineWidgets, QtCore, QtWidgets, QtWebEngineCore

from .UI.docViewWidgetUI import Ui_docViewerWindow
from sas.qtgui.Utilities.TabbedModelEditor import TabbedModelEditor


class DocViewWindow(QtWidgets.QDialog, Ui_docViewerWindow):
    def __init__(self, parent=None, source=None):
        super(DocViewWindow, self).__init__(parent._parent)
        self.parent = parent
        self.setupUi(self)
        # disable the context help icon
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Documentation Viewer")

        self.source = source

        self.loadHtml()

        self.initializeSignals()

    def initializeSignals(self):
        self.editButton.clicked.connect(self.onEdit)

    def onEdit(self):
        """
        Open editor window.
        """
        # Convert QUrl to pathname:
        from re import findall
        # Extract path from QUrl
        path = findall(r"(?<=file:\/\/\/).+\.html", str(self.webEngineViewer.url()))
        # Test to see if we're dealing with a model html file or other html file
        if "models" in path[0]:
            file = splitext(basename(path[0]))[0]
            print(file)
            self.editorWindow =  TabbedModelEditor(parent=self.parent,
                                                   edit_only=True,
                                                   load_file=file,
                                                   model=True)
        else:
            self.editorWindow =  TabbedModelEditor(parent=self.parent,
                                                   edit_only=True,
                                                   load_file=file,
                                                   model=False)
        self.editorWindow.show()
        

    def loadHtml(self):
        """
        Loads the HTML file specified when this python is called from another part of the program.
        """
        url = QtCore.QUrl.fromLocalFile(abspath(self.source))
        settings = self.webEngineViewer.settings()
        # Allows QtWebEngine to access MathJax and code highlighting APIs
        settings.setAttribute(QtWebEngineCore.QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QtWebEngineCore.QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        self.webEngineViewer.load(url)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win =  DocViewWindow()
    win.show()
    app.exec_()