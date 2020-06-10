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

        self.assertTrue(self.widget.is1D,)
        self.assertFalse(self.widget.isBSL)
        self.assertEqual(self.widget.ifile, '')
        self.assertEqual(self.widget.qfile, '')
        self.assertEqual(self.widget.ofile, '')
        self.assertEqual(self.widget.metadata,{})


    def testOnHelp(self):
        """ Test the default help renderer """

        self.widget.parent.showHelp = MagicMock()
        self.widget.onHelp()
        self.assertTrue(self.widget.parent.showHelp.called_once())
        #args = self.widget.manager.showHelp.call_args
        #self.assertIn('data_operator_help.html', args[0][0])

    def testOnIFileOpen(self):
        """
        Testing intensity file read in.
        :return:
        """
        filename = os.path.join("UnitTesting", "FIT2D_I.TXT")
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[filename, ''])
        self.widget.onIFileOpen()

        # check updated values in ui, read from loaded file
        self.assertEqual(self.widget.txtIFile.text(), 'FIT2D_I.TXT')
        self.assertEqual(self.widget.ifile, 'UnitTesting/FIT2D_I.TXT')

    def testOnQFileOpen(self):
        """
        Testing intensity file read in.
        :return:
        """
        filename = os.path.join("UnitTesting", "FIT2D_Q.TXT")
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[filename, ''])
        self.widget.onQFileOpen()

        # check updated values in ui, read from loaded file
        self.assertEqual(self.widget.txtQFile.text(), 'FIT2D_Q.TXT')
        self.assertEqual(self.widget.qfile, 'UnitTesting/FIT2D_Q.TXT')
       