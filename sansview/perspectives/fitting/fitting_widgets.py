
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################


import wx
from wx.lib.scrolledpanel import ScrolledPanel

WIDTH = 400
HEIGHT = 300
MAX_NBR_DATA = 4

class DataDialog(wx.Dialog):
    """
    Allow file selection at loading time
    """
    def __init__(self, data_list, parent=None, text='',
                 nb_data=MAX_NBR_DATA, *args, **kwds):
        wx.Dialog.__init__(self, parent, *args, **kwds)
        self.SetTitle("Data Selection")
        self._max_data = nb_data
        self._nb_selected_data = nb_data
        
        self.SetSize((WIDTH, HEIGHT))
        self.list_of_ctrl = []
        if not data_list:
            return 
        select_data_text = " %s Data selected.\n" % str(self._nb_selected_data)
        self._data_text_ctrl = wx.StaticText(self, -1, str(select_data_text))
        self._data_text_ctrl.SetForegroundColour('blue')
        self._sizer_main = wx.BoxSizer(wx.VERTICAL)
        self._sizer_txt = wx.BoxSizer(wx.VERTICAL)
        self._sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        self._choice_sizer = wx.GridBagSizer(5, 5)
        self._panel = ScrolledPanel(self, style=wx.RAISED_BORDER,
                               size=(WIDTH-20, HEIGHT-50))
        self._panel.SetupScrolling()
        self.__do_layout(data_list, text=text)
        
    def __do_layout(self, data_list, text=''):
        """
        layout the dialog
        """
        if not data_list or len(data_list) <= 1:
            return 
        #add text
        if text.strip() == "":
            text = "Fitting: We recommend that you selected"
            text += " no more than '%s' data\n" % str(self._max_data)
            text += "for adequate plot display size. \n" 
            text += "unchecked data won't be send to fitting . \n" 
        text_ctrl = wx.StaticText(self, -1, str(text))
        self._sizer_txt.Add(text_ctrl)
        iy = 0
        ix = 0
        data_count = 0
        for i in range(len(data_list)):
            data_count += 1
            cb = wx.CheckBox(self._panel, -1, str(data_list[i].name), (10, 10))
            wx.EVT_CHECKBOX(self, cb.GetId(), self._count_selected_data)
            if data_count <= MAX_NBR_DATA:
                cb.SetValue(True)
            else:
                cb.SetValue(False)
            self.list_of_ctrl.append((cb, data_list[i]))
            self._choice_sizer.Add(cb, (iy, ix),
                           (1, 1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
            iy += 1
        self._panel.SetSizer(self._choice_sizer)
        #add sizer
        self._sizer_button.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        button_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self._sizer_button.Add(button_cancel, 0,
                          wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        button_OK = wx.Button(self, wx.ID_OK, "Ok")
        button_OK.SetFocus()
        self._sizer_button.Add(button_OK, 0,
                                wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        static_line = wx.StaticLine(self, -1)
        
        self._sizer_txt.Add(self._panel, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
        self._sizer_main.Add(self._sizer_txt, 1, wx.EXPAND|wx.ALL, 10)
        self._sizer_main.Add(self._data_text_ctrl, 0, 
                             wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
        self._sizer_main.Add(static_line, 0, wx.EXPAND, 0)
        self._sizer_main.Add(self._sizer_button, 0, wx.EXPAND|wx.ALL, 10)
        self.SetSizer(self._sizer_main)
        self.Layout()
        
    def get_data(self):
        """
        return the selected data
        """
        temp = []
        for item in self.list_of_ctrl:
            cb, data = item
            if cb.GetValue():
                temp.append(data)
        return temp
    
    def _count_selected_data(self, event):
        """
        count selected data
        """
        if event.GetEventObject().GetValue():
            self._nb_selected_data += 1
        else:
            self._nb_selected_data -= 1
        select_data_text = " %s Data selected.\n" % str(self._nb_selected_data)
        self._data_text_ctrl.SetLabel(select_data_text)
        if self._nb_selected_data <= self._max_data:
            self._data_text_ctrl.SetForegroundColour('blue')
        else:
            self._data_text_ctrl.SetForegroundColour('red')
        
       