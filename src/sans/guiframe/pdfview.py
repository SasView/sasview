# Read PDF files by embeding the Adobe Acrobat Reader
# wx.activex module uses class ActiveX control

import  wx
import os
if wx.Platform == '__WXMSW__':
    from wx.lib.pdfwin import PDFWindow

from wx.lib.scrolledpanel import ScrolledPanel
STYLE = wx.TE_MULTILINE|wx.TE_READONLY|wx.SUNKEN_BORDER|wx.HSCROLL

class TextPanel(ScrolledPanel):
    """
    Panel that contains the text
    """
    def __init__(self, parent, text=None):
        """
        """
        ScrolledPanel.__init__(self, parent, id=-1)
        self.SetupScrolling()
        self.parent = parent
        self.text = text
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.textctl = wx.TextCtrl(self, -1, size=(-1, -1), style=STYLE)
        self.textctl.SetValue(self.text)
        sizer.Add(self.textctl, proportion=1, flag=wx.EXPAND)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        wx.EVT_CLOSE(self.parent, self.OnClose)
                
    def OnClose(self, event):
        """
        Close panel
        """
        self.parent.Destroy()
        
class TextFrame(wx.Frame):
    """
    Frame for PDF panel
    """
    def __init__(self, parent, id, title, text):
        """
        Init
        
        :param parent: parent panel/container
        :param path: full path of the pdf file 
        """
        # Initialize the Frame object
        wx.Frame.__init__(self, parent, id, title,
                          wx.DefaultPosition, wx.Size(600, 830))
        # make an instance of the class
        TextPanel(self, text) 
        self.SetFocus()
        
class PDFPanel(wx.Panel):
    """
    Panel that contains the pdf reader
    """
    def __init__(self, parent, path=None):
        """
        """
        wx.Panel.__init__(self, parent, id=-1)
        
        self.parent = parent
        self.path = path
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.pdf = PDFWindow(self, style=wx.SUNKEN_BORDER)
        
        sizer.Add(self.pdf, proportion=1, flag=wx.EXPAND)
        
        btn = wx.Button(self, wx.NewId(), "Open PDF File")
        self.Bind(wx.EVT_BUTTON, self.OnOpenButton, btn)
        btnSizer.Add(btn, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)

        self.pdf.LoadFile(self.path)
        btn = wx.Button(self, wx.NewId(), "Previous Page")
        self.Bind(wx.EVT_BUTTON, self.OnPrevPageButton, btn)
        btnSizer.Add(btn, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)

        btn = wx.Button(self, wx.NewId(), "Next Page")
        self.Bind(wx.EVT_BUTTON, self.OnNextPageButton, btn)
        btnSizer.Add(btn, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        
        btn = wx.Button(self, wx.NewId(), "Close")
        self.Bind(wx.EVT_BUTTON, self.OnClose, btn)
        btnSizer.Add(btn, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        btnSizer.Add((50,-1), proportion=2, flag=wx.EXPAND)
        sizer.Add(btnSizer, proportion=0, flag=wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        wx.EVT_CLOSE(self.parent, self.OnClose)
        
    def OnOpenButton(self, event):
        """
        Open file button
        """
        # make sure you have PDF files available on your drive
        dlg = wx.FileDialog(self, wildcard="*.pdf")
        dlg.SetDirectory(os.path.dirname(self.path))
        if dlg.ShowModal() == wx.ID_OK:
            wx.BeginBusyCursor()
            file = dlg.GetPath()
            self.pdf.LoadFile(file)
            self.parent.SetTitle(os.path.basename(file.split('.')[0]))
            wx.EndBusyCursor()
        dlg.Destroy()
        # Let Panel know the file changed: Avoiding C++ error
        self.Update()
        
    def OnLoad(self, event=None, path=None):
        """
        Load a pdf file
        
        : Param path: full path to the file
        """
        self.pdf.LoadFile(path)

        
    def OnPrevPageButton(self, event):
        """
        Goes to Previous page
        """
        self.pdf.gotoPreviousPage()

    def OnNextPageButton(self, event):
        """
        Goes to Next page
        """
        self.pdf.gotoNextPage()
        
    def OnClose(self, event):
        """
        Close panel
        """
        self.parent.Destroy()

class PDFFrame(wx.Frame):
    """
    Frame for PDF panel
    """
    def __init__(self, parent, id, title, path):
        """
        Init
        
        :param parent: parent panel/container
        :param path: full path of the pdf file 
        """
        # Initialize the Frame object
        wx.Frame.__init__(self, parent, id, title,
                          wx.DefaultPosition, wx.Size(600, 830))
        # make an instance of the class
        PDFPanel(self, path) 
        
class ViewApp(wx.App):
    def OnInit(self):
        path = None
        frame = PDFFrame(None, -1, "PDFView", path=path)  
         
        frame.Show(True)
        #self.SetTopWindow(frame)
        
        return True
               
if __name__ == "__main__": 
    app = ViewApp(0)
    app.MainLoop()     
