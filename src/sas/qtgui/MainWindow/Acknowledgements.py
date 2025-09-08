from PySide6 import QtWidgets
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

import sas.sasview
import sas.system.version
import sas.system.zenodo

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
        doi = sas.system.zenodo.__DOI__
        acknowledgement_text_1 = "This work benefited from the use of the SasView application, originally developed " \
                                 "under NSF Award DMR - 0520547. SasView also contains code developed with funding" \
                                 " from the EU Horizon 2020 programme under the SINE2020 project Grant No 654000."

        self.textBrowser.setText(acknowledgement_text_1)
        acknowledgement_text_2 = 'M. Doucet et al. SasView Version ' + str(version) + ', ' + str(doi)
        self.textBrowser_2.setText(acknowledgement_text_2)
