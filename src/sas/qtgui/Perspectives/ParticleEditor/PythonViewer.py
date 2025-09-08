
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from sas.qtgui.Perspectives.ParticleEditor.defaults import default_text
from sas.qtgui.Perspectives.ParticleEditor.syntax_highlight import PythonHighlighter


class PythonViewer(QtWidgets.QTextEdit):
    """ Python text editor window"""

    build_trigger = Signal()

    def __init__(self, parent=None):
        super().__init__()

        # System independent monospace font
        f = QFont("unexistent")
        f.setStyleHint(QFont.Monospace)
        f.setPointSize(10)
        f.setWeight(QFont.Weight(700))
        self.setFont(f)

        self.code_highlighter = PythonHighlighter(self.document())

        self.setText(default_text)


    def keyPressEvent(self, e):
        """ Itercepted key press event"""
        if e.key() == Qt.Key_Tab:

            if e.modifiers() == Qt.ShiftModifier:
                # TODO: Multiline adjust, tab and shift-tab
                pass

            # Swap out tabs for four spaces
            self.textCursor().insertText("    ")
            return

        if e.key() == Qt.Key_Return and e.modifiers() == Qt.ShiftModifier:
            self.build_trigger.emit()

        else:
            super().keyPressEvent(e)

    def insertFromMimeData(self, source):
        """ Keep own highlighting"""
        self.insertPlainText(source.text())

def main():
    """ Demo/testing window"""
    app = QtWidgets.QApplication([])
    viewer = PythonViewer()

    viewer.show()
    app.exec_()


if __name__ == "__main__":
    main()
