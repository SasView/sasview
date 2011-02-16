
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

if sys.platform.count("win32") > 0:
    _STATICBOX_WIDTH = 450
    PANEL_WIDTH = 500 
    PANEL_HEIGHT = 700
    FONT_VARIANT = 0
else:
    _STATICBOX_WIDTH = 480
    PANEL_WIDTH = 530
    PANEL_HEIGHT = 700
    FONT_VARIANT = 1
    

        
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
        # report string
        self.report_list = list
        # put image path in the report string
        self.report_html = self.report_list[0] % "memory:img_inv.png"
        # layout
        self._setup_layout()
        
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
                            wildcard='HTML files (*.html)|*.html|'+
                            'Text files (*.txt)|*.txt',
                            style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR)
        dlg.SetFilterIndex(0) #Set .html files to be default

        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        
        fName = dlg.GetPath()
        ext_num = dlg.GetFilterIndex()     

        #set file extensions  
        if ext_num == 0:
            ext = '.html'
            img_ext = '_img4html.png'
            report_frame = self.report_list[0]
        elif ext_num == 1:
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
        if ext_num == 0:
            report = report_frame % pic_fname
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
        
        : data: html string
        : filename: name of file to be saved
        """
        import ho.pisa as pisa
        f = file(filename, "wb")
        # pisa requires some extra packages, see their web-site
        pdf = pisa.CreatePDF(data, f)
        # close the file here otherwise it will be open until quitting
        #the application.
        f.close()

        return not pdf.err

        
        