"""
Implement grid used to store data
"""
import wx
import numpy
import sys
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
    def __init__(self, parent, panel=None):
        """
        """
        sheet.CSheet.__init__(self, parent)
        self.SetLabelBackgroundColour('#DBD4D4')
        self.panel = panel
        self.col_names = []
        self._cols = 0
        self._rows = 0
        self.SetNumberRows(self._cols)
        self.SetNumberCols(self._rows)
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.on_right_click)
        self.axis_value = []
        self.axis_label = ""
       
        
    def on_right_click(self, event):
        print "on double click", event.GetRow(), event.GetCol()
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
        self.panel.set_xaxis(x=self.axis_value, label=self.axis_label)
   
    def on_set_y_axis(self, event):
        self.panel.set_yaxis(y=self.axis_value, label=self.axis_label)     
            
    def set_data(self, data):
        """
        """
        if data is None:
            data = {}
        if  len(data) > 0:
            self.data = data
            self.col_names = data.keys()
            self.col_names.sort() 
            self._cols = len(self.data.keys()) 
            self._rows = max([len(v) for v in self.data.values()]) 
            self.SetNumberRows(int(self._rows))
            self.SetNumberCols(int(self._cols))
            for index  in range(len(self.col_names)):
                self.SetColLabelValue(index, str(self.col_names[index]))
                
            col = 0
            for value_list in self.data.values():
                for row in range(len(value_list)):
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
                    style= wx.NB_BOTTOM)
        PanelBase.__init__(self, parent)
    
        self.parent = parent
        self.manager = manager
        self.data = data
        self.grid = GridPage(self, panel=self.parent)
        self.AddPage(self.grid, "Batch")
        self.grid.SetFocus()
        
    def set_data(self, data):
        if data is None:
            data = {}
        pos = self.GetSelection()
        if pos != -1:
            selected_page = self.GetPage(pos)
            selected_page.set_data(data)  
            return
        if  len(data) > 0:
            self.data = data
            self.col_names = data.keys()
            self.col_names.sort() 
            self._cols = len(self.data.keys()) 
            self._rows = max([len(v) for v in self.data.values()]) 
            selected_page.SetNumberRows(int(self._rows))
            selected_page.SetNumberCols(int(self._cols))
            for index  in range(len(self.col_names)):
                self.SetColLabelValue(index, str(self.col_names[index]))
        return
        
        if  len(data) > 0:
            self.data = data
            self.col_names = data.keys()
            self.col_names.sort() 
            self._cols = len(self.data.keys()) 
            self._rows = max([len(v) for v in self.data.values()]) 
            for index in xrange(self._rows):
                self.row_names.append( str(index))
                self.AppendRows(index)  
                self.SetColLabelValue(index)
         
            #AppendCols(self, numCols, updateLabels)
            #SetColLabelValue(int col, const wxString& value)
            #AppendRows(self, numRows, updateLabels)    
       

class TableBase(Grid.PyGridTableBase):
    """
     grid receiving dictionary data structure as input
    """
    def __init__(self, data=None):
        """data is a dictionary of key=column_name , value list of row value.
        
        :Note: the value stored in the list will be append to the grid in the same order .
        :example:data = {col_1:[value1, value2], col_2:[value11, value22]}
        +--------++--------++--------+
        | Index  | col_1    | col2   |
        +--------++--------++--------+
        | Index1 | value1  | value2  |
        +--------++--------++--------+
        | Index2 | value11  | value22|
        +--------++--------++--------+
        """
        # The base class must be initialized *first*
        Grid.PyGridTableBase.__init__(self)
        self.data = {}
        self._rows = 0
        self._cols = 0
        self.col_names = []
        self.row_names = []
        
        if data is None:
            data = {}
        self.set_data(data)
        
    def set_data(self, data):
        if  len(data) > 0:
            self.data = data
            self.col_names = data.keys()
            self.col_names.sort() 
            self._cols = len(self.data.keys()) 
            self._rows = max([len(v) for v in self.data.values()]) 
            for index in xrange(self._rows):
                self.row_names.append( str(index))
         
    
          
    def GetNumberCols(self):
        return self._cols

    def GetNumberRows(self):
        return self._rows

    def GetColLabelValue(self, col):
        if len(self.col_names) > col:
            return self.col_names[col]
        
    def GetRowLabelValue(self, row):
        if len(self.row_names) > row:
            return self.row_names[row]

    def GetValue(self, row, col):
        pos = int(row)
        if len(self.data[self.col_names[col]]) > pos:
            return str(self.data[self.col_names[col]][pos])

    def GetRawValue(self, row, col):
        pos = int(row)
        if len(self.data[self.col_names[col]]) > pos:
            return self.data[self.col_names[col]][row]

    def SetValue(self, row, col, value):
        if len(self.data) == 0:
            return
        pos = int(row)
        if len(self.data[self.col_names[col]]) > pos:
            self.data[self.col_names[col]][row] = value
            
    def getRaw(self, row):
        pos = int(row)
        row_value = []
        for col in xrange(self.data.values()):
            if len(col) < pos:
                row_value.append(None)
            else:
                row_value.append(col[pos])
        return row_value
            

class Table(Grid.Grid):
    def __init__(self, parent, data=None):
        """
        """
        Grid.Grid.__init__(self, parent, -1)
        self._table = TableBase(data=data)
        self.SetTable(self._table)
        self.Bind(Grid.EVT_GRID_LABEL_RIGHT_CLICK, self.on_context_menu)
        
    def on_context_menu(self, event):
        row, col = event.GetRow(), event.GetCol()
        print "right click", row, col
        
    def set_data(self, data):
        self._table.set_data(data)
        
class SPanel(ScrolledPanel):
    def __init__(self, parent, *args, **kwds):
        ScrolledPanel.__init__(self, parent , *args, **kwds)
        self.SetupScrolling()  

class GridPanel(SPanel):
    def __init__(self, parent,data=None, *args, **kwds):
        SPanel.__init__(self, parent , *args, **kwds)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.plotting_sizer = wx.FlexGridSizer(3, 5, 10, 5)
        w, h = self.GetSize()
        #self.panel_grid = SPanel(self, -1, size=(w, -1))
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
                             NewPlotEvent(plot=new_plot, group_id=str(new_plot.group_id), title ="batch"))    
    def layout_grid(self):
        """
        Draw the area related to the grid
        """
        self.grid = Notebook(parent=self)
        self.grid.set_data(self._data)
        #self.grid = Table(parent=self, data=self._data)
        #vbox = wx.BoxSizer(wx.HORIZONTAL)
        self.grid_sizer.Add(self.grid, 1, wx.EXPAND, 0)
        #self.panel_grid.SetSizer(vbox)
        
    def layout_grid1(self):
        """
        Draw the area related to the grid
        """
        self.grid = Table(parent=self.panel_grid, data=self._data)
        vbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox.Add(self.grid, 1, wx.EXPAND, 0)
        self.panel_grid.SetSizer(vbox)
       
    def layout_plotting_area(self):
        """
        Draw area containing options to plot
        """
        self.x_axis_label = wx.TextCtrl(self, -1)
       
        self.y_axis_label = wx.TextCtrl(self, -1)
        
        self.x_axis_value = wx.TextCtrl(self, -1)
        self.y_axis_value = wx.TextCtrl(self, -1)
       
        self.x_axis_unit = wx.TextCtrl(self, -1)
        self.y_axis_unit = wx.TextCtrl(self, -1)
        self.plot_button = wx.Button(self, -1, "Plot")
        wx.EVT_BUTTON(self, self.plot_button.GetId(), self.on_plot)
        self.plotting_sizer.AddMany([(wx.StaticText(self, -1, "x"), 1, wx.LEFT, 10),
                                     (self.x_axis_label,  wx.TOP|wx.BOTTOM|wx.LEFT, 10),
                                      (self.x_axis_value,  wx.TOP|wx.BOTTOM|wx.LEFT, 10),
                                     (wx.StaticText(self, -1 , "unit"), 1, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE|wx.EXPAND, 0),
                                      (self.x_axis_unit),
                                      (wx.StaticText(self, -1, "y"), 1, wx.LEFT, 10),
                                       (self.y_axis_label,  wx.TOP|wx.BOTTOM|wx.LEFT, 10),
                                      (self.y_axis_value, wx.TOP|wx.BOTTOM|wx.LEFT, 10),
                                     (wx.StaticText(self, -1 , "unit"), 1, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE|wx.EXPAND, 0),
                                      (self.y_axis_unit),
                                      (-1, -1),
                                      (-1, -1),
                                      (-1, -1),
                                      (self.plot_button, 1, wx.LEFT, 30)])
   
        
    def add_column(self):
        if self.grid is not None:
            self.grid.add_column()
        
        
class GridFrame(wx.Frame):
    def __init__(self, parent=None, data=None, id=-1, title="Batch Results", size=(500, 400)):
        wx.Frame.__init__(self, parent=parent, id=id, title=title, size=size)
        self.parent = parent
        self.panel = GridPanel(self, data)
        menubar = wx.MenuBar()
        edit = wx.Menu()
        id_col = wx.NewId()
        edit.Append(id_col, 'Edit', '' )
        menubar.Append(edit, "&New column")
        self.SetMenuBar(menubar)
        wx.EVT_MENU(self, id_col, self.on_add_column)

        
    def on_add_column(self, event):
        self.panel.add_column()
    def set_data(self, data):
        self.panel.set_data(data)
      
      
if __name__ == "__main__":
    app = wx.App()
   
    try:
        data = {}
        j = 0
        for i in range(4):
            j += 1
            data["index"+str(i)] = [i/j, i*j, i, i+j]
            
        frame = TestFrame(data=data)
        frame.Show(True)
    except:
        print sys.exc_value
        
    app.MainLoop()