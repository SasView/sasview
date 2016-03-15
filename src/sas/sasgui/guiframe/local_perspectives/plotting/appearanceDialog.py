#!/usr/bin/python
"""
Dialog for appearance of plot symbols, color, size etc.

This software was developed by Institut Laue-Langevin as part of
Distributed Data Analysis of Neutron Scattering Experiments (DANSE).

Copyright 2012 Institut Laue-Langevin
"""
import wx
import operator

class appearanceDialog(wx.Frame):
    """
    Appearance dialog
    """
    def __init__(self, parent, title):
        """
        Initialization of the Panel
        """
        super(appearanceDialog,
              self).__init__(parent, title=title, size=(570, 450),
                             style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)

        self.okay_clicked = False
        self.parent = parent
        self.symbo_labels = self.parent.get_symbol_label()
        self.color_labels = self.parent.get_color_label()
        self.init_ui()
        self.Centre()
        self.Show()

    def init_ui(self):
        """
        Create spacing needed
        """
        panel = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)

        ivbox1 = wx.BoxSizer(wx.VERTICAL)
        ivbox2 = wx.BoxSizer(wx.VERTICAL)

        ihbox1 = wx.BoxSizer(wx.HORIZONTAL)
        ihbox2 = wx.BoxSizer(wx.HORIZONTAL)

        symbolstaticbox = wx.StaticBox(panel, -1, 'Symbol')
        symbolstaticboxsizer = wx.StaticBoxSizer(symbolstaticbox, wx.VERTICAL)

        # add widgets - reverse order!
        # texts
        symboltext = wx.StaticText(panel, label='Shape')
        colortext = wx.StaticText(panel, label='Color')
        sizetext = wx.StaticText(panel, label='Size ')
        labeltext = wx.StaticText(panel, label='Legend Label')

        # selection widgets
        self.symbollistbox = wx.ListBox(panel, -1, size=(200, 200))
        self.colorlistbox = wx.ComboBox(panel, style=wx.CB_READONLY,
                                        size=(185, -1))
        self.sizecombobox = wx.ComboBox(panel, style=wx.CB_READONLY,
                                        size=(90, -1))
        self.sizecombobox.Bind(wx.EVT_COMBOBOX, self.combo_click)
        self.sizecustombutton = wx.Button(panel, label='Custom...')
        self.sizecustombutton.Bind(wx.EVT_BUTTON, self.custom_size)
        self.labeltextbox = wx.TextCtrl(panel, -1, "", size=(440, -1))

        # buttons
        okbutton = wx.Button(panel, label='OK')
        okbutton.Bind(wx.EVT_BUTTON, self.on_ok)
        cancelbutton = wx.Button(panel, label='Cancel')
        cancelbutton.Bind(wx.EVT_BUTTON, self.close_dlg)

        # now Add all the widgets to relevant spacer - tricky
        ivbox1.Add(symboltext, flag=wx.ALL | wx.ALIGN_LEFT, border=10)
        ivbox1.Add(self.symbollistbox, flag=wx.ALL | wx.ALIGN_LEFT, border=10)

        ihbox1.Add(sizetext, flag=wx.ALL | wx.ALIGN_LEFT, border=10)
        ihbox1.Add(self.sizecombobox,
                   flag=wx.ALL | wx.RIGHT | wx.ALIGN_LEFT, border=10)
        ihbox1.Add(self.sizecustombutton,
                   flag=wx.ALIGN_LEFT | wx.ALL, border=10)

        ihbox2.Add(colortext, flag=wx.ALL | wx.ALIGN_LEFT, border=10)
        ihbox2.Add(self.colorlistbox, flag=wx.ALL | wx.ALIGN_LEFT, border=10)

        ivbox2.Add(ihbox1, flag=wx.ALIGN_LEFT, border=10)
        ivbox2.Add(ihbox2, flag=wx.ALIGN_LEFT, border=10)

        hbox1.Add(ivbox1, flag=wx.ALIGN_LEFT, border=10)
        hbox1.Add(ivbox2, flag=wx.ALIGN_LEFT, border=10)

        hbox2.Add(okbutton, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
        hbox2.Add(cancelbutton, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)

        hbox3.Add(labeltext, flag=wx.EXPAND | wx.ALL | wx.ALIGN_LEFT, border=10)
        hbox3.Add(self.labeltextbox, flag=wx.EXPAND | wx.ALL | wx.ALIGN_LEFT, border=10)

        symbolstaticboxsizer.Add(hbox1, flag=wx.ALL | wx.EXPAND, border=10)
        vbox.Add(symbolstaticboxsizer, flag=wx.ALL | wx.EXPAND, border=10)
        vbox.Add(hbox3, flag=wx.EXPAND | wx.RIGHT, border=10)
        vbox.Add(wx.StaticLine(panel), 0, wx.ALL | wx.EXPAND, 5)
        vbox.Add(hbox2, flag=wx.RIGHT | wx.ALIGN_RIGHT, border=10)

        panel.SetSizer(vbox)

        self.populate_symbol()
        self.populate_color()
        self.populate_size()

        self.SetDefaultItem(self.symbollistbox)

    def custom_size(self, event):
        """
        On custom size
        """
        dlg = wx.TextEntryDialog(self, 'Enter custom size', 'Custom size', str(self.final_size))
        if dlg.ShowModal() == wx.ID_OK:
            if float(dlg.GetValue()) < 0:
                msg = "Unfortunately imaginary icons are not yet supported."
                msg += "Please enter a positive value"
                dial = wx.MessageDialog(None, msg, 'Error', wx.OK | wx.ICON_ERROR)
                dial.ShowModal()
                dlg.Destroy()
                self.custom_size(event)
            else:
                self.final_size = dlg.GetValue()
                dlg.Destroy()
        else:
            dlg.Destroy()

    def set_defaults(self, size, color, symbol, label):
        """
        Set Defaults
        """
        self.final_size = size
        # set up gui values
        self.labeltextbox.SetValue(label)
        if size % 1 == 0 and size > 1 and size < 11:
            self.sizecombobox.SetSelection(int(size) - 1)
        else:
            self.sizecombobox.SetSelection(4)
        self.symbollistbox.SetSelection(self.sorted_sym_dic[symbol])
        colorname = appearanceDialog.find_key(self.parent.get_color_label(), color)
        self.colorlistbox.SetStringSelection(colorname)

    def populate_symbol(self):
        """
        Populate Symbols
        """
        self.sorted_symbo_labels = sorted(self.symbo_labels.iteritems(),
                                          key=operator.itemgetter(1))
        self.sorted_sym_dic = {}
        i = 0
        for label in self.sorted_symbo_labels:
            self.symbollistbox.Append(str(label[0]))
            self.sorted_sym_dic[str(label[0])] = i
            i += 1

    def populate_color(self):
        """
        Populate Colors
        """
        sortedcolor_labels = sorted(self.color_labels.iteritems(),
                                    key=operator.itemgetter(1))
        for color in sortedcolor_labels:
            self.colorlistbox.Append(str(color[0]))

    def populate_size(self):
        """
        Populate Size
        """
        for i in range(1, 11):
            self.sizecombobox.Append(str(i) + '.0')

    def combo_click(self, event):
        """
        Combox on click
        """
        event.Skip()
        self.final_size = self.sizecombobox.GetValue()

    def close_dlg(self, event):
        """
        On Close Dlg
        """
        event.Skip()
        self.Destroy()

    @staticmethod
    def find_key(dic, val):
        """
        Find key
        """
        return [k for k, v in dic.iteritems() if v == val][0]

    def get_current_values(self):
        """
        Get Current Values
        :returns : (size, color, symbol, dataname)
        """
        size = float(self.final_size)
        name = str(self.labeltextbox.GetValue())
        seltuple = self.symbollistbox.GetSelections()
        symbol = appearanceDialog.find_key(self.sorted_sym_dic,
                                           int(seltuple[0]))
        color = str(self.colorlistbox.GetValue())
        return(size, color, symbol, name)

    def on_ok(self, event):
        """
        On OK button clicked
        """
        event.Skip()
        self.okay_clicked = True
        self.Close()
