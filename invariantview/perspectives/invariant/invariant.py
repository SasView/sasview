"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2009, University of Tennessee
"""
import wx

from sans.invariant import invariant

from DataLoader.data_info import Data1D as LoaderData1D
from sans.guiframe.dataFitting import Theory1D, Data1D

from sans.guicomm.events import NewPlotEvent, StatusEvent
from sans.guicomm.events import ERR_DATA
class Plugin:
    """
        This class defines the interface for invariant Plugin class
        that can be used by the gui_manager.
         
    """
    
    def __init__(self, standalone=False):
        """
            Abstract class for gui_manager Plugins.
        """
        ## Plug-in name. It will appear on the application menu.
        self.sub_menu = "Invariant"
        
        ## Reference to the parent window. Filled by get_panels() below.
        self.parent = None
        #dictionary containing data name and error on dy of that data 
        self.err_dy = {}
        ## List of panels that you would like to open in AUI windows
        #  for your plug-in. This defines your plug-in "perspective"
        self.perspective = []
       
    def populate_menu(self, id, parent):
        """
            Create and return the list of application menu
            items for the plug-in. 
            
            @param id: deprecated. Un-used.
            @param parent: parent window
            @return: plug-in menu
        """
        return []
    
    def help(self, evt):
        """
            Show a general help dialog. 
            TODO: replace the text with a nice image
            provide more hint on the SLD calculator
        """
        from help_panel import  HelpWindow
        frame = HelpWindow(None, -1)    
        frame.Show(True)
        
    def get_panels(self, parent):
        """
            Create and return the list of wx.Panels for your plug-in.
            Define the plug-in perspective.
            
            Panels should inherit from DefaultPanel defined below,
            or should present the same interface. They must define
            "window_caption" and "window_name".
            
            @param parent: parent window
            @return: list of panels
        """
        ## Save a reference to the parent
        self.parent = parent
        #add error back to the data
        self.parent.Bind(ERR_DATA, self._on_data_error)
        from invariant_panel import InvariantPanel
        self.invariant_panel = InvariantPanel(parent=self.parent)
        self.invariant_panel.set_manager(manager=self)
        self.perspective.append(self.invariant_panel.window_name)   
        # Return the list of panels
        return [self.invariant_panel]
    
    def get_tools(self):
        """
            Returns a set of menu entries for tools
        """
        return []
        
    
    def get_context_menu(self, graph=None):
        """
            This method is optional.
        
            When the context menu of a plot is rendered, the 
            get_context_menu method will be called to give you a 
            chance to add a menu item to the context menu.
            
            A ref to a Graph object is passed so that you can
            investigate the plot content and decide whether you
            need to add items to the context menu.  
            
            This method returns a list of menu items.
            Each item is itself a list defining the text to 
            appear in the menu, a tool-tip help text, and a
            call-back method.
            
            @param graph: the Graph object to which we attach the context menu
            @return: a list of menu items with call-back function
        """
        self.graph = graph
        invariant_option = "Compute invariant"
        invariant_hint = "Will displays the invariant panel for futher computation"
       
        for item in self.graph.plottables:
            if item.name == graph.selected_plottable :
                if issubclass(item.__class__,LoaderData1D):
           
                    if item.name !="$I_{obs}(q)$" and item.name !="$P_{fit}(r)$":
                        if hasattr(item, "group_id"):
                            return [[invariant_option, 
                                        invariant_hint, self._compute_invariant]]
        return []   

    
    def get_perspective(self):
        """
            Get the list of panel names for this perspective
        """
        return self.perspective
    
    def on_perspective(self, event):
        """
            Call back function for the perspective menu item.
            We notify the parent window that the perspective
            has changed.
            @param event: menu event
        """
        self.parent.set_perspective(self.perspective)
    
    def post_init(self):
        """
            Post initialization call back to close the loose ends
        """
        pass
    
    def set_default_perspective(self):
        """
           Call back method that True to notify the parent that the current plug-in
           can be set as default  perspective.
           when returning False, the plug-in is not candidate for an automatic 
           default perspective setting
        """
        return False
    
    def copy_data(self, item, dy=None):
        """
            receive a data 1D and the list of errors on dy
            and create a new data1D data
            @param return 
        """
        id = None
        if hasattr(item,"id"):
            id = item.id

        data = Data1D(x=item.x, y=item.y, dx=None, dy=None)
        data.copy_from_datainfo(item)
        item.clone_without_data(clone=data)    
        data.dy = dy
        data.name = item.name
        ## allow to highlight data when plotted
        data.interactive = item.interactive
        ## when 2 data have the same id override the 1 st plotted
        data.id = id
        data.group_id = item.group_id
        return data
    
    def _on_data_error(self, event):
        """
            receives and event from plotting plu-gins to store the data name and 
            their errors of y coordinates for 1Data hide and show error
        """
        self.err_dy = event.err_dy
        
    def _compute_invariant(self, event):    
        """
            Open the invariant panel to invariant computation
        """
        self.panel = event.GetEventObject()
        Plugin.on_perspective(self,event=event)
        for plottable in self.panel.graph.plottables:
            if plottable.name == self.panel.graph.selected_plottable:
                ## put the errors values back to the model if the errors were hiden
                ## before sending them to the fit engine
                if len(self.err_dy)>0:
                    dy = plottable.dy
                    if plottable.name in  self.err_dy.iterkeys():
                        dy = self.err_dy[plottable.name]
                    data = self.copy_data(plottable, dy)
                else:
                    data = plottable
                # Store reference to data
                self.__data = data
                # Set the data set to be user for invariant calculation
                self.invariant_panel.set_data(data=data)
        
    def plot_theory(self, data=None, name=None):
        """
            Receive a data set and post a NewPlotEvent to parent.
            @param data: extrapolated data to be plotted
            @param name: Data's name to use for the legend
        """
        if data is None:
            new_plot = Theory1D(x=[], y=[], dy=None)
        else:
            scale =self.invariant_panel.get_scale()
            background = self.invariant_panel.get_background()
            
            if scale != 0:
                # Put back the sacle and bkg for plotting
                data.y = (data.y )/scale
                new_plot = Theory1D(x=data.x, y=data.y, dy=None)
            else:
                msg = "Scale can not be zero."
                raise ValueError, msg

        new_plot.name = name
        new_plot.xaxis(self.__data._xaxis, self.__data._xunit)
        new_plot.yaxis(self.__data._yaxis, self.__data._yunit)
        new_plot.group_id = self.__data.group_id
        new_plot.id = self.__data.id + name
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title=self.__data.name))
        
    def plot_data(self, scale, background):
        """
            replot the current data if the user enters a new scale or background
        """
        new_plot = scale * self.__data - background
        new_plot.name = self.__data.name
        new_plot.group_id = self.__data.group_id
        new_plot.id = self.__data.id 
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title=new_plot.name))
        
