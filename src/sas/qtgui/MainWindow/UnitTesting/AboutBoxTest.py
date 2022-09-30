import sys
import unittest
import webbrowser

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtTest import QTest
from PyQt5 import QtCore
from unittest.mock import MagicMock

import sas.sasview
import sas.system.version
from sas import config
from sas.system import web, legal

# Local
from sas.qtgui.MainWindow.AboutBox import AboutBox

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class AboutBoxTest(unittest.TestCase):
    '''Test the AboutBox'''
    def setUp(self):
        '''Create the AboutBox'''
        self.widget = AboutBox(None)

    def tearDown(self):
        '''Destroy the AboutBox'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        assert isinstance(self.widget, QtWidgets.QWidget)
        assert self.widget.windowTitle() == "About"
        assert self.widget.cmdOK.text() == "OK"

        assert "SasView" in self.widget.label_2.text()
        # Link buttons pixmaps don't contain image filenames, so can't check this.
        # self.assertEqual(self.widget.cmdLinkUT.icon().name(), "utlogo.gif")


    def testVersion(self):
        """
        Assure the version number is as expected
        """
        version = self.widget.lblVersion
        assert isinstance(version, QtWidgets.QLabel)
        assert str(version.text()) == str(sas.system.version.__version__)

    def testAbout(self):
        """
        Assure the about label is filled properly
        """
        about = self.widget.lblAbout
        assert isinstance(about, QtWidgets.QLabel)
        # License
        assert str(legal.copyright) in about.text()
        # URLs
        assert str(web.homepage_url) in about.text()
        assert str(config.download_url) in about.text()
        assert str(config.help_email) in about.text()

        # Are links enabled?
        assert about.openExternalLinks()

    def testAddActions(self):
        """
        Assure link buttons are set up correctly
        """
        webbrowser.open = MagicMock()
        all_hosts = [
                config.nist_url,
                config.umd_url,
                config.sns_url,
                config.nsf_url,
                config.isis_url,
                config.ess_url,
                config.ill_url,
                config.ansto_url,
                config.inst_url,
                config.delft_url,
                config.bam_url,
                config.diamond_url]

        # Press the buttons
        buttonList = self.widget.findChildren(QtWidgets.QPushButton)
        for button in buttonList:
            QTest.mouseClick(button, QtCore.Qt.LeftButton)
            #open_link = webbrowser.open.call_args
            args, _ = webbrowser.open.call_args
            # args[0] contains the actual argument sent to open()
            assert args[0] in all_hosts

        # The above test also greedily catches the OK button,
        # so let's test it separately.
        # Show the widget
        self.widget.show()
        assert self.widget.isVisible()
        # Click on the OK button
        QTest.mouseClick(self.widget.cmdOK, QtCore.Qt.LeftButton)
        # assure the widget is no longer seen
        assert not self.widget.isVisible()

if __name__ == "__main__":
    unittest.main()
