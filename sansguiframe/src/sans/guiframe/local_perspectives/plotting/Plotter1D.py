
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2008, University of Tennessee
################################################################################


import wx
import sys
import os
import pylab
import math
import numpy
import time

from danse.common.plottools.PlotPanel import PlotPanel
from danse.common.plottools.SizeDialog import SizeDialog
from danse.common.plottools.LabelDialog import LabelDialog
#from danse.common.plottools.plottables import Graph
from sans.guiframe import dataFitting 
from sans.guiframe.events import EVT_NEW_PLOT
from sans.guiframe.events import StatusEvent 
from sans.guiframe.events import NewPlotEvent
from sans.guiframe.events import NewColorEvent
from sans.guiframe.events import SlicerEvent
from sans.guiframe.events import PanelOnFocusEvent
from sans.guiframe.events import EVT_NEW_LOADED_DATA
from sans.guiframe.utils import PanelMenu
from sans.guiframe.dataFitting import Data1D
from sans.guiframe.panel_base import PanelBase
from binder import BindArtist

DEFAULT_QMAX = 0.05
DEFAULT_QSTEP = 0.001
DEFAULT_BEAM = 0.005
BIN_WIDTH = 1


class ModelPanel1D(PlotPanel, PanelBase):
    """
    Plot panel for use with the GUI manager
    """
    
    ## Internal name for the AUI manager
    window_name = "plotpanel"
    ## Title to appear on top of the window
    window_caption = "Graph"
    ## Flag to tell the GUI manager that this panel is not
    #  tied to any perspective
    ALWAYS_ON = True
    ## Group ID
    group_id = None
    
    def __init__(self, parent, id=-1, color = None,
                 dpi=None, style=wx.NO_FULL_REPAINT_ON_RESIZE, **kwargs):
        PlotPanel.__init__(self, parent, id=id, style=style, **kwargs)
        PanelBase.__init__(self, parent)
        ## Reference to the parent window
        self.parent = parent
        ## Plottables
        self.plots = {}
        #context menu
        self._slicerpop = None
        
        self._available_data = []
        self._menu_add_ids = []
        self._symbol_labels = self.get_symbol_label()
        self._color_labels = self.get_color_label()
        self.currColorIndex = ""
        self._is_changed_legend_label = False
      
        self.hide_menu = None
        ## Unique ID (from gui_manager)
        self.uid = None
        self.x_size = None
        ## Default locations
        #self._default_save_location = os.getcwd() 
        self.size = None       
        ## Graph        
        #self.graph = Graph()
        self.graph.xaxis("\\rm{Q}", 'A^{-1}')
        self.graph.yaxis("\\rm{Intensity} ", "cm^{-1}")
        self.graph.render(self)
        
        # In resizing event
        self.resizing = False
        self.canvas.set_resizing(self.resizing)
        self.Bind(wx.EVT_SIZE, self._OnReSize)
        self._add_more_tool()
        self.parent.SetFocus() 
        
    def get_symbol_label(self):
        """
        Associates label to symbol
        """
        _labels = {}
        i = 0
        _labels['Circle'] = i
        i += 1
        _labels['Cross X '] = i
        i += 1
        _labels['Triangle Down'] = i
        i += 1
        _labels['Triangle Up'] = i
        i += 1
        _labels['Triangle Left'] = i
        i += 1
        _labels['Triangle Right'] = i
        i += 1
        _labels['Cross +'] = i
        i += 1
        _labels['Square'] = i
        i += 1
        _labels['Diamond'] = i
        i += 1
        _labels['Diamond'] = i
        i += 1
        _labels['Hexagon1'] = i
        i += 1
        _labels['Hexagon2'] = i
        i += 1
        _labels['Pentagon'] = i
        i += 1
        _labels['Line'] = i
        return _labels
    
    def get_color_label(self):
        """
        Associates label to a specific color
        """
        _labels = {}
        i = 0
        _labels['Blue'] = i
        i += 1
        _labels['Green'] = i
        i += 1
        _labels['Red'] = i
        i += 1
        _labels['Cyan'] = i
        i += 1
        _labels['Magenta'] = i
        i += 1
        _labels['Yellow'] = i
        i += 1
        _labels['Black'] = i
        return _labels

    
    def set_data(self, list=None):
        """
        """
        pass
    
    def _reset(self):
        """
        Resets internal data and graph
        """    
        self.graph.reset()
        self.plots      = {}
        if self.is_zoomed:
            self.is_zoomed = False
        
    def _OnReSize(self, event):   
        """
        On response of the resize of a panel, set axes_visiable False
        """
        # It was found that wx >= 2.9.3 sends an event even if no size changed.
        # So manually recode the size (=x_size) and compare here.
        if self.x_size != None:
            if self.x_size == self.GetSize():
                self.resizing = False
                self.canvas.set_resizing(self.resizing)
                return
        self.x_size = self.GetSize()

        # Ready for another event
        # Do not remove this Skip. Otherwise it will get runtime error on wx>=2.9.
        event.Skip() 
        # set the resizing flag
        self.resizing = True
        self.canvas.set_resizing(self.resizing)
        self.parent.set_schedule(True)
        pos_x, pos_y = self.GetPositionTuple()
        if pos_x != 0 and pos_y != 0:
            self.size, _ = self.GetClientSizeTuple()
        #self.SetSizer(self.sizer)
        try:
            pixels = self.GetClientSize()
            self._SetSize(pixels)
            self.figure.Update()
            self.Update()
        except:
            pass
        
    def set_resizing(self, resizing=False):
        """
        Set the resizing (True/False)
        """
        self.resizing = resizing
        #self.canvas.set_resizing(resizing)
    
    def schedule_full_draw(self, func='append'):    
        """
        Put self in schedule to full redraw list
        """
        # append/del this panel in the schedule list
        self.parent.set_schedule_full_draw(self, func)
        

    def remove_data_by_id(self, id):
        """'
        remove data from plot
        """
        if id in self.plots.keys():
            data =  self.plots[id]
            self.graph.delete(data)
            data_manager = self._manager.parent.get_data_manager()
            data_list, theory_list = data_manager.get_by_id(id_list=[id])
            
            if id in data_list.keys():
                data = data_list[id]
            if id in theory_list.keys():
                data = theory_list[id]
            
            del self.plots[id]
            self.graph.render(self)
            self.subplot.figure.canvas.draw_idle()    
            if len(self.graph.plottables) == 0:
                #onRemove: graph is empty must be the panel must be destroyed
                self.parent.delete_panel(self.uid)

        
    def plot_data(self, data):
        """
        Data is ready to be displayed
        
        :param event: data event
        """
        if data.id in self.plots.keys():
            #Recover panel prop.s
            xlo, xhi = self.subplot.get_xlim()
            ylo, yhi = self.subplot.get_ylim()
            old_data = self.plots[data.id]
            if self._is_changed_legend_label:
                data.label = old_data.label
            data.custom_color = old_data.custom_color
            data.symbol = old_data.symbol
            data.markersize = old_data.markersize
            # Replace data
            self.graph.replace(data)
            self.plots[data.id] = data
            ## Set the view scale for all plots
            try:
                self._onEVT_FUNC_PROPERTY()
            except:
                msg=" Encountered singular points..."
                wx.PostEvent(self.parent, StatusEvent(status=\
                    "Plotting Erorr: %s"% msg, info="error")) 
            # Check if zoomed
            toolbar_zoomed = self.toolbar.GetToolEnabled(self.toolbar._NTB2_BACK)
            if self.is_zoomed or toolbar_zoomed:
                # Recover the x,y limits
                self.subplot.set_xlim((xlo, xhi))     
                self.subplot.set_ylim((ylo, yhi))  
            # Update Graph menu and help string        
            pos = self.parent._window_menu.FindItem(self.window_caption)
            helpString = 'Show/Hide Graph: '
            for plot in  self.plots.itervalues():
                helpString += (' ' + str(plot.label) +';')
            self.parent._window_menu.SetHelpString(pos, helpString)
        else:
            self.plots[data.id] = data
            self.graph.add(self.plots[data.id]) 
            ## Set the view scale for all plots
            try:
                self._onEVT_FUNC_PROPERTY()
            except:
                msg=" Encountered singular points..."
                wx.PostEvent(self.parent, StatusEvent(status=\
                    "Plotting Erorr: %s"% msg, info="error")) 
            self.toolbar.update()
            if self.is_zoomed:
                self.is_zoomed = False
      
          
    def draw_plot(self):
        """
        Draw plot
        """
        self.draw()  

    def onLeftDown(self,event): 
        """ 
        left button down and ready to drag
        Display the position of the mouse on the statusbar
        """
        PlotPanel.onLeftDown(self, event)
        ax = event.inaxes
        if ax != None:
            try:
                pos_x = float(event.xdata)# / size_x
                pos_y = float(event.ydata)# / size_y
                pos_x = "%8.3g"% pos_x
                pos_y = "%8.3g"% pos_y
                self.position = str(pos_x), str(pos_y)
                wx.PostEvent(self.parent, StatusEvent(status=self.position))
            except:
                self.position = None  
        # unfocus all
        self.parent.set_plot_unfocus()  
        #post nd event to notify guiframe that this panel is on focus
        wx.PostEvent(self.parent, PanelOnFocusEvent(panel=self))

        
    def _ontoggle_hide_error(self, event):
        """
        Toggle error display to hide or show
        """
        # Check zoom
        xlo, xhi = self.subplot.get_xlim()
        ylo, yhi = self.subplot.get_ylim()

        selected_plot = self.plots[self.graph.selected_plottable]
        if self.hide_menu.GetText() == "Hide Error Bar":
            selected_plot.hide_error = True
        else:
            selected_plot.hide_error = False
        ## increment graph color
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()  
        # Check if zoomed
        toolbar_zoomed = self.toolbar.GetToolEnabled(self.toolbar._NTB2_BACK)
        if self.is_zoomed or toolbar_zoomed:
            # Recover the x,y limits
            self.subplot.set_xlim((xlo, xhi))     
            self.subplot.set_ylim((ylo, yhi)) 

          
    def _onRemove(self, event):
        """
        Remove a plottable from the graph and render the graph 
        
        :param event: Menu event
        
        """
        ## Check if there is a selected graph to remove
        if self.graph.selected_plottable in self.plots.keys():
            selected_plot = self.plots[self.graph.selected_plottable]
            id = self.graph.selected_plottable
            self.remove_data_by_id(id)
            
    def onContextMenu(self, event):
        """
        1D plot context menu
        
        :param event: wx context event
        
        """
        self._slicerpop = PanelMenu()
        self._slicerpop.set_plots(self.plots)
        self._slicerpop.set_graph(self.graph)     
        # Various plot options
        id = wx.NewId()
        self._slicerpop.Append(id, '&Save Image', 'Save image as PNG')
        wx.EVT_MENU(self, id, self.onSaveImage)
        id = wx.NewId()
        self._slicerpop.Append(id, '&Print Image', 'Print image ')
        wx.EVT_MENU(self, id, self.onPrint)
        id = wx.NewId()
        self._slicerpop.Append(id, '&Print Preview', 'Print preview')
        wx.EVT_MENU(self, id, self.onPrinterPreview)
        
        id = wx.NewId()
        self._slicerpop.Append(id, '&Copy to Clipboard', 'Copy to the clipboard')
        wx.EVT_MENU(self, id, self.OnCopyFigureMenu)
                
        self._slicerpop.AppendSeparator()

        #add menu of other plugins
        item_list = self.parent.get_context_menu(self)

        if (not item_list == None) and (not len(item_list) == 0):
            for item in item_list:
                try:
                    id = wx.NewId()
                    self._slicerpop.Append(id, item[0], item[1])
                    wx.EVT_MENU(self, id, item[2])
                except:
                    msg = "ModelPanel1D.onContextMenu: "
                    msg += "bad menu item  %s" % sys.exc_value
                    wx.PostEvent(self.parent, StatusEvent(status=msg))
                    pass
            self._slicerpop.AppendSeparator()
        #id = wx.NewId()
        #self._slicerpop.Append(id, '&Print image', 'Print image')
        if self.graph.selected_plottable in self.plots:
            plot = self.plots[self.graph.selected_plottable]
            
            id = wx.NewId()
            name = plot.name
            self._slicerpop.Append(id, "&Save Points as a File")
            wx.EVT_MENU(self, id, self._onSave)
            self._slicerpop.AppendSeparator()
            if self.parent.ClassName.count('wxDialog') == 0: 
                id = wx.NewId()
                self._slicerpop.Append(id, '&Linear Fit')
                wx.EVT_MENU(self, id, self.onFitting)
                self._slicerpop.AppendSeparator()
    
                id = wx.NewId()
                self._slicerpop.Append(id, "Remove %s Curve" % name)
                wx.EVT_MENU(self, id, self._onRemove)
                if not plot.is_data:
                    id = wx.NewId()
                    self._slicerpop.Append(id, '&Freeze', 'Freeze')
                    wx.EVT_MENU(self, id, self.onFreeze)
                self._slicerpop.AppendSeparator()    
                symbol_menu = wx.Menu()
                for label in self._symbol_labels:
                    id = wx.NewId()
                    symbol_menu.Append(id, str(label), str(label))
                    wx.EVT_MENU(self, id, self.onChangeSymbol)
                id = wx.NewId()
                self._slicerpop.AppendMenu(id,'&Modify Symbol',  symbol_menu)
                
                color_menu = wx.Menu()
                for label in self._color_labels:
                    id = wx.NewId()
                    color_menu.Append(id, str(label), str(label))
                    wx.EVT_MENU(self, id, self.onChangeColor)
                id = wx.NewId()
                self._slicerpop.AppendMenu(id, '&Modify Symbol Color', color_menu)
                
                size_menu = wx.Menu()
                for i in range(10):
                    id = wx.NewId()
                    size_menu.Append(id, str(i), str(i))
                    wx.EVT_MENU(self, id, self.onChangeSize)
                id = wx.NewId()
                size_menu.Append(id, '&Custom', 'Custom')
                wx.EVT_MENU(self, id, self.onChangeSize)
                id = wx.NewId()
                self._slicerpop.AppendMenu(id, '&Modify Symbol Size', size_menu)
                
                self.hide_menu = self._slicerpop.Append(id, "Hide Error Bar")
    
                if plot.dy is not None and plot.dy != []:
                    if plot.hide_error :
                        self.hide_menu.SetText('Show Error Bar')
                    else:
                        self.hide_menu.SetText('Hide Error Bar')
                else:
                    self.hide_menu.Enable(False)
                wx.EVT_MENU(self, id, self._ontoggle_hide_error)
                
                self._slicerpop.AppendSeparator()
                id = wx.NewId()
                self._slicerpop.Append(id, '&Edit Legend Label', 'Edit Legend Label')
                wx.EVT_MENU(self, id, self.onEditLabels)
                # Option to hide
                #TODO: implement functionality to hide a plottable (legend click)

        loc_menu = wx.Menu()
        for label in self._loc_labels:
            id = wx.NewId()
            loc_menu.Append(id, str(label), str(label))
            wx.EVT_MENU(self, id, self.onChangeLegendLoc)
        id = wx.NewId()
        self._slicerpop.AppendMenu(id, '&Modify Legend Location', loc_menu)
        
        id = wx.NewId()
        self._slicerpop.Append(id, '&Toggle Legend On/Off', 'Toggle Legend On/Off')
        wx.EVT_MENU(self, id, self.onLegend)
        self._slicerpop.AppendSeparator()
        
        id = wx.NewId()
        self._slicerpop.Append(id, '&Edit Y Axis Label')
        wx.EVT_MENU(self, id, self._on_yaxis_label)     
        id = wx.NewId()
        self._slicerpop.Append(id, '&Edit X Axis Label')
        wx.EVT_MENU(self, id, self._on_xaxis_label)

        id = wx.NewId()
        self._slicerpop.Append(id, '&Toggle Grid On/Off', 'Toggle Grid On/Off')
        wx.EVT_MENU(self, id, self.onGridOnOff)
        self._slicerpop.AppendSeparator()
        
        if self.position != None:
            id = wx.NewId()
            self._slicerpop.Append(id, '&Add Text')
            wx.EVT_MENU(self, id, self._on_addtext)
            id = wx.NewId()
            self._slicerpop.Append(id, '&Remove Text')
            wx.EVT_MENU(self, id, self._on_removetext)
            self._slicerpop.AppendSeparator()
        id = wx.NewId()
        self._slicerpop.Append(id, '&Change Scale')
        wx.EVT_MENU(self, id, self._onProperties)
        self._slicerpop.AppendSeparator()
        id = wx.NewId()
        self._slicerpop.Append(id, '&Reset Graph Range')
        wx.EVT_MENU(self, id, self.onResetGraph)  
        try:
            pos_evt = event.GetPosition()
            pos = self.ScreenToClient(pos_evt)
        except:
            pos_x, pos_y = self.toolbar.GetPositionTuple()
            pos = (pos_x, pos_y + 5)
        
        if self.parent.ClassName.count('wxDialog') == 0:    
            self._slicerpop.AppendSeparator()
            id = wx.NewId()
            self._slicerpop.Append(id, '&Window Title')
            wx.EVT_MENU(self, id, self.onChangeCaption)
        
        self.PopupMenu(self._slicerpop, pos)
        
    def onFreeze(self, event):
        """
        """
        plot = self.plots[self.graph.selected_plottable]
        self.parent.onfreeze([plot.id])
        
    def onEditLabels(self, event):
        """
        Edit legend label
        """
        selected_plot = self.plots[self.graph.selected_plottable]
        label = selected_plot.label
        dial = LabelDialog(None, -1, 'Change Legend Label', label)
        if dial.ShowModal() == wx.ID_OK:
            newLabel = dial.getText() 
            selected_plot.label = newLabel
            # Updata Graph menu help string
            pos = self.parent._window_menu.FindItem(self.window_caption)
            helpString = 'Show/Hide Graph: '
            for plot in  self.plots.itervalues():
                helpString += (' ' + str(plot.label) +';')
            self.parent._window_menu.SetHelpString(pos, helpString)
            self._is_changed_legend_label = True
            #break
        dial.Destroy()
        
        ## render the graph
        try:
            self._onEVT_FUNC_PROPERTY()
        except:
            msg=" Encountered singular points..."
            wx.PostEvent(self.parent, StatusEvent(status=\
                    "Plotting Erorr: %s"% msg, info="error")) 
    
    def onChangeColor(self, event):
        """
        Changes the color of the graph when selected
        """
        menu = event.GetEventObject()
        id = event.GetId()
        label =  menu.GetLabel(id)
        selected_plot = self.plots[self.graph.selected_plottable]
        selected_plot.custom_color = self._color_labels[label]
        ## Set the view scale for all plots
        self._check_zoom_plot()
        #self._onEVT_FUNC_PROPERTY()
        #wx.PostEvent(self.parent,
        #              NewColorEvent(color=selected_plot.custom_color,
        #                                     id=selected_plot.id))
    
    def onChangeSize(self, event):
        
        menu = event.GetEventObject()
        id = event.GetId()
        label =  menu.GetLabel(id)
        selected_plot = self.plots[self.graph.selected_plottable]
        
        if label == "&Custom":
            sizedial = SizeDialog(None, -1, 'Change Marker Size')
            if sizedial.ShowModal() == wx.ID_OK:
                try:
                    label = sizedial.getText()
                    selected_plot.markersize = int(label)
                    self._check_zoom_plot()
                except:
                    msg = 'Symbol Size: Got an invalid Value.'
                    wx.PostEvent( self.parent, 
                          StatusEvent(status= msg, info='error'))
            sizedial.Destroy()


    
    def onChangeSymbol(self, event):
        """
        """
        menu = event.GetEventObject()
        id = event.GetId()
        label =  menu.GetLabel(id)
        selected_plot = self.plots[self.graph.selected_plottable]
        selected_plot.symbol = self._symbol_labels[label]
        ## Set the view scale for all plots
        self._check_zoom_plot()
        #self._onEVT_FUNC_PROPERTY()
        ## render the graph
        #self.graph.render(self)
        #self.subplot.figure.canvas.draw_idle()
        
        
        
    def _onsaveTXT(self, path):
        """
        Save file as txt
            
        :TODO: Refactor and remove this method. See TODO in _onSave.
        
        """
        data = self.plots[self.graph.selected_plottable]
       
        if not path == None:
            out = open(path, 'w')
            has_errors = True
            if data.dy == None or data.dy == []:
                has_errors = False
            # Sanity check
            if has_errors:
                try:
                    if len(data.y) != len(data.dy):
                        has_errors = False
                except:
                    has_errors = False
            if has_errors:
                if data.dx != None or data.dx != []:
                    out.write("<X>   <Y>   <dY>   <dX>\n")
                else:
                    out.write("<X>   <Y>   <dY>\n")
            else:
                out.write("<X>   <Y>\n")
                
            for i in range(len(data.x)):
                if has_errors:
                    if data.dx != None or data.dx != []:
                        out.write("%g  %g  %g  %g\n" % (data.x[i], 
                                                    data.y[i],
                                                    data.dy[i],
                                                    data.dx[i]))
                    else:
                        out.write("%g  %g  %g\n" % (data.x[i], 
                                                    data.y[i],
                                                    data.dy[i]))
                else:
                    out.write("%g  %g\n" % (data.x[i], 
                                            data.y[i]))
            out.close()                 
            try:
                self._default_save_location = os.path.dirname(path)
                self.parent._default_save_location = self._default_save_location
            except:
                pass    
                
    def _onSave(self, evt):
        """
        Save a data set to a text file
        
        :param evt: Menu event
        
        """
       
        path = None
        wildcard = "Text files (*.txt)|*.txt|"\
                    "CanSAS 1D files(*.xml)|*.xml" 
        default_name = self.plots[self.graph.selected_plottable].label
        if default_name.count('.') > 0:
            default_name = default_name.split('.')[0]
        default_name += "_out"
        if self.parent != None:
            self._default_save_location = self.parent._default_save_location
        dlg = wx.FileDialog(self, "Choose a file",
                            self._default_save_location,
                            default_name, wildcard , wx.SAVE)
       
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            # ext_num = 0 for .txt, ext_num = 1 for .xml
            # This is MAC Fix
            ext_num = dlg.GetFilterIndex()
            if ext_num == 0:
                format = '.txt'
            else:
                format = '.xml'
            path = os.path.splitext(path)[0] + format
            mypath = os.path.basename(path)
            
            #TODO: This is bad design. The DataLoader is designed 
            #to recognize extensions.
            # It should be a simple matter of calling the .
            #save(file, data, '.xml') method
            # of the sans.dataloader.loader.Loader class.
            from sans.dataloader.loader import  Loader
            #Instantiate a loader 
            loader = Loader() 
            data = self.plots[self.graph.selected_plottable]
            format = ".txt"
            if os.path.splitext(mypath)[1].lower() == format:
                # Make sure the ext included in the file name
                # especially on MAC
                fName = os.path.splitext(path)[0] + format
                self._onsaveTXT(fName)
            format = ".xml"
            if os.path.splitext(mypath)[1].lower() == format:
                # Make sure the ext included in the file name
                # especially on MAC
                fName = os.path.splitext(path)[0] + format
                loader.save(fName, data, format)
            try:
                self._default_save_location = os.path.dirname(path)
                self.parent._default_save_location = self._default_save_location
            except:
                pass    
        dlg.Destroy()

    def _add_more_tool(self):
        """
        Add refresh, add/delete button in the tool bar
        """
        if self.parent.__class__.__name__ != 'ViewerFrame':
            return
        self.toolbar.AddSeparator()
        id_delete = wx.NewId()
        delete =  wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_TOOLBAR)
        self.toolbar.AddSimpleTool(id_delete, delete,
                           'Delete', 'permanently Delete')

        self.toolbar.Realize()
        wx.EVT_TOOL(self, id_delete,  self._on_delete)
        
        """
        self.toolbar.AddSeparator()
        id_text = wx.NewId()
        text =  wx.ArtProvider.GetBitmap(wx.ART_CUT, wx.ART_TOOLBAR)
        self.toolbar.AddSimpleTool(id_text, text,
                           'Remove Text from Plot', 'Removes text from plot')

        self.toolbar.Realize()
        wx.EVT_TOOL(self, id_text,  self._on_removetext)
        """
    def _on_delete(self, event): 
        """
        Refreshes the plotpanel on refresh tollbar button
        """
        
        if self.parent is not None:
            wx.PostEvent(self.parent, 
                         NewPlotEvent(group_id=self.group_id,
                                      action="delete"))
            
            