import sys
from os.path import abspath, dirname
from PySide6 import QtGui, QtWebEngineWidgets, QtCore, QtWidgets, QtWebEngineCore

from .UI.docViewWidgetUI import Ui_docViewerWindow
from sas.qtgui.Utilities.TabbedModelEditor import TabbedModelEditor


class docViewWindow(QtWidgets.QDialog, Ui_docViewerWindow):
    def __init__(self, parent=None, source=None):
        super(docViewWindow, self).__init__()
        self.parent = parent
        self.setupUi(self)
        self.setWindowTitle("Documentation Viewer")

        self.loadHtml(source=source)

        self.initializeSignals()

    def initializeSignals(self):
        self.editButton.clicked.connect(self.onEdit)

    def onEdit(self):
        """
        Open editor window.
        """
        # Convert QUrl to pathname:
        from re import search
        # path = search(r"Q.*\'\)", str(self.webEngineViewer.url()))
        print(str(self.webEngineViewer.url()))
        # print(path)
        self.editorWindow =  TabbedModelEditor(parent=self.parent, edit_only=True, load=None)
        self.editorWindow.show()
        

    def loadHtml(self, source=None):
        """
        Loads the HTML file specified when this python is called from another part of the program.
        """
        url = QtCore.QUrl.fromLocalFile(abspath(source))
        settings = self.webEngineViewer.settings()
        # Allows QtWebEngine to access MathJax and code highlighting APIs
        settings.setAttribute(QtWebEngineCore.QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QtWebEngineCore.QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        self.webEngineViewer.load(url)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win =  docViewWindow()
    win.show()
    app.exec()