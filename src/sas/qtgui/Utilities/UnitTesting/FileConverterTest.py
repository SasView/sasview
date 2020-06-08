import sys
import os
import unittest
import webbrowser
import tempfile
from unittest.mock import MagicMock, patch

from PyQt5 import QtGui
from PyQt5 import QtWidgets

from sas.qtgui.Utilities.GuiUtils import Communicate

# Local
from sas.qtgui.Utilities.FileConverter import FileConverterWidget

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)


class FileConverterTest(unittest.TestCase):
    """ Test the simple FileConverter dialog """
    def setUp(self):
        """ Create FileConverter dialog """

        class dummy_manager(object):
            def communicator(self):
                return Communicate()

        self.widget = FileConverterWidget(dummy_manager())

    def tearDown(self):
        """ Destroy the GUI """

        self.widget.close()
        self.widget = None

    def testDefaults(self):
        """ Test the GUI in its default state """

        self.assertIsInstance(self.widget, QtWidgets.QDialog)

        # Default title
        self.assertEqual(self.widget.windowTitle(), "File Converter")

        # Modal window
        self.assertFalse(self.widget.isModal())

        # Size policy
        self.assertEqual(self.widget.sizePolicy().Policy(), QtWidgets.QSizePolicy.Fixed)

        # self.assertEqual(self.widget.is1D)
        #
        # self.is1D = True
        # self.isBSL = False
        # self.ifile = ""
        # self.qfile = ""
        # self.ofile = ""
        # self.metadata = {}
        # self.setValidators()


    def testOnHelp(self):
        """ Test the default help renderer """

        self.widget.parent.showHelp = MagicMock()
        self.widget.onHelp()
        self.assertTrue(self.widget.parent.showHelp.called_once())
        #args = self.widget.manager.showHelp.call_args
        #self.assertIn('data_operator_help.html', args[0][0])
