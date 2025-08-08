import logging
import os
import sys

import pytest
from PySide6 import QtPrintSupport, QtWidgets
from PySide6.QtTest import QTest
from xhtml2pdf import pisa

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
    def testOnPrint(self, widget, mocker):
        ''' Printing the report '''
        document = widget.txtBrowser.document()
        mocker.patch.object(document, 'print_')

        # test rejected dialog
        mocker.patch.object(QtPrintSupport.QPrintDialog, 'exec_', return_value=QtWidgets.QDialog.Rejected)

        # invoke the method
        widget.onPrint()

        # Assure printing was not done
        assert not document.print_.called

        # test accepted dialog
        mocker.patch.object(QtPrintSupport.QPrintDialog, 'exec_', return_value=QtWidgets.QDialog.Accepted)

        # This potentially spawns a "file to write to" dialog, if say, a PrintToPDF is the
        # default printer

        # invoke the method
        #widget.onPrint()

        # Assure printing was done
        #assert document.print.called

    @pytest.mark.xfail(reason="2022-09 already broken")
    # RuntimeError: wrapped C/C++ object of type ReportDialog has been deleted
    def testOnSave(self, widget, mocker):
        ''' Saving the report to a file '''
        # PDF save
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=["test.pdf", "(*.pdf)"])
        mocker.patch.object(os, 'startfile', create=True)
        mocker.patch.object(os, 'system')

        # conversion failed
        mocker.patch.object(widget, 'save_pdf', return_value=1)

        # invoke the method
        widget.onSave()

        # Check that the file wasn't saved
        if os.name == 'nt':  # Windows
            assert not os.startfile.called
        elif sys.platform == "darwin":  # Mac
            assert not os.system.called

        # conversion succeeded
        temp_html2pdf = widget.save_pdf
        mocker.patch.object(widget, 'save_pdf', return_value=0)

        # invoke the method
        widget.onSave()

        # Check that the file was saved
        if os.name == 'nt':  # Windows
            assert os.startfile.called
        elif sys.platform == "darwin":  # Mac
            assert os.system.called

        # TXT save
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=["test.txt", "(*.txt)"])
        mocker.patch.object(widget, 'onTXTSave', create=True)
        # invoke the method
        widget.onSave()

        # Check that the file was saved
        assert widget.onTXTSave

        # HTML save
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=["test.html", "(*.html)"])
        mocker.patch.object(widget, 'write_string')
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
    def testHTML2PDF(self, widget, mocker):
        ''' html to pdf conversion '''
        class pisa_dummy:
            err = 0
        mocker.patch.object(pisa, 'CreatePDF', return_value=pisa_dummy())
        mocker.patch.object(builtins, 'open', return_value="y")

        QTest.qWait(100)

        data = widget.txtBrowser.toHtml()
        return_value = widget.save_pdf(data, "b")

        assert pisa.CreatePDF.called
        assert return_value == 0

        # Try to raise somewhere
        pisa.CreatePDF.side_effect = Exception("Failed")

        mocker.patch.object(logging, 'error')

        #run the method
        return_value = widget.save_pdf(data, "c")

        assert logging.error.called
        #logging.error.assert_called_with("Error creating pdf")
