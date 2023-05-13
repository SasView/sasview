
from PySide6 import QtWidgets
from PySide6.QtGui import QFont

from sas.qtgui.Perspectives.ParticleEditor.syntax_highlight import PythonHighlighter

class OutputViewer(QtWidgets.QTextEdit):
    """ Python text editor window"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # System independent monospace font
        f = QFont("unexistent")
        f.setStyleHint(QFont.Monospace)
        self.setFont(f)

        self.code_highlighter = PythonHighlighter(self.document())

    def keyPressEvent(self, e):
        """ Itercepted key press event"""

        # Do nothing

        return

def main():
    app = QtWidgets.QApplication([])
    viewer = OutputViewer()

    viewer.show()
    app.exec_()


if __name__ == "__main__":
    main()
