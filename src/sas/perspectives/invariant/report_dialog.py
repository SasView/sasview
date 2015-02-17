
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################

"""
Dialog report panel to show and summarize the results of 
the invariant calculation.
"""
import wx
import sys
import os
import wx.html as html
import logging
ISPDF = False
if sys.platform == "win32":
    _STATICBOX_WIDTH = 450
    PANEL_WIDTH = 500 
    PANEL_HEIGHT = 700
    FONT_VARIANT = 0
    ISMAC = False
    ISPDF = True
elif sys.platform == "darwin":
    _STATICBOX_WIDTH = 480
    PANEL_WIDTH = 530
    PANEL_HEIGHT = 700
    FONT_VARIANT = 1
    ISMAC = True
    ISPDF = True
  
class ReportDialog(wx.Dialog):
    """
    The report dialog box. 
    """
    
    def __init__(self,  list, *args, **kwds):
        """
        Initialization. The parameters added to Dialog are:
        
        :param list: report_list (list of html_str, text_str, image)
        from invariant_state
        """
        kwds["style"] = wx.RESIZE_BORDER|wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        kwds["image"] = 'Dynamic Image'
        # title
        self.SetTitle("Report: Invariant computaion")
        # size
        self.SetSize((720, 650))
        # font size 
        self.SetWindowVariant(variant=FONT_VARIANT)

        # check if tit is MAC
        self.is_pdf = ISPDF
        
        # report string
        self.report_list = list
        # put image path in the report string
        self.report_html = self.report_list[0] % "memory:img_inv.png"
        # layout
        self._setup_layout()
        # wild card
        # pdf supporting only on MAC
        if self.is_pdf:
        	self.wild_card = ' PDF files (*.pdf)|*.pdf|'
        else:
        	self.wild_card = ''
        self.wild_card += 'HTML files (*.html)|*.html|'
        self.wild_card += 'Text files (*.txt)|*.txt'
  
        
        
    def _setup_layout(self):
        """
        Set up layout
        """
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        # buttons
        id = wx.ID_OK
        button_close = wx.Button(self, id, "Close")
        button_close.SetToolTipString("Close this report window.") 
        #hbox.Add((5,10), 1 , wx.EXPAND|wx.ADJUST_MINSIZE,0)
        hbox.Add(button_close)
        button_close.SetFocus()

        id = wx.NewId()
        button_preview = wx.Button(self, id, "Preview")
        button_preview.SetToolTipString("Print preview this report.")
        button_preview.Bind(wx.EVT_BUTTON, self.onPreview,
                            id=button_preview.GetId()) 
        hbox.Add(button_preview)

        id = wx.NewId()
        button_print = wx.Button(self, id, "Print")
        button_print.SetToolTipString("Print this report.")
        button_print.Bind(wx.EVT_BUTTON, self.onPrint,
                          id=button_print.GetId()) 
        hbox.Add(button_print)
        
        id = wx.NewId()
        button_save = wx.Button(self, id, "Save" )
        button_save.SetToolTipString("Save this report.")
        button_save.Bind(wx.EVT_BUTTON, self.onSave, id = button_save.GetId()) 
        hbox.Add(button_save)     
        
        # panel for report page
        #panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)
        # html window
        self.hwindow = html.HtmlWindow(self,style=wx.BORDER)
        # set the html page with the report string
        self.hwindow.SetPage(self.report_html)
        
        # add panels to boxsizers
        vbox.Add(hbox)
        vbox.Add(self.hwindow, 1, wx.EXPAND|wx.ALL,0)

        self.SetSizer(vbox)
        self.Centre()
        self.Show(True)
		

    def onSave(self, event=None):
        """
        Save
        """
        #todo: complete saving fig file and as a txt file
        dlg = wx.FileDialog(self, "Choose a file",
                            wildcard=self.wild_card,
                            style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR)
        dlg.SetFilterIndex(0) #Set .html files to be default

        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return

        fName = dlg.GetPath()
        ext_num = dlg.GetFilterIndex()  
        # index correction 
        if not self.is_pdf:
        	ind_cor = 1 
        else:
        	ind_cor = 0 
        #set file extensions  
        if ext_num == (0 + 2 * ind_cor):
			# TODO: Sort this case out
            ext = '.pdf'
            img_ext = '_img.png'
            fName = os.path.splitext(fName)[0] + ext
            dlg.Destroy()

            #pic (png) file path/name
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
            
            #open pdf
            if pdf:
                try:
                    #Windows
                    os.startfile(str(fName))
                except:
                    try:
                        #Mac
                        os.system("open %s"% fName)
                    except:
                        #DO not open
                        pass
            #delete image file
            os.remove(pic_fname)
            return
        elif ext_num == (1 - ind_cor):
            ext = '.html'
            img_ext = '_img4html.png'
            report_frame = self.report_list[0]
        elif ext_num == (2 - ind_cor):
            ext = '.txt'   
            # changing the image extension actually changes the image
            # format on saving
            img_ext = '_img4txt.pdf'
            report = self.report_list[1]
        else:
            return

        #file name     
        fName = os.path.splitext(fName)[0] + ext
        dlg.Destroy()
        #pic (png) file path/name
        pic_fname = os.path.splitext(fName)[0] + img_ext
        #put the image path in html string
        if ext_num == (1 - ind_cor):
            report = report_frame % os.path.basename(pic_fname)

        f = open(fName, 'w')
        f.write(report)
        f.close()
        #save png file using pic_fname
        self.report_list[2].savefig(pic_fname)
        
            
    def onPreview(self, event=None):
        """
        Preview
        
        : event: Preview button event
        """
        previewh = html.HtmlEasyPrinting(name="Printing", parentWindow=self)
        previewh.PreviewText(self.report_html)
        if event is not None:
            event.Skip()
    
    def onPrint(self, event=None):
        """
        Print
        
        : event: Print button event
        """
        printh = html.HtmlEasyPrinting(name="Printing", parentWindow=self)
        printh.PrintText(self.report_html)
        if event is not None:
            event.Skip()

    def OnClose(self,event=None):
        """
        Close the Dialog
        
        : event: Close button event
        """
        self.Close()
    
    def HTML2PDF(self, data, filename):
        """
        Create a PDF file from html source string.
        Returns True is the file creation was successful. 
        
        : data: html string
        : filename: name of file to be saved
        """
        try:
            from xhtml2pdf import pisa
            # open output file for writing (truncated binary)
            resultFile = open(filename, "w+b")
            # convert HTML to PDF
            pisaStatus = pisa.CreatePDF(data, dest=resultFile)
            # close output file
            resultFile.close()
            self.Update()
            return pisaStatus.err
        except:
            logging.error("Error creating pdf: %s" % sys.exc_value)
        return False
