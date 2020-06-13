import sys
import os
import unittest
import numpy as np

from unittest.mock import MagicMock, patch

from PyQt5 import QtWidgets

from sas.qtgui.Utilities.GuiUtils import Communicate
from sas.qtgui.Utilities.FileConverter import FileConverterWidget
import sas.sascalc.file_converter.FileConverterUtilities as Utilities

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class dummy_manager(object):
    HELP_DIRECTORY_LOCATION = "html"
    communicate = Communicate()
    _parent = QtWidgets.QDialog()

class FileConverterTest(unittest.TestCase):
    """ Test the simple FileConverter dialog """
    def setUp(self):
        """ Create FileConverter dialog """
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
        self.assertTrue(self.widget.cmdConvert)

        iqdata = np.array([Utilities.extract_ascii_data(self.widget.ifile)])
        self.assertAlmostEqual(iqdata[0][0], 224.08691, places=4)

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
        self.assertTrue(self.widget.cmdConvert)

        qdata = Utilities.extract_ascii_data(self.widget.qfile)
        self.assertAlmostEqual(qdata[0], 0.13073, places=4)

    def testOnConvert(self):
        """

        :return:
        """
        ifilename = os.path.join("UnitTesting", "FIT2D_I.TXT")
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[ifilename, ''])
        self.widget.onIFileOpen()
        qfilename = os.path.join("UnitTesting", "FIT2D_Q.TXT")
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[qfilename, ''])
        self.widget.onQFileOpen()

        self.assertFalse(self.widget.isBSL)
        self.assertTrue(self.widget.is1D)

        ofilemame = os.path.join('UnitTesting', 'FIT2D_IQ.xml')
        self.widget.ofile = ofilemame

        self.widget.chkLoadFile.setChecked(False)
        self.widget.onConvert()

        test_metadata = self.widget.metadata
        self.assertEqual(test_metadata['title'], '')
        self.assertEqual(test_metadata['run_name'], {'': ''})
        self.assertEqual(test_metadata['instrument'], '')
        self.assertEqual(test_metadata['detector'][0].name, '') #What is the reason to have it as array
        self.assertEqual(test_metadata['sample'].name, '')
        self.assertEqual(test_metadata['source'].name, '')

        #TODO Load xml file to check if it has what is upposed to have 

