from PySide6 import QtWidgets
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

import sas.sasview
import sas.system.citation
import sas.system.version

from .UI.AcknowledgementsUI import Ui_Acknowledgements


class Acknowledgements(QtWidgets.QDialog, Ui_Acknowledgements):

    def __init__(self, parent=None):
        super(Acknowledgements, self).__init__(parent)
        self.setupUi(self)

        icon = QIcon()
        icon.addFile(":/res/ball.ico", QSize(), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        self.addText()

    def addText(self):
        """
        Modify the labels so the text corresponds to the current version
        """
        version = sas.system.version.__version__
        doi = sas.system.citation.__DOI__
        release_manager = sas.system.citation.__RELEASE_MANAGER__
        acknowledgement_text_1 = sas.system.citation.__ACKNOWLEDGEMENT__
        self.textBrowser.setText(acknowledgement_text_1)
        acknowledgement_text_2 = f'{release_manager}, et al. SasView Version {version} {doi}'
        self.textBrowser_2.setText(acknowledgement_text_2)
