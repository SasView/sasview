"""
Dialog report panel to show and summarize the results of
the fitting calculation.
"""
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################

import wx
import os
import wx.html as html

from sas.sasgui.guiframe.report_dialog import BaseReportDialog

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
        self.SetTitle("Report: Fitting")

        # number of images of plot
        self.nimages = len(self.report_list[2])
        self.report_html = self.report_list[0]
        # layout
        self._setup_layout()

    def onSave(self, event=None):
        """
        Save
        """
        #todo: complete saving fig file and as a txt file
        dlg = wx.FileDialog(self, "Choose a file",
                            wildcard=self.wild_card,
                            style=wx.SAVE | wx.OVERWRITE_PROMPT | wx.CHANGE_DIR)
        dlg.SetFilterIndex(0)  # Set .html files to be default

        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return

        fName = dlg.GetPath()
        basename = os.path.splitext(fName)[0]
        ext_num = dlg.GetFilterIndex()
        dlg.Destroy()

        if ext_num == 0 and self.index_offset == 0:  # has pdf
            ext = ".pdf"
        elif ext_num == 1 - self.index_offset:
            ext = ".html"
        elif ext_num == 2 - self.index_offset:
            ext = ".txt"
        else:
            logger.warn("unknown export format in report dialog")
            return
        filename = basename + ext

        # save figures
        pictures = []
        for num in range(self.nimages):
            pic_name = basename + '_img%s.png' % num
            # save the image for use with pdf writer
            self.report_list[2][num].savefig(pic_name)
            pictures.append(pic_name)

        # translate png references int html from in-memory name to on-disk name
        html = self.report_html.replace("memory:img_fit", basename+'_img')

        #set file extensions
        img_ext = []
        if ext == ".pdf":
            # write pdf as a pdf file
            pdf = self.HTML2PDF(data=html, filename=filename)

            # delete images used to create the pdf
            for pic_name in pictures:
                os.remove(pic_name)

            #open pdf viewer
            if pdf:
                try:
                    if os.name == 'nt':  # Windows
                        os.startfile(fName)
                    elif sys.platform == "darwin":  # Mac
                        os.system("open %s" % fName)
                except Exception as exc:
                    # cannot open pdf
                    logging.error(str(exc))

        elif ext == ".html":
            with open(filename, 'w') as f:
                f.write(html)

        elif ext == ".txt":
            with open(filename, 'w') as f:
                f.write(self.report_list[1])

        self.Update()
