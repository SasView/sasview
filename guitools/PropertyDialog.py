#!/usr/bin/python

# myDialog.py

import wx

class Properties(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title, size=(350, 200))
        """
            for the properties window
        """
        self.parent = parent
        panel = wx.Panel(self, -1, style=wx.SIMPLE_BORDER)   
        vbox  = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.GridBagSizer(5,0)
        vbox.Add(panel, 1, wx.EXPAND | wx.ALL)
     
        ix = 1
        iy = 1
        sizer.Add(wx.StaticText(panel, -1, 'X'),(iy, ix))
        ix += 2
        sizer.Add(wx.StaticText(panel, -1, 'Y'),(iy, ix))
        ix += 2
        sizer.Add(wx.StaticText(panel, -1, 'View'),(iy, ix))
        iy += 1
        ix = 1
        self.xvalue = wx.ComboBox(panel, -1)
        sizer.Add(self.xvalue,(iy,ix))
        ix +=2
        self.yvalue = wx.ComboBox(panel, -1)
        sizer.Add( self.yvalue,(iy, ix))
        ix +=2
        self.view =wx.ComboBox(panel, -1)
        sizer.Add(self.view,(iy,ix))
        ix =3
        iy +=3
        btCancel=wx.Button(panel, wx.ID_CANCEL,'Cancel' )
        sizer.Add(btCancel,(iy,ix))
        ix +=2
        btOk = wx.Button(panel, wx.ID_OK, "Ok")
        sizer.Add(btOk,(iy, ix))
        
        # scale value for x
        self.xvalue.SetValue("x")
        self.xvalue.Insert("x",0)
        self.xvalue.Insert("x^(2)",1)
        self.xvalue.Insert("log10(x)",2)
        
        
        # scale value for y
        self.yvalue.SetValue("log10(y)")
        self.yvalue.Insert("y",0)
        self.yvalue.Insert("1/y",1)
        self.yvalue.Insert("ln(y)",2)
        self.yvalue.Insert("y^(2)",3)
        self.yvalue.Insert("1/sqrt(y)",4)
        self.yvalue.Insert("log10(y)",5)
        self.yvalue.Insert("ln(y*x)",6)
        self.yvalue.Insert("ln(y*x^(2))",7)
        self.yvalue.Insert("ln(y*x^(4))",8)
        
        # type of view or model used 
        self.view.SetValue("Guinier lny vs x^(2)")
        self.view.Insert("Guinier lny vs x^(2)",0)
        panel.SetSizer(sizer)
        self.SetSizer(vbox)
        self.Centre()
           
        
    def setValues(self,x,y):
        return  self.xvalue.SetValue(x),  self.yvalue.SetValue(y)
        
    def getValues(self):
        return self.xvalue.GetValue(), self.yvalue.GetValue()

if __name__ == "__main__": 
    app = wx.App()
    dialog = Properties(None, -1, 'Properties')
    dialog.ShowModal()
    app.MainLoop()


