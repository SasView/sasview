
from PySide6 import QtWidgets
from PySide6.QtGui import QFont

from sas.qtgui.Perspectives.ParticleEditor.syntax_highlight import PythonHighlighter
from sas.system.version import __version__ as version

initial_text = f"<p><b>Particle Designer Log - SasView {version}</b></p>"

class OutputViewer(QtWidgets.QTextEdit):
    """ Python text editor window"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # System independent monospace font
        f = QFont("unexistent")
        f.setStyleHint(QFont.Monospace)
        f.setPointSize(9)
        f.setWeight(QFont.Weight(500))

        self.setFont(f)

        self.setText(initial_text)

    def keyPressEvent(self, e):
        """ Itercepted key press event"""

        # Do nothing

        return

    def addError(self, text):
        pass

    def addText(self, text):
        pass



def main():
    app = QtWidgets.QApplication([])
    viewer = OutputViewer()

    viewer.show()
    app.exec_()


if __name__ == "__main__":
    main()
