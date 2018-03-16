"""
Implement grid used to store results of a batch fit.

This is in Guiframe rather than fitting which is probably where it should be.
Actually could be a generic framework implemented in fit gui module.  At this
point however there this grid behaves independently of the fitting panel and
only knows about information sent to it but not about the fits or fit panel and
thus cannot feed back to the fitting panel.  This could change in the future.

The organization of the classes goes as:

.. note:: Path to this is: /sasview/src/sas/sasgui/guiframe/data_processor.py

.. note:: Path to image is: /sasview/src/sas/sasgui/guiframe/media/BatchGridClassLayout.png

.. image:: ../../user/sasgui/guiframe/BatchGridClassLayout.png
   :align: center

"""
from __future__ import print_function

import os
import sys
import copy
import math
import re
import wx
import numpy as np

import wx.aui
from wx.aui import AuiNotebook as nb
import wx.lib.sheet as sheet
from wx.lib.scrolledpanel import ScrolledPanel

from sas.sasgui.guiframe.panel_base import PanelBase
from sas.sasgui.guiframe.events import NewPlotEvent
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.plottools import plottables
from sas.sasgui.guiframe.dataFitting import Data1D


FUNC_DICT = {"sqrt": "math.sqrt",
             "pow": "math.sqrt"}

class BatchCell(object):
    """
    Object describing a cell in  the grid.
    """
    def __init__(self):
        """
        Initialize attributes of class (label, value, col, row, object)
        """
        self.label = ""
        self.value = None
        self.col = -1
        self.row = -1
        self.object = []


def parse_string(sentence, list):
    """
    Return a dictionary of column label and index or row selected

    :param sentence: String to parse
    :param list: list of columns label
    :returns: col_dict
    """

    p2 = re.compile(r'\d+')
    p = re.compile(r'[\+\-\*\%\/]')
    labels = p.split(sentence)
    col_dict = {}
    for elt in labels:
        rang = None
        temp_arr = []
        for label in  list:
            label_pos = elt.find(label)
            separator_pos = label_pos + len(label)
            if label_pos != -1 and len(elt) >= separator_pos  and\
                elt[separator_pos] == "[":
                # the label contain , meaning the range selected is not 
                # continuous
                if elt.count(',') > 0:
                    new_temp = []
                    temp = elt.split(label)
                    for item in temp:
                        range_pos = item.find(":")
                        if range_pos != -1:
                            rang = p2.findall(item)
                            for i in xrange(int(rang[0]), int(rang[1]) + 1):
                                new_temp.append(i)
                    temp_arr += new_temp
                else:
                    # continuous range
                    temp = elt.split(label)
                    for item in temp:
                        if item.strip() != "":
                            range_pos = item.find(":")
                            if range_pos != -1:
                                rang = p2.findall(item)
                                for i in xrange(int(rang[0]), int(rang[1]) + 1):
                                    temp_arr.append(i)
                col_dict[elt] = (label, temp_arr)
    return col_dict


class SPanel(ScrolledPanel):
    """
    ensure proper scrolling of GridPanel 
    
    Adds a SetupScrolling call to the normal ScrolledPanel init.    
    GridPanel then subclasses this class
    
    """
    def __init__(self, parent, *args, **kwds):
        """
        initialize ScrolledPanel then force a call to SetupScrolling

        """
        ScrolledPanel.__init__(self, parent, *args, **kwds)
        self.SetupScrolling()


class GridCellEditor(sheet.CCellEditor):
    """
    Custom cell editor

    This subclasses the sheet.CCellEditor (itself a subclass of
    grid.GridCellEditor) in order to override two of its methods:
    PaintBackrgound and EndEdit.
    
    This is necessary as the sheet module is broken in wx 3.0.2 and
    improperly subclasses grid.GridCellEditor
    """
    def __init__(self, grid):
        """
        Override of CCellEditor init. Runs the grid.GridCellEditor init code
        """
        super(GridCellEditor, self).__init__(grid)

    def PaintBackground(self, dc, rect, attr):
        """
        Overrides wx.sheet.CCellEditor.PaintBackground which incorrectly calls
        the base class method.

        In wx3.0 all paint objects must explicitly
        have a wxPaintDC (Device Context) object.  Thus the paint event which
        generates a call to this method provides such a DC object and the
        base class in grid expects to receive that object.  sheet was apparently
        not updated to reflect this and hence fails.  This could thus
        become obsolete in a future bug fix of wxPython.

        Apart from adding a dc variable in the list of arguments in the def
        and in the call to the base class the rest of this method is copied
        as is from sheet.CCellEditor.PaintBackground

        **From original GridCellEditor docs:**

        Draws the part of the cell not occupied by the edit control.  The
        base class version just fills it with background colour from the
        attribute.

        .. note:: There is no need to override this if you don't need
                  to do something out of the ordinary.

        :param dc: the wxDC object for the paint
        """
        # Call base class method.
        DC = dc
        super(sheet.CCellEditor,self).PaintBackground(DC, rect, attr)

    def EndEdit(self, row, col, grid, previous):
        """
        Commit editing the current cell. Returns True if the value has changed.

        :param previous: previous value in the cell
        """
        changed = False                             # Assume value not changed
        val = self._tc.GetValue()                   # Get value in edit control
        if val != self._startValue:                 # Compare
            changed = True                          # If different then changed is True
            grid.GetTable().SetValue(row, col, val) # Update the table
        self._startValue = ''                       # Clear the class' start value
        self._tc.SetValue('')                       # Clear contents of the edit control
        return changed


class GridPage(sheet.CSheet):
    """
    Class that receives the results of a batch fit.

    GridPage displays the received results in a wx.grid using sheet.  This is
    then used by GridPanel and GridFrame to present the full GUI.
    """
    def __init__(self, parent, panel=None):
        """
        Initialize

        Initialize all the attributes of GridPage, and the events. include
        the init stuff from sheet.CSheet as well.
        """
        #sheet.CSheet.__init__(self, parent)

        # The following is the __init__ from CSheet. ##########################
        # We re-write it here because the class is broken in wx 3.0,
        # such that the cell editor is not able to receive the right
        # number of parameters when it is called. The only way to
        # pick a different cell editor is apparently to re-write the __init__.
        wx.grid.Grid.__init__(self, parent, -1)

        # Init variables
        self._lastCol = -1              # Init last cell column clicked
        self._lastRow = -1              # Init last cell row clicked
        self._selected = None           # Init range currently selected
                                        # Map string datatype to default renderer/editor
        self.RegisterDataType(wx.grid.GRID_VALUE_STRING,
                              wx.grid.GridCellStringRenderer(),
                              GridCellEditor(self))

        self.CreateGrid(4, 3)           # By default start with a 4 x 3 grid
        self.SetColLabelSize(18)        # Default sizes and alignment
        self.SetRowLabelSize(50)
        self.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_BOTTOM)
        self.SetColSize(0, 75)          # Default column sizes
        self.SetColSize(1, 75)
        self.SetColSize(2, 75)

        # Sink events
        self.Bind(wx.grid.EVT_GRID_RANGE_SELECT, self.OnRangeSelect)
        self.Bind(wx.grid.EVT_GRID_ROW_SIZE, self.OnRowSize)
        self.Bind(wx.grid.EVT_GRID_COL_SIZE, self.OnColSize)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnGridSelectCell)
        # NOTE: the following bind to standard sheet methods that are
        # overriden in this subclassn - actually we have currently
        # disabled the on_context_menu that would override the OnRightClick
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.OnCellChange)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnLeftClick)
        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightClick)
        #self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnLeftDoubleClick)
        # This ends the __init__ section for CSheet. ##########################



        # The following events must be bound even if CSheet is working 
        # properly and does not need the above re-implementation of the
        # CSheet init method.  Basically these override any intrinsic binding
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.on_right_click)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.on_left_click)

        self.AdjustScrollbars()
        #self.SetLabelBackgroundColour('#DBD4D4')
        self.uid = wx.NewId()
        self.parent = parent
        self.panel = panel
        self.col_names = []
        self.data_inputs = {}
        self.data_outputs = {}
        self.data = None
        self.details = ""
        self.file_name = None
        self._cols = 50
        self._rows = 3001
        self.last_selected_row = -1
        self.last_selected_col = -1
        self.col_width = 30
        self.row_height = 20
        self.max_row_touse = 0
        self.axis_value = []
        self.axis_label = ""
        self.selected_cells = []
        self.selected_cols = []
        self.selected_rows = []
        self.plottable_cells = []
        self.plottable_flag = False
        self.SetColMinimalAcceptableWidth(self.col_width)
        self.SetRowMinimalAcceptableHeight(self.row_height)
        self.SetNumberRows(self._rows)
        self.SetNumberCols(self._cols)
        color = self.parent.GetBackgroundColour()
        for col in range(self._cols):
            self.SetCellBackgroundColour(0, col, color)
        self.AutoSize()
        self.list_plot_panels = {}
        self.default_col_width = 75
        self.EnableEditing(True)
        if self.GetNumberCols() > 0:
            self.default_col_width = self.GetColSize(0)
        # We have moved these to the top of the init section with the
        # rest of the grid event bindings from the sheet init when
        # appropriate
        #self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.on_left_click)
        #self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.on_right_click)
        #self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.on_selected_cell)
        #self.Bind(wx.grid.EVT_GRID_CMD_CELL_CHANGE, self.on_edit_cell)
        #self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onContextMenu)

    def OnLeftClick(self, event):
        """
        Overrides sheet.CSheet.OnLefClick.

        Processes when a cell is selected by left clicking on that cell. First
        process the base Sheet method then the current class specific method
        """
        sheet.CSheet.OnLeftClick(self, event)
        self.on_selected_cell(event)


    def OnCellChange(self, event):
        """
        Overrides sheet.CSheet.OnCellChange.  

        Processes when a cell has been edited by a cell editor. Checks for the
        edited row being outside the max row to use attribute and if so updates
        the last row.  Then calls the base handler using skip.
        """
        row, _ = event.GetRow(), event.GetCol()
        if row > self.max_row_touse:
            self.max_row_touse = row
        if self.data is None:
            self.data = {}
        event.Skip()

    def on_selected_cell(self, event):
        """
        Handler catching cell selection.

        Called after calling base 'on left click' method.
        """

        flag = event.CmdDown() or event.ControlDown()
        flag_shift = event.ShiftDown()
        row, col = event.GetRow(), event.GetCol()
        cell = (row, col)
        if not flag and not flag_shift:
            self.selected_cols = []
            self.selected_rows = []
            self.selected_cells = []
            self.axis_label = ""
            self.axis_value = []
            self.plottable_list = []
            self.plottable_cells = []
            self.plottable_flag = False
        self.last_selected_col = col
        self.last_selected_row = row
        if col >= 0:
            if flag:
                label_row = row
            else:
                label_row = 0
            self.axis_label = self.GetCellValue(label_row, col)
            self.selected_cols.append(col)
        if flag_shift:
            if not self.selected_rows:
                min_r = 1
            else:
                min_r = min(self.selected_rows)
            for row_s in range(min_r, row + 1):
                cel = (row_s, col)
                if cel not in self.selected_cells:
                    if row > 0:
                        self.selected_cells.append(cel)
                        self.selected_rows.append(row)
            for row_s in self.selected_rows:
                cel = (row_s, col)
                if row_s > row:
                    try:
                        self.selected_cells.remove(cel)
                    except:
                        pass
                    try:
                        self.selected_rows.remove(row_s)
                    except:
                        pass
        elif flag:
            if cell not in self.selected_cells:
                if row > 0:
                    self.selected_cells.append(cell)
                    self.selected_rows.append(row)
            else:
                try:
                    self.selected_cells.remove(cell)
                except:
                    pass
                try:
                    self.selected_rows.remove(row)
                except:
                    pass
        else:
            self.selected_cells.append(cell)
            self.selected_rows.append(row)
        self.axis_value = []
        for cell_row, cell_col in self.selected_cells:
            if cell_row > 0 and cell_row < self.max_row_touse:
                self.axis_value.append(self.GetCellValue(cell_row, cell_col))
        event.Skip()

    def on_left_click(self, event):
        """
        Is triggered when the left mouse button is clicked while the mouse
        is hovering over the column 'label.'

        This processes the information on the selected column: the column name
        (in row 0 of column) and the range of cells with a valid value to be
        used by the GridPanel set_axis methods.
        """

        flag = event.CmdDown() or event.ControlDown()

        col = event.GetCol()
        row = event.GetRow()

        if not flag:
            self.selected_cols = []
            self.selected_rows = []
            self.selected_cells = []
            self.axis_label = ""
            self.axis_value = []
            self.plottable_list = []
            self.plottable_cells = []
            self.plottable_flag = False

        self.last_selected_col = col
        self.last_selected_row = row
        if row != -1 and row not in self.selected_rows:
            self.selected_rows.append(row)

        if col != -1:
            for row in range(1, self.GetNumberRows() + 1):
                cell = (row, col)
                if row > 0 and row < self.max_row_touse:
                    if cell not in self.selected_cells:
                        self.selected_cells.append(cell)
                    else:
                        if flag:
                            self.selected_cells.remove(cell)
            self.selected_cols.append(col)
            self.axis_value = []
            for cell_row, cell_col in self.selected_cells:
                val = self.GetCellValue(cell_row, cell_col)
                if not val:
                    self.axis_value.append(self.GetCellValue(cell_row, cell_col))
            self.axis_label = self.GetCellValue(0, col)
            if not self.axis_label:
                self.axis_label = " "
        event.Skip()

    def on_right_click(self, event):
        """
        Is triggered when the right mouse button is clicked while the mouse
        is hovering over the column 'label.'

        This brings up a context menu that allows the deletion of the column,
        or the insertion of a new column either to the right or left of the
        current column.  If inserting a new column can insert a blank column or
        choose a number of hidden columns.  By default all the error parameters
        are in hidden columns so as to save space on the grid.  Also any other
        intrinsic variables stored with the data such as Temperature, pressure,
        time etc can be used to populate this menu.
        """

        col = event.GetCol()
        row = event.GetRow()
        # Ignore the index column
        if col < 0 or row != -1:
            return
        self.selected_cols = []
        self.selected_cols.append(col)
        # Slicer plot popup menu
        slicerpop = wx.Menu()
        col_label_menu = wx.Menu()
        c_name = self.GetCellValue(0, col)
        label = "Insert column before %s " % str(c_name)
        slicerpop.AppendSubMenu(col_label_menu, '&%s' % str(label), str(label))
        row = 0
        label = self.GetCellValue(row, col)
        self.insert_col_menu(col_label_menu, label, self)

        col_after_menu = wx.Menu()
        label = "Insert column after %s " % str(c_name)
        slicerpop.AppendSubMenu(col_after_menu, '&%s' % str(label), str(label))
        self.insert_after_col_menu(col_after_menu, label, self)

        wx_id = wx.NewId()
        hint = 'Remove selected column %s'
        slicerpop.Append(wx_id, '&Remove Column', hint)
        wx.EVT_MENU(self, wx_id, self.on_remove_column)

        pos = wx.GetMousePosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(slicerpop, pos)
        event.Skip()

    def insert_col_menu(self, menu, label, window):
        """
        method called to populate the 'insert column before current column'
        submenu.
        """

        if self.data is None:
            return
        id = wx.NewId()
        title = "Empty"
        hint = 'Insert empty column before %s' % str(label)
        menu.Append(id, title, hint)
        wx.EVT_MENU(window, id, self.on_insert_column)
        row = 0
        col_name = [self.GetCellValue(row, col) for col in range(self.GetNumberCols())]
        for c_name in self.data.keys():
            if c_name not in col_name and self.data[c_name]:
                wx_id = wx.NewId()
                hint = "Insert %s column before the " % str(c_name)
                hint += " %s column" % str(label)
                menu.Append(wx_id, '&%s' % str(c_name), hint)
                wx.EVT_MENU(window, wx_id, self.on_insert_column)

    def insert_after_col_menu(self, menu, label, window):
        """
        Method called to populate the 'insert column after current column'
        submenu
        """

        if self.data is None:
            return
        wx_id = wx.NewId()
        title = "Empty"
        hint = 'Insert empty column after %s' % str(label)
        menu.Append(wx_id, title, hint)
        wx.EVT_MENU(window, wx_id, self.on_insert_after_column)
        row = 0
        col_name = [self.GetCellValue(row, col)
                        for col in range(self.GetNumberCols())]
        for c_name in self.data.keys():
            if c_name not in col_name and self.data[c_name]:
                wx_id = wx.NewId()
                hint = "Insert %s column after the " % str(c_name)
                hint += " %s column" % str(label)
                menu.Append(wx_id, '&%s' % str(c_name), hint)
                wx.EVT_MENU(window, wx_id, self.on_insert_after_column)

    def on_remove_column(self, event=None):
        """
        Called when user chooses remove from the column right click menu
        Checks the columnn exists then calls the remove_column method
        """

        if self.selected_cols is not None or len(self.selected_cols) > 0:
            col = self.selected_cols[0]
            self.remove_column(col=col, numCols=1)

    def remove_column(self, col, numCols=1):
        """
        Remove the col column from the current grid
        """

        # add data to the grid    
        row = 0
        col_name = self.GetCellValue(row, col)
        self.data[col_name] = []
        for row in range(1, self.GetNumberRows() + 1):
            if row < self.max_row_touse:
                value = self.GetCellValue(row, col)
                self.data[col_name].append(value)
                for k, value_list in self.data.iteritems():
                    if k != col_name:
                        length = len(value_list)
                        if length < self.max_row_touse:
                            diff = self.max_row_touse - length
                            for i in range(diff):
                                self.data[k].append("")
        self.DeleteCols(pos=col, numCols=numCols, updateLabels=True)

    def on_insert_column(self, event):
        """
        Called when user chooses insert 'column before' submenu
        of the column context menu obtained when right clicking on a given
        column header.

        Sets up to insert column into the current grid before the current
        highlighted column location and sets up what to populate that column
        with.  Then calls insert_column method to actually do the insertion. 
        """

        if self.selected_cols is not None or len(self.selected_cols) > 0:
            col = self.selected_cols[0]
            # add data to the grid
            wx_id = event.GetId()
            col_name = event.GetEventObject().GetLabelText(wx_id)
            self.insert_column(col=col, col_name=col_name)
            if  not issubclass(event.GetEventObject().__class__, wx.Menu):
                col += 1
                self.selected_cols[0] += 1

    def on_insert_after_column(self, event):
        """
        Called when user chooses insert 'column after' submenu
        of the column context menu obtained when right clicking on a given
        column header.

        Sets up to insert column into the current grid after the current
        highlighted column location and sets up what to populate that column
        with.  Then calls insert_column method to actually do the insertion. 
        """

        if self.selected_cols is not None or len(self.selected_cols) > 0:
            col = self.selected_cols[0] + 1
            # add data to the grid
            wx_id = event.GetId()
            col_name = event.GetEventObject().GetLabelText(wx_id)
            self.insert_column(col=col, col_name=col_name)
            if  not issubclass(event.GetEventObject().__class__, wx.Menu):
                self.selected_cols[0] += 1

    def insert_column(self, col, col_name):
        """
        Insert column at position col with data[col_name] into the current
        grid.
        """

        row = 0
        self.InsertCols(pos=col, numCols=1, updateLabels=True)
        if col_name.strip() != "Empty":
            self.SetCellValue(row, col, str(col_name.strip()))
        if col_name in self.data.keys():
            value_list = self.data[col_name]
            cell_row = 1
            for value in value_list:
                label = value#format_number(value, high=True)
                self.SetCellValue(cell_row, col, str(label))
                cell_row += 1
        self.AutoSizeColumn(col, True)
        width = self.GetColSize(col)
        if width < self.default_col_width:
            self.SetColSize(col, self.default_col_width)
        color = self.parent.GetBackgroundColour()
        self.SetCellBackgroundColour(0, col, color)
        self.ForceRefresh()

    def on_set_x_axis(self, event):
        """
        Just calls the panel version of the method
        """

        self.panel.set_xaxis(x=self.axis_value, label=self.axis_label)

    def on_set_y_axis(self, event):
        """
        Just calls the panel version of the method
        """

        self.panel.set_yaxis(y=self.axis_value, label=self.axis_label)

    def set_data(self, data_inputs, data_outputs, details, file_name):
        """
        Add data to the grid

        :param data_inputs: data to use from the context menu of the grid
        :param data_ouputs: default columns displayed
        """

        self.file_name = file_name
        self.details = details

        if data_outputs is None:
            data_outputs = {}
        self.data_outputs = data_outputs
        if data_inputs is None:
            data_inputs = {}
        self.data_inputs = data_inputs
        self.data = {}
        for item in (self.data_outputs, self.data_inputs):
            self.data.update(item)

        if  len(self.data_outputs) > 0:
            self._cols = self.GetNumberCols()
            self._rows = self.GetNumberRows()
            self.col_names = self.data_outputs.keys()
            self.col_names.sort()
            nbr_user_cols = len(self.col_names)
            #Add more columns to the grid if necessary
            if nbr_user_cols > self._cols:
                new_col_nbr = nbr_user_cols - self._cols + 1
                self.AppendCols(new_col_nbr, True)
            #Add more rows to the grid if necessary
            nbr_user_row = len(self.data_outputs.values()[0])
            if nbr_user_row > self._rows + 1:
                new_row_nbr = nbr_user_row - self._rows + 1
                self.AppendRows(new_row_nbr, True)
            # add data to the grid
            wx.CallAfter(self.set_grid_values)
        self.ForceRefresh()

    def set_grid_values(self):
        """
        Set the values in grids
        """

        # add data to the grid
        row = 0
        col = 0
        cell_col = 0
        for col_name in  self.col_names:
            # use the first row of the grid to add user defined labels
            self.SetCellValue(row, col, str(col_name))
            col += 1
            cell_row = 1
            value_list = self.data_outputs[col_name]

            for value in value_list:
                label = value
                if issubclass(value.__class__, BatchCell):
                    label = value.label
                try:
                    float(label)
                    label = str(label)#format_number(label, high=True)
                except:
                    label = str(label)
                self.SetCellValue(cell_row, cell_col, label)
                self.AutoSizeColumn(cell_col, True)
                width = self.GetColSize(cell_col)
                if width < self.default_col_width:
                    self.SetColSize(cell_col, self.default_col_width)

                cell_row += 1
            cell_col += 1
            if cell_row > self.max_row_touse:
                self.max_row_touse = cell_row

    def get_grid_view(self):
        """
        Return value contained in the grid
        """

        grid_view = {}
        for col in xrange(self.GetNumberCols()):
            label = self.GetCellValue(row=0, col=col)
            label = label.strip()
            if label != "":
                grid_view[label] = []
                for row in range(1, self.max_row_touse):
                    value = self.GetCellValue(row=row, col=col)
                    if value != "":
                        grid_view[label].append(value)
                    else:
                        grid_view[label].append(None)
        return grid_view

    def get_nofrows(self):
        """
        Return number of total rows
        """
        return self._rows

    def onContextMenu(self, event):
        """
        Method to handle cell right click context menu. 

        THIS METHOD IS NOT CURRENTLY USED.  It is designed to provide a
        cell pop up context by right clicking on a cell and gives the
        option to cut, paste, and clear. This will probably be removed in
        future versions and is being superceded by more traditional cut and
        paste options.
        """

        wx_id = wx.NewId()
        c_menu = wx.Menu()
        copy_menu = c_menu.Append(wx_id, '&Copy', 'Copy the selected cells')
        wx.EVT_MENU(self, wx_id, self.on_copy)

        wx_id = wx.NewId()
        c_menu.Append(wx_id, '&Paste', 'Paste the selected cells')
        wx.EVT_MENU(self, wx_id, self.on_paste)

        wx_id = wx.NewId()
        clear_menu = c_menu.Append(wx_id, '&Clear', 'Clear the selected cells')
        wx.EVT_MENU(self, wx_id, self.on_clear)

        # enable from flag
        has_selection = False
        selected_cel = self.selected_cells
        if len(selected_cel) > 0:
            _row, _col = selected_cel[0]
            has_selection = self.IsInSelection(_row, _col)
        if len(self.selected_cols) > 0:
            has_selection = True
        if len(self.selected_rows) > 0:
            has_selection = True
        copy_menu.Enable(has_selection)
        clear_menu.Enable(has_selection)
        try:
            # mouse event pos
            pos_evt = event.GetPosition()
            self.PopupMenu(c_menu, pos_evt)
        except:
            return

    def on_copy(self, event):
        """
        Called when copy is chosen from cell right click context menu

        THIS METHOD IS NOT CURRENTLY USED.  it is part of right click cell
        context menu which is being removed. This will probably be removed in
        future versions and is being superceded by more traditional cut and
        paste options
        """

        self.Copy()

    def on_paste(self, event):
        """
        Called when paste is chosen from cell right click context menu

        THIS METHOD IS NOT CURRENTLY USED.  it is part of right click cell
        context menu which is being removed. This will probably be removed in
        future versions and is being superceded by more traditional cut and
        paste options
        """

        if self.data is None:
            self.data = {}
        if self.file_name is None:
            self.file_name = 'copied_data'
        self.Paste()

    def on_clear(self, event):
        """
        Called when clear cell is chosen from cell right click context menu

        THIS METHOD IS NOT CURRENTLY USED.  it is part of right click cell
        context menu which is being removed. This will probably be removed in
        future versions and is being superceded by more traditional cut and
        paste options
        """

        self.Clear()

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
                    style=wx.aui.AUI_NB_WINDOWLIST_BUTTON |
                    wx.aui.AUI_BUTTON_DOWN |
                    wx.aui.AUI_NB_DEFAULT_STYLE |
                    wx.CLIP_CHILDREN)
        PanelBase.__init__(self, parent)
        self.gpage_num = 1
        self.enable_close_button()
        self.parent = parent
        self.manager = manager
        self.data = data
        #add empty page
        self.add_empty_page()
        self.pageClosedEvent = wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE
        self.Bind(self.pageClosedEvent, self.on_close_page)

    def add_empty_page(self):
        """
        """
        grid = GridPage(self, panel=self.parent)
        self.AddPage(grid, "", True)
        pos = self.GetPageIndex(grid)
        title = "Table" + str(self.gpage_num)
        self.SetPageText(pos, title)
        self.SetSelection(pos)
        self.enable_close_button()
        self.gpage_num += 1
        return grid, pos

    def enable_close_button(self):
        """
        display the close button on the tab if more than 1 tab exits.
        Otherwise remove the close button
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
        Return the select cell range from a given selected column. Checks that
        all cells are from the same column
        """

        pos = self.GetSelection()
        grid = self.GetPage(pos)
        #grid.selected_cols = [grid.GetSelectedRows()]#
        if len(grid.selected_cols) >= 1:
            col = grid.selected_cols[0]
            for c in grid.selected_cols:
                if c != col:
                    msg = "Edit axis doesn't understand this selection.\n"
                    msg += "Please select only one column"
                    raise (ValueError, msg)
            for (_, cell_col) in grid.selected_cells:
                if cell_col != col:
                    msg = "Cannot use cells from different columns for "
                    msg += "this operation.\n"
                    msg += "Please select elements of the same col.\n"
                    raise (ValueError, msg)

            # Finally check the highlighted cell if any cells missing
            self.get_highlighted_row(True)
        else:
            msg = "No item selected.\n"
            msg += "Please select only one column or one cell"
            raise (ValueError, msg)
        return grid.selected_cells

    def get_highlighted_row(self, is_number=True):
        """
        Add highlight rows
        """

        pos = self.GetSelection()
        grid = self.GetPage(pos)
        col = grid.selected_cols[0]
        # Finally check the highlighted cell if any cells missing
        for row in range(grid.get_nofrows()):
            if grid.IsInSelection(row, col):
                cel = (row, col)
                if row < 1 and not is_number:
                    continue
                # empty cell
                if not grid.GetCellValue(row, col).lstrip().rstrip():
                    if cel in grid.selected_cells:
                        grid.selected_cells.remove(cel)
                    continue
                if is_number:
                    try:
                        float(grid.GetCellValue(row, col))
                    except:
                        # non numeric cell
                        if cel in grid.selected_cells:
                            grid.selected_cells.remove(cel)
                        continue
                if cel not in grid.selected_cells:
                    grid.selected_cells.append(cel)

    def get_column_labels(self):
        """
        return dictionary of columns labels on the current page
        """

        pos = self.GetSelection()
        grid = self.GetPage(pos)
        labels = {}
        for col in range(grid.GetNumberCols()):
            label = grid.GetColLabelValue(int(col))
            if label.strip() != "":
                labels[label.strip()] = col
        return labels

    def create_axis_label(self, cell_list):
        """
        Receive a list of cells and  create a string presenting the selected
        cells that can be used as data for one axis of a plot.

        :param cell_list: list of tuple
        """
        pos = self.GetSelection()
        grid = self.GetPage(pos)
        label = ""
        col_name = ""
        def create_label(col_name, row_min=None, row_max=None):
            """
            """
            result = " "
            if row_min is not  None or row_max is not None:
                if row_min is None:
                    result = str(row_max) + "]"
                elif row_max is None:
                    result = str(col_name) + "[" + str(row_min) + ":"
                else:
                    result = str(col_name) + "[" + str(row_min) + ":"
                    result += str(row_max) + "]"
            return str(result)

        if len(cell_list) > 0:
            if len(cell_list) == 1:
                row_min, col = cell_list[0]
                col_name = grid.GetColLabelValue(int(col))

                col_title = grid.GetCellValue(0, col)
                label = create_label(col_name, row_min + 1, row_min + 1)
                return  label, col_title
            else:
                temp_list = copy.deepcopy(cell_list)
                temp_list.sort()
                length = len(temp_list)
                row_min, col = temp_list[0]
                row_max, _ = temp_list[length - 1]
                col_name = grid.GetColLabelValue(int(col))
                col_title = grid.GetCellValue(0, col)

                index = 0
                for row in xrange(row_min, row_max + 1):
                    if index > 0 and index < len(temp_list):
                        new_row, _ = temp_list[index]
                        if row != new_row:
                            temp_list.insert(index, (None, None))
                            if index - 1 >= 0:
                                new_row, _ = temp_list[index - 1]
                                if new_row is not None and new_row != ' ':
                                    label += create_label(col_name, None,
                                                          int(new_row) + 1)
                                else:
                                    label += "]"
                                label += ","
                            if index + 1 < len(temp_list):
                                new_row, _ = temp_list[index + 1]
                                if new_row is not None:
                                    label += create_label(col_name,
                                                          int(new_row) + 1, None)
                    if row_min is not None and row_max is not None:
                        if index == 0:
                            label += create_label(col_name,
                                                  int(row_min) + 1, None)
                        elif index == len(temp_list) - 1:
                            label += create_label(col_name, None,
                                                  int(row_max) + 1)
                    index += 1
                # clean up the list
                label_out = ''
                for item in label.split(','):
                    if item.split(":")[1] == "]":
                        continue
                    else:
                        label_out += item + ","

                return label_out, col_title

    def on_close_page(self, event):
        """
        close the page
        """

        if self.GetPageCount() == 1:
            event.Veto()
        wx.CallAfter(self.enable_close_button)

    def set_data(self, data_inputs, data_outputs, details="", file_name=None):
        """
        """
        if data_outputs is None or data_outputs == {}:
            return
        inputs, outputs = self.get_odered_results(data_inputs, data_outputs)
        for pos in range(self.GetPageCount()):
            grid = self.GetPage(pos)
            if grid.data is None:
                #Found empty page
                grid.set_data(data_inputs=inputs,
                              data_outputs=outputs,
                              details=details,
                              file_name=file_name)
                self.SetSelection(pos)
                return

        grid, pos = self.add_empty_page()
        grid.set_data(data_inputs=inputs,
                      data_outputs=outputs,
                      file_name=file_name,
                      details=details)

    def get_odered_results(self, inputs, outputs=None):
        """
        Order a list of 'inputs.' Used to sort rows and columns to present
        in batch results grid.
        """

        # Let's re-order the data from the keys in 'Data' name.
        if outputs is None:
            return
        try:
            # For outputs from batch
            to_be_sort = [str(item.label) for item in outputs['Data']]
        except:
            # When inputs are from an external file
            return inputs, outputs
        inds = np.lexsort((to_be_sort, to_be_sort))
        for key in outputs.keys():
            key_list = outputs[key]
            temp_key = [item for item in key_list]
            for ind in inds:
                temp_key[ind] = key_list[inds[ind]]
            outputs[key] = temp_key
        for key in inputs.keys():
            key_list = inputs[key]
            if len(key_list) == len(inds):
                temp_key = [item for item in key_list]
                for ind in inds:
                    temp_key[ind] = key_list[inds[ind]]
                inputs[key] = temp_key
            else:
                inputs[key] = []

        return inputs, outputs

    def add_column(self):
        """
        Append a new column to the grid
        """

        # I Believe this is no longer used now that we have removed the 
        # edit menu from the menubar - PDB July 12, 2015
        pos = self.GetSelection()
        grid = self.GetPage(pos)
        grid.AppendCols(1, True)

    def on_remove_column(self):
        """
        Remove the selected column from the grid
        """
        # I Believe this is no longer used now that we have removed the 
        # edit menu from the menubar - PDB July 12, 2015
        pos = self.GetSelection()
        grid = self.GetPage(pos)
        grid.on_remove_column(event=None)

class GridPanel(SPanel):
    """
    A ScrolledPanel class that contains the grid sheet as well as a number of
    widgets to create interesting plots and buttons for help etc.
    """

    def __init__(self, parent, data_inputs=None,
                 data_outputs=None, *args, **kwds):
        """
        Initialize the GridPanel
        """

        SPanel.__init__(self, parent, *args, **kwds)

        self.vbox = wx.BoxSizer(wx.VERTICAL)

        self.plotting_sizer = wx.FlexGridSizer(3, 7, 10, 5)
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.grid_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.vbox.AddMany([(self.grid_sizer, 1, wx.EXPAND, 0),
                           (wx.StaticLine(self, -1), 0, wx.EXPAND, 0),
                           (self.plotting_sizer),
                           (self.button_sizer, 0, wx.BOTTOM, 10)])
        self.parent = parent
        self._data_inputs = data_inputs
        self._data_outputs = data_outputs
        self.x = []
        self.y = []
        self.dy = []
        self.x_axis_label = None
        self.y_axis_label = None
        self.dy_axis_label = None
        self.x_axis_title = None
        self.y_axis_title = None
        self.x_axis_unit = None
        self.y_axis_unit = None
        self.view_button = None
        self.plot_button = None
        self.notebook = None
        self.plot_num = 1

        self.layout_grid()
        self.layout_plotting_area()
        self.SetSizer(self.vbox)

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

    def set_dyaxis(self, label="", dy=None):
        """
        """
        if dy is None:
            dy = []
        self.dy = dy
        self.dy_axis_label.SetValue("%s[:]" % str(label))

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
                    try:
                        axis.append(float(value))
                    except:
                        msg = "Invalid data in row %s column %s" % (str(row), str(col))
                        wx.PostEvent(self.parent.parent,
                                     StatusEvent(status=msg, info="error"))
                        return None
            else:
                axis.append(None)
        return axis

    def on_view(self, event):
        """
        Get object represented by the given cells and plot them.  Basically
        plot the colum in y vs the column in x.
        """

        pos = self.notebook.GetSelection()
        grid = self.notebook.GetPage(pos)
        title = self.notebook.GetPageText(pos)
        self.notebook.get_highlighted_row(False)
        if len(grid.selected_cells) == 0:
            msg = "Highlight a Data or Chi2 column first..."
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg, info="error"))
            return
        elif len(grid.selected_cells) > 20:
            msg = "Too many data (> 20) to plot..."
            msg += "\n Please select no more than 20 data."
            wx.MessageDialog(self, msg, 'Plotting', wx.OK)
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg, info="error"))
            return

        for cell in grid.selected_cells:
            row, col = cell
            label_row = 0
            label = grid.GetCellValue(label_row, col)
            if label in grid.data:
                values = grid.data[label]
                if row > len(values) or row < 1:
                    msg = "Invalid cell was chosen."
                    wx.PostEvent(self.parent.parent, StatusEvent(status=msg, info="error"))
                    continue
                else:
                    value = values[row - 1]
                if issubclass(value.__class__, BatchCell):
                    if value.object is None or len(value.object) == 0:
                        msg = "Row %s , " % str(row)
                        msg += "Column %s is NOT " % str(label)
                        msg += "the results of fits to view..."
                        wx.PostEvent(self.parent.parent, StatusEvent(status=msg, info="error"))
                        return
                    for new_plot in value.object:
                        if new_plot is None or \
                         not issubclass(new_plot.__class__,
                                        plottables.Plottable):
                            msg = "Row %s , " % str(row)
                            msg += "Column %s is NOT " % str(label)
                            msg += "the results of fits to view..."
                            wx.PostEvent(self.parent.parent,
                                         StatusEvent(status=msg, info="error"))
                            return
                        if issubclass(new_plot.__class__, Data1D):
                            if label in grid.list_plot_panels.keys():
                                group_id = grid.list_plot_panels[label]
                            else:
                                group_id = str(new_plot.group_id) + str(grid.uid)
                                grid.list_plot_panels[label] = group_id
                            if group_id not in new_plot.list_group_id:
                                new_plot.group_id = group_id
                                new_plot.list_group_id.append(group_id)
                        else:
                            if label.lower() in ["data", "chi2"]:
                                if len(grid.selected_cells) != 1:
                                    msg = "2D View: Please select one data set"
                                    msg += " at a time for View Fit Results."
                                    wx.PostEvent(self.parent.parent,
                                                 StatusEvent(status=msg, info="error"))
                                    return

                        wx.PostEvent(self.parent.parent,
                                     NewPlotEvent(plot=new_plot,
                                                  group_id=str(new_plot.group_id),
                                                  title=title))
                        msg = "Plotting the View Fit Results  completed!"
                        wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
                else:
                    msg = "Row %s , " % str(row)
                    msg += "Column %s is NOT " % str(label)
                    msg += "the results of fits to view..."
                    wx.PostEvent(self.parent.parent, StatusEvent(status=msg, info="error"))
                    return

    def on_plot(self, event):
        """
        Evaluate the contains of textcrtl and plot result
        """

        pos = self.notebook.GetSelection()
        grid = self.notebook.GetPage(pos)
        column_names = {}
        if grid is not None:
            column_names = self.notebook.get_column_labels()
        #evaluate x
        sentence = self.x_axis_label.GetValue()
        try:
            if sentence.strip() == "":
                msg = "Select column values for x axis"
                raise (ValueError, msg)
        except:
            msg = "X axis value error."
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg, info="error"))
            return
        dict = parse_string(sentence, column_names.keys())

        try:
            sentence = self.get_sentence(dict, sentence, column_names)
            x = eval(sentence)
        except:
            msg = "Need a proper x-range."
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg, info="error"))
            return
        #evaluate y
        sentence = self.y_axis_label.GetValue()
        try:
            if sentence.strip() == "":
                msg = "select value for y axis"
                raise (ValueError, msg)
        except:
            msg = "Y axis value error."
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg, info="error"))
            return
        dict = parse_string(sentence, column_names.keys())
        try:
            sentence = self.get_sentence(dict, sentence, column_names)
            y = eval(sentence)
        except:
            msg = "Need a proper y-range."
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg, info="error"))
            return
        #evaluate y
        sentence = self.dy_axis_label.GetValue()
        dy = None
        if sentence.strip() != "":
            dict = parse_string(sentence, column_names.keys())
            sentence = self.get_sentence(dict, sentence, column_names)
            try:
                dy = eval(sentence)
            except:
                msg = "Need a proper dy-range."
                wx.PostEvent(self.parent.parent, StatusEvent(status=msg, info="error"))
                return
        if len(x) != len(y) or (len(x) == 0 or len(y) == 0):
            msg = "Need same length for X and Y axis and both greater than 0"
            msg += " to plot.\n"
            msg += "Got X length = %s, Y length = %s" % (str(len(x)), str(len(y)))
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg, info="error"))
            return
        if dy is not None and (len(y) != len(dy)):
            msg = "Need same length for Y and dY axis and both greater than 0"
            msg += " to plot.\n"
            msg += "Got Y length = %s, dY length = %s" % (str(len(y)), str(len(dy)))
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg, info="error"))
            return
        if dy is None:
            dy = np.zeros(len(y))
        #plotting
        new_plot = Data1D(x=x, y=y, dy=dy)
        new_plot.id = wx.NewId()
        new_plot.is_data = False
        new_plot.group_id = wx.NewId()
        y_title = self.y_axis_title.GetValue()
        x_title = self.x_axis_title.GetValue()
        title = "%s_vs_%s" % (y_title, x_title)
        new_plot.xaxis(x_title, self.x_axis_unit.GetValue())
        new_plot.yaxis(y_title, self.y_axis_unit.GetValue())
        try:
            title = y_title.strip()
            title += "_" + self.notebook.GetPageText(pos)
            title += "_" + str(self.plot_num)
            self.plot_num += 1
            new_plot.name = title
            new_plot.xtransform = "x"
            new_plot.ytransform = "y"
            wx.PostEvent(self.parent.parent,
                         NewPlotEvent(plot=new_plot,
                                      group_id=str(new_plot.group_id), title=title))
            msg = "Plotting completed!"
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
            self.parent.parent.update_theory(data_id=new_plot.id, theory=new_plot)
        except:
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg, info="error"))

    def on_help(self, event):
        """
        Bring up the Batch Grid Panel Usage Documentation whenever
        the HELP button is clicked.

        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".  Note that when using old
        versions of Wx (before 2.9) and thus not the release version of
        installers, the help comes up at the top level of the file as
        webbrowser does not pass anything past the # to the browser when it is
        running "file:///...."

        :param evt: Triggers on clicking the help button
        """

        #import documentation window here to avoid circular imports
        #if put at top of file with rest of imports.
        from documentation_window import DocumentationWindow

        _TreeLocation = "user/sasgui/perspectives/fitting/fitting_help.html"
        _PageAnchor = "#batch-fit-mode"
        _doc_viewer = DocumentationWindow(self, -1, _TreeLocation, _PageAnchor,
                                          "Batch Mode Help")

    def get_sentence(self, dict, sentence, column_names):
        """
        Get sentence from dict
        """

        for tok, (col_name, list) in dict.iteritems():
            col = column_names[col_name]
            axis = self.get_plot_axis(col, list)
            if axis is None:
                return None
            sentence = sentence.replace(tok, "numpy.array(%s)" % str(axis))
        for key, value in FUNC_DICT.iteritems():
            sentence = sentence.replace(key.lower(), value)
        return sentence

    def layout_grid(self):
        """
        Draw the area related to the grid by adding it as the first element
        in the panel's grid_sizer
        """

        self.notebook = Notebook(parent=self)
        self.notebook.set_data(self._data_inputs, self._data_outputs)
        self.grid_sizer.Add(self.notebook, 1, wx.EXPAND, 0)

    def layout_plotting_area(self):
        """
        Add the area containing all the plot options, buttons etc to a plotting
        area sizer to later be added to the top level grid_sizer
        """

        view_description = wx.StaticBox(self, -1, 'Plot Fits/Residuals')
        note = "To plot the fits (or residuals), click the 'View Fits' button"
        note += "\n after highlighting the Data names (or Chi2 values)."
        note_text = wx.StaticText(self, -1, note)
        boxsizer1 = wx.StaticBoxSizer(view_description, wx.HORIZONTAL)
        self.x_axis_title = wx.TextCtrl(self, -1)
        self.y_axis_title = wx.TextCtrl(self, -1)
        self.x_axis_label = wx.TextCtrl(self, -1, size=(200, -1))
        self.y_axis_label = wx.TextCtrl(self, -1, size=(200, -1))
        self.dy_axis_label = wx.TextCtrl(self, -1, size=(200, -1))
        self.x_axis_add = wx.Button(self, -1, "Add")
        self.x_axis_add.Bind(event=wx.EVT_BUTTON, handler=self.on_edit_axis,
                             id=self.x_axis_add.GetId())
        self.y_axis_add = wx.Button(self, -1, "Add")
        self.y_axis_add.Bind(event=wx.EVT_BUTTON, handler=self.on_edit_axis,
                             id=self.y_axis_add.GetId())
        self.dy_axis_add = wx.Button(self, -1, "Add")
        self.dy_axis_add.Bind(event=wx.EVT_BUTTON, handler=self.on_edit_axis,
                              id=self.dy_axis_add.GetId())
        self.x_axis_unit = wx.TextCtrl(self, -1)
        self.y_axis_unit = wx.TextCtrl(self, -1)
        self.view_button = wx.Button(self, -1, "View Fits")
        view_tip = "Highlight the data set or the Chi2 column first."
        self.view_button.SetToolTipString(view_tip)
        wx.EVT_BUTTON(self, self.view_button.GetId(), self.on_view)
        self.plot_button = wx.Button(self, -1, "Plot")
        plot_tip = "Highlight a column for each axis and \n"
        plot_tip += "click the Add buttons first."

        self.plot_button.SetToolTipString(plot_tip)

        self.help_button = wx.Button(self, -1, "HELP")
        self.help_button.SetToolTipString("Get Help for Batch Mode")
        self.help_button.Bind(wx.EVT_BUTTON, self.on_help)

        boxsizer1.AddMany([(note_text, 0, wx.LEFT, 10),
                           (self.view_button, 0, wx.LEFT | wx.RIGHT, 10)])
        self.button_sizer.AddMany([(boxsizer1, 0,
                                    wx.LEFT | wx.RIGHT | wx.BOTTOM, 10),
                                   (self.plot_button, 0,
                                    wx.LEFT | wx.TOP | wx.BOTTOM, 12),
                                   (self.help_button,0,
                                    wx.LEFT | wx.TOP | wx.BOTTOM, 12)])

        wx.EVT_BUTTON(self, self.plot_button.GetId(), self.on_plot)
        self.plotting_sizer.AddMany(\
                   [(wx.StaticText(self, -1, "X-axis Label\nSelection Range"), 1,
                     wx.TOP | wx.BOTTOM | wx.LEFT, 10),
                    (self.x_axis_label, 1, wx.TOP | wx.BOTTOM, 10),
                    (self.x_axis_add, 1, wx.TOP | wx.BOTTOM | wx.RIGHT, 10),
                    (wx.StaticText(self, -1, "X-axis Label"), 1, wx.TOP | wx.BOTTOM | wx.LEFT, 10),
                    (self.x_axis_title, 1, wx.TOP | wx.BOTTOM, 10),
                    (wx.StaticText(self, -1, "X-axis Unit"), 1, wx.TOP | wx.BOTTOM, 10),
                    (self.x_axis_unit, 1, wx.TOP | wx.BOTTOM, 10),
                    (wx.StaticText(self, -1, "Y-axis Label\nSelection Range"), 1,
                     wx.BOTTOM | wx.LEFT, 10),
                    (self.y_axis_label, wx.BOTTOM, 10),
                    (self.y_axis_add, 1, wx.BOTTOM | wx.RIGHT, 10),
                    (wx.StaticText(self, -1, "Y-axis Label"), 1,
                     wx.BOTTOM | wx.LEFT, 10),
                    (self.y_axis_title, wx.BOTTOM, 10),
                    (wx.StaticText(self, -1, "Y-axis Unit"), 1, wx.BOTTOM, 10),
                    (self.y_axis_unit, 1, wx.BOTTOM, 10),
                    (wx.StaticText(self, -1, "dY-Bar (Optional)\nSelection Range"),
                     1, wx.BOTTOM | wx.LEFT, 10),
                    (self.dy_axis_label, wx.BOTTOM, 10),
                    (self.dy_axis_add, 1, wx.BOTTOM | wx.RIGHT, 10),
                    (-1, -1),
                    (-1, -1),
                    (-1, -1),
                    (-1, 1)])

    def on_edit_axis(self, event):
        """
        Get the selected column on  the visible grid and set values for axis
        """

        try:
            cell_list = self.notebook.on_edit_axis()
            label, title = self.create_axis_label(cell_list)
        except:
            msg = str(sys.exc_value)
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg, info="error"))
            return
        tcrtl = event.GetEventObject()
        if tcrtl == self.x_axis_add:
            self.edit_axis_helper(self.x_axis_label, self.x_axis_title, label, title)
        elif tcrtl == self.y_axis_add:
            self.edit_axis_helper(self.y_axis_label, self.y_axis_title, label, title)
        elif tcrtl == self.dy_axis_add:
            self.edit_axis_helper(self.dy_axis_label, None, label, None)

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

        if label is not None:
            tcrtl_label.SetValue(str(label))
        if title is not None:
            tcrtl_title.SetValue(str(title))

    def add_column(self):
        """
        """
        # I Believe this is no longer used now that we have removed the
        # edit menu from the menubar - PDB July 12, 2015
        if self.notebook is not None:
            self.notebook.add_column()

    def on_remove_column(self):
        """
        """
        # I Believe this is no longer used now that we have removed the
        # edit menu from the menubar - PDB July 12, 2015
        if self.notebook is not None:
            self.notebook.on_remove_column()


class GridFrame(wx.Frame):
    """
    The main wx.Frame for the batch results grid
    """

    def __init__(self, parent=None, data_inputs=None, data_outputs=None, id=-1,
                 title="Batch Fitting Results Panel", size=(800, 500)):
        """
        Initialize the Frame
        """

        wx.Frame.__init__(self, parent=parent, id=id, title=title, size=size)
        self.parent = parent
        self.panel = GridPanel(self, data_inputs, data_outputs)
        menubar = wx.MenuBar()
        self.SetMenuBar(menubar)

        self.curr_col = None
        self.curr_grid = None
        self.curr_col_name = ""
        self.file = wx.Menu()
        menubar.Append(self.file, "&File")

        hint = "Open file containing batch results"
        open_menu = self.file.Append(wx.NewId(), 'Open ', hint)
        wx.EVT_MENU(self, open_menu.GetId(), self.on_open)

        hint = "Open the the current grid into excel"
        self.open_excel_menu = self.file.Append(wx.NewId(), 'Open with Excel', hint)
        wx.EVT_MENU(self, self.open_excel_menu.GetId(), self.open_with_excel)
        self.file.AppendSeparator()
        self.save_menu = self.file.Append(wx.NewId(), 'Save As', 'Save into File')
        wx.EVT_MENU(self, self.save_menu.GetId(), self.on_save_page)

        # We need to grab a WxMenu handle here, otherwise the next one to grab
        # the handle will be treated as the Edi)t Menu handle when checking in
        # on_menu_open event handler and thus raise an exception when it hits an 
        # unitialized object.  Alternative is to comment out that whole section
        # in on_menu_open, but that would make it more difficult to undo the
        # hidding of the menu.   PDB  July 12, 2015.
        #
        # To enable the Edit menubar comment out next line and uncomment the
        # following line.
        self.edit = wx.Menu()
        #self.add_edit_menu()

        self.Bind(wx.EVT_MENU_OPEN, self.on_menu_open)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def add_edit_menu(self, menubar):
        """
        populates the edit menu on the menubar.  Not activated as of SasView
        3.1.0
        """
        self.edit = wx.Menu()

        add_table_menu = self.edit.Append(-1, 'New Table',
                                          'Add a New Table')
        self.edit.AppendSeparator()
        wx.EVT_MENU(self, add_table_menu.GetId(), self.add_table)

        self.copy_menu = self.edit.Append(-1, 'Copy',
                                          'Copy the selected cells')
        wx.EVT_MENU(self, self.copy_menu.GetId(), self.on_copy)
        self.paste_menu = self.edit.Append(-1, 'Paste',
                                           'Paste the selected Cells')
        wx.EVT_MENU(self, self.paste_menu.GetId(), self.on_paste)
        self.clear_menu = self.edit.Append(-1, 'Clear',
                                           'Clear the selected Cells')
        wx.EVT_MENU(self, self.clear_menu.GetId(), self.on_clear)

        self.edit.AppendSeparator()
        hint = "Insert column before the selected column"
        self.insert_before_menu = wx.Menu()
        self.insertb_sub_menu = self.edit.AppendSubMenu(self.insert_before_menu,
                                                        'Insert Before', hint)
        hint = "Insert column after the selected column"
        self.insert_after_menu = wx.Menu()
        self.inserta_sub_menu = self.edit.AppendSubMenu(self.insert_after_menu,
                                                        'Insert After', hint)
        hint = "Remove the selected column"
        self.remove_menu = self.edit.Append(-1, 'Remove Column', hint)
        wx.EVT_MENU(self, self.remove_menu.GetId(), self.on_remove_column)
        menubar.Append(self.edit, "&Edit")

    def on_copy(self, event):
        """
        On Copy from the Edit menu item on the menubar
        """
        # I Believe this is no longer used now that we have removed the 
        # edit menu from the menubar - PDB July 12, 2015
        if event is not None:
            event.Skip()
        pos = self.panel.notebook.GetSelection()
        grid = self.panel.notebook.GetPage(pos)
        grid.Copy()

    def on_paste(self, event):
        """
        On Paste from the Edit menu item on the menubar
        """
        # I Believe this is no longer used now that we have removed the 
        # edit menu from the menubar - PDB July 12, 2015
        if event is not None:
            event.Skip()
        pos = self.panel.notebook.GetSelection()
        grid = self.panel.notebook.GetPage(pos)
        grid.on_paste(None)

    def on_clear(self, event):
        """
        On Clear from the Edit menu item on the menubar
        """
        # I Believe this is no longer used now that we have removed the 
        # edit menu from the menubar - PDB July 12, 2015
        pos = self.panel.notebook.GetSelection()
        grid = self.panel.notebook.GetPage(pos)
        grid.Clear()

    def GetLabelText(self, id):
        """
        Get Label Text
        """
        for item in self.insert_before_menu.GetMenuItems():
            m_id = item.GetId()
            if m_id == id:
                return item.GetLabel()

    def on_remove_column(self, event):
        """
        On remove column from the Edit menu Item on the menubar
        """
        # I Believe this is no longer used now that we have removed the 
        # edit menu from the menubar - PDB July 12, 2015
        pos = self.panel.notebook.GetSelection()
        grid = self.panel.notebook.GetPage(pos)
        grid.on_remove_column(event=None)

    def on_menu_open(self, event):
        """
        On menu open
        """
        if self.file == event.GetMenu():
            pos = self.panel.notebook.GetSelection()
            grid = self.panel.notebook.GetPage(pos)
            has_data = (grid.data is not None and grid.data != {})
            self.open_excel_menu.Enable(has_data)
            self.save_menu.Enable(has_data)

        if self.edit == event.GetMenu():
            #get the selected column
            pos = self.panel.notebook.GetSelection()
            grid = self.panel.notebook.GetPage(pos)
            col_list = grid.GetSelectedCols()
            has_selection = False
            selected_cel = grid.selected_cells
            if len(selected_cel) > 0:
                _row, _col = selected_cel[0]
                has_selection = grid.IsInSelection(_row, _col)
            if len(grid.selected_cols) > 0:
                has_selection = True
            if len(grid.selected_rows) > 0:
                has_selection = True
            self.copy_menu.Enable(has_selection)
            self.clear_menu.Enable(has_selection)

            if len(col_list) > 0:
                self.remove_menu.Enable(True)
            else:
                self.remove_menu.Enable(False)
            if len(col_list) == 0 or len(col_list) > 1:
                self.insertb_sub_menu.Enable(False)
                self.inserta_sub_menu.Enable(False)
                label = "Insert Column Before"
                self.insertb_sub_menu.SetText(label)
                label = "Insert Column After"
                self.inserta_sub_menu.SetText(label)
            else:
                self.insertb_sub_menu.Enable(True)
                self.inserta_sub_menu.Enable(True)

                col = col_list[0]
                col_name = grid.GetCellValue(row=0, col=col)
                label = "Insert Column Before " + str(col_name)
                self.insertb_sub_menu.SetText(label)
                for item in self.insert_before_menu.GetMenuItems():
                    self.insert_before_menu.DeleteItem(item)
                grid.insert_col_menu(menu=self.insert_before_menu,
                                     label=col_name, window=self)
                label = "Insert Column After " + str(col_name)
                self.inserta_sub_menu.SetText(label)
                for item in self.insert_after_menu.GetMenuItems():
                    self.insert_after_menu.DeleteItem(item)
                grid.insert_after_col_menu(menu=self.insert_after_menu,
                                           label=col_name, window=self)
        event.Skip()



    def on_save_page(self, event):
        """
        Saves data in grid to a csv file.

        At this time only the columns displayed get saved.  Thus any error
        bars not inserted before saving will not be saved in the file
        """

        if self.parent is not None:
            pos = self.panel.notebook.GetSelection()
            grid = self.panel.notebook.GetPage(pos)
            if grid.file_name is None or grid.file_name.strip() == "" or \
                grid.data is None or len(grid.data) == 0:
                name = self.panel.notebook.GetPageText(pos)
                msg = " %s has not data to save" % str(name)
                wx.PostEvent(self.parent,
                             StatusEvent(status=msg, info="error"))

                return
            reader, ext = os.path.splitext(grid.file_name)
            path = None
            if self.parent is not None:
                location = os.path.dirname(grid.file_name)
                dlg = wx.FileDialog(self, "Save Project file",
                                    location, grid.file_name, ext, wx.SAVE)
                path = None
                if dlg.ShowModal() == wx.ID_OK:
                    path = dlg.GetPath()
                dlg.Destroy()
                if path is not None:
                    if self.parent is not None:
                        data = grid.get_grid_view()
                        self.parent.write_batch_tofile(data=data,
                                                       file_name=path,
                                                       details=grid.details)

    def on_open(self, event):
        """
        Open file containing batch result
        """

        if self.parent is not None:
            self.parent.on_read_batch_tofile(self)

    def open_with_excel(self, event):
        """
        open excel and display batch result in Excel
        """

        if self.parent is not None:
            pos = self.panel.notebook.GetSelection()
            grid = self.panel.notebook.GetPage(pos)
            data = grid.get_grid_view()
            if grid.file_name is None or grid.file_name.strip() == "" or \
                grid.data is None or len(grid.data) == 0:
                name = self.panel.notebook.GetPageText(pos)
                msg = " %s has not data to open on excel" % str(name)
                wx.PostEvent(self.parent,
                             StatusEvent(status=msg, info="error"))

                return
            self.parent.open_with_externalapp(data=data,
                                              file_name=grid.file_name,
                                              details=grid.details)

    def on_close(self, event):
        """
        """
        self.Hide()

    def on_append_column(self, event):
        """
        Append a new column to the grid
        """
        self.panel.add_column()

    def set_data(self, data_inputs, data_outputs, details="", file_name=None):
        """
        Set data
        """
        self.panel.notebook.set_data(data_inputs=data_inputs,
                                     file_name=file_name,
                                     details=details,
                                     data_outputs=data_outputs)

    def add_table(self, event):
        """
        Add a new table
        """
        # DO not event.Skip(): it will make 2 pages
        self.panel.notebook.add_empty_page()

class BatchOutputFrame(wx.Frame):
    """
    Allow to select where the result of batch will be displayed or stored
    """
    def __init__(self, parent, data_inputs, data_outputs, file_name="",
                 details="", *args, **kwds):
        """
        Initialize dialog

        :param parent: Window instantiating this dialog
        :param result: result to display in a grid or export to an external\
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
        self.local_app_selected = wx.RadioButton(self.panel, -1, text, style=wx.RB_GROUP)
        self.Bind(wx.EVT_RADIOBUTTON, self.onselect,
                  id=self.local_app_selected.GetId())
        text = "Open with Excel"
        self.external_app_selected = wx.RadioButton(self.panel, -1, text)
        self.Bind(wx.EVT_RADIOBUTTON, self.onselect, id=self.external_app_selected.GetId())
        text = "Save to File"
        self.save_to_file = wx.CheckBox(self.panel, -1, text)
        self.Bind(wx.EVT_CHECKBOX, self.onselect, id=self.save_to_file.GetId())
        self.local_app_selected.SetValue(True)
        self.external_app_selected.SetValue(False)
        self.save_to_file.SetValue(False)
        button_close = wx.Button(self.panel, -1, "Close")
        button_close.Bind(wx.EVT_BUTTON, id=button_close.GetId(), handler=self.on_close)
        button_apply = wx.Button(self.panel, -1, "Apply")
        button_apply.Bind(wx.EVT_BUTTON, id=button_apply.GetId(), handler=self.on_apply)
        button_apply.SetFocus()
        hint = ""
        hint_sizer.Add(wx.StaticText(self.panel, -1, hint))
        hint_sizer.Add(selection_sizer)
        #draw area containing radio buttons
        ix = 0
        iy = 0
        selection_sizer.Add(self.local_app_selected, (iy, ix),
                            (1, 1), wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        iy += 1
        selection_sizer.Add(self.external_app_selected, (iy, ix),
                            (1, 1), wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        iy += 1
        selection_sizer.Add(self.save_to_file, (iy, ix),
                            (1, 1), wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        #contruction the sizer contaning button
        button_sizer.Add((20, 20), 1, wx.EXPAND | wx.ADJUST_MINSIZE, 0)

        button_sizer.Add(button_close, 0,
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        button_sizer.Add(button_apply, 0,
                         wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 10)
        vbox.Add(hint_sizer, 0, wx.EXPAND | wx.ALL, 10)
        vbox.Add(wx.StaticLine(self.panel, -1), 0, wx.EXPAND, 0)
        vbox.Add(button_sizer, 0, wx.TOP | wx.BOTTOM, 10)
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
            _, ext = os.path.splitext(self.file_name)
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
                if path is not None:
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
            data["index" + str(i)] = [i / j, i * j, i, i + j]

        data_input = copy.deepcopy(data)
        data_input["index5"] = [10, 20, 40, 50]
        frame = GridFrame(data_outputs=data, data_inputs=data_input)
        frame.Show(True)
    except:
        print(sys.exc_value)

    app.MainLoop()
