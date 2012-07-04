#!/usr/bin/python

"""

Dialog for general graph appearance


/**
	This software was developed by Institut Laue-Langevin as part of
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE).

	Copyright 2012 Institut Laue-Langevin

**/


"""

import wx
from matplotlib.font_manager import FontProperties
from danse.common.plottools.SimpleFont import SimpleFont

COLOR = ['black', 'blue', 'green', 'red', 'cyan', 'magenta', 'yellow']


class graphAppearance(wx.Frame):

    def __init__(self,parent,title):
        super(graphAppearance,self).__init__(parent, title=title,size=(520,435))

        self.InitUI()
        self.Centre()
        self.Show()

        self.xfont = None
        self.yfont = None


    def InitUI(self):

        panel = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)

        xhbox1 = wx.BoxSizer(wx.HORIZONTAL)
        xhbox2 = wx.BoxSizer(wx.HORIZONTAL)
        yhbox1 = wx.BoxSizer(wx.HORIZONTAL)
        yhbox2 = wx.BoxSizer(wx.HORIZONTAL)


        legendLocText = wx.StaticText(panel, label='Legend location: ')
        self.legendLocCombo = wx.ComboBox(panel,style = wx.CB_READONLY, size=(180,-1))
        self.fillLegendLocs()

        self.toggleLegend = wx.CheckBox(panel, label='Toggle legend on/off')
        self.toggleGrid = wx.CheckBox(panel, label='Toggle grid on/off')

        
        xStaticBox = wx.StaticBox(panel,-1, 'x-axis label')
        xStaticBoxSizer = wx.StaticBoxSizer(xStaticBox, wx.VERTICAL)
        yStaticBox = wx.StaticBox(panel,-1, 'y-axis label')
        yStaticBoxSizer = wx.StaticBoxSizer(yStaticBox, wx.VERTICAL)


        xaxisLabel = wx.StaticText(panel, label='X-axis: ')
        yaxisLabel = wx.StaticText(panel, label='Y-axis: ')
        unitLabel1 = wx.StaticText(panel, label='Units: ')
        unitLabel2 = wx.StaticText(panel, label='Units: ')

        self.xaxisText = wx.TextCtrl(panel,-1,"",size=(220,-1))
        self.yaxisText = wx.TextCtrl(panel,-1,"",size=(220,-1))

        self.xaxisUnitText = wx.TextCtrl(panel,-1,"",size=(100,-1))
        self.yaxisUnitText = wx.TextCtrl(panel,-1,"",size=(100,-1))



        xcolorLabel = wx.StaticText(panel, label='Font color: ')
        self.xfontColor = wx.ComboBox(panel,size=(100,-1),style=wx.CB_READONLY)
        self.xfillColors()
        self.xfontColor.SetSelection(0)
        xfontButton = wx.Button(panel, label='Font')
        xfontButton.Bind(wx.EVT_BUTTON,self.onxFont)

        ycolorLabel = wx.StaticText(panel, label='Font color: ')
        self.yfontColor = wx.ComboBox(panel,size=(100,-1),style=wx.CB_READONLY)
        self.yfillColors()
        self.yfontColor.SetSelection(0)
        yfontButton = wx.Button(panel, label='Font')
        yfontButton.Bind(wx.EVT_BUTTON,self.onyFont)

        

        self.cancelButton = wx.Button(panel, label='Cancel')
        self.okButton = wx.Button(panel, label='OK')

        self.cancelButton.Bind(wx.EVT_BUTTON,self.onCancel)
        self.okButton.Bind(wx.EVT_BUTTON,self.onOK)


        xhbox1.Add(xaxisLabel,flag= wx.ALL | wx.EXPAND  | wx.ALIGN_LEFT,border=10)
        xhbox1.Add(self.xaxisText,flag=wx.ALL | wx.EXPAND  | wx.ALIGN_LEFT,border=10)
        xhbox1.Add(unitLabel1,flag=wx.ALL | wx.EXPAND  | wx.ALIGN_RIGHT,border=10)
        xhbox1.Add(self.xaxisUnitText, flag=wx.ALL | wx.EXPAND  | wx.ALIGN_RIGHT,border=10)

        yhbox1.Add(yaxisLabel,flag= wx.ALL | wx.EXPAND  | wx.ALIGN_LEFT,border=10)
        yhbox1.Add(self.yaxisText,flag=wx.ALL | wx.EXPAND  | wx.ALIGN_LEFT,border=10)
        yhbox1.Add(unitLabel2,flag=wx.ALL | wx.EXPAND  | wx.ALIGN_RIGHT,border=10)
        yhbox1.Add(self.yaxisUnitText, flag=wx.ALL | wx.EXPAND  | wx.ALIGN_RIGHT,border=10)

        xhbox2.Add(xcolorLabel,flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
        xhbox2.Add(self.xfontColor,flag=wx.ALL | wx.ALIGN_RIGHT, border=5)
        xhbox2.Add(xfontButton,flag=wx.ALL | wx.ALIGN_RIGHT, border=5)

        yhbox2.Add(ycolorLabel,flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
        yhbox2.Add(self.yfontColor,flag=wx.ALL | wx.ALIGN_RIGHT, border=5)
        yhbox2.Add(yfontButton,flag=wx.ALL | wx.ALIGN_RIGHT, border=5)


        hbox1.Add(legendLocText, flag =  wx.ALL | wx.EXPAND  | wx.ALIGN_LEFT, border=5)
        hbox1.Add(self.legendLocCombo, flag =  wx.ALL | wx.EXPAND  | wx.ALIGN_LEFT, border=5)
        hbox1.Add((5,-1))
        hbox1.Add(self.toggleLegend, flag = wx.ALL | wx.EXPAND  | wx.ALIGN_LEFT, border=5)

        hbox2.Add(self.okButton, flag = wx.ALL | wx.ALIGN_RIGHT, border=5)
        hbox2.Add(self.cancelButton, flag = wx.ALL | wx.ALIGN_RIGHT, border=5)
        hbox2.Add((15,-1))

        xStaticBoxSizer.Add(xhbox1,flag= wx.EXPAND ,border=5)
        xStaticBoxSizer.Add(xhbox2, flag=wx.ALL | wx.ALIGN_RIGHT, border=5)
        yStaticBoxSizer.Add(yhbox1,flag= wx.EXPAND ,border=5)
        yStaticBoxSizer.Add(yhbox2, flag=wx.ALL | wx.ALIGN_RIGHT, border=5)

        vbox.Add((-1,20))
        vbox.Add(hbox1, flag = wx.EXPAND | wx.ALL, border=5)
        vbox.Add(xStaticBoxSizer, flag = wx.ALL | wx.EXPAND, border=10)
        vbox.Add(yStaticBoxSizer, flag = wx.ALL | wx.EXPAND, border=10)

        vbox.Add(self.toggleGrid, flag = wx.ALIGN_RIGHT | wx.RIGHT, border=20)
        vbox.Add(hbox2, flag = wx.ALIGN_RIGHT | wx.ALL , border=5)


        panel.SetSizer(vbox)

    def xfillColors(self):
        list = COLOR
        for idx in range(len(list)):
            self.xfontColor.Append(list[idx],idx)

    def yfillColors(self):
        list = COLOR
        for idx in range(len(list)):
            self.yfontColor.Append(list[idx],idx)

    def onxFont(self,e):
        title = 'Modify x axis font'

        fonty = SimpleFont(self,wx.NewId(),title)
        fonty.set_default_font(self.xfont)
        if(fonty.ShowModal() == wx.ID_OK):
            self.xfont = fonty.get_font()

    def onyFont(self,e):
        title = 'Modify y axis font'
        fonty = SimpleFont(self,wx.NewId(),title)
        fonty.set_default_font(self.yfont)
        if(fonty.ShowModal() == wx.ID_OK):
            self.yfont = fonty.get_font()

    def onOK(self,e):
        self.Close()

    def onCancel(self, e):
        self.Destroy()


    def get_loc_label(self):
        """
        Associates label to a specific legend location
        """
        _labels = {}
        i = 0
        _labels['best'] = i
        i += 1
        _labels['upper right'] = i
        i += 1
        _labels['upper left'] = i
        i += 1
        _labels['lower left'] = i
        i += 1
        _labels['lower right'] = i
        i += 1
        _labels['right'] = i
        i += 1
        _labels['center left'] = i
        i += 1
        _labels['center right'] = i
        i += 1
        _labels['lower center'] = i
        i += 1
        _labels['upper center'] = i
        i += 1
        _labels['center'] = i
        return _labels


    def fillLegendLocs(self):

        # labels = []
        # for label in self.get_loc_label():
        #     labels.append(str(label))

        # for label in reversed(labels):
        #     self.legendLocCombo.Append(label)
        for label in self.get_loc_label():
            self.legendLocCombo.Append(label)


    def setDefaults(self,grid,legend,xlab,ylab,xunit,yunit,
                    xaxis_font,yaxis_font,legend_loc,
                    xcolor,ycolor):
        self.toggleGrid.SetValue(grid)
        self.toggleLegend.SetValue(legend)
        self.xaxisText.SetValue(xlab)
        self.yaxisText.SetValue(ylab)
        self.xaxisUnitText.SetValue(xunit)
        self.yaxisUnitText.SetValue(yunit)
        self.xfont = xaxis_font
        self.yfont = yaxis_font

        if not xcolor:
            self.xfontColor.SetSelection(0)
        else:
            self.xfontColor.SetStringSelection(xcolor)

        if not ycolor:
            self.yfontColor.SetSelection(0)
        else:
            self.yfontColor.SetStringSelection(ycolor)
            

        
        self.legendLocCombo.SetStringSelection(legend_loc)


    def getAppInfo(self):
        grid_on = self.toggleGrid.GetValue()
        legend_on = self.toggleLegend.GetValue()
        xlab = self.xaxisText.GetValue()
        ylab = self.yaxisText.GetValue()
        xunit = self.xaxisUnitText.GetValue()
        yunit = self.yaxisUnitText.GetValue()
        legend_loc = self.get_loc_label()[self.legendLocCombo.GetStringSelection()]
        xcolor = self.xfontColor.GetValue()
        ycolor = self.yfontColor.GetValue()


        return [grid_on,legend_on,xlab,ylab,xunit,yunit,
                self.xfont,self.yfont,
                xcolor,ycolor,legend_loc]



if __name__ == '__main__':

    app = wx.App()
    graphD = graphAppearance(None,title='Modify graph appearance')
    app.MainLoop()



