
import wx
from wx.lib.popupctl import PopButton

class GuiPopButton(PopButton):
    def __init__(self, parent, *args, **kwrds):
        PopButton.__init__(self, parent, *args, **kwrds)
        self.parent = parent
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
          
    def OnLeftDown(self, event):
        if not self.IsEnabled():
            return
        self.didDown = True
        self.up = False
        self.CaptureMouse()
        self.parent.SetFocus()
        self.Refresh()
        

        
class BitmapPopUpButton(wx.PyControl):
    def __init__(self, parent, gui_bitmap=None, gui_size=(-1, -1),*args, **kwrds):
        if kwrds.has_key('value'):
            del kwrds['value']
        style = kwrds.get('style', 0)
        if (style & wx.BORDER_MASK) == 0:
            style |= wx.BORDER_NONE
            kwrds['style'] = wx.BORDER_NONE
        wx.PyControl.__init__(self, parent, *args, **kwrds)
        if gui_bitmap is None:
            gui_bitmap = wx.NullBitmap
        self._button = wx.BitmapButton(parent=self, id=-1, 
                                      bitmap=gui_bitmap, size=gui_size)
        self.bCtrl = GuiPopButton(self, wx.ID_ANY, style=wx.BORDER_NONE)
        print "hello"
        sizer =  wx.GridBagSizer() 
        self.SetSizer(sizer)
        sizer.Add(self._button, pos=(0, 0))
        sizer.Add(self.bCtrl,  pos=(0, 1))
        
        self.pop = None
        self.content = None
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.bCtrl.Bind(wx.EVT_BUTTON, self.OnButton, self.bCtrl)
        self.Bind(wx.EVT_SET_FOCUS, self.OnFocus)

        self.SetInitialSize(kwrds.get('size', wx.DefaultSize))
        self.Layout() 
        self.SendSizeEvent()
  
    def Create(self, parent, id, bitmap, pos, size, style, validator, name):
        """
        Acutally create the GUI BitmapButton for 2-phase creation.
        """
        raise NotImplemented
    
    def GetBitmapDisabled(self):
        """
        Returns the bitmap for the disabled state
        """
        return self._button.GetBitmapDisabled() 
        
    def GetBitmapFocus(self):
        """
        Returns the bitmap for the focused state.
        """
        return self._button.GetBitmapFocus()
        
    def GetBitmapHover(self):
        """
        Returns the bitmap used when 
        the mouse is over the button, may be invalid.
        """
        return self._button.GetBitmapHover()
        
    def GetBitmapLabel(self): 
        """
        Returns the label bitmap (the one passed to the constructor).
        """
        return self._button.GetBitmapLabel()
        
    def GetBitmapSelected(self) :
        """
        Returns the bitmap for the selected state. 
        """
        return self._button.GetBitmapSelected()
        
    def GetMarginX(self):
        """
        """
        return self._button.GetMarginX()
        
    def GetMarginY(self):
        """
        """
        return self._button.GetMarginY()
        
    def SetBitmapDisabled(self, bitmap):
        """
        Sets the bitmap for the disabled button appearance. 
        """
    def SetBitmapFocus(self, bitmap):
        """
        Sets the bitmap for the button appearance 
        when it has the keyboard focus. 
        """
        self._button.SetBitmapFocus(bitmap)

    def SetBitmapHover(self, hover):
        """
        Sets the bitmap to be shown when the mouse is over the button. 
        """
        self._button.SetBitmapHover(hover)
        
    def SetBitmapLabel(self, bitmap): 
        """Sets the bitmap label for the button. 
        """
        self._button.SetBitmapLabel(bitmap)
    
    def SetBitmapSelected(self, bitmap):
        """
        """
        self._button.SetBitmapSelected(bitmap)

    def SetMargins(self, x, y):
        """
        """
        self._button.SetMargins(x, y) 

    def OnFocus(self,evt):
        # embedded control should get focus on TAB keypress
        self._button.SetFocus()
        evt.Skip()

    def OnSize(self, evt):
        # layout the child widgets
        w,h = self.GetClientSize()
        self._button.SetDimensions(0, 0, 
                                   w - self.marginWidth - self.buttonWidth, h)
        self.bCtrl.SetDimensions(w - self.buttonWidth, 0, self.buttonWidth, h)

    def DoGetBestSize(self):
        # calculate the best size of the combined control based on the
        # needs of the child widgets.
        tbs = self._button.GetBestSize()
        return wx.Size(tbs.width + self.marginWidth + self.buttonWidth,
                       tbs.height)
    def OnButton(self, evt):
        if not self.pop:
            if self.content:
                self.pop = PopupDialog(self, self.content)
                del self.content
            else:
                print 'No Content to pop'
        if self.pop:
            self.pop.Display()
       
    def Enable(self, flag):
        wx.PyControl.Enable(self,flag)
        self._button.Enable(flag)
        self.bCtrl.Enable(flag)

    def SetPopupContent(self, content):
        if not self.pop:
            self.content = content
            self.content.Show(False)
        else:
            self.pop.SetContent(content)

    def FormatContent(self):
        pass

    def PopDown(self):
        if self.pop:
            self.pop.EndModal(1)

    def SetBitmapDisabled(self, bitmap):
        self._button.SetBitmapDisabled(bitmap)

    def SetMargins(self, x, y):
        self._button.SetMargins(x, y) 

    def SetFont(self, font):
        self._button.SetFont(font)

    def GetFont(self):
        return self._button.GetFont()

    def _get_marginWidth(self):
        if 'wxMac' in wx.PlatformInfo:
            return 6
        else:
            return 3
    marginWidth = property(_get_marginWidth)

    def _get_buttonWidth(self):
        return 20
    buttonWidth = property(_get_buttonWidth)