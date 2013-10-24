import wx
import sys
if sys.platform.count("win32") > 0:
    FONT_VARIANT = 0
    PNL_WIDTH = 270
else:
    FONT_VARIANT = 1
    PNL_WIDTH = 300
    
class LabelDialog(wx.Dialog):
    def __init__(self, parent, id, title, label):
        wx.Dialog.__init__(self, parent, id, title, size=(PNL_WIDTH, 150))

        #panel = wx.Panel(self, -1)
        #Font
        self.SetWindowVariant(variant=FONT_VARIANT)
        mainbox = wx.BoxSizer(wx.VERTICAL)
        vbox = wx.BoxSizer(wx.VERTICAL)
        textbox = wx.BoxSizer(wx.HORIZONTAL)
        
        text1 = "Enter a new title/label:"
        msg = wx.StaticText(self, -1, text1,(30,15), style=wx.ALIGN_LEFT)
        msg.SetLabel(text1)
        self.myTxtCtrl = wx.TextCtrl(self, -1, '', (200, 30))
        self.myTxtCtrl.SetValue(str(label))
        textbox.Add(self.myTxtCtrl, flag=wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 
                 border=10, proportion=2)
        vbox.Add(msg, flag=wx.ALL, border=10, proportion=1)
        vbox.Add(textbox, flag=wx.EXPAND|wx.TOP|wx.BOTTOM|wx.ADJUST_MINSIZE,
                 border=5)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self,wx.ID_OK, 'OK', size=(70, 25))
        closeButton = wx.Button(self,wx.ID_CANCEL, 'Cancel', size=(70, 25))
        
        hbox.Add(okButton, wx.LEFT, 10)
        hbox.Add((20, 20))
        hbox.Add(closeButton, wx.LEFT, 10)

        mainbox.Add(vbox, flag=wx.LEFT, border=5)
        mainbox.Add(wx.StaticLine(self), 0, wx.ALL|wx.EXPAND, 5)
        mainbox.Add(hbox, flag=wx.CENTER, 
                    border=20)
        self.SetSizer(mainbox)
    
    def getText(self):
        return self.myTxtCtrl.GetValue()
