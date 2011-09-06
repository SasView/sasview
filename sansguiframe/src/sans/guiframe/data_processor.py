"""
Implement grid used to store data
"""
import wx
import numpy
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
        cell = (event.GetRow(), event.GetCol())
        if not flag:
            self.selected_cells = []
        if cell in self.selected_cells:
            self.selected_cells.remove(cell)
        else:
            self.selected_cells.append(cell)
        event.Skip()
      
    def on_left_click(self, event):
        """
        Catch the left click on label mouse event
        """
        flag = event.CmdDown() or event.ControlDown()
        col = event.GetCol()
        if not flag:
            self.selected_cols  = []
        if col not in self.selected_cols:
            self.selected_cols.append(col)
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
            
    def set_data(self, data):
        """
        Add data to the grid
        """
        if data is None:
            data = {}
        if  len(data) > 0:
            self._cols = self.GetNumberCols()
            self._rows = self.GetNumberRows()
            self.data = data
            self.col_names = data.keys()
            self.col_names.sort() 
            nbr_user_cols = len(self.col_names)
            #Add more columns to the grid if necessary
            if nbr_user_cols > self._cols:
                new_col_nbr = nbr_user_cols -  self._cols 
                self.AppendCols(new_col_nbr, True)
            #Add more rows to the grid if necessary  
            nbr_user_row = len(self.data.values())
            if nbr_user_row > self._rows + 1:
                new_row_nbr =  nbr_user_row - self._rows 
                self.AppendRows(new_row_nbr, True)
            # add data to the grid    
            label_row = 0
            for index  in range(nbr_user_cols):
                # use the first row of the grid to add user defined labels
                self.SetCellValue(label_row, index, str(self.col_names[index]))
            col = 0
            for value_list in self.data.values():
                for row in range(1, len(value_list)):
                    self.SetCellValue(row, col, str(value_list[row]))
                col += 1
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
            row_min, _  = temp_list[0]    
            row_max = row_min
            label += str(col_name) + "[" + str(row_min) + ":"
            print "temp_list", temp_list
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
                    print "here"
        print "label ", label             
        return label 
    
    def on_close_page(self, event):
        """
        close the page
        """
        if self.GetPageCount() == 1:
            event.Veto()
        self.enable_close_button()
        
    def set_data(self, data):
        if data is None:
            return
            
        grid = GridPage(self, panel=self.parent)
        grid.set_data(data)  
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
    def __init__(self, parent,data=None, *args, **kwds):
        SPanel.__init__(self, parent , *args, **kwds)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.plotting_sizer = wx.FlexGridSizer(3, 7, 10, 5)
        self.grid_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.vbox.AddMany([(self.grid_sizer, 1, wx.EXPAND, 0),
                           (wx.StaticLine(self, -1), 0, wx.EXPAND, 0),
                           (self.plotting_sizer)])
        self.parent = parent
        self._data = data
        self.x = []
        self.y  = []
        self.x_axis_label = None
        self.y_axis_label = None
        self.x_axis_value = None
        self.y_axis_value = None
        self.x_axis_unit = None
        self.y_axis_unit = None
        self.plot_button = None
        self.grid = None
        self.layout_grid()
        self.layout_plotting_area()
        self.SetSizer(self.vbox)
        
    def set_data(self, data):
        """
        """
        if self.grid is not None:
            self.grid.set_data(data)
        
    def set_xaxis(self, label="", x=None) :
        if x is None:
            x = []
        self.x = x
        self.x_axis_value.SetValue("%s[:]" % str(label))
        self.x_axis_label.SetValue(str(label))
        
    def set_yaxis(self, label="", y=None) :
        if y is None:
            y = []
        self.y = y
        self.y_axis_value.SetValue("%s[:]" % str(label))
        self.y_axis_label.SetValue(str(label))
        
    def on_plot(self, event):
        """
        plotting
        """ 
        new_plot = Data1D(x=self.x, y=self.y)
        new_plot.id =  wx.NewId()
        new_plot.group_id = wx.NewId()
        title = "%s vs %s" % (self.y_axis_label.GetValue(), self.x_axis_label.GetValue())
        new_plot.xaxis(self.x_axis_label.GetValue(), self.x_axis_unit.GetValue())
        new_plot.yaxis(self.y_axis_label.GetValue(), self.y_axis_unit.GetValue())
        wx.PostEvent(self.parent.parent, 
                             NewPlotEvent(plot=new_plot, 
                        group_id=str(new_plot.group_id), title ="batch"))    
    def layout_grid(self):
        """
        Draw the area related to the grid
        """
        self.grid = Notebook(parent=self)
        self.grid.set_data(self._data)
        self.grid_sizer.Add(self.grid, 1, wx.EXPAND, 0)
       
    def layout_plotting_area(self):
        """
        Draw area containing options to plot
        """
        self.x_axis_label = wx.TextCtrl(self, -1)
        self.y_axis_label = wx.TextCtrl(self, -1)
        self.x_axis_value = wx.TextCtrl(self, -1, size=(200, -1))
        self.y_axis_value = wx.TextCtrl(self, -1, size=(200, -1))
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
                    (wx.StaticText(self, -1, "x-axis label"), 1, wx.LEFT, 10),
                    (self.x_axis_label, wx.TOP|wx.BOTTOM|wx.LEFT, 10),
                    (wx.StaticText(self, -1, "x-axis value"), 1, wx.LEFT, 10),
                    (self.x_axis_value, wx.TOP|wx.BOTTOM|wx.LEFT, 10),
                    (self.x_axis_add, 1, wx.LEFT|wx.RIGHT, 0),
                    (wx.StaticText(self, -1 , "unit"), 1, wx.LEFT|wx.RIGHT, 0),
                    (self.x_axis_unit, 0, wx.LEFT, 0),
                    (wx.StaticText(self, -1, "y-axis label"), 1, wx.LEFT, 10),
                    (self.y_axis_label,  wx.TOP|wx.BOTTOM|wx.LEFT, 10),
                    (wx.StaticText(self, -1, "y-axis value"), 1, wx.LEFT, 10),
                    (self.y_axis_value, wx.TOP|wx.BOTTOM|wx.LEFT, 10),
                    (self.y_axis_add, 1, wx.LEFT|wx.RIGHT, 0),
                    (wx.StaticText(self, -1 , "unit"), 1, wx.LEFT|wx.RIGHT, 0),
                    (self.y_axis_unit, 0, wx.LEFT, 0),
                      (-1, -1),
                      (-1, -1),
                      (-1, -1),
                      (-1, -1),
                      (-1, -1),
                      (-1, -1),
                      (self.plot_button, 1, wx.LEFT, 0)])
   
    def on_edit_axis(self, event):
        """
        Get the selected column on  the visible grid and set values for axis
        """
        cell_list = self.grid.on_edit_axis()
        self.create_axis_label(cell_list)
        
    def create_axis_label(self, cell_list):
        """
        Receive a list of cells and  create a string presenting the selected 
        cells. 
        :param cell_list: list of tuple
        
        """
        if self.grid is not None:
            return self.grid.create_axis_label(cell_list)
    
    def edit_axis_helper(self, tcrtl_label, tcrtl_value):
        """
        """
    def add_column(self):
        """
        """
        if self.grid is not None:
            self.grid.add_column()
        
    def on_remove_column(self):
        """
        """
        if self.grid is not None:
            self.grid.on_remove_column()
        
        
class GridFrame(wx.Frame):
    def __init__(self, parent=None, data=None, id=-1, 
                 title="Batch Results", size=(700, 400)):
        wx.Frame.__init__(self, parent=parent, id=id, title=title, size=size)
        self.parent = parent
        self.panel = GridPanel(self, data)
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
        
    def set_data(self, data):
        """
        """
        self.panel.set_data(data)
      
      
if __name__ == "__main__":
    app = wx.App()
   
    try:
        data = {}
        j = 0
        for i in range(4):
            j += 1
            data["index"+str(i)] = [i/j, i*j, i, i+j]
            
        frame = GridFrame(data=data)
        frame.Show(True)
    except:
        print sys.exc_value
        
    app.MainLoop()