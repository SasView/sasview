import functools
from PyQt5 import QtWidgets, QtCore

import sas.sasview
import sas.qtgui.Utilities.LocalConfig as LocalConfig
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.UI import images_rc
from sas.qtgui.UI import main_resources_rc

from .UI.AcknowledgementsUI import Ui_Acknowledgements

class Acknowledgements(QtWidgets.QDialog, Ui_Acknowledgements):
    def __init__(self, parent=None):
        super(Acknowledgements, self).__init__(parent)
        self.setupUi(self)
        # disable the context help icon
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        self.addText()

        #self.addActions()

    def addText(self):
        """
        Modify the labels so the text corresponds to the current version
        """
        version = sas.sasview.__version__
        doi = sas.sasview.__DOI__
        acknowledgement_text_1 = "This work benefited from the use of the SasView application, originally developed " \
                                 "under NSF Award DMR - 0520547. SasView also contains code developed with funding" \
                                 " from the EU Horizon 2020 programme under the SINE2020 project Grant No 654000."

        self.textBrowser.setText(acknowledgement_text_1)
        acknowledgement_text_2 = 'M. Doucet et al. SasView Version ' + str(version) + ', ' + str(doi)
        self.textBrowser_2.setText(acknowledgement_text_2)


    # def addActions(self):
    #     """
    #     Add actions to the logo push buttons
    #     """
    #
    #     self.cmdOK.clicked.connect(self.close)
