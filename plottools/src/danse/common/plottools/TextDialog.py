import wx
import sys

if sys.platform.count("win32") > 0:
    FONT_VARIANT = 0
    PNL_WIDTH = 460
else:
    FONT_VARIANT = 1
    PNL_WIDTH = 500
FAMILY = ['serif', 'sans-serif', 'fantasy', 'monospace']
SIZE = [8, 9, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
STYLE = ['normal', 'italic']
WEIGHT = ['light', 'normal', 'bold']
COLOR = ['black', 'blue', 'green', 'red', 'cyan', 'magenta', 'yellow']


class TextDialog(wx.Dialog):
    def __init__(self, parent, id, title, label='', unit=None):
        """
        Dialog window pops- up when selecting 'Add Text' on the toolbar
        """
        wx.Dialog.__init__(self, parent, id, title, size=(PNL_WIDTH, 280))
        self.parent = parent
        #Font
        self.SetWindowVariant(variant=FONT_VARIANT)
        # default
        self.family = FAMILY[1]
        self.size = SIZE[3]
        self.style = STYLE[0]
        self.weight = WEIGHT[1]
        self.color = COLOR[0]
        self.tick_label = False
        #Dialog interface
        vbox  = wx.BoxSizer(wx.VERTICAL)
        text_box = wx.BoxSizer(wx.HORIZONTAL)
        sizer = wx.GridBagSizer(1, 3)
        _BOX_WIDTH = 60
        font_size = 12
        font_description= wx.StaticBox(self, -1, 'Font',
                                       size=(PNL_WIDTH-20, 70))
        font_box = wx.StaticBoxSizer(font_description, wx.VERTICAL)
        family_box = wx.BoxSizer(wx.HORIZONTAL)
        style_box = wx.BoxSizer(wx.HORIZONTAL)
        #tcA
        if unit != None:
            styles = wx.TAB_TRAVERSAL
            height = -1
            unit_text = wx.StaticText(self, -1, 'Unit :')
            unit_text.SetToolTipString("Unit of the axis.")
            self.unit_ctrl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, -1))
            self.unit_ctrl.SetValue(str(unit))
            unit_box = wx.BoxSizer(wx.HORIZONTAL)
            tick_label_text = wx.StaticText(self, -1, 'Tick label')
            tick_label_text.SetToolTipString("Apply to tick label too.")
            self.tick_label_check = wx.CheckBox(self, -1, 
                                                '', (10, 10))
            self.tick_label_check.SetValue(False)
            self.tick_label_check.SetToolTipString("Apply to tick label too.")
            wx.EVT_CHECKBOX(self, self.tick_label_check.GetId(), 
                            self.on_tick_label)
            enter_text = 'Enter text:'
        else:
            styles = wx.TAB_TRAVERSAL|wx.TE_MULTILINE|wx.TE_LINEWRAP|\
                              wx.TE_PROCESS_ENTER|wx.SUNKEN_BORDER|wx.HSCROLL
            height = 60
            unit_text = None
            self.unit_ctrl = None
            unit_box = None
            tick_label_text = None
            self.tick_label_check = None
            enter_text = 'Enter text'
            if len(label) > 0:
                enter_text += " (this text won't be auto-updated if modified.):"
            else:
                enter_text += ":"
        self.textString = wx.TextCtrl(self, -1, size=(PNL_WIDTH-30, height ),\
                                                        style=styles)
        self.textString.SetValue(str(label))
        self.textString.SetToolTipString("The text that will be displayed.")
        #font family
        self.fontFamily = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        wx.EVT_COMBOBOX(self.fontFamily, -1, self.on_family)
        self.fontFamily.SetMinSize((_BOX_WIDTH, -1))
        self._set_family_list()
        self.fontFamily.SetSelection(1)
        self.fontFamily.SetToolTipString("Font family of the text.")
        #font weight
        self.fontWeight = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        wx.EVT_COMBOBOX(self.fontWeight, -1, self.on_weight)
        self.fontWeight.SetMinSize((_BOX_WIDTH, -1))
        self._set_weight_list()
        self.fontWeight.SetSelection(1)
        self.fontWeight.SetToolTipString("Font weight of the text.")
        #font family
        self.fontSize = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        wx.EVT_COMBOBOX(self.fontSize, -1, self.on_size)
        self.fontSize.SetMinSize((_BOX_WIDTH, -1))
        self._set_size_list()
        self.fontSize.SetSelection(5)
        self.fontSize.SetToolTipString("Font size of the text.")
        #font style
        self.fontStyle = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        wx.EVT_COMBOBOX(self.fontStyle, -1, self.on_style)
        self.fontStyle.SetMinSize((_BOX_WIDTH, -1))
        self._set_style_list()
        self.fontStyle.SetSelection(0)
        self.fontStyle.SetToolTipString("Font style of the text.")
        #font color
        self.fontColor = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        wx.EVT_COMBOBOX(self.fontColor, -1, self.on_color)
        self.fontColor.SetMinSize((_BOX_WIDTH, -1))
        self._set_color_list()
        self.fontColor.SetSelection(0)
        self.fontColor.SetToolTipString("Font color of the text.")
        # Buttons on the bottom
        self.static_line_1 = wx.StaticLine(self, -1)
        self.okButton = wx.Button(self,wx.ID_OK, 'OK', size=(_BOX_WIDTH, 25))
        self.closeButton = wx.Button(self,wx.ID_CANCEL, 'Cancel',
                                     size=(_BOX_WIDTH, 25))
        
        # Intro
        explanation = "Select font properties :"
        vbox.Add(sizer)
        ix = 0
        iy = 1
        sizer.Add(wx.StaticText(self, -1, explanation), (iy, ix),
                 (1, 1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        family_box.Add(wx.StaticText(self, -1, 'Family :'), -1, 0)
        family_box.Add(self.fontFamily, -1, 0)
        family_box.Add((_BOX_WIDTH/2,-1))
        family_box.Add(wx.StaticText(self, -1, 'Size :'), -1, 0)
        family_box.Add(self.fontSize, -1, 0)
        if unit_box != None:
            family_box.Add((_BOX_WIDTH/2, -1))
            family_box.Add(tick_label_text, -1, 0)
            family_box.Add(self.tick_label_check, -1, 0)
        style_box.Add(wx.StaticText(self, -1, 'Style :'), -1, 0)
        style_box.Add(self.fontStyle, -1, 0)
        style_box.Add((_BOX_WIDTH/2,-1))
        style_box.Add(wx.StaticText(self, -1, 'Weight :'), -1, 0)
        style_box.Add(self.fontWeight, -1, 0)
        style_box.Add((_BOX_WIDTH/2,-1))
        style_box.Add(wx.StaticText(self, -1, 'Color :'), -1, 0)
        style_box.Add(self.fontColor, -1, 0)
        font_box.Add(family_box, -1, 10)
        font_box.Add(style_box, -1, 10)
        iy += 1
        ix = 0
        sizer.Add(font_box, (iy, ix),
                  (1, 1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        iy += 2
        ix = 0
        sizer.Add(wx.StaticText(self, -1, enter_text), (iy, ix),
                 (1, 1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        text_box.Add((15, 10))
        text_box.Add(self.textString)
        vbox.Add(text_box, 0, wx.EXPAND, 15)
        if unit_box != None:
            unit_box.Add(unit_text, -1, 0)
            unit_box.Add(self.unit_ctrl, -1, 0)
            vbox.Add((5,5))
            vbox.Add(unit_box, 0,wx.LEFT, 15)
        
        vbox.Add((10, 10))
        vbox.Add(self.static_line_1, 0, wx.EXPAND, 10)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_button.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(self.okButton, 0, 
                         wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        sizer_button.Add(self.closeButton, 0,
                          wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        vbox.Add(sizer_button, 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.SetSizer(vbox)
        self.Centre()
        
    def _set_family_list(self):
        """
        Set the list of font family
        """
        # list of family choices
        list = FAMILY
        for idx in range(len(list)):
            self.fontFamily.Append(list[idx], idx)
                 
    def _set_size_list(self):
        """
        Set the list of font size
        """
        # list of size choices
        list = SIZE
        for idx in range(len(list)):
            self.fontSize.Append(str(list[idx]),idx)   
                 
    def _set_weight_list(self):
        """
        Set the list of font weight
        """
        # list of weight choices
        list = WEIGHT
        for idx in range(len(list)):
            self.fontWeight.Append(list[idx], idx)
            
    def _set_style_list(self):
        """
        Set the list of font style
        """
        # list of style choices
        list = STYLE
        for idx in range(len(list)):
            self.fontStyle.Append(list[idx], idx)
            
    def _set_color_list(self):
        """
        Set the list of font color
        """
        # list of tyle choices
        list = COLOR
        for idx in range(len(list)):
            self.fontColor.Append(list[idx], idx)
            
    def on_tick_label(self, event):
        """
        Set the font for tick label
        """
        event.Skip()
        self.tick_label = self.tick_label_check.GetValue()
                   
    def on_family(self, event):
        """
        Set the family
        """
        event.Skip()
        self.family = self.fontFamily.GetValue()
                 
    def on_style(self, event):
        """
        Set the style
        """
        event.Skip()
        self.style = self.fontStyle.GetValue()
            
    def on_weight(self, event):
        """
        Set the weight
        """
        event.Skip()
        self.weight = self.fontWeight.GetValue()
    
    def on_size(self, event):
        """
        Set the size
        """
        event.Skip()
        self.size = self.fontSize.GetValue()
    
    def on_color(self, event):
        """
        Set the color
        """
        event.Skip()
        self.color = self.fontColor.GetValue()
           
    def getText(self):
        """
        Returns text string as input by user.
        """
        return self.textString.GetValue()
    
    def getUnit(self):
        """
        Returns unit string as input by user.
        """
        return self.unit_ctrl.GetValue()
        
    def getX(self):  
        """
        Returns x coordinate of text box
        """
        return float(self.xString.GetValue())
        
    def getY(self):
        """
        Returns y coordinate of text box
        """
        return float(self.yString.GetValue())
    
    def getFamily(self):
        """
        Returns font family for the text box
        """
        return str(self.family)
    
    def getStyle(self):
        """
        Returns font tyle for the text box
        """
        return str(self.style)

    def getWeight(self):
        """
        Returns font weight for the text box
        """
        return str(self.weight)
          
    def getSize(self):
        """
        Returns font size for the text box
        """
        return int(self.size)
    
    def getColor(self):
        """
        Returns font size for the text box
        """
        return str(self.color)
    
    def getTickLabel(self):
        """
        Bool for use on tick label
        """
        return self.tick_label
