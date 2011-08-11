
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

class SizeDialog(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title, size=(300, 175))

        #panel = wx.Panel(self, -1)
        
        mainbox = wx.BoxSizer(wx.VERTICAL)
        vbox = wx.BoxSizer(wx.VERTICAL)
        textbox = wx.BoxSizer(wx.HORIZONTAL)
        
        text1 = "Enter in a custom size (float values > 0 accepted)"
        msg = wx.StaticText(self, -1, text1,(30,15), style=wx.ALIGN_CENTRE)
        msg.SetLabel(text1)
        self.myTxtCtrl = wx.TextCtrl(self, -1, '', (100, 50))
        
        textbox.Add(self.myTxtCtrl, flag=wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 
                 border=10, proportion=2)
        vbox.Add(msg, flag=wx.ALL, border=10, proportion=1)
        vbox.Add(textbox, flag=wx.EXPAND|wx.TOP|wx.BOTTOM|wx.ADJUST_MINSIZE,
                 border=10)
    
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self,wx.ID_OK, 'OK', size=(70, 30))
        closeButton = wx.Button(self,wx.ID_CANCEL, 'Close', size=(70, 30))
        hbox.Add(okButton, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 
                 border=10)
        hbox.Add(closeButton, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 
                 border=10)
        
        mainbox.Add(vbox, flag=wx.ALL, border=10)
        mainbox.Add(hbox, flag=wx.EXPAND|wx.TOP|wx.BOTTOM|wx.ADJUST_MINSIZE, 
                    border=10)
        self.SetSizer(mainbox)
    
    def getText(self):
        return self.myTxtCtrl.GetValue()

class ModelPanel1D(PlotPanel, PanelBase):
    """
    Plot panel for use with the GUI manager
    """
    
    ## Internal name for the AUI manager
    window_name = "plotpanel"
    ## Title to appear on top of the window
    window_caption = "Plot Panel"
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
      
        self.hide_menu = None
        ## Unique ID (from gui_manager)
        self.uid = None
        self.x_size = None
        ## Default locations
        self._default_save_location = os.getcwd() 
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
            #replace
            self.graph.replace(data)
            self.plots[data.id] = data
        else:
            self.plots[data.id] = data
            self.graph.add(self.plots[data.id]) 

        ## Set the view scale for all plots
        self._onEVT_FUNC_PROPERTY()
        ## render the graph<=No need this done in canvas
        #self.graph.render(self)
        #self.subplot.figure.canvas.draw_idle()
    
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
            position = "x: %8.3g    y: %8.3g" % (event.xdata, event.ydata)
            wx.PostEvent(self.parent, StatusEvent(status=position))
        # unfocus all
        self.parent.set_plot_unfocus()  
        #post nd event to notify guiframe that this panel is on focus
        wx.PostEvent(self.parent, PanelOnFocusEvent(panel=self))

        
    def _ontoggle_hide_error(self, event):
        """
        Toggle error display to hide or show
        """
        
        selected_plot = self.plots[self.graph.selected_plottable]
        if self.hide_menu.GetText() == "Hide Error":
            selected_plot.hide_error = True
        else:
            selected_plot.hide_error = False
        ## increment graph color
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()  
          
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
            self._slicerpop.AppendSeparator()
            if plot.name != 'SLD':
                wx.EVT_MENU(self, id, self._onSave)
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
                
                self._slicerpop.AppendSeparator()
    
                id = wx.NewId()
                self.hide_menu = self._slicerpop.Append(id, "Hide Error")
    
                if plot.dy is not None and plot.dy != []:
                    if plot.hide_error :
                        self.hide_menu.SetText('Show Error')
                    else:
                        self.hide_menu.SetText('Hide Error')
                else:
                    self.hide_menu.Enable(False)
                wx.EVT_MENU(self, id, self._ontoggle_hide_error)
                
                self._slicerpop.AppendSeparator()
                # Option to hide
                #TODO: implement functionality to hide a plottable (legend click)
        
        
        id = wx.NewId()
        self._slicerpop.Append(id, '&Change scale')
        wx.EVT_MENU(self, id, self._onProperties)
        id = wx.NewId()
        self._slicerpop.Append(id, '&Reset Graph')
        wx.EVT_MENU(self, id, self.onResetGraph)  
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self._slicerpop, pos)
     
    def onFreeze(self, event):
        """
        """
        plot = self.plots[self.graph.selected_plottable]
        self.parent.onfreeze([plot.id])
    
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
        self._onEVT_FUNC_PROPERTY()
        ## render the graph
        #self.graph.render(self)
        #self.subplot.figure.canvas.draw_idle()
        print "PARENT: ", self.parent
        wx.PostEvent(self.parent,
                      NewColorEvent(color=selected_plot.custom_color,
                                             id=selected_plot.id))
    
    def onChangeSize(self, event):
        
        menu = event.GetEventObject()
        id = event.GetId()
        label =  menu.GetLabel(id)
        selected_plot = self.plots[self.graph.selected_plottable]
        
        if label == "&Custom":
            sizedial = SizeDialog(None, -1, 'Change Marker Size')
            if sizedial.ShowModal() == wx.ID_OK:
                label = sizedial.getText()
            sizedial.Destroy()

        selected_plot.marker_size = int(label)
        self._onEVT_FUNC_PROPERTY()
        ## Set the view scale for all plots
        
        ## render the graph
        #self.graph.render(self)
        #self.subplot.figure.canvas.draw_idle()

    
    def onChangeSymbol(self, event):
        """
        """
        menu = event.GetEventObject()
        id = event.GetId()
        label =  menu.GetLabel(id)
        selected_plot = self.plots[self.graph.selected_plottable]
        selected_plot.symbol = self._symbol_labels[label]
        ## Set the view scale for all plots
        self._onEVT_FUNC_PROPERTY()
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
                if data.dx != None:
                    out.write("<X>   <Y>   <dY>   <dX>\n")
                else:
                    out.write("<X>   <Y>   <dY>\n")
            else:
                out.write("<X>   <Y>\n")
                
            for i in range(len(data.x)):
                if has_errors:
                    if data.dx != None:
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
        dlg = wx.FileDialog(self, "Choose a file",
                            self._default_save_location,
                             "", wildcard , wx.SAVE)
       
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
            # of the DataLoader.loader.Loader class.
            from DataLoader.loader import  Loader
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
            except:
                pass    
        dlg.Destroy()

    def _add_more_tool(self):
        """
        Add refresh button in the tool bar
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

    def _on_delete(self, event): 
        """
        Refreshes the plotpanel on refresh tollbar button
        """
        
        if self.parent is not None:
            wx.PostEvent(self.parent, 
                         NewPlotEvent(group_id=self.group_id,
                                      action="delete"))
            