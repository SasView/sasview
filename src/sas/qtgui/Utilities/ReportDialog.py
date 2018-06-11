import os
import sys
import re
import logging
from xhtml2pdf import pisa

from PyQt5 import QtWidgets
from PyQt5 import QtPrintSupport

import sas.qtgui.Utilities.GuiUtils as GuiUtils

from sas.qtgui.Utilities.UI.ReportDialogUI import Ui_ReportDialogUI


class ReportDialog(QtWidgets.QDialog, Ui_ReportDialogUI):
    """
    Class for stateless grid-like printout of model parameters for mutiple models
    """
    def __init__(self, parent=None, report_list=None):

        super(ReportDialog, self).__init__(parent._parent)
        self.setupUi(self)

        assert isinstance(report_list, list)
        assert len(report_list) == 3

        self.data_html, self.data_txt, self.data_images = report_list

        # Fill in the table from input data
        self.setupDialog(self.data_html)

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
            document.print(printer)
        except Exception as ex:
            # Printing can return various exceptions, let's catch them all
            logging.error("Print report failed with: " + str(ex))

    def onSave(self):
        """
        Display the Save As... prompt and save the report if instructed so
        """
        # Choose user's home directory
        location = os.path.expanduser('~')
        # Use a sensible filename default
        default_name = os.path.join(location, 'fit_report.pdf')
        kwargs = {
            'parent'   : self,
            'caption'  : 'Save Report',
            'directory': default_name,
            'filter'   : 'PDF file (*.pdf);;HTML file (*.html);;Text file (*.txt)',
            'options'  : QtWidgets.QFileDialog.DontUseNativeDialog}
        # Query user for filename.
        filename_tuple = QtWidgets.QFileDialog.getSaveFileName(**kwargs)
        filename = filename_tuple[0]
        if not filename:
            return
        extension = filename_tuple[1]

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

        # Create files with charts
        pictures = self.getPictures(basename)

        # translate png references into html from base64 string to on-disk name
        cleanr = re.compile('<img src="data:image.*>')
        replacement_name = ""
        for picture in pictures:
            replacement_name += '<img src="'+ picture + '"><p></p>'

        # <img src="data:image/png;.*>  => <img src=filename>
        html = re.sub(cleanr, replacement_name, self.data_html)

        if ext.lower() == ".txt":
            txt_ascii = GuiUtils.replaceHTMLwithASCII(self.data_txt)
            self.onTXTSave(txt_ascii, filename)
        if ext.lower() == ".html":
            self.onHTMLSave(html, filename)
        if ext.lower() == ".pdf":
            html_utf = GuiUtils.replaceHTMLwithUTF8(html)
            pdf_success = self.HTML2PDF(html_utf, filename)
            # delete images used to create the pdf
            for pic_name in pictures:
                os.remove(pic_name)
            #open pdf viewer
            if pdf_success == 0:
                try:
                    if os.name == 'nt':  # Windows
                        os.startfile(filename)
                    elif sys.platform == "darwin":  # Mac
                        os.system("open %s" % filename)
                except Exception as ex:
                    # cannot open pdf.
                    # We don't know what happened in os.* , so broad Exception is required
                    logging.error(str(ex))

    def getPictures(self, basename):
        """
        Returns list of saved MPL figures
        """
        # save figures
        pictures = []
        for num, image in enumerate(self.data_images):
            pic_name = basename + '_img%s.png' % num
            # save the image for use with pdf writer
            image.savefig(pic_name)
            pictures.append(pic_name)
        return pictures

    @staticmethod
    def onTXTSave(data, filename):
        """
        Simple txt file serializatio
        """
        with open(filename, 'w') as f:
            f.write(data)

    @staticmethod
    def onHTMLSave(html, filename):
        """
        HTML file write
        """
        with open(filename, 'w') as f:
            f.write(html)

    @staticmethod
    def HTML2PDF(data, filename):
        """
        Create a PDF file from html source string.
        Returns True is the file creation was successful.
        : data: html string
        : filename: name of file to be saved
        """
        try:
            # open output file for writing (truncated binary)
            with open(filename, "w+b") as resultFile:
                # convert HTML to PDF
                pisaStatus = pisa.CreatePDF(data.encode("UTF-8"),
                                            dest=resultFile,
                                            encoding='UTF-8')
                return pisaStatus.err
        except Exception as ex:
            logging.error("Error creating pdf: " + str(ex))
        return False


