
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont



from sas.qtgui.Perspectives.ParticleEditor.syntax_highlight import PythonHighlighter

default_text = '''""" Default text goes here...
 
should probably define a simple function
"""

def sld(x,y,z):
    """ A cube with 100Ang side length"""
    
    inside = (np.abs(x) < 50) & (np.abs(y) < 50) & (np.abs(z) < 50)
    
    out = np.zeros_like(x)
    
    out[inside] = 1
    
    return out

'''
class PythonViewer(QtWidgets.QTextEdit):
    """ Python text editor window"""
    def __init__(self, parent=None):
        super().__init__(parent)

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
            # Swap out tabs for four spaces
            self.textCursor().insertText("    ")
            return
        else:
            super().keyPressEvent(e)

def main():
    """ Demo/testing window"""
    app = QtWidgets.QApplication([])
    viewer = PythonViewer()

    viewer.show()
    app.exec_()


if __name__ == "__main__":
    main()
