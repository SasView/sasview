from PySide6 import QtWidgets

from sas.qtgui.Perspectives.ParticleEditor.FunctionViewer import FunctionViewer
from sas.qtgui.Perspectives.ParticleEditor.PythonViewer import PythonViewer
from sas.qtgui.Perspectives.ParticleEditor.OutputViewer import OutputViewer
from sas.qtgui.Perspectives.ParticleEditor.UI.DesignWindowUI import Ui_DesignWindow
class DesignWindow(QtWidgets.QDialog, Ui_DesignWindow):
    def __init__(self, parent=None):
        super().__init__()

        self.setupUi(self)

        definitionLayout = QtWidgets.QVBoxLayout()
        self.definitionTab.setLayout(definitionLayout)

        self.pythonViewer = PythonViewer()
        self.outputViewer = OutputViewer()

        definitionLayout.addWidget(self.pythonViewer)
        definitionLayout.addWidget(self.outputViewer)

        self.functionViewer = FunctionViewer()
        self.densityViewerContainer.layout().addWidget(self.functionViewer)

        self.setWindowTitle("Placeholder title")

        self.parent = parent


def main():
    """ Demo/testing window"""

    from sas.qtgui.convertUI import main

    main()

    app = QtWidgets.QApplication([])
    window = DesignWindow()

    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
