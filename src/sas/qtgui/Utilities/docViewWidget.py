import sys
from os.path import abspath
from PySide6 import QtGui, QtWebEngineWidgets, QtCore, QtWidgets, QtWebEngineCore
from .UI.docViewWidgetUI import Ui_docViewerWindow


class docViewWindow(QtWidgets.QDialog, Ui_docViewerWindow):
    def __init__(self, filepath, parent=None):
        super(docViewWindow, self).__init__(parent._parent)
        self.parent = parent
        #self.ui = Ui_docViewerWindow()
        self.setupUi(self)
        self.setWindowTitle("Documentation Viewer")
        self.load_html(filepath)

    def load_html(self, filepath):
        # html = abspath("../sasview/docs/sphinx-docs/build/html/index.html")
        html = abspath(filepath)
        url = QtCore.QUrl.fromLocalFile(html)
        settings = self.webEngineViewer.settings()
        # Allows QtWebEngine to access MathJax and code highlighting APIs
        settings.setAttribute(QtWebEngineCore.QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QtWebEngineCore.QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        self.webEngineViewer.load(url)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = docViewWindow()
    win.show()
    app.exec()