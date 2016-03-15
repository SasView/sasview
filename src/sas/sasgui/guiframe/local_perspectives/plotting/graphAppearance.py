#!/usr/bin/python

"""

Dialog for general graph appearance

This software was developed by Institut Laue-Langevin as part of
Distributed Data Analysis of Neutron Scattering Experiments (DANSE).

Copyright 2012 Institut Laue-Langevin
"""

import wx
from sas.sasgui.plottools.SimpleFont import SimpleFont

COLOR = ['black', 'blue', 'green', 'red', 'cyan', 'magenta', 'yellow']


class graphAppearance(wx.Frame):

    def __init__(self, parent, title, legend=True):
        super(graphAppearance, self).__init__(parent, title=title, size=(520, 435))

        self.legend = legend

        self.InitUI()
        self.Centre()
        self.Show()

        self.xfont = None
        self.yfont = None
        self.is_xtick = False
        self.is_ytick = False

    def InitUI(self):

        panel = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)

        xhbox1 = wx.BoxSizer(wx.HORIZONTAL)
        xhbox2 = wx.BoxSizer(wx.HORIZONTAL)
        yhbox1 = wx.BoxSizer(wx.HORIZONTAL)
        yhbox2 = wx.BoxSizer(wx.HORIZONTAL)

        if self.legend:
            legendLocText = wx.StaticText(panel, label='Legend location: ')
            self.legend_loc_combo = wx.ComboBox(panel, style=wx.CB_READONLY, size=(180, -1))
            self.fillLegendLocs()
        else:
            self.legend_loc_combo = None

        if self.legend:
            self.toggle_legend = wx.CheckBox(panel, label='Toggle legend on/off')
        else:
            self.toggle_legend = None

        self.toggle_grid = wx.CheckBox(panel, label='Toggle grid on/off')

        xstatic_box = wx.StaticBox(panel, -1, 'x-axis label')
        xstatic_box_sizer = wx.StaticBoxSizer(xstatic_box, wx.VERTICAL)
        ystatic_box = wx.StaticBox(panel, -1, 'y-axis label')
        ystatic_box_sizer = wx.StaticBoxSizer(ystatic_box, wx.VERTICAL)

        xaxis_label = wx.StaticText(panel, label='X-axis: ')
        yaxis_label = wx.StaticText(panel, label='Y-axis: ')
        unitlabel_1 = wx.StaticText(panel, label='Units: ')
        unitlabel_2 = wx.StaticText(panel, label='Units: ')

        self.xaxis_text = wx.TextCtrl(panel, -1, "", size=(220, -1))
        self.yaxis_text = wx.TextCtrl(panel, -1, "", size=(220, -1))

        self.xaxis_unit_text = wx.TextCtrl(panel, -1, "", size=(100, -1))
        self.yaxis_unit_text = wx.TextCtrl(panel, -1, "", size=(100, -1))

        xcolorLabel = wx.StaticText(panel, label='Font color: ')
        self.xfont_color = wx.ComboBox(panel, size=(100, -1), style=wx.CB_READONLY)
        self.xfill_colors()
        self.xfont_color.SetSelection(0)
        xfont_button = wx.Button(panel, label='Font')
        xfont_button.Bind(wx.EVT_BUTTON, self.on_x_font)

        ycolorLabel = wx.StaticText(panel, label='Font color: ')
        self.yfont_color = wx.ComboBox(panel, size=(100, -1), style=wx.CB_READONLY)
        self.yfill_colors()
        self.yfont_color.SetSelection(0)
        yfont_button = wx.Button(panel, label='Font')
        yfont_button.Bind(wx.EVT_BUTTON, self.on_y_font)

        self.cancel_button = wx.Button(panel, label='Cancel')
        self.ok_button = wx.Button(panel, label='OK')

        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.ok_button.Bind(wx.EVT_BUTTON, self.on_ok)

        xhbox1.Add(xaxis_label, flag=wx.ALL | wx.EXPAND | wx.ALIGN_LEFT, border=10)
        xhbox1.Add(self.xaxis_text, flag=wx.ALL | wx.EXPAND | wx.ALIGN_LEFT, border=10)
        xhbox1.Add(unitlabel_1, flag=wx.ALL | wx.EXPAND | wx.ALIGN_RIGHT, border=10)
        xhbox1.Add(self.xaxis_unit_text, flag=wx.ALL | wx.EXPAND | wx.ALIGN_RIGHT, border=10)

        yhbox1.Add(yaxis_label, flag=wx.ALL | wx.EXPAND | wx.ALIGN_LEFT, border=10)
        yhbox1.Add(self.yaxis_text, flag=wx.ALL | wx.EXPAND | wx.ALIGN_LEFT, border=10)
        yhbox1.Add(unitlabel_2, flag=wx.ALL | wx.EXPAND | wx.ALIGN_RIGHT, border=10)
        yhbox1.Add(self.yaxis_unit_text, flag=wx.ALL | wx.EXPAND | wx.ALIGN_RIGHT, border=10)

        xhbox2.Add(xcolorLabel, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
        xhbox2.Add(self.xfont_color, flag=wx.ALL | wx.ALIGN_RIGHT, border=5)
        xhbox2.Add(xfont_button, flag=wx.ALL | wx.ALIGN_RIGHT, border=5)

        yhbox2.Add(ycolorLabel, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
        yhbox2.Add(self.yfont_color, flag=wx.ALL | wx.ALIGN_RIGHT, border=5)
        yhbox2.Add(yfont_button, flag=wx.ALL | wx.ALIGN_RIGHT, border=5)

        if self.legend:
            hbox1.Add(legendLocText, flag=wx.ALL | wx.EXPAND | wx.ALIGN_LEFT, border=5)
            hbox1.Add(self.legend_loc_combo, flag=wx.ALL | wx.EXPAND | wx.ALIGN_LEFT, border=5)

        if self.legend:
            hbox1.Add((5, -1))
            hbox1.Add(self.toggle_legend, flag=wx.ALL | wx.EXPAND | wx.ALIGN_LEFT, border=5)

        hbox2.Add(self.ok_button, flag=wx.ALL | wx.ALIGN_RIGHT, border=5)
        hbox2.Add(self.cancel_button, flag=wx.ALL | wx.ALIGN_RIGHT, border=5)
        hbox2.Add((15, -1))

        xstatic_box_sizer.Add(xhbox1, flag=wx.EXPAND, border=5)
        xstatic_box_sizer.Add(xhbox2, flag=wx.ALL | wx.ALIGN_RIGHT, border=5)
        ystatic_box_sizer.Add(yhbox1, flag=wx.EXPAND, border=5)
        ystatic_box_sizer.Add(yhbox2, flag=wx.ALL | wx.ALIGN_RIGHT, border=5)

        vbox.Add((-1, 20))
        vbox.Add(hbox1, flag=wx.EXPAND | wx.ALL, border=5)
        vbox.Add(xstatic_box_sizer, flag=wx.ALL | wx.EXPAND, border=10)
        vbox.Add(ystatic_box_sizer, flag=wx.ALL | wx.EXPAND, border=10)

        vbox.Add(self.toggle_grid, flag=wx.ALIGN_RIGHT | wx.RIGHT, border=20)
        vbox.Add(hbox2, flag=wx.ALIGN_RIGHT | wx.ALL, border=5)

        panel.SetSizer(vbox)

    def xfill_colors(self):
        c_list = COLOR
        for idx in range(len(c_list)):
            self.xfont_color.Append(c_list[idx], idx)

    def yfill_colors(self):
        c_list = COLOR
        for idx in range(len(c_list)):
            self.yfont_color.Append(c_list[idx], idx)

    def on_x_font(self, e):
        title = 'Modify x axis font'

        fonty = SimpleFont(self, wx.NewId(), title)
        fonty.set_default_font(self.xfont)
        fonty.set_ticklabel_check(self.is_xtick)
        if fonty.ShowModal() == wx.ID_OK:
            self.xfont = fonty.get_font()
            self.is_xtick = fonty.get_ticklabel_check()

    def on_y_font(self, e):
        title = 'Modify y axis font'
        fonty = SimpleFont(self, wx.NewId(), title)
        fonty.set_default_font(self.yfont)
        fonty.set_ticklabel_check(self.is_ytick)
        if fonty.ShowModal() == wx.ID_OK:
            self.yfont = fonty.get_font()
            self.is_ytick = fonty.get_ticklabel_check()

    def on_ok(self, e):
        self.Close()

    def on_cancel(self, e):
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
        #     self.legend_loc_combo.Append(label)
        for label in self.get_loc_label():
            self.legend_loc_combo.Append(label)


    def setDefaults(self, grid, legend, xlab, ylab, xunit, yunit,
                    xaxis_font, yaxis_font, legend_loc,
                    xcolor, ycolor, is_xtick, is_ytick):
        self.toggle_grid.SetValue(grid)
        if self.legend:
            self.toggle_legend.SetValue(legend)
        self.xaxis_text.SetValue(xlab)
        self.yaxis_text.SetValue(ylab)
        self.xaxis_unit_text.SetValue(xunit)
        self.yaxis_unit_text.SetValue(yunit)
        self.xfont = xaxis_font
        self.yfont = yaxis_font
        self.is_xtick = is_xtick
        self.is_ytick = is_ytick

        if not xcolor:
            self.xfont_color.SetSelection(0)
        else:
            self.xfont_color.SetStringSelection(xcolor)

        if not ycolor:
            self.yfont_color.SetSelection(0)
        else:
            self.yfont_color.SetStringSelection(ycolor)


        if self.legend:
            self.legend_loc_combo.SetStringSelection(legend_loc)


    # get whether grid is toggled on/off
    def get_togglegrid(self):
        return self.toggle_grid.GetValue()

    # get whether legend is toggled on/off
    def get_togglelegend(self):
        return self.toggle_legend.GetValue()

    # get x label
    def get_xlab(self):
        return self.xaxis_text.GetValue()

    # get y label
    def get_ylab(self):
        return self.yaxis_text.GetValue()

    # get x unit
    def get_xunit(self):
        return self.xaxis_unit_text.GetValue()

    # get y unit
    def get_yunit(self):
        return self.yaxis_unit_text.GetValue()

    # get legend location
    def get_legend_loc(self):
        return self.get_loc_label()[self.legend_loc_combo.GetStringSelection()]

    # get x axis label color
    def get_xcolor(self):
        return self.xfont_color.GetValue()

    # get y axis label color
    def get_ycolor(self):
        return self.yfont_color.GetValue()

    # get x axis font (type is FontProperties)
    def get_xfont(self):
        return self.xfont

    # get y axis font
    def get_yfont(self):
        return self.yfont

    def get_xtick_check(self):
        return self.is_xtick

    def get_ytick_check(self):
        return self.is_ytick


if __name__ == '__main__':

    app = wx.App()
    graphD = graphAppearance(None, title='Modify graph appearance')
    app.MainLoop()



