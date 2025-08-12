
import pytest
from PySide6 import QtWidgets

# Local
from sas.qtgui.MainWindow.WelcomePanel import WelcomePanel


class WelcomePanelTest:
    '''Test the WelcomePanel'''

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the WelcomePanel'''
        w = WelcomePanel(None)

        yield w

        w.close()

    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget, QtWidgets.QDialog)
        assert widget.windowTitle() == "Welcome"

    def testVersion(self, widget):
        '''Test the version string'''
        version = widget.lblVersion
        assert isinstance(version, QtWidgets.QLabel)

        assert "SasView" in version.text()
        for inst in "UTK, UMD, ESS, NIST, ORNL, ISIS, ILL, DLS, TUD, BAM, ANSTO".split(", "):
            assert inst in version.text()
