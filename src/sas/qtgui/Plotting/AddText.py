from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from sas.qtgui.Plotting.UI.AddTextUI import Ui_AddText


class AddText(QtWidgets.QDialog, Ui_AddText):
    """ Simple GUI for a single line text query """
    def __init__(self, parent=None):
        super(AddText, self).__init__()
        self.setupUi(self)

        icon = QIcon()
        icon.addFile(":/res/ball.ico", QSize(), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        self._font = QtGui.QFont()
        self._color = "black"
        self.btnFont.clicked.connect(self.onFontChange)
        self.btnColor.clicked.connect(self.onColorChange)

    def text(self):
        return self.textEdit.toPlainText()

    def font(self):
        return self._font

    def color(self):
        return self._color

    def onFontChange(self, event):
        """
        Pop up the standard Qt Font change dialog
        """
        self._font, ok = QtWidgets.QFontDialog.getFont(parent=self)
        if ok:
            self.textEdit.setFont(self._font)

    def onColorChange(self, event):
        """
        Pop up the standard Qt color change dialog
        """
        # Pick up the chosen color
        self._color = QtWidgets.QColorDialog.getColor(parent=self)
        # Update the text control
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Text, self._color)
        self.textEdit.setPalette(palette)

        # Save the color as #RRGGBB
        self._color = str(self._color.name())
