import sys
import unittest
import webbrowser

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtTest import QTest
from PyQt5 import QtCore
from unittest.mock import MagicMock

from sas import config
from sas.system import web

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
        self.assertIsInstance(self.widget, QtWidgets.QWidget)
        self.assertEqual(self.widget.windowTitle(), "About")
        self.assertEqual(self.widget.cmdOK.text(), "OK")

        self.assertIn("SasView", self.widget.label_2.text())
        # Link buttons pixmaps don't contain image filenames, so can't check this.
        # self.assertEqual(self.widget.cmdLinkUT.icon().name(), "utlogo.gif")


    def testVersion(self):
        """
        Assure the version number is as expected
        """
        version = self.widget.lblVersion
        self.assertIsInstance(version, QtWidgets.QLabel)
        self.assertEqual(str(version.text()), str(config.__version__))

    def testAbout(self):
        """
        Assure the about label is filled properly
        """
        about = self.widget.lblAbout
        self.assertIsInstance(about, QtWidgets.QLabel)
        # build version
        self.assertIn(str(config.__build__), about.text())
        # License
        self.assertIn(str(config._copyright), about.text())
        # URLs
        self.assertIn(str(web.homepage_url), about.text())
        self.assertIn(str(config.download_url), about.text())
        self.assertIn(str(config._license), about.text())

        # Are links enabled?
        self.assertTrue(about.openExternalLinks())

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
            self.assertIn(args[0], all_hosts)

        # The above test also greedily catches the OK button,
        # so let's test it separately.
        # Show the widget
        self.widget.show()
        self.assertTrue(self.widget.isVisible())
        # Click on the OK button
        QTest.mouseClick(self.widget.cmdOK, QtCore.Qt.LeftButton)
        # assure the widget is no longer seen
        self.assertFalse(self.widget.isVisible())

if __name__ == "__main__":
    unittest.main()
