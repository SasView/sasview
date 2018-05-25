"""
GUI for the data operations panel (sum and multiply)
"""
import wx
import sys
import time
import numpy as np
from sas.sascalc.dataloader.data_info import Data1D
from sas.sasgui.plottools.PlotPanel import PlotPanel
from sas.sasgui.plottools.plottables import Graph
from sas.sasgui.plottools import transform
from matplotlib.font_manager import FontProperties
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.perspectives.calculator import calculator_widgets as widget
from sas.sasgui.guiframe.documentation_window import DocumentationWindow

#Control panel width
if sys.platform.count("win32") > 0:
    PANEL_TOP = 0
    PANEL_WIDTH = 790
    PANEL_HEIGTH = 370
    FONT_VARIANT = 0
    _BOX_WIDTH = 200
    ON_MAC = False
else:
    PANEL_TOP = 60
    _BOX_WIDTH = 230
    PANEL_WIDTH = 900
    PANEL_HEIGTH = 430
    FONT_VARIANT = 1
    ON_MAC = True

class DataOperPanel(wx.ScrolledWindow):
    """
    """
    def __init__(self, parent, *args, **kwds):
        kwds['name'] = "Data Operation"
        kwds["size"] = (PANEL_WIDTH, PANEL_HEIGTH)
        wx.ScrolledWindow.__init__(self, parent, *args, **kwds)
        self.parent = parent
        #sizers etc.
        self.main_sizer = None
        self.name_sizer = None
        self.button_sizer = None
        self.data_namectr = None
        self.numberctr = None
        self.data1_cbox = None
        self.operator_cbox = None
        self.data2_cbox = None
        self.data_title_tcl = None
        self.out_pic = None
        self.equal_pic = None
        self.data1_pic = None
        self.operator_pic = None
        self.data2_pic = None
        self.output = None
        self._notes = None
        #text grayed color
        self.color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BACKGROUND)
        #data
        self._data = self.get_datalist()
        self._do_layout()
        self.fill_data_combox()
        self.fill_oprator_combox()
        self.Bind(wx.EVT_SET_FOCUS, self.set_panel_on_focus)

    def _define_structure(self):
        """
        define initial sizer
        """
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        title = "Data Operation "
        title += "[ + (add); - (subtract); "
        title += "* (multiply); / (divide); "
        title += "| (append) ]"
        name_box = wx.StaticBox(self, -1, title)
        self.name_sizer = wx.StaticBoxSizer(name_box, wx.HORIZONTAL)
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

    def _layout_name(self):
        """
        Do the layout for data name related widgets
        """
        new_data_sizer = wx.BoxSizer(wx.VERTICAL)
        equal_sizer = wx.BoxSizer(wx.VERTICAL)
        old_data1_sizer = wx.BoxSizer(wx.VERTICAL)
        operator_sizer = wx.BoxSizer(wx.VERTICAL)
        old_data2_sizer = wx.BoxSizer(wx.VERTICAL)
        data2_hori_sizer = wx.BoxSizer(wx.HORIZONTAL)
        data_name = wx.StaticText(self, -1, 'Output Data Name')
        equal_name = wx.StaticText(self, -1, ' =', size=(50, 25))
        data1_name = wx.StaticText(self, -1, 'Data1')
        operator_name = wx.StaticText(self, -1, 'Operator')
        data2_name = wx.StaticText(self, -1, 'Data2 (or Number)')
        self.data_namectr = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, 25), style=wx.TE_PROCESS_ENTER)
        self.data_namectr.SetToolTipString("Hit 'Enter' key after typing.")
        self.data_namectr.SetValue(str('MyNewDataName'))
        self.numberctr = wx.TextCtrl(self, -1, size=(_BOX_WIDTH / 3, 25), style=wx.TE_PROCESS_ENTER)
        self.numberctr.SetToolTipString("Hit 'Enter' key after typing.")
        self.numberctr.SetValue(str(1.0))
        self.data1_cbox = wx.ComboBox(self, -1, size=(_BOX_WIDTH, 25),
                                      style=wx.CB_READONLY)
        self.operator_cbox = wx.ComboBox(self, -1, size=(70, 25),
                                         style=wx.CB_READONLY)
        operation_tip = "Add: +, Subtract: -, "
        operation_tip += "Multiply: *, Divide: /, "
        operation_tip += "Append(Combine): | "
        self.operator_cbox.SetToolTipString(operation_tip)
        self.data2_cbox = wx.ComboBox(self, -1, size=(_BOX_WIDTH * 2 / 3, 25),
                                       style=wx.CB_READONLY)

        self.out_pic = SmallPanel(self, -1, True,
                                    size=(_BOX_WIDTH, _BOX_WIDTH),
                                    style=wx.NO_BORDER)
        self.equal_pic = SmallPanel(self, -1, True, '=',
                                    size=(50, _BOX_WIDTH),
                                    style=wx.NO_BORDER)
        self.data1_pic = SmallPanel(self, -1, True,
                                    size=(_BOX_WIDTH, _BOX_WIDTH),
                                    style=wx.NO_BORDER)
        self.operator_pic = SmallPanel(self, -1, True, '+',
                                    size=(70, _BOX_WIDTH),
                                    style=wx.NO_BORDER)
        self.data2_pic = SmallPanel(self, -1, True,
                                    size=(_BOX_WIDTH, _BOX_WIDTH),
                                    style=wx.NO_BORDER)
        for ax in self.equal_pic.axes:
            ax.set_frame_on(False)
        for ax in self.operator_pic.axes:
            ax.set_frame_on(False)

        new_data_sizer.AddMany([(data_name, 0, wx.LEFT, 3),
                                       (self.data_namectr, 0, wx.LEFT, 3),
                                       (self.out_pic, 0, wx.LEFT, 3)])
        equal_sizer.AddMany([(13, 13), (equal_name, 0, wx.LEFT, 3),
                                       (self.equal_pic, 0, wx.LEFT, 3)])
        old_data1_sizer.AddMany([(data1_name, 0, wx.LEFT, 3),
                                       (self.data1_cbox, 0, wx.LEFT, 3),
                                       (self.data1_pic, 0, wx.LEFT, 3)])
        operator_sizer.AddMany([(operator_name, 0, wx.LEFT, 3),
                                 (self.operator_cbox, 0, wx.LEFT, 3),
                                 (self.operator_pic, 0, wx.LEFT, 3)])
        data2_hori_sizer.AddMany([(self.data2_cbox, 0, wx.LEFT, 0),
                                       (self.numberctr, 0, wx.RIGHT, 0)])
        old_data2_sizer.AddMany([(data2_name, 0, wx.LEFT, 3),
                                       (data2_hori_sizer, 0, wx.LEFT, 3),
                                       (self.data2_pic, 0, wx.LEFT, 3)])
        self.name_sizer.AddMany([(new_data_sizer, 0, wx.LEFT | wx.TOP, 5),
                                       (equal_sizer, 0, wx.TOP, 5),
                                       (old_data1_sizer, 0, wx.TOP, 5),
                                       (operator_sizer, 0, wx.TOP, 5),
                                       (old_data2_sizer, 0, wx.TOP, 5)])
        self.data2_cbox.Show(True)

        self._show_numctrl(self.numberctr, False)

        wx.EVT_TEXT_ENTER(self.data_namectr, -1, self.on_name)
        wx.EVT_TEXT(self.numberctr, -1, self.on_number)
        wx.EVT_COMBOBOX(self.data1_cbox, -1, self.on_select_data1)
        wx.EVT_COMBOBOX(self.operator_cbox, -1, self.on_select_operator)
        wx.EVT_COMBOBOX(self.data2_cbox, -1, self.on_select_data2)

    def _show_numctrl(self, ctrl, enable=True):
        """
        Show/Hide on Win
        Enable/Disable on MAC
        """
        if ON_MAC:
            ctrl.Enable(enable)
            children = ctrl.GetChildren()
            if len(children) > 0:
                ctrl.GetChildren()[0].SetBackGroundColour(self.color)
            if enable:
                wx.EVT_TEXT_ENTER(self.numberctr, -1, self.on_number)
        else:
            if not ctrl.IsEnabled():
                ctrl.Enable(True)
            ctrl.Show(enable)

    def on_name(self, event=None):
        """
        On data name typing
        """
        if event is not None:
            event.Skip()
        item = event.GetEventObject()
        if item.IsEnabled():
            self._set_textctrl_color(item, 'white')
        else:
            self._set_textctrl_color(item, self.color)
        text = item.GetValue().strip()
        self._check_newname(text)

    def _check_newname(self, name=None):
        """
        Check name ctr strings
        """
        self.send_warnings('')
        msg = ''
        if name is None:
            text = self.data_namectr.GetValue().strip()
        else:
            text = name
        state_list = list(self.get_datalist().values())
        name_list = []
        for state in state_list:
            if state.data is None:
                theory_list = state.get_theory()
                theory, _ = list(theory_list.values())[0]
                d_name = str(theory.name)
            else:
                d_name = str(state.data.name)
            name_list.append(d_name)
        if text in name_list:
            self._set_textctrl_color(self.data_namectr, 'pink')
            msg = "DataOperation: The name already exists."
        if len(text) == 0:
            self._set_textctrl_color(self.data_namectr, 'pink')
            msg = "DataOperation: Type the data name first."
        if self._notes:
            self.send_warnings(msg, 'error')
        self.name_sizer.Layout()
        self.Refresh()

    def _set_textctrl_color(self, ctrl, color):
        """
        Set TextCtrl color
        """
        if ON_MAC:
            children = ctrl.GetChildren()
            if len(children) > 0:
                children[0].SetBackgroundColour(color)
        else:
            ctrl.SetBackgroundColour(color)
        self.name_sizer.Layout()

    def on_number(self, event=None, control=None):
        """
        On selecting Number for Data2
        """
        self.send_warnings('')
        item = control
        if item is None and event is not None:
            item = event.GetEventObject()
        elif item is None:
            raise ValueError("Event or control must be supplied")
        text = item.GetValue().strip()
        if self.numberctr.IsShown():
            if self.numberctr.IsEnabled():
                self._set_textctrl_color(self.numberctr, 'white')
                try:
                    val = float(text)
                    pos = self.data2_cbox.GetCurrentSelection()
                    self.data2_cbox.SetClientData(pos, val)
                except:
                    self._set_textctrl_color(self.numberctr, 'pink')
                    if event is None:
                        msg = "DataOperation: Number requires a float number."
                        self.send_warnings(msg, 'error')
                    return False
            else:
                self._set_textctrl_color(self.numberctr, self.color)

        self.put_text_pic(self.data2_pic, content=str(val))
        self.check_data_inputs()
        if self.output is not None:
            self.output.name = str(self.data_namectr.GetValue())
        self.draw_output(self.output)
        self.Refresh()
        return True

    def on_select_data1(self, event=None):
        """
        On select data1
        """
        self.send_warnings('')
        item = event.GetEventObject()
        pos = item.GetCurrentSelection()
        data = item.GetClientData(pos)
        if data is None:
            content = "?"
            self.put_text_pic(self.data1_pic, content)
        else:
            self.data1_pic.add_image(data)
        self.check_data_inputs()
        if self.output is not None:
            self.output.name = str(self.data_namectr.GetValue())
        self.draw_output(self.output)

    def on_select_operator(self, event=None):
        """
        On Select an Operator
        """
        self.send_warnings('')
        item = event.GetEventObject()
        text = item.GetValue().strip()
        self.put_text_pic(self.operator_pic, content=text)
        self.check_data_inputs()
        if self.output is not None:
            self.output.name = str(self.data_namectr.GetValue())
        self.draw_output(self.output)

    def on_select_data2(self, event=None):
        """
        On Selecting Data2
        """
        self.send_warnings('')
        item = event.GetEventObject()
        text = item.GetValue().strip().lower()
        self._show_numctrl(self.numberctr, text == 'number')
        pos = item.GetCurrentSelection()
        data = item.GetClientData(pos)
        content = "?"
        if not (self.numberctr.IsShown() and self.numberctr.IsEnabled()):
            if data is None:
                content = "?"
                self.put_text_pic(self.data2_pic, content)
            else:
                self.data2_pic.add_image(data)
            self.check_data_inputs()
        else:
            content = str(self.numberctr.GetValue().strip())
            try:
                content = float(content)
                data = content
            except:
                self._set_textctrl_color(self.numberctr, 'pink')
                content = "?"
                data = None
            item.SetClientData(pos, data)
            if data is not None:
                self.check_data_inputs()

            self.put_text_pic(self.data2_pic, content)

        if self.output is not None:
            self.output.name = str(self.data_namectr.GetValue())
        self.draw_output(self.output)

    def put_text_pic(self, pic=None, content=''):
        """
        Put text to the pic
        """
        pic.set_content(content)
        pic.add_text()
        pic.draw()

    def check_data_inputs(self):
        """
        Check data1 and data2 whether or not they are ready for operation
        """
        self._set_textctrl_color(self.data1_cbox, 'white')
        self._set_textctrl_color(self.data2_cbox, 'white')
        flag = False
        pos1 = self.data1_cbox.GetCurrentSelection()
        data1 = self.data1_cbox.GetClientData(pos1)
        if data1 is None:
            self.output = None
            return flag
        pos2 = self.data2_cbox.GetCurrentSelection()
        data2 = self.data2_cbox.GetClientData(pos2)

        if data2 is None:
            self.output = None
            return flag
        if self.numberctr.IsShown():
            if self.numberctr.IsEnabled():
                self._set_textctrl_color(self.numberctr, 'white')
                try:
                    float(data2)
                    if self.operator_cbox.GetValue().strip() == '|':
                        msg = "DataOperation: This operation can not accept "
                        msg += "a float number."
                        self.send_warnings(msg, 'error')
                        self._set_textctrl_color(self.numberctr, 'pink')
                        self.output = None
                        return flag
                except:
                    msg = "DataOperation: Number requires a float number."
                    self.send_warnings(msg, 'error')
                    self._set_textctrl_color(self.numberctr, 'pink')
                    self.output = None
                    return flag
            else:
                self._set_textctrl_color(self.numberctr, self.color)
        elif data1.__class__.__name__ != data2.__class__.__name__:
            self._set_textctrl_color(self.data1_cbox, 'pink')
            self._set_textctrl_color(self.data2_cbox, 'pink')
            msg = "DataOperation: Data types must be same."
            self.send_warnings(msg, 'error')
            self.output = None
            return flag
        try:
            self.output = self.make_data_out(data1, data2)
        except:
            self._check_newname()
            self._set_textctrl_color(self.data1_cbox, 'pink')
            self._set_textctrl_color(self.data2_cbox, 'pink')
            msg = "DataOperation: %s" % sys.exc_info()[1]
            self.send_warnings(msg, 'error')
            self.output = None
            return flag
        return True

    def make_data_out(self, data1, data2):
        """
        Make a temp. data output set
        """
        output = None
        pos = self.operator_cbox.GetCurrentSelection()
        operator = self.operator_cbox.GetClientData(pos)
        try:
            exec("output = data1 %s data2" % operator)
        except:
            raise
        return output


    def draw_output(self, output):
        """
        Draw output data(temp)
        """
        out = self.out_pic
        if output is None:
            content = "?"
            self.put_text_pic(out, content)
        else:
            out.add_image(output)
        wx.CallAfter(self.name_sizer.Layout)
        self.Layout()
        self.Refresh()

    def _layout_button(self):
        """
            Do the layout for the button widgets
        """
        self.bt_apply = wx.Button(self, -1, "Apply", size=(_BOX_WIDTH / 2, -1))
        app_tip = "Generate the Data and send to Data Explorer."
        self.bt_apply.SetToolTipString(app_tip)
        self.bt_apply.Bind(wx.EVT_BUTTON, self.on_click_apply)

        self.bt_help = wx.Button(self, -1, "HELP")
        app_tip = "Get help on Data Operations."
        self.bt_help.SetToolTipString(app_tip)
        self.bt_help.Bind(wx.EVT_BUTTON, self.on_help)

        self.bt_close = wx.Button(self, -1, 'Close', size=(_BOX_WIDTH / 2, -1))
        self.bt_close.Bind(wx.EVT_BUTTON, self.on_close)
        self.bt_close.SetToolTipString("Close this panel.")

        self.button_sizer.AddMany([(PANEL_WIDTH / 2, 25),
                                   (self.bt_apply, 0, wx.RIGHT, 10),
                                   (self.bt_help, 0, wx.RIGHT, 10),
                                   (self.bt_close, 0, wx.RIGHT, 10)])

    def _do_layout(self):
        """
        Draw the current panel
        """
        self._define_structure()
        self._layout_name()
        self._layout_button()
        self.main_sizer.AddMany([(self.name_sizer, 0, wx.EXPAND | wx.ALL, 10),
                                (self.button_sizer, 0,
                                          wx.EXPAND | wx.TOP | wx.BOTTOM, 5)])
        self.SetSizer(self.main_sizer)
        self.SetScrollbars(20, 20, 25, 65)
        self.SetAutoLayout(True)

    def set_panel_on_focus(self, event):
        """
        On Focus at this window
        """
        if event is not None:
            event.Skip()
        self._data = self.get_datalist()
        if ON_MAC:
            self.fill_data_combox()
        else:
            children = self.GetChildren()
            # update the list only when it is on the top
            if self.FindFocus() in children:
                self.fill_data_combox()

    def fill_oprator_combox(self):
        """
        fill the current combobox with the operator
        """
        operator_list = [' +', ' -', ' *', " /", " |"]
        for oper in operator_list:
            pos = self.operator_cbox.Append(str(oper))
            self.operator_cbox.SetClientData(pos, str(oper.strip()))
        self.operator_cbox.SetSelection(0)


    def fill_data_combox(self):
        """
        fill the current combobox with the available data
        """
        pos_pre1 = self.data1_cbox.GetCurrentSelection()
        pos_pre2 = self.data2_cbox.GetCurrentSelection()
        current1 = self.data1_cbox.GetLabel()
        current2 = self.data2_cbox.GetLabel()
        if pos_pre1 < 0:
            pos_pre1 = 0
        if pos_pre2 < 0:
            pos_pre2 = 0
        self.data1_cbox.Clear()
        self.data2_cbox.Clear()

        if not self._data:
            pos = self.data1_cbox.Append('No Data Available')
            self.data1_cbox.SetSelection(pos)
            self.data1_cbox.SetClientData(pos, None)
            pos2 = self.data2_cbox.Append('No Data Available')
            self.data2_cbox.SetSelection(pos2)
            self.data2_cbox.SetClientData(pos2, None)
            return
        pos1 = self.data1_cbox.Append('Select Data')
        self.data1_cbox.SetSelection(pos1)
        self.data1_cbox.SetClientData(pos1, None)
        pos2 = self.data2_cbox.Append('Select Data')
        self.data2_cbox.SetSelection(pos2)
        self.data2_cbox.SetClientData(pos2, None)
        pos3 = self.data2_cbox.Append('Number')
        val = None
        if (self.numberctr.IsShown() and self.numberctr.IsEnabled()):
            try:
                val = float(self.numberctr.GetValue())
            except:
                val = None
        self.data2_cbox.SetClientData(pos3, val)
        dnames = []
        ids = list(self._data.keys())
        for id in ids:
            if id is not None:
                if self._data[id].data is not None:
                    dnames.append(self._data[id].data.name)
                else:
                    theory_list = self._data[id].get_theory()
                    theory, _ = list(theory_list.values())[0]
                    dnames.append(theory.name)
        ind = np.argsort(dnames)
        if len(ind) > 0:
            val_list = np.array(list(self._data.values()))[ind]
            for datastate in val_list:
                data = datastate.data
                if data is not None:
                    name = data.name
                    pos1 = self.data1_cbox.Append(str(name))
                    self.data1_cbox.SetClientData(pos1, data)
                    pos2 = self.data2_cbox.Append(str(name))
                    self.data2_cbox.SetClientData(pos2, data)
                    if str(current1) == str(name):
                      pos_pre1 = pos1
                    if str(current2) == str(name):
                      pos_pre2 = pos2
                try:
                    theory_list = datastate.get_theory()
                    for theory, _ in list(theory_list.values()):
                        th_name = theory.name
                        posth1 = self.data1_cbox.Append(str(th_name))
                        self.data1_cbox.SetClientData(posth1, theory)
                        posth2 = self.data2_cbox.Append(str(th_name))
                        self.data2_cbox.SetClientData(posth2, theory)
                        if str(current1) == str(th_name):
                            pos_pre1 = posth1
                        if str(current2) == str(th_name):
                            pos_pre2 = posth2
                except:
                    continue
        self.data1_cbox.SetSelection(pos_pre1)
        self.data2_cbox.SetSelection(pos_pre2)

    def get_datalist(self):
        """
        """
        data_manager = self.parent.parent.get_data_manager()
        if data_manager is not None:
            return  data_manager.get_all_data()
        else:
            return {}

    def on_click_apply(self, event):
        """
        changes are saved in data object imported to edit
        """
        self.send_warnings('')
        self.data_namectr.SetBackgroundColour('white')
        state_list = list(self.get_datalist().values())
        name = self.data_namectr.GetValue().strip()
        name_list = []
        for state in state_list:
            if state.data is None:
                theory_list = state.get_theory()
                theory, _ = list(theory_list.values())[0]
                d_name = str(theory.name)
            else:
                d_name = str(state.data.name)
            name_list.append(d_name)
        if name in name_list:
            self._set_textctrl_color(self.data_namectr, 'pink')
            msg = "The Output Data Name already exists...   "
            wx.MessageBox(msg, 'Error')
            return
        if name == '':
            self._set_textctrl_color(self.data_namectr, 'pink')
            msg = "Please type the output data name first...   "
            wx.MessageBox(msg, 'Error')
            return
        if self.output is None:
            msg = "No Output Data has been generated...   "
            wx.MessageBox(msg, 'Error')
            return
        if self.numberctr.IsEnabled() and self.numberctr.IsShown():
            valid_num = self.on_number(control=self.numberctr)
            if not valid_num:
                return
        # send data to data manager
        self.output.name = name
        self.output.run = "Data Operation"
        self.output.instrument = "SasView"
        self.output.id = str(name) + str(time.time())
        data = {self.output.id :self.output}
        self.parent.parent.add_data(data)
        self.name_sizer.Layout()
        self.Refresh()
        #must post event here
        event.Skip()

    def on_help(self, event):
        """
        Bring up the Data Operations Panel Documentation whenever
        the HELP button is clicked.

        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".  Note that when using old
        versions of Wx (before 2.9) and thus not the release version of
        installers, the help comes up at the top level of the file as
        webbrowser does not pass anything past the # to the browser when it is
        running "file:///...."

    :param evt: Triggers on clicking the help button
    """

        _TreeLocation = "user/sasgui/perspectives/calculator/"
        _TreeLocation += "data_operator_help.html"
        _doc_viewer = DocumentationWindow(self, -1, _TreeLocation, "",
                                          "Data Operation Help")

    def disconnect_panels(self):
        """
        """
        self.out_pic.connect.disconnect()
        self.equal_pic.connect.disconnect()
        self.data1_pic.connect.disconnect()
        self.operator_pic.connect.disconnect()
        self.data2_pic.connect.disconnect()

    def on_close(self, event):
        """
        leave data as it is and close
        """
        self.parent.OnClose()

    def set_plot_unfocus(self):
        """
        Unfocus on right click
        """

    def send_warnings(self, msg='', info='info'):
        """
        Send warning to status bar
        """
        wx.PostEvent(self.parent.parent, StatusEvent(status=msg, info=info))

class SmallPanel(PlotPanel):
    """
    PlotPanel for Quick plot and masking plot
    """
    def __init__(self, parent, id= -1, is_number=False, content='?', **kwargs):
        """
        """
        PlotPanel.__init__(self, parent, id=id, **kwargs)
        self.is_number = is_number
        self.content = content
        self.point = None
        self.position = (0.4, 0.5)
        self.scale = 'linear'
        self.prevXtrans = "x"
        self.prevYtrans = "y"
        self.viewModel = "--"
        self.subplot.set_xticks([])
        self.subplot.set_yticks([])
        self.add_text()
        self.figure.subplots_adjust(left=0.1, bottom=0.1)

    def set_content(self, content=''):
        """
        Set text content
        """
        self.content = str(content)

    def add_toolbar(self):
        """
        Add toolbar
        """
        # Not implemented
        pass

    def on_set_focus(self, event):
        """
        send to the parenet the current panel on focus
        """
        pass

    def add_image(self, plot):
        """
        Add Image
        """
        self.content = ''
        self.textList = []
        self.plots = {}
        self.clear()
        self.point = plot
        try:
            self.figure.delaxes(self.figure.axes[0])
            self.subplot = self.figure.add_subplot(111)
            #self.figure.delaxes(self.figure.axes[1])
        except:
            pass
        try:
            name = plot.name
        except:
            name = plot.filename
        self.plots[name] = plot

        #init graph
        self.graph = Graph()

        #add plot
        self.graph.add(plot)
        #draw
        self.graph.render(self)

        try:
            self.figure.delaxes(self.figure.axes[1])
        except:
            pass
        self.subplot.figure.canvas.resizing = False
        self.subplot.tick_params(axis='both', labelsize=9)
        # Draw zero axis lines
        self.subplot.axhline(linewidth=1, color='r')
        self.subplot.axvline(linewidth=1, color='r')

        self.erase_legend()
        try:
            # mpl >= 1.1.0
            self.figure.tight_layout()
        except:
            self.figure.subplots_adjust(left=0.1, bottom=0.1)
        self.subplot.figure.canvas.draw()

    def add_text(self):
        """
        Text in the plot
        """
        if not self.is_number:
            return

        self.clear()
        try:
            self.figure.delaxes(self.figure.axes[0])
            self.subplot = self.figure.add_subplot(111)
            self.figure.delaxes(self.figure.axes[1])
        except:
            pass
        self.subplot.set_xticks([])
        self.subplot.set_yticks([])
        label = self.content
        FONT = FontProperties()
        xpos, ypos = (0.4, 0.5)
        font = FONT.copy()
        font.set_size(14)

        self.textList = []
        self.subplot.set_xlim((0, 1))
        self.subplot.set_ylim((0, 1))

        try:
            if self.content != '?':
                float(label)
        except:
            self.subplot.set_frame_on(False)
        try:
            # mpl >= 1.1.0
            self.figure.tight_layout()
        except:
            self.figure.subplots_adjust(left=0.1, bottom=0.1)
        if len(label) > 0 and xpos > 0 and ypos > 0:
            new_text = self.subplot.text(str(xpos), str(ypos), str(label),
                                           fontproperties=font)
            self.textList.append(new_text)

    def erase_legend(self):
        """
        Remove Legend
        """
        #for ax in self.axes:
        self.remove_legend(self.subplot)

    def onMouseMotion(self, event):
        """
        Disable dragging 2D image
        """

    def onWheel(self, event):
        """
        """

    def onLeftDown(self, event):
        """
        Disables LeftDown
        """

    def onPick(self, event):
        """
        Remove Legend
        """
        for ax in self.axes:
            self.remove_legend(ax)


    def draw(self):
        """
        Draw
        """
        if self.dimension == 3:
            pass
        else:
            self.subplot.figure.canvas.resizing = False
            self.subplot.tick_params(axis='both', labelsize=9)
            self.erase_legend()
            self.subplot.figure.canvas.draw_idle()
            try:
                self.figure.delaxes(self.figure.axes[1])
            except:
                pass


    def onContextMenu(self, event):
        """
        Default context menu for a plot panel
        """
        id = wx.NewId()
        slicerpop = wx.Menu()
        data = self.point
        if issubclass(data.__class__, Data1D):
            slicerpop.Append(id, '&Change Scale')
            wx.EVT_MENU(self, id, self._onProperties)
        else:
            slicerpop.Append(id, '&Toggle Linear/Log Scale')
            wx.EVT_MENU(self, id, self.ontogglescale)
        try:
            # mouse event
            pos_evt = event.GetPosition()
            pos = self.ScreenToClient(pos_evt)
        except:
            # toolbar event
            pos_x, pos_y = self.toolbar.GetPositionTuple()
            pos = (pos_x, pos_y + 5)
        self.PopupMenu(slicerpop, pos)

    def ontogglescale(self, event):
        """
        On toggle 2d scale
        """
        self._onToggleScale(event)
        try:
            # mpl >= 1.1.0
            self.figure.tight_layout()
        except:
            self.figure.subplots_adjust(left=0.1, bottom=0.1)
        try:
            self.figure.delaxes(self.figure.axes[1])
        except:
            pass

    def _onProperties(self, event):
        """
        when clicking on Properties on context menu ,
        The Property dialog is displayed
        The user selects a transformation for x or y value and
        a new plot is displayed
        """
        list = []
        list = self.graph.returnPlottable()
        if len(list(list.keys())) > 0:
            first_item = list(list.keys())[0]
            if first_item.x != []:
                from sas.sasgui.plottools.PropertyDialog import Properties
                dial = Properties(self, -1, 'Change Scale')
                # type of view or model used
                dial.xvalue.Clear()
                dial.yvalue.Clear()
                dial.view.Clear()
                dial.xvalue.Insert("x", 0)
                dial.xvalue.Insert("log10(x)", 1)
                dial.yvalue.Insert("y", 0)
                dial.yvalue.Insert("log10(y)", 1)
                dial.view.Insert("--", 0)
                dial.view.Insert("Linear y vs x", 1)
                dial.setValues(self.prevXtrans, self.prevYtrans, self.viewModel)
                dial.Update()
                if dial.ShowModal() == wx.ID_OK:
                    self.xLabel, self.yLabel, self.viewModel = dial.getValues()
                    if self.viewModel == "Linear y vs x":
                        self.xLabel = "x"
                        self.yLabel = "y"
                        self.viewModel = "--"
                        dial.setValues(self.xLabel, self.yLabel, self.viewModel)
                    self._onEVT_FUNC_PROPERTY()
                dial.Destroy()

    def _onEVT_FUNC_PROPERTY(self, remove_fit=True):
        """
        Receive the x and y transformation from myDialog,
        Transforms x and y in View
        and set the scale
        """
        list = []
        list = self.graph.returnPlottable()
        # Changing the scale might be incompatible with
        # currently displayed data (for instance, going
        # from ln to log when all plotted values have
        # negative natural logs).
        # Go linear and only change the scale at the end.
        self.set_xscale("linear")
        self.set_yscale("linear")
        _xscale = 'linear'
        _yscale = 'linear'
        for item in list:
            item.setLabel(self.xLabel, self.yLabel)
            # control axis labels from the panel itself
            yname, yunits = item.get_yaxis()
            xname, xunits = item.get_xaxis()
            # Goes through all possible scales
            # Goes through all possible scales
            if(self.xLabel == "x"):
                item.transformX(transform.toX, transform.errToX)
                self.graph._xaxis_transformed("%s" % xname, "%s" % xunits)
            if(self.xLabel == "log10(x)"):
                item.transformX(transform.toX_pos, transform.errToX_pos)
                _xscale = 'log'
                self.graph._xaxis_transformed("%s" % xname, "%s" % xunits)
            if(self.yLabel == "y"):
                item.transformY(transform.toX, transform.errToX)
                self.graph._yaxis_transformed("%s" % yname, "%s" % yunits)
            if(self.yLabel == "log10(y)"):
                item.transformY(transform.toX_pos, transform.errToX_pos)
                _yscale = 'log'
                self.graph._yaxis_transformed("%s" % yname, "%s" % yunits)
            item.transformView()
        self.prevXtrans = self.xLabel
        self.prevYtrans = self.yLabel
        self.set_xscale(_xscale)
        self.set_yscale(_yscale)
        self.draw()

class DataOperatorWindow(widget.CHILD_FRAME):
    def __init__(self, parent, manager, *args, **kwds):
        kwds["size"] = (PANEL_WIDTH, PANEL_HEIGTH)
        widget.CHILD_FRAME.__init__(self, parent, *args, **kwds)
        self.parent = parent
        self.manager = manager
        self.panel = DataOperPanel(parent=self)
        wx.EVT_CLOSE(self, self.OnClose)
        self.SetPosition((wx.LEFT, PANEL_TOP))
        self.Show()

    def OnClose(self, event=None):
        """
        On close event
        """
        if self.manager is not None:
            self.manager.data_operator_frame = None
        self.panel.disconnect_panels()
        self.Destroy()


if __name__ == "__main__":

    app = wx.App()
    widget.CHILD_FRAME = wx.Frame
    window = DataOperatorWindow(parent=None, data=[], title="Data Editor")
    app.MainLoop()
