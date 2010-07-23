
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
Dialog report panel to show and summarize the results of the invariant calculation.
"""
    

import wx
import sys,os
import wx.html as html

if sys.platform.count("win32")>0:
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
    
    def __init__(self,  string, *args, **kwds):
        """
        Initialization. The parameters added to Dialog are:
        
        :param string: report_string  from invariant_state
        """
        kwds["style"] = wx.RESIZE_BORDER|wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        # title
        self.SetTitle("Report: Invariant computaion")
        # size
        self.SetSize((720, 650))
        # font size 
        self.SetWindowVariant(variant=FONT_VARIANT)
        # report string
        self.report_string =string
        # layout
        self._setup_layout()

    def _setup_layout(self):
        """
        Set up layout
        """
        # panel for buttons
        bpanel = wx.Panel(self, -1)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        # buttons
        id = wx.NewId()
        button_save = wx.Button(self, id, "Save")
        button_save.SetToolTipString("Save this report.")
        button_save.Bind(wx.EVT_BUTTON, self.onSave, id = button_save.GetId()) 
        hbox.Add(button_save)

        id = wx.NewId()
        button_preview = wx.Button(self, id, "Preview")
        button_preview.SetToolTipString("Print preview this report.")
        button_preview.Bind(wx.EVT_BUTTON, self.onPreview, id = button_preview.GetId()) 
        #hbox.Add(button_preview)

        id = wx.NewId()
        button_print = wx.Button(self, id, "Print")
        button_print.SetToolTipString("Print this report.")
        button_print.Bind(wx.EVT_BUTTON, self.onPrint, id = button_print.GetId()) 
        hbox.Add(button_print)
        
        
        # panel for report page
        panel = wx.Panel(self, -1)
        vbox= wx.BoxSizer(wx.VERTICAL)
        # html window
        self.hwindow = html.HtmlWindow(panel, -1,style=wx.BORDER,size=(700,500))
        # set the html page with the report string
        self.hwindow.SetPage(self.report_string)
        # add panels to boxsizers
        hbox.Add(bpanel)
        vbox.Add(hbox,40, wx.EXPAND)
        vbox.Add(panel,500, wx.EXPAND)

        self.SetSizerAndFit(vbox)
        self.Centre()
        self.Show(True)

    def onSave(self,event):
        """
        """
        pass
    
    def onPreview(self,event):
        """
        """
        pass
    
    def onPrint(self,event):
        """
        """
        gg=html.HtmlEasyPrinting(name="Printing", parentWindow=self)
        
        gg.PreviewText(self.report_string)
        
        