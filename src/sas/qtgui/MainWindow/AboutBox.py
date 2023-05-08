import functools
import os
from PySide6 import QtWidgets, QtCore

import sas.sasview
import sas.qtgui.Utilities.GuiUtils as GuiUtils
import sas.system.version
from sas.system import web, legal
from .UI.AboutUI import Ui_AboutUI

class AboutBox(QtWidgets.QDialog, Ui_AboutUI):
    def __init__(self, parent=None):
        super(AboutBox, self).__init__(parent)
        self.setupUi(self)
        # disable the context help icon
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        self.setWindowTitle("About")

        self.addText()

        self.addActions()

    def addText(self):
        """
        Modify the labels so the text corresponds to the current version
        """
        version = sas.system.version.__version__

        self.lblVersion.setText(str(version))
        lbl_font = self.font()
        lbl_font.setPointSize(24)
        self.lblVersion.setFont(lbl_font)

        dir_path = os.path.split(sas.__file__)[0]
        installation_path = os.path.split(dir_path)[0]

        about_text = f"""
        <html>
            <head/>
            <body>
                <p>
                    {legal.copyright}
                </p>
                <p>
                    <a href="{web.homepage_url}">{web.homepage_url}</a>
                </p>
                <p>
                    Installation path: {installation_path}
                </p>                
                <p>A list of individual contributors can be found at: 
                <a href="{web.homepage_url}/people">{web.homepage_url}/people</a></p>
                <p>
                    Comments? Bugs? Requests?
                    <br/>
                    <a href="mailto:{web.help_email}">Send us a ticket</a>
                </p>
                <br/>
                <p>
                    <a href="{web.download_url}">Get the latest version</a>
                </p>
                <br/>
            </body>
        </html>
        """

        self.lblAbout.setText(about_text)

        # Enable link clicking on the label
        self.lblAbout.setOpenExternalLinks(True)

    def addActions(self):
        """
        Add actions to the logo push buttons
        """
        self.cmdLinkUT.clicked.connect(functools.partial(
            GuiUtils.openLink, web.inst_url))
        self.cmdLinkUMD.clicked.connect(functools.partial(
            GuiUtils.openLink, web.umd_url))
        self.cmdLinkNIST.clicked.connect(functools.partial(
            GuiUtils.openLink, web.nist_url))
        self.cmdLinkSNS.clicked.connect(functools.partial(
            GuiUtils.openLink, web.sns_url))
        self.cmdLinkISIS.clicked.connect(functools.partial(
            GuiUtils.openLink, web.isis_url))
        self.cmdLinkESS.clicked.connect(functools.partial(
            GuiUtils.openLink, web.ess_url))
        self.cmdLinkILL.clicked.connect(functools.partial(
            GuiUtils.openLink, web.ill_url))
        self.cmdLinkANSTO.clicked.connect(functools.partial(
            GuiUtils.openLink, web.ansto_url))
        self.cmdLinkBAM.clicked.connect(functools.partial(
            GuiUtils.openLink, web.bam_url))
        self.cmdLinkDELFT.clicked.connect(functools.partial(
            GuiUtils.openLink, web.delft_url))
        self.cmdLinkDIAMOND.clicked.connect(functools.partial(
            GuiUtils.openLink, web.diamond_url))

        self.cmdOK.clicked.connect(self.close)
