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

        if self.report_list[2] != None:
            # put image path in the report string
            if len(self.report_list[2]) == 1:
                self.report_html = self.report_list[0] % \
                                    "memory:img_fit0.png"
            elif len(self.report_list[2]) == 2:
                self.report_html = self.report_list[0] % \
                                    ("memory:img_fit0.png",
                                     "memory:img_fit1.png")
            # allows up to three images
            else:
                self.report_html = self.report_list[0] % \
                                    ("memory:img_fit0.png",
                                     "memory:img_fit1.png",
                                     "memory:img_fit2.png")
        else:
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
        ext_num = dlg.GetFilterIndex()

        #set file extensions
        img_ext = []
        pic_fname = []
        #PDF
        if ext_num == (0 + 2 * self.index_offset):
            # TODO: Sort this case out
            ext = '.pdf'

            fName = os.path.splitext(fName)[0] + ext
            dlg.Destroy()
            #pic (png) file path/name
            for num in range(self.nimages):
                im_ext = '_img%s.png' % num
                #img_ext.append(im_ext)
                pic_name = os.path.splitext(fName)[0] + im_ext
                pic_fname.append(pic_name)
                # save the image for use with pdf writer
                self.report_list[2][num].savefig(pic_name)

            #put the image path in html string
            report_frame = self.report_list[0]
            #put image name strings into the html file
            #Note:The str for pic_fname shouldn't be removed.
            if self.nimages == 1:
                html = report_frame % str(pic_fname[0])
            elif self.nimages == 2:
                html = report_frame % (str(pic_fname[0]), str(pic_fname[1]))
            elif self.nimages == 3:
                html = report_frame % (str(pic_fname[0]), str(pic_fname[1]),
                                          str(pic_fname[2]))

            # make/open file in case of absence
            f = open(fName, 'w')
            f.close()
            # write pdf as a pdf file
            pdf = self.HTML2PDF(data=html, filename=fName)

            #open pdf
            if pdf:
                try:
                    #Windows
                    os.startfile(str(fName))
                except:
                    try:
                        #Mac
                        os.system("open %s" % fName)
                    except:
                        #DO not open
                        pass
            #delete image file
            for num in range(self.nimages):
                os.remove(pic_fname[num])
            return
        #HTML + png(graph)
        elif ext_num == (1 - self.index_offset):
            ext = '.html'
            for num in range(self.nimages):
                img_ext.append('_img4html%s.png' % num)
            report_frame = self.report_list[0]
        #TEXT + pdf(graph)
        elif ext_num == (2 - self.index_offset):
            ext = '.txt'
            # changing the image extension actually changes the image
            # format on saving
            for num in range(self.nimages):
                img_ext.append('_img4txt%s.pdf' % num)
            report = self.report_list[1]
        else:
            return

        #file name
        fName = os.path.splitext(fName)[0] + ext
        dlg.Destroy()

        #pic (png) file path/name
        for num in range(self.nimages):
            pic_name = os.path.splitext(fName)[0] + img_ext[num]
            pic_fname.append(pic_name)
        #put the image path in html string
        if ext_num == (1 - self.index_offset):
            if self.nimages == 1:
                report = report_frame % os.path.basename(pic_fname[0])
            elif self.nimages == 2:
                report = report_frame % (os.path.basename(pic_fname[0]),
                                         os.path.basename(pic_fname[1]))
            elif self.nimages == 3:
                report = report_frame % (os.path.basename(pic_fname[0]),
                                         os.path.basename(pic_fname[1]),
                                         os.path.basename(pic_fname[2]))
        f = open(fName, 'w')
        f.write(report)
        f.close()
        self.Update()
        #save png file using pic_fname
        for num in range(self.nimages):
            self.report_list[2][num].savefig(pic_fname[num])
