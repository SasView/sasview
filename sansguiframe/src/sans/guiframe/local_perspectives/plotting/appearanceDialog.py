#!/usr/bin/python

"""

Dialog for appearance of plot symbols, color, size etc.


/**
    This software was developed by Institut Laue-Langevin as part of
    Distributed Data Analysis of Neutron Scattering Experiments (DANSE).

    Copyright 2012 Institut Laue-Langevin

**/


"""

import wx
import operator


# main appearance dialog starts here:


class appearanceDialog(wx.Frame):

    def __init__(self,parent,title):
        super(appearanceDialog,self).__init__(parent, title=title,size=(570,450), style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)

        self.okay_clicked = False
        self.parent = parent
        self.symbolLabels = self.parent.get_symbol_label()
        self.colorLabels = self.parent.get_color_label()


        self.InitUI()
        self.Centre()
        self.Show()

  
    def InitUI(self):

        # create spacing needed
        panel = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)

        ivbox1 = wx.BoxSizer(wx.VERTICAL)
        ivbox2 = wx.BoxSizer(wx.VERTICAL)
 
        ihbox1 = wx.BoxSizer(wx.HORIZONTAL)
        ihbox2 = wx.BoxSizer(wx.HORIZONTAL)

        symbolStaticBox = wx.StaticBox(panel, -1, 'Symbol')
        symbolStaticBoxSizer = wx.StaticBoxSizer(symbolStaticBox, wx.VERTICAL)

        # add widgets - reverse order!

        # texts
        symbolText = wx.StaticText(panel, label='Shape')
        colorText = wx.StaticText(panel, label='Color')
        sizeText = wx.StaticText(panel, label='Size ')
        labelText = wx.StaticText(panel, label='Legend label')

        # selection widgets
        self.symbolListBox = wx.ListBox(panel,-1,size=(200,200))
        self.colorListBox = wx.ComboBox(panel,style=wx.CB_READONLY, size=(195,-1))
        self.sizeComboBox = wx.ComboBox(panel,style=wx.CB_READONLY, size=(90,-1))
        self.sizeComboBox.Bind(wx.EVT_COMBOBOX, self.combo_click)
        self.sizeCustomButton = wx.Button(panel, label='Custom...')
        self.sizeCustomButton.Bind(wx.EVT_BUTTON, self.customSize)
        self.labelTextBox = wx.TextCtrl(panel,-1, "",size=(-1,-1))

        # buttons
        OkButton = wx.Button(panel, label='OK')
        OkButton.Bind(wx.EVT_BUTTON,self.onOK)
        cancelButton = wx.Button(panel, label='Cancel')
        cancelButton.Bind(wx.EVT_BUTTON, self.CloseDlg)

        # now Add all the widgets to relevant spacer - tricky
        ivbox1.Add(symbolText, flag =  wx.ALL  | wx.ALIGN_LEFT ,border=10)
        ivbox1.Add(self.symbolListBox, flag = wx.ALL | wx.ALIGN_LEFT ,border=10)

        ihbox1.Add(sizeText, flag = wx.ALL| wx.ALIGN_LEFT , border=10)
        ihbox1.Add(self.sizeComboBox, flag =  wx.ALL|wx.RIGHT | wx.ALIGN_LEFT , border=10)
        ihbox1.Add(self.sizeCustomButton, flag = wx.ALIGN_LEFT | wx.ALL, border=10)

        ihbox2.Add(colorText,flag = wx.ALL | wx.ALIGN_LEFT, border=10)
        ihbox2.Add(self.colorListBox, flag = wx.ALL  | wx.ALIGN_LEFT, border=10)



        ivbox2.Add(ihbox1, flag =wx.ALIGN_LEFT,border=10)
        ivbox2.Add(ihbox2, flag =wx.ALIGN_LEFT,border=10)

        
        hbox1.Add(ivbox1,flag =wx.ALIGN_LEFT ,border=10)
        hbox1.Add(ivbox2,flag =wx.ALIGN_LEFT ,border=10)

   
        hbox2.Add(OkButton, flag = wx.ALL |  wx.ALIGN_RIGHT, border=10)
        hbox2.Add(cancelButton, flag = wx.ALL | wx.ALIGN_RIGHT, border=10)

        hbox3.Add(labelText, flag= wx.EXPAND | wx.RIGHT |  wx.ALIGN_LEFT, border=10)
        hbox3.Add(self.labelTextBox, wx.EXPAND | wx.RIGHT |wx.ALIGN_LEFT , border=10)
  
        symbolStaticBoxSizer.Add(hbox1,flag = wx.ALL | wx.EXPAND,border=10)
        vbox.Add(symbolStaticBoxSizer, flag = wx.ALL | wx.EXPAND,border=10)

        vbox.Add(hbox3,flag = wx.ALL | wx.EXPAND | wx.ALIGN_RIGHT, border=10)


        vbox.Add(hbox2,flag = wx.ALL  | wx.ALIGN_RIGHT, border=10)


        panel.SetSizer(vbox)

        self.populateSymbol()
        self.populateColor()
        self.populateSize()

        self.SetDefaultItem(self.symbolListBox)

    def customSize(self,e):
        dlg = wx.TextEntryDialog(self,
                                 'Enter custom size',
                                 'Custom size',
                                 str(self.final_size))
        if(dlg.ShowModal() == wx.ID_OK):
            if(float(dlg.GetValue()) < 0):
                dial = wx.MessageDialog(None, 
                                        'Unfortunately imaginary icons are not yet supported. Please enter a positive value',
                                        'Error',
                                        wx.OK | wx.ICON_ERROR)
                dial.ShowModal()
                dlg.Destroy()
                self.customSize(e)
            else:
                self.final_size = dlg.GetValue()
                dlg.Destroy()
        else:
            dlg.Destroy()

    def setDefaults(self,size,color,symbol,label):
        self.final_size = size
        # set up gui values
        self.labelTextBox.SetValue(label)
        if(size % 1 == 0 and size > 1 and size < 11):
            self.sizeComboBox.SetSelection(int(size) - 1)
        else:
            self.sizeComboBox.SetSelection(4)
        self.symbolListBox.SetSelection(self.sorted_sym_dic[symbol])
        colorname = appearanceDialog.find_key(self.parent.get_color_label(),color)
        self.colorListBox.SetStringSelection(colorname)

    def populateSymbol(self):
        self.sorted_symbolLabels = sorted(self.symbolLabels.iteritems(),key=operator.itemgetter(1))
        self.sorted_sym_dic = {}
        i = 0
        for label in self.sorted_symbolLabels:
            self.symbolListBox.Append(str(label[0]))
            self.sorted_sym_dic[str(label[0])] = i
            i += 1

    def populateColor(self):
        sortedcolorLabels = sorted(self.colorLabels.iteritems(),key=operator.itemgetter(1))
        
        for color in sortedcolorLabels:
             self.colorListBox.Append(str(color[0]))
 
    def populateSize(self):

        for i in range(1,11):
            self.sizeComboBox.Append(str(i) + '.0')

    def combo_click(self,e):
        self.final_size = self.sizeComboBox.GetValue()

    def CloseDlg(self,e):
        self.Destroy()


    def get_symbol_label(self):
        """
        Associates label to symbol
        """
        _labels = {}
        i = 0
        _labels['Circle'] = i
        i += 1
        _labels['Cross X '] = i
        i += 1
        _labels['Triangle Down'] = i
        i += 1
        _labels['Triangle Up'] = i
        i += 1
        _labels['Triangle Left'] = i
        i += 1
        _labels['Triangle Right'] = i
        i += 1
        _labels['Cross +'] = i
        i += 1
        _labels['Square'] = i
        i += 1
        _labels['Diamond'] = i
        i += 1
        _labels['Hexagon1'] = i
        i += 1
        _labels['Hexagon2'] = i
        i += 1
        _labels['Pentagon'] = i
        i += 1
        _labels['Line'] = i
        i += 1
        _labels['Dash'] = i
        i += 1
        _labels['Vline'] = i
        i += 1
        _labels['Step'] = i
        return _labels
    
    def get_color_label(self):
        """
        Associates label to a specific color
        """
        _labels = {}
        i = 0
        _labels['Blue'] = i
        i += 1
        _labels['Green'] = i
        i += 1
        _labels['Red'] = i
        i += 1
        _labels['Cyan'] = i
        i += 1
        _labels['Magenta'] = i
        i += 1
        _labels['Yellow'] = i
        i += 1
        _labels['Black'] = i
        return _labels

    @staticmethod
    def find_key(dic,val):
        return [k for k, v in dic.iteritems() if v == val][0]
        
    def getCurrentValues(self): # returns (size,color,symbol,dataname)

        size = float(self.final_size)
        name = str(self.labelTextBox.GetValue())
        selTuple = self.symbolListBox.GetSelections()
        symbol = appearanceDialog.find_key(self.sorted_sym_dic,int(selTuple[0]))
        color = str(self.colorListBox.GetValue()) 
 
        return(size,color,symbol,name)

    def onOK(self,e):
        self.okay_clicked = True

        self.Close()
