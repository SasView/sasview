import os
import sys
import unittest
import logging
from xhtml2pdf import pisa

import pytest

from unittest.mock import MagicMock

from PyQt5 import QtWidgets, QtPrintSupport
from PyQt5.QtTest import QTest

# set up import paths

import sas.qtgui.Utilities.GuiUtils as GuiUtils
# Local
from sas.qtgui.Utilities.Reports.ReportDialog import ReportDialog

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class ReportDialogTest(unittest.TestCase):
    '''Test the report dialog'''
    def setUp(self):
        '''Create the dialog'''
        class dummy_manager(QtWidgets.QWidget):
            _parent = QtWidgets.QWidget()
            def communicator(self):
                return GuiUtils.Communicate()
            def communicate(self):
                return GuiUtils.Communicate()

        class dummy_report:
            html = "test_html"
            text = "test_txt"
            test_images = []

        #self.test_list = [test_html, test_txt, test_images]
        self.test_report = dummy_report()
        self.widget = ReportDialog(parent=dummy_manager(), report_data=self.test_report)

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget = None

    @pytest.mark.xfail(reason="2022-09 already broken")
    # RuntimeError: wrapped C/C++ object of type QTextBrowser has been deleted
    def testDefaults(self):
        '''Look at the default state of the widget'''
        self.assertIn(self.test_report.html, self.widget.txtBrowser.toHtml())
        self.assertTrue(self.widget.txtBrowser.isReadOnly())

    @pytest.mark.xfail(reason="2022-09 already broken")
    # RuntimeError: wrapped C/C++ object of type QTextBrowser has been deleted
    def testOnPrint(self):
        ''' Printing the report '''
        document = self.widget.txtBrowser.document()
        document.print = MagicMock()
        self.setUp()
        # test rejected dialog
        QtPrintSupport.QPrintDialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Rejected)

        # invoke the method
        self.widget.onPrint()

        # Assure printing was not done
        self.assertFalse(document.print.called)

        # test accepted dialog
        QtPrintSupport.QPrintDialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Accepted)

        # This potentially spawns a "file to write to" dialog, if say, a PrintToPDF is the
        # default printer

        # invoke the method
        #self.widget.onPrint()

        # Assure printing was done
        #self.assertTrue(document.print.called)


    def testOnSave(self):
        ''' Saving the report to a file '''
        # PDF save
        QtWidgets.QFileDialog.getSaveFileName = MagicMock(return_value=["test.pdf", "(*.pdf)"])
        os.startfile = MagicMock()
        os.system = MagicMock()
        self.setUp()

        # conversion failed
        self.widget.save_pdf = MagicMock(return_value=1)

        # invoke the method
        self.widget.onSave()

        # Check that the file wasn't saved
        if os.name == 'nt':  # Windows
            self.assertFalse(os.startfile.called)
        elif sys.platform == "darwin":  # Mac
            self.assertFalse(os.system.called)

        # conversion succeeded
        temp_html2pdf = self.widget.save_pdf
        self.widget.save_pdf = MagicMock(return_value=0)

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
        self.widget.write_string = MagicMock()
        # invoke the method
        self.widget.onSave()

        # Check that the file was saved
        self.assertTrue(self.widget.write_string)

        self.widget.save_pdf = temp_html2pdf


    def testGetPictures(self):
        ''' Saving MPL charts and returning filenames '''
        pass

    @pytest.mark.xfail(reason="2022-09 already broken")
    # RuntimeError: wrapped C/C++ object of type QTextBrowser has been deleted
    def testHTML2PDF(self):
        ''' html to pdf conversion '''
        class pisa_dummy(object):
            err = 0
        pisa.CreatePDF = MagicMock(return_value=pisa_dummy())
        open = MagicMock(return_value="y")
        self.setUp()

        QTest.qWait(100)

        data = self.widget.txtBrowser.toHtml()
        return_value = self.widget.save_pdf(data, "b")

        self.assertTrue(pisa.CreatePDF.called)
        self.assertEqual(return_value, 0)

        # Try to raise somewhere
        pisa.CreatePDF.side_effect = Exception("Failed")

        logging.error = MagicMock()

        #run the method
        return_value = self.widget.save_pdf(data, "c")

        self.assertTrue(logging.error.called)
        #logging.error.assert_called_with("Error creating pdf")

