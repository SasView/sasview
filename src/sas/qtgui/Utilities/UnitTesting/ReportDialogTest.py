import os
import sys
import unittest
import logging
from xhtml2pdf import pisa

from unittest.mock import mock_open, patch

from unittest.mock import MagicMock

from PyQt5 import QtWidgets, QtPrintSupport

# set up import paths
import path_prepare

import sas.qtgui.Utilities.GuiUtils as GuiUtils
# Local
from sas.qtgui.Utilities.ReportDialog import ReportDialog

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class ReportDialogTest(unittest.TestCase):
    '''Test the report dialog'''
    def setUp(self):
        '''Create the dialog'''
        class dummy_manager(object):
            _parent = QtWidgets.QWidget()
            def communicator(self):
                return GuiUtils.Communicate()
            def communicate(self):
                return GuiUtils.Communicate()

        test_html = "test_html"
        test_txt = "test_txt"
        test_images = []
        self.test_list = [test_html, test_txt, test_images]
        self.widget = ReportDialog(parent=dummy_manager(), report_list=self.test_list)

    def tearDown(self):
        '''Destroy the GUI'''
        #self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Look at the default state of the widget'''
        self.assertIn(self.test_list[0], self.widget.txtBrowser.toHtml())
        self.assertTrue(self.widget.txtBrowser.isReadOnly())

    def testOnPrint(self):
        ''' Printing the report '''
        document = self.widget.txtBrowser.document()
        document.print = MagicMock()

        # test rejected dialog
        QtPrintSupport.QPrintDialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Rejected)

        # invoke the method
        self.widget.onPrint()

        # Assure printing was not done
        self.assertFalse(document.print.called)

        # test accepted dialog
        QtPrintSupport.QPrintDialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Accepted)

        # invoke the method
        self.widget.onPrint()

        # Assure printing was done
        self.assertTrue(document.print.called)


    def testOnSave(self):
        ''' Saving the report to a file '''
        # PDF save
        QtWidgets.QFileDialog.getSaveFileName = MagicMock(return_value=["test.pdf", "(*.pdf)"])
        os.startfile = MagicMock()
        os.system = MagicMock()

        # conversion failed
        self.widget.HTML2PDF = MagicMock(return_value=1)

        # invoke the method
        self.widget.onSave()

        # Check that the file wasn't saved
        if os.name == 'nt':  # Windows
            self.assertFalse(os.startfile.called)
        elif sys.platform == "darwin":  # Mac
            self.assertFalse(os.system.called)

        # conversion succeeded
        self.widget.HTML2PDF = MagicMock(return_value=0)

        # invoke the method
        self.widget.onSave()

        # Check that the file was saved
        if os.name == 'nt':  # Windows
            self.assertTrue(os.startfile.called)
        elif sys.platform == "darwin":  # Mac
            self.assertTrue(os.system.called)

        # TXT save
        QtWidgets.QFileDialog.getSaveFileName = MagicMock(return_value=["test.txt", "(*.txt)"])
        self.widget.onTXTSave = MagicMock()
        # invoke the method
        self.widget.onSave()

        # Check that the file was saved
        self.assertTrue(self.widget.onTXTSave)

        # HTML save
        QtWidgets.QFileDialog.getSaveFileName = MagicMock(return_value=["test.html", "(*.html)"])
        self.widget.onHTMLSave = MagicMock()
        # invoke the method
        self.widget.onSave()

        # Check that the file was saved
        self.assertTrue(self.widget.onHTMLSave)

    def testGetPictures(self):
        ''' Saving MPL charts and returning filenames '''
        pass

    def testHTML2PDF(self):
        ''' html to pdf conversion '''
        class pisa_dummy(object):
            err = 0
        pisa.CreatePDF = MagicMock(return_value=pisa_dummy())
        open = MagicMock(return_value="y")

        data = self.widget.txtBrowser.toHtml()
        return_value = self.widget.HTML2PDF(data, "b")

        self.assertTrue(pisa.CreatePDF.called)
        self.assertEqual(return_value, 0)

        # Try to raise somewhere
        pisa.CreatePDF.side_effect = Exception("Failed")

        logging.error = MagicMock()

        #run the method
        return_value = self.widget.HTML2PDF(data, "c")

        self.assertTrue(logging.error.called)
        logging.error.assert_called_with("Error creating pdf: Failed")

