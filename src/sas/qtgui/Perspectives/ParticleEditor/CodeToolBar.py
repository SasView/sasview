from PySide6 import QtGui, QtWidgets

import sas.qtgui.Perspectives.ParticleEditor.UI.icons_rc  # noqa: F401
from sas.qtgui.Perspectives.ParticleEditor.UI.CodeToolBarUI import Ui_CodeToolBar


class CodeToolBar(QtWidgets.QWidget, Ui_CodeToolBar):
    def __init__(self, parent=None):
        super().__init__()

        self.setupUi(self)


        load_icon = QtGui.QIcon()
        load_icon.addPixmap(QtGui.QPixmap(":/particle_editor/upload-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.loadButton.setIcon(load_icon)

        save_icon = QtGui.QIcon()
        save_icon.addPixmap(QtGui.QPixmap(":/particle_editor/download-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.saveButton.setIcon(save_icon)

        build_icon = QtGui.QIcon()
        build_icon.addPixmap(QtGui.QPixmap(":/particle_editor/hammer-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.buildButton.setIcon(build_icon)

        scatter_icon = QtGui.QIcon()
        scatter_icon.addPixmap(QtGui.QPixmap(":/particle_editor/scatter-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.scatterButton.setIcon(scatter_icon)
