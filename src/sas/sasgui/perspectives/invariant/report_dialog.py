
################################################################################
# This software was developed by the University of Tennessee as part of the
# Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
# project funded by the US National Science Foundation.
#
# See the license text in license.txt
#
# copyright 2009, University of Tennessee
################################################################################

"""
Dialog report panel to show and summarize the results of
the invariant calculation.
"""
import wx
import os
import sys
import logging

from sas.sasgui.guiframe.report_dialog import BaseReportDialog

logger = logging.getLogger(__name__)

class ReportDialog(BaseReportDialog):
    """
    The report dialog box.
    """

    def __init__(self, report_list, *args, **kwds):
        """
        Initialization. The parameters added to Dialog are:

        :param report_list: list of html_str, text_str, image
        from invariant_state
        """
        super(ReportDialog, self).__init__(report_list, *args, **kwds)

        # title
        self.SetTitle("Report: Invariant computaion")

        # put image path in the report string
        self.report_html = self.report_list[0] % "memory:img_inv.png"
        # layout
        self._setup_layout()

    def onSave(self, event=None):
        """
        Save
        """
        # todo: complete saving fig file and as a txt file
        dlg = wx.FileDialog(self, "Choose a file",
                            wildcard=self.wild_card,
                            style=wx.SAVE | wx.OVERWRITE_PROMPT | wx.CHANGE_DIR)
        dlg.SetFilterIndex(0)  # Set .html files to be default

        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return

        fName = dlg.GetPath()
        ext_num = dlg.GetFilterIndex()
        # set file extensions
        if ext_num == (0 + 2 * self.index_offset):
            # TODO: Sort this case out
            ext = '.pdf'
            img_ext = '_img.png'
            fName = os.path.splitext(fName)[0] + ext
            dlg.Destroy()

            # pic (png) file path/name
            pic_fname = os.path.splitext(fName)[0] + img_ext
            # save the image for use with pdf writer
            self.report_list[2].savefig(pic_fname)

            # put the image file path in the html data
            html = self.report_list[0] % str(pic_fname)

            # make/open file in case of absence
            f = open(fName, 'w')
            f.close()
            # write pdf as a pdf file
            pdf = self.HTML2PDF(data=html, filename=fName)

            # open pdf
            if pdf:
                try:
                    # Windows
                    os.startfile(str(fName))
                except:
                    try:
                        # Mac
                        os.system("open %s" % fName)
                    except:
                        # DO not open
                        logger.error("Could not open file: %s" % sys.exc_info()[1])
            # delete image file
            os.remove(pic_fname)
            return
        elif ext_num == (1 - self.index_offset):
            ext = '.html'
            img_ext = '_img4html.png'
            report_frame = self.report_list[0]
        elif ext_num == (2 - self.index_offset):
            ext = '.txt'
            # changing the image extension actually changes the image
            # format on saving
            img_ext = '_img4txt.pdf'
            report = self.report_list[1]
        else:
            return

        # file name
        fName = os.path.splitext(fName)[0] + ext
        dlg.Destroy()
        # pic (png) file path/name
        pic_fname = os.path.splitext(fName)[0] + img_ext
        # put the image path in html string
        if ext_num == (1 - self.index_offset):
            report = report_frame % os.path.basename(pic_fname)

        f = open(fName, 'w')
        f.write(report)
        f.close()
        # save png file using pic_fname
        self.report_list[2].savefig(pic_fname)
