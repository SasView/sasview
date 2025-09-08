
from PySide6 import QtWidgets
from PySide6.QtGui import QFont

from sas.system.version import __version__ as version

initial_text = f"<p><b>Particle Editor Log - SasView {version}</b></p>"

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

    def _htmlise(self, text):
        return "<br>".join(text.split("\n"))

    def appendAndMove(self, text):
        self.append(text)
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def reset(self):
        self.setText(initial_text)

    def addError(self, text):
        self.appendAndMove(f'<span style="color:Tomato;"><b>{self._htmlise(text)}</b></span>')

    def addText(self, text):
        self.appendAndMove(f'<span style="color:Black;">{self._htmlise(text)}</span>')

    def addWarning(self, text):
        self.appendAndMove(f'<span style="color:Orange;"><b>{self._htmlise(text)}</b></span>')



def main():
    app = QtWidgets.QApplication([])
    viewer = OutputViewer()

    viewer.show()
    app.exec_()


if __name__ == "__main__":
    main()
