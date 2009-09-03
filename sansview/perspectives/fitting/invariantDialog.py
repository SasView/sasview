"""
    Provide GUI for invariant calculation
"""
import wx
from invariant import InvariantCalculator
_BOX_WIDTH = 76
_STATICBOX_WIDTH = 200


class InvariantDialog(wx.Dialog):
    """
        Panel displaying results of calculations
    """
    def __init__(self, parent,base=None, id = -1, *args, **kwds ):
        wx.Dialog.__init__(self, parent, id = id, *args, **kwds)
        #Object that receives status event
        self.base= base
        self.calculator = InvariantCalculator()
    
        self._do_layout()
        self.SetAutoLayout(True)
        self.Layout()
       

    def _do_layout(self):
        """
            Draw window content
        """
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        
        self.q_result_txt= wx.StaticText(self, -1, "Q*")
        self.q_result_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH ,-1))
        self.q_unit_txt= wx.StaticText(self, -1, "[A^(-3)cm^(-1)]")
        
        definitionbox = wx.StaticBox(self, -1, "Definitions")
        boxsizer = wx.StaticBoxSizer(definitionbox, wx.VERTICAL)
        boxsizer.SetMinSize((_STATICBOX_WIDTH,-1))
        text= "this is the definition"
        self.definition_txt= wx.StaticText(self, -1, text)
        sizer_definition = wx.BoxSizer(wx.VERTICAL)
        sizer_definition.Add(self.definition_txt)
        boxsizer.Add( sizer_definition )
        sizer2.Add(boxsizer,0, wx.EXPAND | wx.ALL, 20)
       
        sizer1.Add(self.q_result_txt,wx.LEFT , 100)
        sizer1.Add(self.q_result_ctl)
        sizer1.Add(self.q_unit_txt)
        
        self.button_OK = wx.Button(self, wx.ID_OK, "OK")
        self.Bind(wx.EVT_BUTTON, self.checkValues, self.button_OK)
        vbox  = wx.BoxSizer(wx.VERTICAL)
        vbox.Add((20,20))
        vbox.Add(sizer1)
        vbox.Add(sizer2)
        vbox.Fit(self) 
        self.SetSizer(vbox)
        
        
class ViewApp(wx.App):
    def OnInit(self):
        dlg = InvariantDialog(None, id=-1, title="Invariant Calculator")    
        dlg.Show(True)
        self.SetTopWindow(dlg)
        
        return True
        

if __name__ == "__main__": 
    app = ViewApp(0)
    app.MainLoop()     
       