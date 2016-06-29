# global
import sys
import os
import functools

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtWebKit

import sas.sasview
import LocalConfig
import GuiUtils

from UI.AboutUI import AboutUI

class AboutBox(AboutUI):
    def __init__(self, parent=None):
        super(AboutBox, self).__init__(parent)
        self.setWindowTitle("About")

        self.addText()

        self.addActions()

    def addText(self):
        """
        Modify the labels so the text corresponds to the current version
        """
        version = sas.sasview.__version__
        build = sas.sasview.__build__

        version_text = r'<html><head/><body><p><span style=" font-size:24pt;">'\
                     + str(version) + r'</span></p></body></html>'
        self.lblVersion.setText(str(version))
        lbl_font = self.font()
        lbl_font.setPointSize(24)
        self.lblVersion.setFont(lbl_font)
        about_text = r'<html><head/><body><p>'
        about_text += '<p>Build ' + str(LocalConfig.__build__) +'</p>'
        about_text += '<p>' + LocalConfig._copyright + '</p>'
        about_text += r'<p><a href=http://www.sasview.org>http://www.sasview.org</a></p><br/>'
        about_text += '<p>Comments? Bugs? Requests?<br/>'
        about_text += r'<a href=mailto:help@sasview.org>Send us a ticket</a></p><br/>'
        about_text += r'<a href=https://github.com/SasView/sasview/releases>Get the latest version</a></p><br/>'
        self.lblAbout.setText(about_text)

        # Enable link clicking on the label
        self.lblAbout.setOpenExternalLinks(True)

    def addActions(self):
        """
        Add actions to the logo push buttons
        """
        self.cmdLinkUT.clicked.connect(functools.partial(GuiUtils.openLink, LocalConfig._inst_url))
        self.cmdLinkUMD.clicked.connect(functools.partial(GuiUtils.openLink, LocalConfig._umd_url))
        self.cmdLinkNIST.clicked.connect(functools.partial(GuiUtils.openLink, LocalConfig._nist_url))
        self.cmdLinkSNS.clicked.connect(functools.partial(GuiUtils.openLink, LocalConfig._sns_url))
        self.cmdLinkISIS.clicked.connect(functools.partial(GuiUtils.openLink, LocalConfig._isis_url))
        self.cmdLinkESS.clicked.connect(functools.partial(GuiUtils.openLink, LocalConfig._ess_url))
        self.cmdLinkILL.clicked.connect(functools.partial(GuiUtils.openLink, LocalConfig._ill_url))

        self.cmdOK.clicked.connect(self.close)
