
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

MAX_NBR_DATA = 4
WIDTH = 430
HEIGHT = 350


class DialogPanel(ScrolledPanel):
    def __init__(self, *args, **kwds):
        ScrolledPanel.__init__(self, *args, **kwds)
        self.SetupScrolling()


class BatchDataDialog(wx.Dialog):
    """
    The current design of Batch  fit allows only of type of data in the data
    set. This allows the user to make a quick selection of the type of data
    to use in fit tab.
    """
    def __init__(self, parent=None, *args, **kwds):
        wx.Dialog.__init__(self, parent, *args, **kwds)
        self.SetSize((WIDTH, HEIGHT))
        self.data_1d_selected = None
        self.data_2d_selected = None
        self._do_layout()

    def _do_layout(self):
        """
        Draw the content of the current dialog window
        """
        vbox = wx.BoxSizer(wx.VERTICAL)
        box_description = wx.StaticBox(self, wx.ID_ANY, str("Hint"))
        hint_sizer = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        selection_sizer = wx.GridBagSizer(5, 5)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.data_1d_selected = wx.RadioButton(self, wx.ID_ANY, 'Data1D',
                                                style=wx.RB_GROUP)
        self.data_2d_selected = wx.RadioButton(self, wx.ID_ANY, 'Data2D')
        self.data_1d_selected.SetValue(True)
        self.data_2d_selected.SetValue(False)
        button_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        button_OK = wx.Button(self, wx.ID_OK, "Ok")
        button_OK.SetFocus()
        hint = "Selected Data set contains both 1D and 2D Data.\n"
        hint += "Please select on type of analysis before proceeding.\n"
        hint_sizer.Add(wx.StaticText(self, wx.ID_ANY, hint))
        #draw area containing radio buttons
        ix = 0
        iy = 0
        selection_sizer.Add(self.data_1d_selected, (iy, ix),
                           (1, 1), wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        iy += 1
        selection_sizer.Add(self.data_2d_selected, (iy, ix),
                           (1, 1), wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        #contruction the sizer contaning button
        button_sizer.Add((20, 20), 1, wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        button_sizer.Add(button_cancel, 0,
                         wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 10)
        button_sizer.Add(button_OK, 0,
                                wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 10)
        vbox.Add(hint_sizer, 0, wx.EXPAND | wx.ALL, 10)
        vbox.Add(selection_sizer, 0, wx.TOP | wx.BOTTOM, 10)
        vbox.Add(wx.StaticLine(self, wx.ID_ANY), 0, wx.EXPAND, 0)
        vbox.Add(button_sizer, 0, wx.TOP | wx.BOTTOM, 10)
        self.SetSizer(vbox)
        self.Layout()

    def get_data(self):
        """
        return 1 if  user requested Data1D , 2 if user requested Data2D
        """
        if self.data_1d_selected.GetValue():
            return 1
        else:
            return 2


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
        self._data_text_ctrl = wx.StaticText(self, wx.ID_ANY, str(select_data_text))

        self._data_text_ctrl.SetForegroundColour('blue')
        self._sizer_main = wx.BoxSizer(wx.VERTICAL)
        self._sizer_txt = wx.BoxSizer(wx.VERTICAL)
        self._sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        self._choice_sizer = wx.GridBagSizer(5, 5)
        self._panel = DialogPanel(self, style=wx.RAISED_BORDER,
                               size=(WIDTH - 20, HEIGHT / 3))
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
        text_ctrl = wx.StaticText(self, wx.ID_ANY, str(text))
        self._sizer_txt.Add(text_ctrl)
        iy = 0
        ix = 0
        data_count = 0
        for i in range(len(data_list)):
            data_count += 1
            cb = wx.CheckBox(self._panel, wx.ID_ANY, str(data_list[i].name), (10, 10))
            wx.EVT_CHECKBOX(self, cb.GetId(), self._count_selected_data)
            if data_count <= MAX_NBR_DATA:
                cb.SetValue(True)
            else:
                cb.SetValue(False)
            self.list_of_ctrl.append((cb, data_list[i]))
            self._choice_sizer.Add(cb, (iy, ix),
                           (1, 1), wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            iy += 1
        self._panel.SetSizer(self._choice_sizer)
        #add sizer
        self._sizer_button.Add((20, 20), 1, wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        button_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self._sizer_button.Add(button_cancel, 0,
                          wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 10)
        button_OK = wx.Button(self, wx.ID_OK, "Ok")
        button_OK.SetFocus()
        self._sizer_button.Add(button_OK, 0,
                                wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 10)
        static_line = wx.StaticLine(self, wx.ID_ANY)
        self._sizer_txt.Add(self._panel, 0, wx.EXPAND | wx.ALL, 10)
        self._sizer_main.Add(self._sizer_txt, 0, wx.EXPAND | wx.ALL, 10)
        self._sizer_main.Add(self._data_text_ctrl, 0, wx.EXPAND | wx.ALL, 10)
        self._sizer_main.Add(static_line, 0, wx.EXPAND, 0)
        self._sizer_main.Add(self._sizer_button, 0, wx.EXPAND | wx.ALL, 10)
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
