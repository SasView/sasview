import wx
from wx import Frame

wx_supports_html2 = float(wx.__version__[:3]) >= 2.9
if wx_supports_html2:
    import wx.html2 as html
else:
    import wx.html as html

class DocumentationWindow(Frame):
    def __init__(self, parent, id, path, title='Help', size=(850, 540)):
        Frame.__init__(self, parent, id, title, size=size)

        if wx_supports_html2:
            # Complete HTML/CSS support!
            self.view = html.WebView.New(self)
            self.view.LoadURL("file://" + path)
        else:
            # This ain't gonna be pretty...
            self.view = html.HtmlWindow(self, -1, style=wx.NO_BORDER)
            self.view.LoadPage(path)
