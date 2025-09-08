import logging
import os
import traceback

from PySide6 import QtCore, QtPrintSupport, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary
from sas.qtgui.Utilities.Reports.reportdata import ReportData
from sas.qtgui.Utilities.Reports.UI.ReportDialogUI import Ui_ReportDialogUI


class ReportDialog(QtWidgets.QDialog, Ui_ReportDialogUI):
    """
    Class for stateless grid-like printout of model parameters for mutiple models
    """
    def __init__(self, report_data: ReportData, parent: QtCore.QObject | None=None):

        super().__init__(parent)
        self.setupUi(self)

        self.report_data = report_data

        #self.save_location = None
        #if 'ReportDialog_directory' in ObjectLibrary.listObjects():
        self.save_location = ObjectLibrary.getObject('ReportDialog_directory')

        # Fill in the table from input data
        self.setupDialog(self.report_data.html)

        # Command buttons
        self.cmdPrint.clicked.connect(self.onPrint)
        self.cmdSave.clicked.connect(self.onSave)

    def setupDialog(self, output=None):
        """
        Display the HTML content in the browser.
        """
        if output is not None:
            self.txtBrowser.setHtml(output)

    def onPrint(self):
        """
        Display the print dialog and send the report to printer
        """
        # Define the printer
        printer = QtPrintSupport.QPrinter()

        # Display the print dialog
        dialog = QtPrintSupport.QPrintDialog(printer)
        dialog.setModal(True)
        dialog.setWindowTitle("Print")
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        document = self.txtBrowser.document()
        try:
            # pylint chokes on this line with syntax-error
            # pylint: disable=syntax-error doesn't seem to help
            document.print_(printer)
        except Exception as ex:
            # Printing can return various exceptions, let's catch them all
            logging.error("Print report failed with: " + str(ex))

    def onSave(self):
        """
        Display the Save As... prompt and save the report if instructed so
        """
        # Choose user's home directory
        if self.save_location is None:
            location = os.path.expanduser('~')
        else:
            location = self.save_location
        # Use a sensible filename default
        default_name = os.path.join(str(location), 'report.pdf')

        parent = self
        caption = 'Save Project'
        filter = 'PDF file (*.pdf);;HTML file (*.html);;Text file (*.txt)'
        directory = default_name
        filename_tuple = QtWidgets.QFileDialog.getSaveFileName(parent, caption, directory, filter, "")
        filename = filename_tuple[0]
        if not filename:
            return
        extension = filename_tuple[1]
        self.save_location = os.path.dirname(filename)
        # lifetime of this widget is short - keep the reference elsewhere
        ObjectLibrary.addObject('ReportDialog_directory', self.save_location)

        try:
            # extract extension from filter
            # e.g. "PDF file (*.pdf)" -> ".pdf"
            ext = extension[extension.find("(")+2:extension.find(")")]
        except IndexError as ex:
            # (ext) not found...
            logging.error("Error while saving report. " + str(ex))
            return
        basename, extension = os.path.splitext(filename)
        if not extension:
            filename = '.'.join((filename, ext))

        if ext.lower() == ".txt":
            self.write_string(self.report_data.text, filename)

        elif ext.lower() == ".html":
            self.write_string(self.report_data.html, filename)

        elif ext.lower() == ".pdf":
            html_utf = GuiUtils.replaceHTMLwithUTF8(self.report_data.html)
            self.save_pdf(html_utf, filename)

        else:
            logging.error(f"Unknown file extension: {ext.lower()}")



    @staticmethod
    def write_string(string, filename):
        """
        Write string to file
        """
        with open(filename, 'wb') as f:
            # weird unit symbols need to be saved as UTF-8
            f.write(bytes(string, 'utf-8'))

    @staticmethod
    def save_pdf(data, filename):
        """
        Create a PDF file from html source string.
        Returns True is the file creation was successful.
        : data: html string
        : filename: name of file to be saved
        """
        # import moved from top due to cost
        from xhtml2pdf import pisa
        try:
            # open output file for writing (truncated binary)
            with open(filename, "w+b") as resultFile:
                # convert HTML to PDF
                pisaStatus = pisa.CreatePDF(data.encode("UTF-8"),
                                            dest=resultFile,
                                            encoding='UTF-8')
                return pisaStatus.err

        except Exception:
            # logging.error("Error creating pdf: " + str(ex))
            logging.error("Error creating pdf: " + traceback.format_exc())
        return False


