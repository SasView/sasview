"""
GUI for the data operation
"""
import wx
import sys
import time
import numpy
from sans.dataloader.data_info import Data2D
from sans.dataloader.data_info import Data1D
from danse.common.plottools.PlotPanel import PlotPanel
from danse.common.plottools.plottables import Graph
from danse.common.plottools.canvas import FigureCanvas
from matplotlib.font_manager import FontProperties
from matplotlib.figure import Figure
from sans.guiframe.events import StatusEvent 
       
#Control panel width 
if sys.platform.count("win32") > 0:
    PANEL_WIDTH = 780
    PANEL_HEIGTH = 370
    FONT_VARIANT = 0
    _BOX_WIDTH = 200
    ON_MAC = False
else:
    _BOX_WIDTH = 230
    PANEL_WIDTH = 890
    PANEL_HEIGTH = 430
    FONT_VARIANT = 1
    ON_MAC = True
      
class DataOperPanel(wx.ScrolledWindow):
    """
    :param data: when not empty the class can 
                same information into a data object
        and post event containing the changed data object to some other frame
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
        #data
        self._data = self.get_datalist()
        self._do_layout()
        self.fill_data_combox()
        self.fill_oprator_combox()
        self.Bind(wx.EVT_PAINT, self.set_panel_on_focus)
             
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
        equal_sizer =  wx.BoxSizer(wx.VERTICAL)
        old_data1_sizer = wx.BoxSizer(wx.VERTICAL)
        operator_sizer = wx.BoxSizer(wx.VERTICAL)
        old_data2_sizer = wx.BoxSizer(wx.VERTICAL)
        data2_hori_sizer = wx.BoxSizer(wx.HORIZONTAL)
        data_name = wx.StaticText(self, -1, 'Output Data Name')  
        equal_name = wx.StaticText(self, -1, ' =',  size=(50, 23)) 
        data1_name = wx.StaticText(self, -1, 'Data1')
        operator_name = wx.StaticText(self, -1, 'Operator')
        data2_name = wx.StaticText(self, -1, 'Data2 (or Number)')
        self.data_namectr = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, 25))
        self.data_namectr.SetToolTipString("Hit 'Enter' key after typing.")
        self.data_namectr.SetValue(str('MyNewDataName'))
        self.numberctr = wx.TextCtrl(self, -1, size=(_BOX_WIDTH/3, 25)) 
        self.numberctr.SetToolTipString("Hit 'Enter' key after typing.")
        self.numberctr.SetValue(str(1.0))
        self.data1_cbox = wx.ComboBox(self, -1, size=(_BOX_WIDTH, 25), 
                                      style=wx.CB_READONLY)
        self.operator_cbox = wx.ComboBox(self, -1, size=(50, -1), 
                                         style=wx.CB_READONLY)
        operation_tip = "Add: +, Subtract: -, "
        operation_tip += "Multiply: *, Divide: /, "
        operation_tip += "Append(Combine): | "
        self.operator_cbox.SetToolTipString(operation_tip)
        self.data2_cbox = wx.ComboBox(self, -1, size=(_BOX_WIDTH*2/3, 25),
                                       style=wx.CB_READONLY)

        self.out_pic = SmallPanel(self, -1, True, size=(_BOX_WIDTH, _BOX_WIDTH), 
                             style=wx.NO_BORDER)
        self.equal_pic = SmallPanel(self, -1, True, '=',  size=(50, _BOX_WIDTH), 
                              style=wx.NO_BORDER)
        self.data1_pic = SmallPanel(self, -1, True, 
                                    size=(_BOX_WIDTH, _BOX_WIDTH), 
                             style=wx.NO_BORDER)
        self.operator_pic = SmallPanel(self, -1, True, 
                                       '+', size=(50, _BOX_WIDTH), 
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
        equal_sizer.AddMany([(13, 15), (equal_name, 0, wx.LEFT, 3),
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
        self.name_sizer.AddMany([(new_data_sizer, 0, wx.LEFT|wx.TOP, 5),
                                       (equal_sizer, 0, wx.TOP, 5),
                                       (old_data1_sizer, 0, wx.TOP, 5),
                                       (operator_sizer, 0, wx.TOP, 5),
                                       (old_data2_sizer, 0, wx.TOP, 5)])
        self.data2_cbox.Show(True)

        self.numberctr.Show(False)

        wx.EVT_TEXT_ENTER(self.data_namectr, -1, self.on_name)
        wx.EVT_TEXT_ENTER(self.numberctr, -1, self.on_number) 
        wx.EVT_COMBOBOX(self.data1_cbox, -1, self.on_select_data1) 
        wx.EVT_COMBOBOX(self.operator_cbox, -1, self.on_select_operator) 
        wx.EVT_COMBOBOX(self.data2_cbox, -1, self.on_select_data2)
        
    def on_name(self, event=None):
        """
        On data name typing
        """
        if event != None:
            event.Skip()
        item = event.GetEventObject()
        item.SetBackgroundColour('white')
        text = item.GetLabel().strip()
        self._check_newname(text)
    
    def _check_newname(self, name=None):
        """
        Check name ctr strings
        """
        self.send_warnings('')
        msg = ''
        if name == None:
            text = self.data_namectr.GetLabel().strip()
        else:
            text = name
        state_list = self.get_datalist().values()
        if text in [str(state.data.name) for state in state_list]:
            self.data_namectr.SetBackgroundColour('pink')
            msg = "DataOperation: The name already exists."
        if len(text) == 0:
            self.data_namectr.SetBackgroundColour('pink')
            msg = "DataOperation: Type the data name first."
        if self._notes:
            self.send_warnings(msg, 'error')
        self.name_sizer.Layout()
        self.Refresh()
                
    def on_number(self, event=None):
        """
        On selecting Number for Data2
        """
        if event != None:
            event.Skip()
        self.send_warnings('')
        self.numberctr.SetBackgroundColour('white')
        item = event.GetEventObject()
        text = item.GetLabel().strip()
        try:
            val = float(text)
            pos = self.data2_cbox.GetSelection()
            self.data2_cbox.SetClientData(pos, val)
        except:
            self.numberctr.SetBackgroundColour('pink')
            msg = "DataOperation: Number requires a float number."
            self.send_warnings(msg, 'error')
            return
        self.put_text_pic(self.data2_pic, content=str(val)) 
        self.check_data_inputs()
        if self.output != None:
            self.output.name = str(self.data_namectr.GetValue())
        self.draw_output(self.output)
        
    def on_select_data1(self, event=None):
        """
        On select data1
        """
        if event != None:
            event.Skip()
        self.send_warnings('')
        item = event.GetEventObject()
        pos = item.GetSelection()
        data = item.GetClientData(pos)
        if data == None:
            content = "?"
            self.put_text_pic(self.data1_pic, content) 
        else:
            self.data1_pic.add_image(data)
        self.check_data_inputs()
        if self.output != None:
            self.output.name = str(self.data_namectr.GetValue())
        self.draw_output(self.output)
        
    def on_select_operator(self, event=None):
        """
        On Select an Operator
        """
        if event != None:
            event.Skip()
        self.send_warnings('')
        item = event.GetEventObject()
        text = item.GetLabel().strip()
        self.put_text_pic(self.operator_pic, content=text) 
        self.check_data_inputs()
        if self.output != None:
            self.output.name = str(self.data_namectr.GetValue())
        self.draw_output(self.output)
        
    def on_select_data2(self, event=None):
        """
        On Selecting Data2
        """
        if event != None:
            event.Skip()
        self.send_warnings('')
        item = event.GetEventObject()
        text = item.GetLabel().strip().lower()
        self.numberctr.Show(text=='number')
        
        pos = item.GetSelection()
        data = item.GetClientData(pos)
        content = "?"
        if not self.numberctr.IsShown():
            if data == None:
                content = "?"
                self.put_text_pic(self.data2_pic, content) 
            else:
                self.data2_pic.add_image(data)
        else:
            if data == None:
                content = str(self.numberctr.GetValue().strip())
                try:
                    content = float(content)
                    data = content
                except:
                    content = "?"
                    data = None
                item.SetClientData(pos, content)
            self.put_text_pic(self.data2_pic, content)   
        self.check_data_inputs()

        if self.output != None:
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
        self.data1_cbox.SetBackgroundColour('white')
        self.data2_cbox.SetBackgroundColour('white')
        flag = False
        pos1 = self.data1_cbox.GetCurrentSelection()
        data1 = self.data1_cbox.GetClientData(pos1)
        if data1 == None:
            self.output = None
            return flag
        pos2 = self.data2_cbox.GetCurrentSelection()
        data2 = self.data2_cbox.GetClientData(pos2)
        if data2 == None:
            self.output = None
            return flag
        if self.numberctr.IsShown():
            self.numberctr.SetBackgroundColour('white')
            try:
                float(data2)
                if self.operator_cbox.GetLabel().strip() == '|':
                    msg = "DataOperation: This operation can not accept "
                    msg += "a float number."
                    self.send_warnings(msg, 'error')
                    self.numberctr.SetBackgroundColour('pink')
                    self.output = None
                    return flag
            except:
                msg = "DataOperation: Number requires a float number."
                self.send_warnings(msg, 'error')
                self.numberctr.SetBackgroundColour('pink')
                self.output = None
                return flag
        elif data1.__class__.__name__ != data2.__class__.__name__:
            self.data1_cbox.SetBackgroundColour('pink')
            self.data2_cbox.SetBackgroundColour('pink')
            msg = "DataOperation: Data types must be same."
            self.send_warnings(msg, 'error')
            self.output = None
            return flag
        try:
            self.output = self.make_data_out(data1, data2)
        except:
            self._check_newname()
            self.data1_cbox.SetBackgroundColour('pink')
            self.data2_cbox.SetBackgroundColour('pink')
            msg = "DataOperation: Data types must be same."
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
        exec "output = data1 %s data2"% operator
        return output
    
    
    def draw_output(self, output):
        """
        Draw output data(temp)
        """
        out = self.out_pic
        if output == None:
            content = "?"
            self.put_text_pic(out, content) 
        else:
            out.add_image(output)
        self.name_sizer.Layout()
        self.Refresh()
                    
    def _layout_button(self):  
        """
            Do the layout for the button widgets
        """ 
        self.bt_apply = wx.Button(self, -1, "Apply", size=(_BOX_WIDTH/2, -1))
        app_tip = "Generate the Data and send to Data Explorer."
        self.bt_apply.SetToolTipString(app_tip)
        self.bt_apply.Bind(wx.EVT_BUTTON, self.on_click_apply)
        
        self.bt_close = wx.Button(self, -1, 'Close', size=(_BOX_WIDTH/2, -1))
        self.bt_close.Bind(wx.EVT_BUTTON, self.on_close)
        self.bt_close.SetToolTipString("Close this panel.")
        
        self.button_sizer.AddMany([(PANEL_WIDTH/2, 25),
                                   (self.bt_apply, 0, wx.RIGHT, 10),
                                   (self.bt_close, 0, wx.RIGHT, 10)])
        
    def _do_layout(self):
        """
        Draw the current panel
        """
        self._define_structure()
        self._layout_name()
        self._layout_button()
        self.main_sizer.AddMany([(self.name_sizer, 0, wx.EXPAND|wx.ALL, 10),
                                (self.button_sizer, 0,
                                          wx.EXPAND|wx.TOP|wx.BOTTOM, 5)])
        self.SetSizer(self.main_sizer)
        self.SetScrollbars(20, 20, 25, 65)
        self.SetAutoLayout(True)
    
    def set_panel_on_focus(self, event):
        """
        On Focus at this window
        """
        if event != None:
            event.Skip()
        self._data = self.get_datalist()
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
            pos3 = self.data2_cbox.Append("Number")
            val = None
            if self.numberctr.IsShown():
                try:
                    val = float(self.numberctr.GetValue())
                except:
                    val = None
            self.data2_cbox.SetClientData(pos3, val)
            return
        pos1 = self.data1_cbox.Append('Select Data')
        self.data1_cbox.SetSelection(pos1)
        self.data1_cbox.SetClientData(pos1, None)
        pos2 = self.data2_cbox.Append('Select Data')
        self.data2_cbox.SetSelection(pos2)
        self.data2_cbox.SetClientData(pos2, None)
        pos3 = self.data2_cbox.Append('Number')
        val = None
        if self.numberctr.IsShown():
            try:
                val = float(self.numberctr.GetValue())
            except:
                val = None
        self.data2_cbox.SetClientData(pos3, val)
        dnames = []
        for dstate in self._data.values():
            if dstate != None:
                if dstate.data != None:
                    dnames.append(dstate.data.name)
        if len(dnames) > 0:
            ind = numpy.argsort(dnames)
            for datastate in numpy.array(self._data.values())[ind]:
                data = datastate.data
                if data != None:
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
                    for theory, _ in theory_list.values():
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
        if data_manager != None:
            return  data_manager.get_all_data()
        else:
            return {}
            
    def on_click_apply(self, event):
        """   
        changes are saved in data object imported to edit
        """
        self.send_warnings('')
        self.data_namectr.SetBackgroundColour('white')
        state_list = self.get_datalist().values()
        name = self.data_namectr.GetLabel().strip()
        if name in [str(state.data.name) for state in state_list]:
            self.data_namectr.SetBackgroundColour('pink')
            msg = "The Output Data Name already exists...   "
            wx.MessageBox(msg, 'Error')
            return
        if name == '':
            self.data_namectr.SetBackgroundColour('pink')
            msg = "Please type the output data name first...   "
            wx.MessageBox(msg, 'Error')
            return
        if self.output == None:
            msg = "No Output Data has been generated...   "
            wx.MessageBox(msg, 'Error')
            return
        # send data to data manager
        self.output.name = name
        self.output.run = "Data Operation"
        self.output.instrument = "SansView"
        self.output.id = str(name) + str(time.time())
        data = {self.output.id :self.output}
        self.parent.parent.add_data(data)
        self.name_sizer.Layout()
        self.Refresh()
        #must post event here
        event.Skip()
    
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
    def __init__(self, parent, id=-1, is_number=False, content='?', **kwargs):
        """
        """ 
        PlotPanel.__init__(self, parent, id=id, **kwargs)
        self.is_number = is_number
        self.content = content
        self.position = (0.4, 0.5)
        self.scale = 'linear'
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
        self.subplot.set_xticks([])
        self.subplot.set_yticks([])
        # Draw zero axis lines
        self.subplot.axhline(linewidth = 1, color='r')  
        self.subplot.axvline(linewidth = 1, color='r')       

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
            self.subplot.figure.canvas.draw_idle() 
       
    def onContextMenu(self, event):
        """
        Default context menu for a plot panel
        """
               
class DataOperatorWindow(wx.Frame):
    def __init__(self, parent, *args, **kwds):
        kwds["size"] = (PANEL_WIDTH, PANEL_HEIGTH)
        wx.Frame.__init__(self, parent, *args, **kwds)
        self.parent = parent
        self.panel = DataOperPanel(parent=self)
        wx.EVT_CLOSE(self, self.OnClose)
        self.CenterOnParent()
        self.Show()
    
    def OnClose(self, event=None):  
        """
        On close event
        """
        self.Show(False)

        
if __name__ == "__main__":
   
    app  = wx.App()
    window = DataOperatorWindow(parent=None, data=[], title="Data Editor")
    app.MainLoop()
 