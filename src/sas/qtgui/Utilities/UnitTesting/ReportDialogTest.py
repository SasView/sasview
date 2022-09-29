import os
import sys
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


class ReportDialogTest:
    '''Test the report dialog'''
    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the dialog'''

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
        w = ReportDialog(parent=dummy_manager(), report_data=self.test_report)

        yield w

    @pytest.mark.xfail(reason="2022-09 already broken")
    # RuntimeError: wrapped C/C++ object of type QTextBrowser has been deleted
    def testDefaults(self, widget):
        '''Look at the default state of the widget'''
        assert self.test_report.html in widget.txtBrowser.toHtml()
        assert widget.txtBrowser.isReadOnly()

    @pytest.mark.xfail(reason="2022-09 already broken")
    # RuntimeError: wrapped C/C++ object of type QTextBrowser has been deleted
    def testOnPrint(self, widget):
        ''' Printing the report '''
        document = widget.txtBrowser.document()
        document.print = MagicMock()

        # test rejected dialog
        QtPrintSupport.QPrintDialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Rejected)

        # invoke the method
        widget.onPrint()

        # Assure printing was not done
        assert not document.print.called

        # test accepted dialog
        QtPrintSupport.QPrintDialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Accepted)

        # This potentially spawns a "file to write to" dialog, if say, a PrintToPDF is the
        # default printer

        # invoke the method
        #widget.onPrint()

        # Assure printing was done
        #self.assertTrue(document.print.called)


    def testOnSave(self, widget):
        ''' Saving the report to a file '''
        # PDF save
        QtWidgets.QFileDialog.getSaveFileName = MagicMock(return_value=["test.pdf", "(*.pdf)"])
        os.startfile = MagicMock()
        os.system = MagicMock()

        # conversion failed
        widget.save_pdf = MagicMock(return_value=1)

        # invoke the method
        widget.onSave()

        # Check that the file wasn't saved
        if os.name == 'nt':  # Windows
            assert not os.startfile.called
        elif sys.platform == "darwin":  # Mac
            assert not os.system.called

        # conversion succeeded
        temp_html2pdf = widget.save_pdf
        widget.save_pdf = MagicMock(return_value=0)

        # invoke the method
        widget.onSave()

        # Check that the file was saved
        if os.name == 'nt':  # Windows
            assert os.startfile.called
        elif sys.platform == "darwin":  # Mac
            assert os.system.called

        # TXT save
        QtWidgets.QFileDialog.getSaveFileName = MagicMock(return_value=["test.txt", "(*.txt)"])
        widget.onTXTSave = MagicMock()
        # invoke the method
        widget.onSave()

        # Check that the file was saved
        assert widget.onTXTSave

        # HTML save
        QtWidgets.QFileDialog.getSaveFileName = MagicMock(return_value=["test.html", "(*.html)"])
        widget.write_string = MagicMock()
        # invoke the method
        widget.onSave()

        # Check that the file was saved
        assert widget.write_string

        widget.save_pdf = temp_html2pdf


    def testGetPictures(self, widget):
        ''' Saving MPL charts and returning filenames '''
        pass

    @pytest.mark.xfail(reason="2022-09 already broken")
    # RuntimeError: wrapped C/C++ object of type QTextBrowser has been deleted
    def testHTML2PDF(self, widget):
        ''' html to pdf conversion '''
        class pisa_dummy(object):
            err = 0
        pisa.CreatePDF = MagicMock(return_value=pisa_dummy())
        open = MagicMock(return_value="y")

        QTest.qWait(100)

        data = widget.txtBrowser.toHtml()
        return_value = widget.save_pdf(data, "b")

        assert pisa.CreatePDF.called
        assert return_value == 0

        # Try to raise somewhere
        pisa.CreatePDF.side_effect = Exception("Failed")

        logging.error = MagicMock()

        #run the method
        return_value = widget.save_pdf(data, "c")

        assert logging.error.called
        #logging.error.assert_called_with("Error creating pdf")
