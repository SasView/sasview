


################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################
import os
import sys
import wx
import copy
import logging, time
from sans.invariant import invariant

from DataLoader.data_info import Data1D as LoaderData1D
from sans.guiframe.dataFitting import Theory1D, Data1D

from sans.guicomm.events import NewPlotEvent, StatusEvent
from sans.guicomm.events import ERR_DATA
from invariant_state import Reader as reader
from DataLoader.loader import Loader
from invariant_panel import InvariantPanel

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
        
        self.state_reader = None   
        """
        # Create a CanSAS/Pr reader
        self.state_reader = Reader(self.set_state)
        l = Loader()
        l.associate_file_reader('.inv', self.state_reader)  
        """   
        # Log startup
        logging.info("Invariant plug-in started")
       
    def populate_menu(self, id, parent):
        """
        Create and return the list of application menu
        items for the plug-in. 
        
        :param id: deprecated. Un-used.
        :param parent: parent window
        
        :return: plug-in menu
        """
        return []
    
    def help(self, evt):
        """
        Show a general help dialog. 
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
        
        :param parent: parent window
        
        :return: list of panels
        """
        ## Save a reference to the parent
        self.parent = parent
        #add error back to the data
        self.parent.Bind(ERR_DATA, self._on_data_error)
        
        
        self.invariant_panel = InvariantPanel(parent=self.parent)
        self.invariant_panel.set_manager(manager=self)
        self.perspective.append(self.invariant_panel.window_name)  
        #Create reader when fitting panel are created
        self.state_reader = reader(self.set_state)   
        #append that reader to list of available reader 
        loader = Loader()
        loader.associate_file_reader(".inv", self.state_reader)
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
        
        :param graph: the Graph object to which we attach the context menu
        
        :return: a list of menu items with call-back function
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
        
        :param event: menu event
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
                self.invariant_panel.set_current_data(data=data)
                
    def save_file(self, filepath, state=None):
        """
        Save data in provided state object.
                
        :param filepath: path of file to write to
        :param state: invariant state 
        """     
        
        # Write the state to file
        # First, check that the data is of the right type

        current_plottable = self.__data

        if issubclass(current_plottable.__class__, LoaderData1D):
            self.state_reader.write(filepath, current_plottable, state)
        else:
            raise RuntimeError, "invariant.save_file: the data being saved is not a DataLoader.data_info.Data1D object" 

    def set_state(self, state, datainfo=None):    
        """
        Call-back method for the state reader.
        This method is called when a .inv file is loaded.
        
        :param state: State object
        """
        try:
            if datainfo is None:
                raise RuntimeError, "invariant.set_state: datainfo parameter cannot be None in standalone mode"
            datainfo.meta_data['invstate'].file = datainfo.meta_data['invstate'].file
            datainfo.name = datainfo.meta_data['invstate'].file
            datainfo.filename = datainfo.meta_data['invstate'].file
            self.__data = datainfo
            self.__data.group_id = datainfo.filename
            self.__data.id = datainfo.filename

            temp_state = copy.deepcopy(state)
            
            # Load the invariant states
            # Make sure the user sees the invariant panel after loading
            self.parent.set_perspective(self.perspective)
            # set state
            self.invariant_panel.set_state(state=temp_state,data=self.__data)              

        except:
            logging.error("invariant.set_state: %s" % sys.exc_value)
        
    
        
    def plot_theory(self, data=None, name=None):
        """
        Receive a data set and post a NewPlotEvent to parent.
        
        :param data: extrapolated data to be plotted
        :param name: Data's name to use for the legend
        """
        import copy
        if data is None:
            new_plot = Theory1D(x=[], y=[], dy=None)
        else:
            scale =self.invariant_panel.get_scale()
            background = self.invariant_panel.get_background()
            
            if scale != 0:
                # Put back the sacle and bkg for plotting
                data.y = (data.y + background)/scale
                new_plot = Theory1D(x=data.x, y=data.y, dy=None)
            else:
                msg = "Scale can not be zero."
                raise ValueError, msg

        new_plot.name = name
        new_plot.xaxis(self.__data._xaxis, self.__data._xunit)
        new_plot.yaxis(self.__data._yaxis, self.__data._yunit)
        new_plot.group_id = self.__data.group_id
        new_plot.id = self.__data.id + name
        # Save theory_data in a state
        if data != None:
            name_head = name.split('-')
            if name_head[0]=='Low':
                self.invariant_panel.state.theory_lowQ = copy.deepcopy(new_plot)
            elif name_head[0]=='High':
                self.invariant_panel.state.theory_highQ = copy.deepcopy(new_plot)

        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title=self.__data.name))
        
    def plot_data(self, scale, background):
        """
        replot the current data if the user enters a new scale or background
        """
        new_plot = scale * self.__data - background
        new_plot.name = self.__data.name
        new_plot.group_id = self.__data.group_id
        new_plot.id = self.__data.id 
       
        # Save data in a state: but seems to never happen 
        if new_plot != None:
            self.invariant_panel.state.data = copy.deepcopy(new_plot)
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title=new_plot.name))
        
