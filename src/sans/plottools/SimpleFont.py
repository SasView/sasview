
"""
This software was developed by Institut Laue-Langevin as part of
Distributed Data Analysis of Neutron Scattering Experiments (DANSE).

Copyright 2012 Institut Laue-Langevin
"""

# this is a dead simple dialog for getting font family, size,style and weight


import wx
from matplotlib.font_manager import FontProperties

FAMILY = ['serif', 'sans-serif', 'fantasy', 'monospace']
SIZE = [8, 9, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
STYLE = ['normal', 'italic']
WEIGHT = ['light', 'normal', 'bold']


class SimpleFont(wx.Dialog):
    def __init__(self,parent,id,title):

        wx.Dialog.__init__(self,parent,id,title,size=(440,160))
        self.parent = parent
#        self.SetWindowVariant(variant=FONT_VARIANT)

        self.family = FAMILY[1]
        self.size = SIZE[3]
        self.style = STYLE[0]
        self.weight = WEIGHT[1]
        self.tick_label = None
        self.tick_label_check = None
        self.InitUI()
        self.Centre()
        self.Show()
        
    def InitUI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)

        gs = wx.GridSizer(2,4,-1,-1)

        self.fontFamily = wx.ComboBox(self,pos=(80,10),style=wx.CB_READONLY,
                                      size=(100,-1))
        self.fontStyle = wx.ComboBox(self,pos=(80,60),style=wx.CB_READONLY,
                                     size=(100,-1))

        self.fontPoint = wx.ComboBox(self,pos=(300,10),style=wx.CB_READONLY,
                                     size=(100,-1))
        self.fontWeight = wx.ComboBox(self,pos=(300,60),
                                      style=wx.CB_READONLY,size=(100,-1))
        self.tick_label_check = wx.CheckBox(self, -1, label='', pos=(80, 100), 
										size=(15, -1))
        self.tick_label_check.SetValue(False)
        self.okButton = wx.Button(self,wx.ID_OK,'OK',pos=(215,100))
        self.closeButton = wx.Button(self,wx.ID_CANCEL,'Cancel',pos=(315,100))
        
        self._set_family_list()
        self._set_style_list()
        self._set_weight_list()
        self._set_point_list()
        
        familyText = wx.StaticText(self, label='Family:', pos=(10,12))
        sizeText = wx.StaticText(self, label='Size:',pos=(220,12))
        styleText = wx.StaticText(self, label='Style:',pos=(10,62))
        weightText = wx.StaticText(self, label='Weight:',pos=(220,62))
        tick_label_text = wx.StaticText(self,label='Tick label?', pos=(10, 100))
        tick_label_text.SetToolTipString("Apply to tick label too.")
		
    def _set_family_list(self):
        # list of font family
        list = FAMILY
        for idx in range(len(list)):
            self.fontFamily.Append(list[idx],idx)

    def _set_style_list(self):
        # list of styles
        list = STYLE
        for idx in range(len(list)):
            self.fontStyle.Append(list[idx],idx)

    def _set_weight_list(self):
        #list of weights
        list = WEIGHT
        for idx in range(len(list)):
            self.fontWeight.Append(list[idx],idx)

    def _set_point_list(self):
        # list of point sizes
        list = SIZE
        for idx in range(len(list)):
            self.fontPoint.Append(str(list[idx]),idx)

    def get_ticklabel_check(self):
        """
        Get tick label check value
        """
        self.tick_label = self.tick_label_check.GetValue()
        return self.tick_label

    def set_ticklabel_check(self, check=False):
        """
        Set tick label check value
        """
        self.tick_label_check.SetValue(check)

    def set_default_font(self,font):
        
        if not font:
            self.fontFamily.SetSelection(1)
            self.fontWeight.SetSelection(1)
            self.fontPoint.SetSelection(3)
            self.fontStyle.SetSelection(0)
        else:
        	self.fontWeight.SetStringSelection(str(font.get_weight()))
        	self.fontPoint.SetStringSelection(str(int(font.get_size())))
        	self.fontFamily.SetStringSelection(str(font.get_family()[0]))
        	self.fontStyle.SetStringSelection(str(font.get_style()))
        	
    def get_font(self):
        FONT = FontProperties()
        font = FONT.copy()
        font.set_size(str(self.fontPoint.GetValue()))
        font.set_name(str(self.fontFamily.GetValue()))
        font.set_slant(str(self.fontStyle.GetValue()))
        font.set_weight(str(self.fontWeight.GetValue()))

        return font
