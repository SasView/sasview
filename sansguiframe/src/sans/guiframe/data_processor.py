"""
Implement grid used to store data
"""
import wx
import numpy
import math
import re
import os
import sys
import copy
from wx.lib.scrolledpanel import ScrolledPanel
import  wx.grid as  Grid
import wx.aui
from wx.aui import AuiNotebook as nb
from sans.guiframe.panel_base import PanelBase
import wx.lib.sheet as sheet

from sans.guiframe.events import NewPlotEvent 
from sans.guiframe.events import StatusEvent  
from sans.guiframe.dataFitting import Data1D

FUNC_DICT = {"sqrt": "math.sqrt",
             "pow": "math.sqrt"}


def parse_string(sentence, list):
    """
    Return a dictionary of column label and index or row selected
    :param sentence: String to parse
    :param list: list of columns label
    """
    toks = []
    p2 = re.compile(r'\d+')
    p = re.compile(r'[\+\-\*\%\/]')
    labels = p.split(sentence)
    col_dict = {}
    for elt in labels:
        rang = None
        temp_arr = []
        for label in  list:
            label_pos =  elt.find(label)
            if label_pos != -1:
                if elt.count(',') > 0:
                    new_temp = []
                    temp = elt.split(label)
                    for item in temp:
                        range_pos = item.find(":")
                        if range_pos != -1:
                            rang = p2.findall(item)
                            for i in xrange(int(rang[0]), int(rang[1])+1 ):
                                new_temp.append(i)
                    temp_arr += new_temp
                else:
                    temp = elt.split(label)
                    for item in temp:
                        range_pos = item.find(":")
                        if range_pos != -1:
                            rang = p2.findall(item)
                            for i in xrange(int(rang[0]), int(rang[1])+1 ):
                                temp_arr.append(i)
                col_dict[elt] = (label, temp_arr)
    return col_dict

class GridPage(sheet.CSheet):
    """
    """
    def __init__(self, parent, panel=None):
        """
        """
        sheet.CSheet.__init__(self, parent)
        self.SetLabelBackgroundColour('#DBD4D4')
        self.AutoSize()
        self.panel = panel
        self.col_names = []
        self.data_inputs = {}
        self.data_outputs = {}
        self._cols = 50
        self._rows = 51
        col_with = 30
        row_height = 20
        self.axis_value = []
        self.axis_label = ""
        self.selected_cells = []
        self.selected_cols = []
        self.SetColMinimalAcceptableWidth(col_with)
        self.SetRowMinimalAcceptableHeight(row_height)
        self.SetNumberRows(self._cols)
        self.SetNumberCols(self._rows)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.on_left_click)
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.on_right_click)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.on_selected_cell)
        
    def on_selected_cell(self, event):
        """
        Handler catching cell selection
        """
        flag = event.CmdDown() or event.ControlDown()
        row, col = event.GetRow(), event.GetCol()
        cell = (row, col)
        if not flag:
            self.selected_cells = []
            self.axis_value = []
            self.axis_label = ""
        if cell in self.selected_cells:
            self.selected_cells.remove(cell)
        else:
            self.selected_cells.append(cell)
        if row > 1:
            if (cell) in self.selected_cells:
                self.axis_value.append(self.GetCellValue(row, col))
        self.axis_label = self.GetCellValue(row, col)
        event.Skip()
      
    def on_left_click(self, event):
        """
        Catch the left click on label mouse event
        """
        flag = event.CmdDown() or event.ControlDown()
        col = event.GetCol()
        if not flag:
            self.selected_cols = []
            self.axis_value = []
            self.axis_label = ""
        if col not in self.selected_cols:
            self.selected_cols.append(col)
        if not flag :
            for row in range(2, self.GetNumberRows()+ 1):
                self.axis_value.append(self.GetCellValue(row, col))
            row = 1
            self.axis_label = self.GetCellValue(row, col)
        event.Skip()
        
    def on_right_click(self, event):
        """
        Catch the right click mouse
        """
        col = event.GetCol()
        if col != -1 and len(self.col_names) > col:
            label = self.col_names[int(col)]
            self.axis_label = label
            if label in self.data.keys():
                col_val = self.data[label]
                self.axis_value = col_val
        # Slicer plot popup menu
        slicerpop = wx.Menu()
        id = wx.NewId()
        slicerpop.Append(id, '&Set X axis', 'Set X axis')
        wx.EVT_MENU(self, id, self.on_set_x_axis)
        
        id = wx.NewId()
        slicerpop.Append(id, '&Set Y axis', 'Set Y axis')
        wx.EVT_MENU(self, id, self.on_set_y_axis)
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(slicerpop, pos)
        
    def on_set_x_axis(self, event):
        """
        """
        self.panel.set_xaxis(x=self.axis_value, label=self.axis_label)
   
    def on_set_y_axis(self, event):
        """
        """
        self.panel.set_yaxis(y=self.axis_value, label=self.axis_label)     
            
    def set_data(self, data_inputs, data_outputs):
        """
        Add data to the grid
        """
        if data_outputs is None:
            data_outputs = {}
        self.data_outputs = data_outputs
        if self.data_inputs is None:
            data_inputs = {}
        self.data_inputs = data_inputs
        
        if  len(self.data_outputs) > 0:
            self._cols = self.GetNumberCols()
            self._rows = self.GetNumberRows()
            self.col_names = self.data_outputs.keys()
            self.col_names.sort() 
            nbr_user_cols = len(self.col_names)
            #Add more columns to the grid if necessary
            if nbr_user_cols > self._cols:
                new_col_nbr = nbr_user_cols -  self._cols 
                self.AppendCols(new_col_nbr, True)
            #Add more rows to the grid if necessary  
            nbr_user_row = len(self.data_outputs.values())
            if nbr_user_row > self._rows + 1:
                new_row_nbr =  nbr_user_row - self._rows 
                self.AppendRows(new_row_nbr, True)
            # add data to the grid    
            row = 0
            col = 0
            cell_col = 0
            for col_name in  self.col_names:
                # use the first row of the grid to add user defined labels
                self.SetCellValue(row, col, str(col_name))
                col += 1
                cell_row =  1
                value_list = self.data_outputs[col_name]
                
                for value in value_list:
                    self.SetCellValue(cell_row, cell_col, str(value))
                    cell_row += 1
                cell_col += 1
            self.AutoSize()
           

class Notebook(nb, PanelBase):
    """
    ## Internal name for the AUI manager
    window_name = "Fit panel"
    ## Title to appear on top of the window
    """
    window_caption = "Notebook "
    
    def __init__(self, parent, manager=None, data=None, *args, **kwargs):
        """
        """
        nb.__init__(self, parent, -1,
                    style= wx.aui.AUI_BUTTON_DOWN|
                    wx.aui.AUI_NB_WINDOWLIST_BUTTON|
                    wx.aui.AUI_NB_DEFAULT_STYLE|
                    wx.CLIP_CHILDREN)
        PanelBase.__init__(self, parent)
        self.enable_close_button()
        self.parent = parent
        self.manager = manager
        self.data = data
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_close_page)
    
    def enable_close_button(self):
        """
        display the close button on tab for more than 1 tabs else remove the 
        close button
        """
        if self.GetPageCount() <= 1:
            style = self.GetWindowStyleFlag() 
            flag = wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
            if style & wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB == flag:
                style = style & ~wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
                self.SetWindowStyle(style)
        else:
            style = self.GetWindowStyleFlag()
            flag = wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
            if style & wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB != flag:
                style |= wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
                self.SetWindowStyle(style)
              
    def on_edit_axis(self):
        """
        Return the select cell of a given selected column
        """
        pos = self.GetSelection()
        grid = self.GetPage(pos)
        if len(grid.selected_cols) > 1:
            msg = "Edit axis doesn't understand this selection.\n"
            msg += "Please select only one column"
            raise ValueError, msg
        list_of_cells = []
        if len(grid.selected_cols) == 1:
            col = grid.selected_cols[0]
            if len(grid.selected_cells) > 0:
                cell_row, cell_col = grid.selected_cells[0]
                if cell_col  != col:
                    msg = "Edit axis doesn't understand this selection.\n"
                    msg += "Please select element of the same col"
                    raise ValueError, msg
            for row in range(grid.GetNumberRows()):
                list_of_cells.append((row + 1 , col))
            for item in grid.selected_cells:
                if item in list_of_cells:
                    list_of_cells.remove(item)
        elif len(grid.selected_cols) == 0:
            list_of_cells = [(row + 1, col) for row, col in grid.selected_cells]
        return list_of_cells
    
    def get_column_labels(self):
        """
        return dictionary of columns labels of the current page
        """
        pos = self.GetSelection()
        grid = self.GetPage(pos)
        labels = {}
        row = 0
        for col in range(grid.GetNumberCols()):
            label = grid.GetCellValue(row, col)
            if label.strip() != "" :
                labels[label.strip()] = col
        return labels
        
    def create_axis_label(self, cell_list):
        """
        Receive a list of cells and  create a string presenting the selected 
        cells. 
        :param cell_list: list of tuple
        
        """
        pos = self.GetSelection()
        grid = self.GetPage(pos)
        label = ""
        col_name = ""
        if len(cell_list) > 0:
            temp_list = copy.deepcopy(cell_list)
            temp_list.sort()
            temp = []
            for item in temp_list:
                if item[0] <= 1:
                    temp.append(item)
            for element in temp:
                temp_list.remove(element)
            row_min, col  = temp_list[0]    
            row_max = row_min
            col_name = grid.GetCellValue(0, col)
            label += str(col_name) + "[" + str(row_min) + ":"
            for index in xrange(len(temp_list)):
                prev = index - 1
                row, _ = temp_list[index]
                if row > row_max + 1 :
                    if prev > 0:
                        row_max, _ = temp_list[prev]
                        label += str(row_max) + "]" + ","
                        row_min = row
                        label  += "[" + str(row_min) + ":"
                row_max = row
                if (index == len(temp_list)- 1):
                    label +=  str(row_max) + "]"     
        return label, col_name
    
    def on_close_page(self, event):
        """
        close the page
        """
        if self.GetPageCount() == 1:
            event.Veto()
        self.enable_close_button()
        
    def set_data(self, data_inputs, data_outputs):
        if data_outputs is None or data_outputs == {}:
            return
        grid = GridPage(self, panel=self.parent)
        grid.set_data(data_inputs, data_outputs)  
        self.AddPage(grid, "")
        pos = self.GetPageIndex(grid)
        title = "Batch " + str(self.GetPageCount())
        self.SetPageText(pos, title)
        
    def add_column(self):
        """
        Append a new column to the grid
        """
        pos = self.GetSelection()
        grid = self.GetPage(pos)
        grid.AppendCols(1, True)
        
    def on_remove_column(self):
        """
        Remove column to the current grid
        """
        pos = self.GetSelection()
        grid = self.GetPage(pos)
        cols_pos = grid.GetSelectedCols() 
        for cpos in cols_pos:
            grid.DeleteCols(cpos)
          
          
class SPanel(ScrolledPanel):
    def __init__(self, parent, *args, **kwds):
        ScrolledPanel.__init__(self, parent , *args, **kwds)
        self.SetupScrolling()  


class GridPanel(SPanel):
    def __init__(self, parent, data_inputs=None,
                 data_outputs=None, *args, **kwds):
        SPanel.__init__(self, parent , *args, **kwds)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.plotting_sizer = wx.FlexGridSizer(3, 7, 10, 5)
        self.grid_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.vbox.AddMany([(self.grid_sizer, 1, wx.EXPAND, 0),
                           (wx.StaticLine(self, -1), 0, wx.EXPAND, 0),
                           (self.plotting_sizer)])
        self.parent = parent
        self._data_inputs = data_inputs
        self._data_outputs = data_outputs
        self.x = []
        self.y  = []
        self.x_axis_label = None
        self.y_axis_label = None
        self.x_axis_title = None
        self.y_axis_title = None
        self.x_axis_unit = None
        self.y_axis_unit = None
        self.plot_button = None
        self.notebook = None
        self.layout_grid()
        self.layout_plotting_area()
        self.SetSizer(self.vbox)
        
    def set_data(self, data_inputs, data_outputs):
        """
        """
        if self.notebook is not None:
            self.notebook.set_data(data_inputs, data_outputs)
        
    def set_xaxis(self, label="", x=None):
        """
        """
        if x is None:
            x = []
        self.x = x
        self.x_axis_label.SetValue("%s[:]" % str(label))
        self.x_axis_title.SetValue(str(label))
        
    def set_yaxis(self, label="", y=None):
        """
        """
        if y is None:
            y = []
        self.y = y
        self.y_axis_label.SetValue("%s[:]" % str(label))
        self.y_axis_title.SetValue(str(label))
        
    def get_plot_axis(self, col, list):
        """
       
        """
        axis = []
        pos = self.notebook.GetSelection()
        grid = self.notebook.GetPage(pos)
        for row in list:
            label = grid.GetCellValue(0, col)
            value = grid.GetCellValue(row - 1, col).strip()
            if value != "":
                if label.lower().strip() == "data":
                    axis.append(float(row - 1))
                else:
                    axis.append(float(value))
            else:
                axis.append(None) 
        return axis
    
    def on_plot(self, event):
        """
        Evaluate the contains of textcrtl and plot result
        """ 
        pos = self.notebook.GetSelection()
        grid = self.notebook.GetPage(pos)
        column_names = {}
        if grid is not None:
            column_names = self.notebook.get_column_labels()
        #evalue x
        sentence = self.x_axis_label.GetValue()
        if sentence.strip() == "":
            msg = "select value for x axis"
            raise ValueError, msg
        dict = parse_string(sentence, column_names.keys())
        for tok, (col_name, list) in dict.iteritems():
            col = column_names[col_name]
            xaxis = self.get_plot_axis(col, list)
            sentence = sentence.replace(tok, 
                                        "numpy.array(%s)" % str(xaxis))
        for key, value in FUNC_DICT.iteritems():
            sentence = sentence.replace(key.lower(), value)
        x = eval(sentence)
        #evaluate y
        sentence = self.y_axis_label.GetValue()
        if sentence.strip() == "":
            msg = "select value for y axis"
            raise ValueError, msg
        dict = parse_string(sentence, column_names.keys())
        for tok, (col_name, list) in dict.iteritems():
            col = column_names[col_name]
            yaxis = self.get_plot_axis(col, list)
            sentence = sentence.replace(tok, 
                                        "numpy.array(%s)" % str(yaxis))
        for key, value in FUNC_DICT.iteritems():
            sentence = sentence.replace(key, value)
        y = eval(sentence)
        #plotting
        new_plot = Data1D(x=x, y=y)
        new_plot.id =  wx.NewId()
        new_plot.group_id = wx.NewId()
        title = "%s vs %s" % (self.y_axis_title.GetValue(), 
                              self.x_axis_title.GetValue())
        new_plot.xaxis(self.x_axis_title.GetValue(), self.x_axis_unit.GetValue())
        new_plot.yaxis(self.y_axis_title.GetValue(), self.y_axis_unit.GetValue())
        try:
            title = self.notebook.GetPageText(pos)
            wx.PostEvent(self.parent.parent, 
                             NewPlotEvent(plot=new_plot, 
                        group_id=str(new_plot.group_id), title =title))    
        except:
            pass
        
    def layout_grid(self):
        """
        Draw the area related to the grid
        """
        self.notebook = Notebook(parent=self)
        self.notebook.set_data(self._data_inputs, self._data_outputs)
        self.grid_sizer.Add(self.notebook, 1, wx.EXPAND, 0)
       
    def layout_plotting_area(self):
        """
        Draw area containing options to plot
        """
        self.x_axis_title = wx.TextCtrl(self, -1)
        self.y_axis_title = wx.TextCtrl(self, -1)
        self.x_axis_label = wx.TextCtrl(self, -1, size=(200, -1))
        self.y_axis_label = wx.TextCtrl(self, -1, size=(200, -1))
        self.x_axis_add = wx.Button(self, -1, "Add")
        self.x_axis_add.Bind(event=wx.EVT_BUTTON, handler=self.on_edit_axis, 
                            id=self.x_axis_add.GetId())
        self.y_axis_add = wx.Button(self, -1, "Add")
        self.y_axis_add.Bind(event=wx.EVT_BUTTON, handler=self.on_edit_axis, 
                            id=self.y_axis_add.GetId())
        self.x_axis_unit = wx.TextCtrl(self, -1)
        self.y_axis_unit = wx.TextCtrl(self, -1)
        self.plot_button = wx.Button(self, -1, "Plot")
        wx.EVT_BUTTON(self, self.plot_button.GetId(), self.on_plot)
        self.plotting_sizer.AddMany([
                    (wx.StaticText(self, -1, "x-axis label"), 1,
                      wx.TOP|wx.BOTTOM|wx.LEFT, 10),
                    (self.x_axis_label, 1, wx.TOP|wx.BOTTOM, 10),
                    (self.x_axis_add, 1, wx.TOP|wx.BOTTOM|wx.RIGHT, 10),
                    (wx.StaticText(self, -1, "x-axis title"), 1, 
                     wx.TOP|wx.BOTTOM|wx.LEFT, 10),
                    (self.x_axis_title, 1, wx.TOP|wx.BOTTOM, 10),
                    (wx.StaticText(self, -1 , "unit"), 1, 
                     wx.TOP|wx.BOTTOM, 10),
                    (self.x_axis_unit, 1, wx.TOP|wx.BOTTOM, 10),
                    (wx.StaticText(self, -1, "y-axis label"), 1, 
                     wx.BOTTOM|wx.LEFT, 10),
                    (self.y_axis_label, wx.BOTTOM, 10),
                    (self.y_axis_add, 1, wx.BOTTOM|wx.RIGHT, 10),
                    (wx.StaticText(self, -1, "y-axis title"), 1, 
                     wx.BOTTOM|wx.LEFT, 10),
                    (self.y_axis_title,  wx.BOTTOM, 10),
                    (wx.StaticText(self, -1 , "unit"), 1, wx.BOTTOM, 10),
                    (self.y_axis_unit, 1, wx.BOTTOM, 10),
                      (-1, -1),
                      (-1, -1),
                      (-1, -1),
                      (-1, -1),
                      (-1, -1),
                      (-1, -1),
                      (self.plot_button, 1, wx.LEFT|wx.BOTTOM, 10)])
   
    def on_edit_axis(self, event):
        """
        Get the selected column on  the visible grid and set values for axis
        """
        cell_list = self.notebook.on_edit_axis()
        label, title = self.create_axis_label(cell_list)
        tcrtl = event.GetEventObject()
        if tcrtl == self.x_axis_add:
            self.edit_axis_helper(self.x_axis_label, self.x_axis_title,
                                   label, title)
        elif tcrtl == self.y_axis_add:
            self.edit_axis_helper(self.y_axis_label, self.y_axis_title,
                                   label, title)
            
    def create_axis_label(self, cell_list):
        """
        Receive a list of cells and  create a string presenting the selected 
        cells. 
        :param cell_list: list of tuple
        
        """
        if self.notebook is not None:
            return self.notebook.create_axis_label(cell_list)
    
    def edit_axis_helper(self, tcrtl_label, tcrtl_title, label, title):
        """
        get controls to modify
        """
        tcrtl_label.SetValue(str(label))
        tcrtl_title.SetValue(str(title))
        
    def add_column(self):
        """
        """
        if self.notebook is not None:
            self.notebook.add_column()
        
    def on_remove_column(self):
        """
        """
        if self.notebook is not None:
            self.notebook.on_remove_column()
        
        
class GridFrame(wx.Frame):
    def __init__(self, parent=None, data_inputs=None, data_outputs=None, id=-1, 
                 title="Batch Results", size=(700, 400)):
        wx.Frame.__init__(self, parent=parent, id=id, title=title, size=size)
        self.parent = parent
        self.panel = GridPanel(self, data_inputs, data_outputs)
        menubar = wx.MenuBar()
        self.SetMenuBar(menubar)
        edit = wx.Menu()
        menubar.Append(edit, "&Edit")
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        add_col_menu = edit.Append(wx.NewId(), 'Add Column', 'Add column')
        wx.EVT_MENU(self, add_col_menu.GetId(), self.on_add_column)
        remove_col_menu = edit.Append(wx.NewId(), 'Remove Column', 
                                      'Remove Column')
        wx.EVT_MENU(self, remove_col_menu.GetId(), self.on_remove_column)

    def on_close(self, event):
        """
        """
        self.Hide()
        
    def on_remove_column(self, event):
        """
        Remove the selected column to the grid
        """
        self.panel.on_remove_column()
        
    def on_add_column(self, event):
        """
        Append a new column to the grid
        """
        self.panel.add_column()
        
    def set_data(self, data_inputs, data_outputs):
        """
        """
        self.panel.set_data(data_inputs, data_outputs)
      
      
class BatchOutputFrame(wx.Frame):
    """
    Allow to select where the result of batch will be displayed or stored
    """
    def __init__(self, parent, data_inputs, data_outputs, file_name="",
                 details="", *args, **kwds):
        """
        :param parent: Window instantiating this dialog
        :param result: result to display in a grid or export to an external 
                application.
        """
        #kwds['style'] = wx.CAPTION|wx.SYSTEM_MENU 
        wx.Frame.__init__(self, parent, *args, **kwds)
        self.parent = parent
        self.panel = wx.Panel(self)
        self.file_name = file_name
        self.details = details
        self.data_inputs = data_inputs
        self.data_outputs = data_outputs
        self.data = {}
        for item in (self.data_outputs, self.data_inputs):
            self.data.update(item)
        self.flag = 1
        self.SetSize((300, 200))
        self.local_app_selected = None
        self.external_app_selected = None
        self.save_to_file = None
        self._do_layout()
    
    def _do_layout(self):
        """
        Draw the content of the current dialog window
        """
        vbox = wx.BoxSizer(wx.VERTICAL)
        box_description = wx.StaticBox(self.panel, -1, str("Batch Outputs"))
        hint_sizer = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        selection_sizer = wx.GridBagSizer(5, 5)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        text = "Open with %s" % self.parent.application_name 
        self.local_app_selected = wx.RadioButton(self.panel, -1, text,
                                                style=wx.RB_GROUP)
        self.Bind(wx.EVT_RADIOBUTTON, self.onselect,
                    id=self.local_app_selected.GetId())
        text = "Open with Excel"
        self.external_app_selected  = wx.RadioButton(self.panel, -1, text)
        self.Bind(wx.EVT_RADIOBUTTON, self.onselect,
                    id=self.external_app_selected.GetId())
        text = "Save to File"
        self.save_to_file = wx.CheckBox(self.panel, -1, text)
        self.Bind(wx.EVT_CHECKBOX, self.onselect,
                    id=self.save_to_file.GetId())
        self.local_app_selected.SetValue(True)
        self.external_app_selected.SetValue(False)
        self.save_to_file.SetValue(False)
        button_close = wx.Button(self.panel, -1, "Close")
        button_close.Bind(wx.EVT_BUTTON, id=button_close.GetId(),
                           handler=self.on_close)
        button_apply = wx.Button(self.panel, -1, "Apply")
        button_apply.Bind(wx.EVT_BUTTON, id=button_apply.GetId(),
                        handler=self.on_apply)
        button_apply.SetFocus()
        hint = ""
        hint_sizer.Add(wx.StaticText(self.panel, -1, hint))
        hint_sizer.Add(selection_sizer)
        #draw area containing radio buttons
        ix = 0
        iy = 0
        selection_sizer.Add(self.local_app_selected, (iy, ix),
                           (1, 1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        iy += 1
        selection_sizer.Add(self.external_app_selected, (iy, ix),
                           (1, 1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        iy += 1
        selection_sizer.Add(self.save_to_file, (iy, ix),
                           (1, 1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        #contruction the sizer contaning button
        button_sizer.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)

        button_sizer.Add(button_close, 0,
                        wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        button_sizer.Add(button_apply, 0,
                                wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        vbox.Add(hint_sizer,  0, wx.EXPAND|wx.ALL, 10)
        vbox.Add(wx.StaticLine(self.panel, -1),  0, wx.EXPAND, 0)
        vbox.Add(button_sizer, 0 , wx.TOP|wx.BOTTOM, 10)
        self.SetSizer(vbox)
        
    def on_apply(self, event):
        """
        Get the user selection and display output to the selected application
        """
        if self.flag == 1:
            self.parent.open_with_localapp(data_inputs=self.data_inputs,
                                            data_outputs=self.data_outputs)
        elif self.flag == 2:
            self.parent.open_with_externalapp(data=self.data, 
                                           file_name=self.file_name,
                                           details=self.details)
    def on_close(self, event):
        """
        close the Window
        """
        self.Close()
        
    def onselect(self, event=None):
        """
        Receive event and display data into third party application
        or save data to file.
        
        """
        if self.save_to_file.GetValue():
            reader, ext = os.path.splitext(self.file_name)
            path = None
            location = os.getcwd()
            if self.parent is not None: 
                location = os.path.dirname(self.file_name)
                dlg = wx.FileDialog(self, "Save Project file",
                            location, self.file_name, ext, wx.SAVE)
                path = None
                if dlg.ShowModal() == wx.ID_OK:
                    path = dlg.GetPath()
                dlg.Destroy()
                if path != None:
                    if self.parent is not None and  self.data is not None:
                        self.parent.write_batch_tofile(data=self.data, 
                                               file_name=path,
                                               details=self.details)
        if self.local_app_selected.GetValue():
            self.flag = 1
        else:
            self.flag = 2
        return self.flag
    
  
        
if __name__ == "__main__":
    app = wx.App()
   
    try:
        data = {}
        j = 0
        for i in range(4):
            j += 1
            data["index"+str(i)] = [i/j, i*j, i, i+j]
            
        frame = GridFrame(data_outputs=data, data_inputs=data)
        frame.Show(True)
    except:
        print sys.exc_value
        
    app.MainLoop()