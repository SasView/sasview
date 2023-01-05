import webbrowser
import pytest

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtTest import QTest
from PyQt5 import QtCore

import sas.sasview
import sas.system.version
from sas.system import web, legal

# Local
from sas.sasview.MainWindow.AboutBox import AboutBox

class AboutBoxTest:
    '''Test the AboutBox'''

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the AboutBox'''
        w = AboutBox(None)
        yield w
        w.close()

    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget, QtWidgets.QWidget)
        assert widget.windowTitle() == "About"
        assert widget.cmdOK.text() == "OK"

        assert "SasView" in widget.label_2.text()
        # Link buttons pixmaps don't contain image filenames, so can't check this.
        # assert widget.cmdLinkUT.icon().name() == "utlogo.gif"


    def testVersion(self, widget):
        """
        Assure the version number is as expected
        """
        version = widget.lblVersion
        assert isinstance(version, QtWidgets.QLabel)
        assert str(version.text()) == str(sas.system.version.__version__)

    def testAbout(self, widget):
        """
        Assure the about label is filled properly
        """
        about = widget.lblAbout
        assert isinstance(about, QtWidgets.QLabel)
        # License
        assert str(legal.copyright) in about.text()
        # URLs
        assert str(web.homepage_url) in about.text()
        assert str(web.download_url) in about.text()
        assert str(web.help_email) in about.text()

        # Are links enabled?
        assert about.openExternalLinks()

    def testAddActions(self, widget, mocker):
        """
        Assure link buttons are set up correctly
        """
        mocker.patch.object(webbrowser, 'open')
        all_hosts = [
                web.nist_url,
                web.umd_url,
                web.sns_url,
                web.nsf_url,
                web.isis_url,
                web.ess_url,
                web.ill_url,
                web.ansto_url,
                web.inst_url,
                web.delft_url,
                web.bam_url,
                web.diamond_url]

        # Press the buttons
        buttonList = widget.findChildren(QtWidgets.QPushButton)
        for button in buttonList:
            QTest.mouseClick(button, QtCore.Qt.LeftButton)
            #open_link = webbrowser.open.call_args
            args, _ = webbrowser.open.call_args
            # args[0] contains the actual argument sent to open()
            assert args[0] in all_hosts

        # The above test also greedily catches the OK button,
        # so let's test it separately.
        # Show the widget
        widget.show()
        assert widget.isVisible()
        # Click on the OK button
        QTest.mouseClick(widget.cmdOK, QtCore.Qt.LeftButton)
        # assure the widget is no longer seen
        assert not widget.isVisible()
