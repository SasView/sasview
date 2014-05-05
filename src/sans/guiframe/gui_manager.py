"""
    Gui manager: manages the widgets making up an application
"""
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txtz
#
#copyright 2008, University of Tennessee
################################################################################


import wx
import wx.aui
import os
import sys
import time
import imp
import warnings
import re
warnings.simplefilter("ignore")
import logging
import httplib

from sans.guiframe.events import EVT_CATEGORY
from sans.guiframe.events import EVT_STATUS
from sans.guiframe.events import EVT_APPEND_BOOKMARK
from sans.guiframe.events import EVT_PANEL_ON_FOCUS
from sans.guiframe.events import EVT_NEW_LOAD_DATA
from sans.guiframe.events import EVT_NEW_COLOR
from sans.guiframe.events import StatusEvent
from sans.guiframe.events import NewPlotEvent
from sans.guiframe.gui_style import GUIFRAME
from sans.guiframe.gui_style import GUIFRAME_ID
from sans.guiframe.data_panel import DataPanel
from sans.guiframe.panel_base import PanelBase
from sans.guiframe.gui_toolbar import GUIToolBar
from sans.guiframe.data_processor import GridFrame
from sans.guiframe.events import EVT_NEW_BATCH
from sans.guiframe.CategoryManager import CategoryManager
from sans.dataloader.loader import Loader
from matplotlib import _pylab_helpers

def get_app_dir():
    """
        The application directory is the one where the default custom_config.py
        file resides.
    """
    # First, try the directory of the executable we are running
    app_path = sys.path[0]
    if os.path.isfile(app_path):
        app_path = os.path.dirname(app_path)
    if os.path.isfile(os.path.join(app_path, "custom_config.py")):
        app_path = os.path.abspath(app_path)
        logging.info("Using application path: %s", app_path)
        return app_path
    
    # Next, try the current working directory
    if os.path.isfile(os.path.join(os.getcwd(), "custom_config.py")):
        logging.info("Using application path: %s", os.getcwd())
        return os.path.abspath(os.getcwd())
    
    # Finally, try the directory of the sasview module
    #TODO: gui_manager will have to know about sasview until we
    # clean all these module variables and put them into a config class
    # that can be passed by sasview.py.
    logging.info(sys.executable)
    logging.info(str(sys.argv))
    from sans import sansview as sasview
    app_path = os.path.dirname(sasview.__file__)
    logging.info("Using application path: %s", app_path)
    return app_path

def get_user_directory():
    """
        Returns the user's home directory
    """
    userdir = os.path.join(os.path.expanduser("~"),".sasview")
    if not os.path.isdir(userdir):
        os.makedirs(userdir)
    return userdir
    
def _find_local_config(file, path):
    """
        Find configuration file for the current application
    """    
    config_module = None
    fObj = None
    try:
        fObj, path_config, descr = imp.find_module(file, [path])
        config_module = imp.load_module(file, fObj, path_config, descr) 
    except:
        logging.error("Error loading %s/%s: %s" % (path, file, sys.exc_value))
    finally:
        if fObj is not None:
            fObj.close()
    logging.info("GuiManager loaded %s/%s" % (path, file))
    return config_module

# Get APP folder
PATH_APP = get_app_dir() 
DATAPATH = PATH_APP

# GUI always starts from the App folder 
#os.chdir(PATH_APP)
# Read in the local config, which can either be with the main
# application or in the installation directory
config = _find_local_config('local_config', PATH_APP)
if config is None:
    config = _find_local_config('local_config', os.getcwd())
    if config is None:
        # Didn't find local config, load the default 
        import sans.guiframe.config as config
        logging.info("using default local_config")        
    else:
        logging.info("found local_config in %s" % os.getcwd())  
else:
    logging.info("found local_config in %s" % PATH_APP)     
           
from sans.guiframe.customdir  import SetupCustom
c_conf_dir = SetupCustom().setup_dir(PATH_APP)
custom_config = _find_local_config('custom_config', c_conf_dir)
if custom_config is None:
    custom_config = _find_local_config('custom_config', os.getcwd())
    if custom_config is None:
        msgConfig = "Custom_config file was not imported"
        logging.info(msgConfig)
    else:
        logging.info("using custom_config in %s" % os.getcwd())
else:
    logging.info("using custom_config from %s" % c_conf_dir)

#read some constants from config
APPLICATION_STATE_EXTENSION = config.APPLICATION_STATE_EXTENSION
APPLICATION_NAME = config.__appname__
SPLASH_SCREEN_PATH = config.SPLASH_SCREEN_PATH
WELCOME_PANEL_ON = config.WELCOME_PANEL_ON
SPLASH_SCREEN_WIDTH = config.SPLASH_SCREEN_WIDTH
SPLASH_SCREEN_HEIGHT = config.SPLASH_SCREEN_HEIGHT
SS_MAX_DISPLAY_TIME = config.SS_MAX_DISPLAY_TIME
if not WELCOME_PANEL_ON:
    WELCOME_PANEL_SHOW = False
else:
    WELCOME_PANEL_SHOW = True
try:
    DATALOADER_SHOW = custom_config.DATALOADER_SHOW
    TOOLBAR_SHOW = custom_config.TOOLBAR_SHOW
    FIXED_PANEL = custom_config.FIXED_PANEL
    if WELCOME_PANEL_ON:
        WELCOME_PANEL_SHOW = custom_config.WELCOME_PANEL_SHOW
    PLOPANEL_WIDTH = custom_config.PLOPANEL_WIDTH
    DATAPANEL_WIDTH = custom_config.DATAPANEL_WIDTH
    GUIFRAME_WIDTH = custom_config.GUIFRAME_WIDTH 
    GUIFRAME_HEIGHT = custom_config.GUIFRAME_HEIGHT
    CONTROL_WIDTH = custom_config.CONTROL_WIDTH 
    CONTROL_HEIGHT = custom_config.CONTROL_HEIGHT
    DEFAULT_PERSPECTIVE = custom_config.DEFAULT_PERSPECTIVE
    CLEANUP_PLOT = custom_config.CLEANUP_PLOT
    # custom open_path
    open_folder = custom_config.DEFAULT_OPEN_FOLDER
    if open_folder != None and os.path.isdir(open_folder):
        DEFAULT_OPEN_FOLDER = os.path.abspath(open_folder)
    else:
        DEFAULT_OPEN_FOLDER = PATH_APP
except:
    DATALOADER_SHOW = True
    TOOLBAR_SHOW = True
    FIXED_PANEL = True
    WELCOME_PANEL_SHOW = False
    PLOPANEL_WIDTH = config.PLOPANEL_WIDTH
    DATAPANEL_WIDTH = config.DATAPANEL_WIDTH
    GUIFRAME_WIDTH = config.GUIFRAME_WIDTH 
    GUIFRAME_HEIGHT = config.GUIFRAME_HEIGHT
    CONTROL_WIDTH = -1 
    CONTROL_HEIGHT = -1
    DEFAULT_PERSPECTIVE = None
    CLEANUP_PLOT = False
    DEFAULT_OPEN_FOLDER = PATH_APP

DEFAULT_STYLE = config.DEFAULT_STYLE

PLUGIN_STATE_EXTENSIONS =  config.PLUGIN_STATE_EXTENSIONS
OPEN_SAVE_MENU = config.OPEN_SAVE_PROJECT_MENU
VIEW_MENU = config.VIEW_MENU
EDIT_MENU = config.EDIT_MENU
extension_list = []
if APPLICATION_STATE_EXTENSION is not None:
    extension_list.append(APPLICATION_STATE_EXTENSION)
EXTENSIONS = PLUGIN_STATE_EXTENSIONS + extension_list
try:
    PLUGINS_WLIST = '|'.join(config.PLUGINS_WLIST)
except:
    PLUGINS_WLIST = ''
APPLICATION_WLIST = config.APPLICATION_WLIST
IS_WIN = True
IS_LINUX = False
CLOSE_SHOW = True
TIME_FACTOR = 2
MDI_STYLE = wx.DEFAULT_FRAME_STYLE
NOT_SO_GRAPH_LIST = ["BoxSum"]
PARENT_FRAME = wx.MDIParentFrame
CHILD_FRAME = wx.MDIChildFrame
if sys.platform.count("win32") < 1:
    IS_WIN = False
    TIME_FACTOR = 2
    if int(str(wx.__version__).split('.')[0]) == 2:
        if int(str(wx.__version__).split('.')[1]) < 9:
            CLOSE_SHOW = False
    if sys.platform.count("darwin") < 1:
        IS_LINUX = True
        PARENT_FRAME = wx.Frame
        CHILD_FRAME = wx.Frame
    
class ViewerFrame(PARENT_FRAME):
    """
    Main application frame
    """
    
    def __init__(self, parent, title, 
                 size=(GUIFRAME_WIDTH, GUIFRAME_HEIGHT),
                 gui_style=DEFAULT_STYLE, 
                 style=wx.DEFAULT_FRAME_STYLE,
                 pos=wx.DefaultPosition):
        """
        Initialize the Frame object
        """

        PARENT_FRAME.__init__(self, parent=parent, title=title, pos=pos, size=size)
        # title
        self.title = title
        self.__gui_style = gui_style       
        path = os.path.dirname(__file__)
        temp_path = os.path.join(path,'images')
        ico_file = os.path.join(temp_path,'ball.ico')
        if os.path.isfile(ico_file):
            self.SetIcon(wx.Icon(ico_file, wx.BITMAP_TYPE_ICO))
        else:
            temp_path = os.path.join(os.getcwd(),'images')
            ico_file = os.path.join(temp_path,'ball.ico')
            if os.path.isfile(ico_file):
                self.SetIcon(wx.Icon(ico_file, wx.BITMAP_TYPE_ICO))
            else:
                ico_file = os.path.join(os.path.dirname(os.path.sys.path[0]),
                             'images', 'ball.ico')
                if os.path.isfile(ico_file):
                    self.SetIcon(wx.Icon(ico_file, wx.BITMAP_TYPE_ICO))
        self.path = PATH_APP
        self.application_name = APPLICATION_NAME 
        ## Application manager
        self._input_file = None
        self.app_manager = None
        self._mgr = None
        #add current perpsective
        self._current_perspective = None
        self._plotting_plugin = None
        self._data_plugin = None
        #Menu bar and item
        self._menubar = None
        self._file_menu = None
        self._data_menu = None
        self._view_menu = None
        self._data_panel_menu = None
        self._help_menu = None
        self._tool_menu = None
        self._applications_menu_pos = -1
        self._applications_menu_name = None
        self._applications_menu = None
        self._edit_menu = None
        self._toolbar_menu = None
        self._save_appl_menu = None
        #tool bar
        self._toolbar = None
        # Status bar
        self.sb = None
        # number of plugins
        self._num_perspectives = 0
        # plot duck cleanup option
        self.cleanup_plots = CLEANUP_PLOT
        ## Find plug-ins
        # Modify this so that we can specify the directory to look into
        self.plugins = []
        #add local plugin
        self.plugins += self._get_local_plugins()
        self.plugins += self._find_plugins()
        ## List of panels
        self.panels = {}
        # List of plot panels
        self.plot_panels = {}
        # default Graph number fot the plotpanel caption
        self.graph_num = 0

        # Default locations
        self._default_save_location = DEFAULT_OPEN_FOLDER       
        # Welcome panel
        self.defaultPanel = None
        self.welcome_panel_class = None
        #panel on focus
        self.panel_on_focus = None
        #control_panel on focus
        self.cpanel_on_focus = None

        self.loader = Loader()   
        #data manager
        self.batch_on = False
        from sans.guiframe.data_manager import DataManager
        self._data_manager = DataManager()
        self._data_panel = None#DataPanel(parent=self)
        if self.panel_on_focus is not None:
            self._data_panel.set_panel_on_focus(
                                self.panel_on_focus.window_caption)
        # list of plot panels in schedule to full redraw
        self.schedule = False
        #self.callback = True
        self._idle_count = 0
        self.schedule_full_draw_list = []
        self.idletimer = wx.CallLater(TIME_FACTOR, self._onDrawIdle)
        
        self.batch_frame = GridFrame(parent=self)
        self.batch_frame.Hide()
        self.on_batch_selection(event=None)
        self.add_icon()
        
        # Register the close event so it calls our own method
        wx.EVT_CLOSE(self, self.WindowClose)
        # Register to status events
        self.Bind(EVT_STATUS, self._on_status_event)
        #Register add extra data on the same panel event on load
        self.Bind(EVT_PANEL_ON_FOCUS, self.set_panel_on_focus)
        self.Bind(EVT_APPEND_BOOKMARK, self.append_bookmark)
        self.Bind(EVT_NEW_LOAD_DATA, self.on_load_data)
        self.Bind(EVT_NEW_BATCH, self.on_batch_selection)
        self.Bind(EVT_NEW_COLOR, self.on_color_selection)
        self.Bind(EVT_CATEGORY, self.on_change_categories)
        self.setup_custom_conf()
        # Preferred window size
        self._window_width, self._window_height = size
        
    def add_icon(self):
        """
        get list of child and attempt to add the default icon 
        """
        
        list_children = self.GetChildren() 
        for frame in list_children:
            self.put_icon(frame)
        
    def put_icon(self, frame): 
        """
        Put icon on the tap of a panel
        """
        if hasattr(frame, "IsIconized"):
            if not frame.IsIconized():
                try:
                    icon = self.GetIcon()
                    frame.SetIcon(icon)
                except:
                    pass  
                
    def get_client_size(self):
        """
        return client size tuple
        """
        width, height = self.GetClientSizeTuple()
        height -= 45
        # Adjust toolbar height
        toolbar = self.GetToolBar()
        if toolbar != None:
            _, tb_h = toolbar.GetSizeTuple()
            height -= tb_h 
        return width, height
    
    def on_change_categories(self, evt):
        # ILL
        fitpanel = None
        for item in self.plugins:
            if hasattr(item, "get_panels"):
                if hasattr(item, "fit_panel"):
                    fitpanel = item.fit_panel

        if fitpanel != None:
            for i in range(0,fitpanel.GetPageCount()):
                fitpanel.GetPage(i)._populate_listbox()



    def on_set_batch_result(self, data_outputs, data_inputs=None,
                             plugin_name=""):
        """
        Display data into a grid in batch mode and show the grid
        """
        t = time.localtime(time.time())
        time_str = time.strftime("%b %d %H;%M of %Y", t)
        details = "File Generated by %s : %s" % (APPLICATION_NAME,
                                                     str(plugin_name))
        details += "on %s.\n" % time_str 
        ext = ".csv"
        file_name = "Batch_" + str(plugin_name)+ "_" + time_str + ext
        file_name = self._default_save_location + str(file_name)
        
        self.open_with_localapp(file_name=file_name,
                                details=details,
                                data_inputs=data_inputs,
                                    data_outputs=data_outputs)
     
    
    def open_with_localapp(self, data_inputs=None, details="", file_name=None,
                           data_outputs=None):
        """
        Display value of data into the application grid
        :param data: dictionary of string and list of items
        """
        self.batch_frame.set_data(data_inputs=data_inputs, 
                                  data_outputs=data_outputs,
                                  details=details,
                                  file_name=file_name)
        self.show_batch_frame(None)
        
    def on_read_batch_tofile(self, base):
        """
        Open a file dialog , extract the file to read and display values
        into a grid
        """
        path = None
        if self._default_save_location == None:
            self._default_save_location = os.getcwd()
        wildcard = "(*.csv; *.txt)|*.csv; *.txt"
        dlg = wx.FileDialog(base, 
                            "Choose a file", 
                            self._default_save_location, "",
                             wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if path is not None:
                self._default_save_location = os.path.dirname(path)
        dlg.Destroy()
        try:
            self.read_batch_tofile(file_name=path)
        except:
            msg = "Error occurred when reading the file; %s\n"% path
            msg += "%s\n"% sys.exc_value
            wx.PostEvent(self, StatusEvent(status=msg,
                                             info="error"))
            
    def read_batch_tofile(self, file_name):
        """
        Extract value from file name and Display them into a grid
        """
        if file_name is None or file_name.strip() == "":
            return
        data = {}
        fd = open(file_name, 'r')
        _, ext = os.path.splitext(file_name)
        separator = None
        if ext.lower() == ".csv":
            separator = ","
        buffer = fd.read()
        lines = buffer.split('\n')
        fd.close()
        column_names_line  = ""
        index = None
        details = ""
        for index in range(len(lines)):
            line = lines[index]
            line.strip()
            count = 0
            if separator == None:
                line.replace('\t', ' ')
                #found the first line containing the label
                col_name_toks = line.split()
                for item in col_name_toks:
                    if item.strip() != "":
                        count += 1
                    else:
                        line = " "
            elif line.find(separator) != -1:
                if line.count(separator) >= 2:
                    #found the first line containing the label
                    col_name_toks = line.split(separator)
                    for item in col_name_toks:
                        if item.strip() != "":
                            count += 1
            else:
                details += line
            if count >= 2:
                column_names_line = line
                break 
           
        if column_names_line.strip() == "" or index is None:
            return 

        col_name_toks = column_names_line.split(separator)
        c_index = 0
        for col_index in range(len(col_name_toks)):
            c_name = col_name_toks[col_index]
            if c_name.strip() != "":
                # distinguish between column name and value
                try:
                    float(c_name)
                    col_name = "Column %s"% str(col_index + 1)
                    index_min = index
                except:
                    col_name = c_name
                    index_min = index + 1
                data[col_name] = [ lines[row].split(separator)[c_index]
                                for row in range(index_min, len(lines)-1)]
                c_index += 1
                
        self.open_with_localapp(data_outputs=data, data_inputs=None,
                                file_name=file_name, details=details)
        
    def write_batch_tofile(self, data, file_name, details=""):
        """
        Helper to write result from batch into cvs file
        """
        self._default_save_location = os.path.dirname(file_name)
        name = os.path.basename(file_name)
        if data is None or file_name is None or file_name.strip() == "":
            return
        _, ext = os.path.splitext(name)
        try:
            fd = open(file_name, 'w')
        except:
            # On Permission denied: IOError
            temp_dir = get_user_directory()
            temp_file_name = os.path.join(temp_dir, name)
            fd = open(temp_file_name, 'w')
        separator = "\t"
        if ext.lower() == ".csv":
            separator = ","
        fd.write(str(details))
        for col_name  in data.keys():
            fd.write(str(col_name))
            fd.write(separator)
        fd.write('\n')
        max_list = [len(value) for value in data.values()]
        if len(max_list) == 0:
            return
        max_index = max(max_list)
        index = 0
        while(index < max_index):
            for value_list in data.values():
                if index < len(value_list):
                    fd.write(str(value_list[index]))
                    fd.write(separator)
                else:
                    fd.write('')
                    fd.write(separator)
            fd.write('\n')
            index += 1
        fd.close()
            
    def open_with_externalapp(self, data, file_name, details=""):
        """
        Display data in the another application , by default Excel
        """
        if not os.path.exists(file_name):
            self.write_batch_tofile(data=data, file_name=file_name,
                                               details=details)
        try:
            from win32com.client import Dispatch
            excel_app = Dispatch('Excel.Application')     
            wb = excel_app.Workbooks.Open(file_name) 
            excel_app.Visible = 1
        except:
            msg = "Error occured when calling Excel.\n"
            msg += "Check that Excel installed in this machine or \n"
            msg += "check that %s really exists.\n" % str(file_name)
            wx.PostEvent(self, StatusEvent(status=msg,
                                             info="error"))
            
         
    def on_batch_selection(self, event=None):
        """
        :param event: contains parameter enable . when enable is set to True
        the application is in Batch mode
        else the application is default mode(single mode)
        """
        if event is not None:
            self.batch_on = event.enable
        for plug in self.plugins:
            plug.set_batch_selection(self.batch_on)
            
    def on_color_selection(self, event):
        """
        :param event: contains parameters for id and color
        """ 
        color, id = event.color, event.id
        for plug in self.plugins:
            plug.add_color(color, id)
        
        
    def setup_custom_conf(self):
        """
        Set up custom configuration if exists
        """
        if custom_config == None:
            return
        
        if not FIXED_PANEL:
            self.__gui_style &= (~GUIFRAME.FIXED_PANEL)
            self.__gui_style |= GUIFRAME.FLOATING_PANEL

        if not DATALOADER_SHOW:
            self.__gui_style &= (~GUIFRAME.MANAGER_ON)

        if not TOOLBAR_SHOW:
            self.__gui_style &= (~GUIFRAME.TOOLBAR_ON)

        if WELCOME_PANEL_SHOW:
            self.__gui_style |= GUIFRAME.WELCOME_PANEL_ON   
             
    def set_custom_default_perspective(self):
        """
        Set default starting perspective
        """
        if custom_config == None:
            return
        for plugin in self.plugins:
            try:
                if plugin.sub_menu == DEFAULT_PERSPECTIVE:
                    
                    plugin.on_perspective(event=None)
                    frame = plugin.get_frame()
                    frame.Show(True)
                    #break
                else:
                    frame = plugin.get_frame()
                    frame.Show(False) 
            except:
                pass  
        return          
                
    def on_load_data(self, event):
        """
        received an event to trigger load from data plugin
        """
        if self._data_plugin is not None:
            self._data_plugin.load_data(event)
            
    def get_current_perspective(self):
        """
        return the current perspective
        """
        return self._current_perspective

    def get_save_location(self):
        """
        return the _default_save_location
        """
        return self._default_save_location
    
    def set_input_file(self, input_file):
        """
        :param input_file: file to read
        """
        self._input_file = input_file
        
    def get_data_manager(self):
        """
        return the data manager.
        """
        return self._data_manager
    
    def get_toolbar(self):
        """
        return the toolbar.
        """
        return self._toolbar
    
    def set_panel_on_focus(self, event):
        """
        Store reference to the last panel on focus
        update the toolbar if available
        update edit menu if available
        """
        if event != None:
            self.panel_on_focus = event.panel
        if self.panel_on_focus is not None:
            #Disable save application if the current panel is in batch mode
            flag = self.panel_on_focus.get_save_flag()
            if self._save_appl_menu != None:
                self._save_appl_menu.Enable(flag)

            if self.panel_on_focus not in self.plot_panels.values():
                for ID in self.panels.keys():
                    if self.panel_on_focus != self.panels[ID]:
                        self.panels[ID].on_kill_focus(None)

            if self._data_panel is not None and \
                            self.panel_on_focus is not None:
                self.set_panel_on_focus_helper()
                #update toolbar
                self._update_toolbar_helper()
                #update edit menu
                self.enable_edit_menu()

    def disable_app_menu(self, p_panel=None):  
        """
        Disables all menus in the menubar
        """
        return
    
    def send_focus_to_datapanel(self, name):  
        """
        Send focusing on ID to data explorer
        """
        if self._data_panel != None:
            self._data_panel.set_panel_on_focus(name)
            
    def set_panel_on_focus_helper(self):
        """
        Helper for panel on focus with data_panel
        """
        caption = self.panel_on_focus.window_caption
        self.send_focus_to_datapanel(caption)
        #update combo
        if self.panel_on_focus in self.plot_panels.values():
            combo = self._data_panel.cb_plotpanel
            combo_title = str(self.panel_on_focus.window_caption)
            combo.SetStringSelection(combo_title)
            combo.SetToolTip( wx.ToolTip(combo_title )) 
        elif self.panel_on_focus != self._data_panel:
            cpanel = self.panel_on_focus
            if self.cpanel_on_focus != cpanel:
                cpanel.on_tap_focus()
                self.cpanel_on_focus = self.panel_on_focus
      
    def reset_bookmark_menu(self, panel):
        """
        Reset Bookmark menu list
        
        : param panel: a control panel or tap where the bookmark is
        """
        cpanel = panel
        if self._toolbar != None and cpanel._bookmark_flag:
            for item in  self._toolbar.get_bookmark_items():
                self._toolbar.remove_bookmark_item(item)
            self._toolbar.add_bookmark_default()
            pos = 0
            for bitem in cpanel.popUpMenu.GetMenuItems():
                pos += 1
                if pos < 3:
                    continue
                id =  bitem.GetId()
                label = bitem.GetLabel()
                self._toolbar.append_bookmark_item(id, label)
                wx.EVT_MENU(self, id, cpanel._back_to_bookmark)
            self._toolbar.Realize()
             

    def build_gui(self):
        """
        Build the GUI by setting up the toolbar, menu and layout.
        """
        # set tool bar
        self._setup_tool_bar()

        # Create the menu bar. To be filled later.
        # WX 3.0 needs us to create the menu bar first.
        self._menubar = wx.MenuBar()
        if wx.VERSION_STRING >= '3.0.0.0':
            self.SetMenuBar(self._menubar)
        self._add_menu_file()
        self._add_menu_edit()
        self._add_menu_view()
        self._add_menu_tool()
        # Set up the layout
        self._setup_layout()
        self._add_menu_application()
        
        # Set up the menu
        self._add_current_plugin_menu()
        self._add_help_menu()
        # Append item from plugin under menu file if necessary
        self._populate_file_menu()
        if not wx.VERSION_STRING >= '3.0.0.0':
            self.SetMenuBar(self._menubar)
        
        try:
            self.load_from_cmd(self._input_file)
        except:
            msg = "%s Cannot load file %s\n" %(str(APPLICATION_NAME), 
                                             str(self._input_file))
            msg += str(sys.exc_value) + '\n'
            logging.error(msg)
        if self._data_panel is not None and len(self.plugins) > 0:
            self._data_panel.fill_cbox_analysis(self.plugins)
        self.post_init()
        # Set Custom default
        self.set_custom_default_perspective()
        # Set up extra custom tool menu
        self._setup_extra_custom()
        self._check_update(None)

    def _setup_extra_custom(self):  
        """
        Set up toolbar and welcome view if needed
        """
        style = self.__gui_style & GUIFRAME.TOOLBAR_ON
        if (style == GUIFRAME.TOOLBAR_ON) & (not self._toolbar.IsShown()):
            self._on_toggle_toolbar() 
        
        # Set Custom deafult start page
        welcome_style = self.__gui_style & GUIFRAME.WELCOME_PANEL_ON
        if welcome_style == GUIFRAME.WELCOME_PANEL_ON:
            self.show_welcome_panel(None)
      
    def _setup_layout(self):
        """
        Set up the layout
        """
        # Status bar
        from sans.guiframe.gui_statusbar import StatusBar
        self.sb = StatusBar(self, wx.ID_ANY)
        self.SetStatusBar(self.sb)
        # Load panels
        self._load_panels()
        self.set_default_perspective()
        
    def SetStatusText(self, *args, **kwds):
        """
        """
        number = self.sb.get_msg_position()
        wx.Frame.SetStatusText(self, number=number, *args, **kwds)
        
    def PopStatusText(self, *args, **kwds):
        """
        """
        field = self.sb.get_msg_position()
        wx.Frame.PopStatusText(self, field=field)
        
    def PushStatusText(self, *args, **kwds):
        """
            FIXME: No message is passed. What is this supposed to do? 
        """
        field = self.sb.get_msg_position()
        wx.Frame.PushStatusText(self, field=field, 
                        string="FIXME: PushStatusText called without text")

    def add_perspective(self, plugin):
        """
        Add a perspective if it doesn't already
        exist.
        """
        self._num_perspectives += 1
        is_loaded = False
        for item in self.plugins:
            item.set_batch_selection(self.batch_on)
            if plugin.__class__ == item.__class__:
                msg = "Plugin %s already loaded" % plugin.sub_menu
                logging.info(msg)
                is_loaded = True  
        if not is_loaded:
            self.plugins.append(plugin)  
            msg = "Plugin %s appended" % plugin.sub_menu
            logging.info(msg)
      
    def _get_local_plugins(self):
        """
        get plugins local to guiframe and others 
        """
        plugins = []
        #import guiframe local plugins
        #check if the style contain guiframe.dataloader
        style1 = self.__gui_style & GUIFRAME.DATALOADER_ON
        style2 = self.__gui_style & GUIFRAME.PLOTTING_ON
        if style1 == GUIFRAME.DATALOADER_ON:
            try:
                from sans.guiframe.local_perspectives.data_loader import data_loader
                self._data_plugin = data_loader.Plugin()
                plugins.append(self._data_plugin)
            except:
                msg = "ViewerFrame._get_local_plugins:"
                msg += "cannot import dataloader plugin.\n %s" % sys.exc_value
                logging.error(msg)
        if style2 == GUIFRAME.PLOTTING_ON:
            try:
                from sans.guiframe.local_perspectives.plotting import plotting
                self._plotting_plugin = plotting.Plugin()
                plugins.append(self._plotting_plugin)
            except:
                msg = "ViewerFrame._get_local_plugins:"
                msg += "cannot import plotting plugin.\n %s" % sys.exc_value
                logging.error(msg)
     
        return plugins
    
    def _find_plugins(self, dir="perspectives"):
        """
        Find available perspective plug-ins
        
        :param dir: directory in which to look for plug-ins
        
        :return: list of plug-ins
        
        """
        plugins = []
        # Go through files in panels directory
        try:
            list = os.listdir(dir)
            ## the default panel is the panel is the last plugin added
            for item in list:
                toks = os.path.splitext(os.path.basename(item))
                name = ''
                if not toks[0] == '__init__':
                    if toks[1] == '.py' or toks[1] == '':
                        name = toks[0]
                    #check the validity of the module name parsed
                    #before trying to import it
                    if name is None or name.strip() == '':
                        continue
                    path = [os.path.abspath(dir)]
                    file = None
                    try:
                        if toks[1] == '':
                            mod_path = '.'.join([dir, name])
                            module = __import__(mod_path, globals(),
                                                locals(), [name])
                        else:
                            (file, path, info) = imp.find_module(name, path)
                            module = imp.load_module( name, file, item, info)
                        if hasattr(module, "PLUGIN_ID"):
                            try: 
                                plug = module.Plugin()
                                if plug.set_default_perspective():
                                    self._current_perspective = plug
                                plugins.append(plug)
                                
                                msg = "Found plug-in: %s" % module.PLUGIN_ID
                                logging.info(msg)
                            except:
                                msg = "Error accessing PluginPanel"
                                msg += " in %s\n  %s" % (name, sys.exc_value)
                                config.printEVT(msg)
                    except:
                        msg = "ViewerFrame._find_plugins: %s" % sys.exc_value
                        logging.error(msg)
                    finally:
                        if not file == None:
                            file.close()
        except:
            # Should raise and catch at a higher level and 
            # display error on status bar
            pass  

        return plugins

    def _get_panels_size(self, p):
        """
        find the proper size of the current panel
        get the proper panel width and height
        """
        self._window_width, self._window_height = self.get_client_size()
        ## Default size
        if DATAPANEL_WIDTH < 0:
            panel_width = int(self._window_width * 0.25)
        else:
            panel_width = DATAPANEL_WIDTH
        panel_height = int(self._window_height)
        style = self.__gui_style & (GUIFRAME.MANAGER_ON)
        if self._data_panel is not None  and (p == self._data_panel):
            return panel_width, panel_height
        if hasattr(p, "CENTER_PANE") and p.CENTER_PANE:
            panel_width = self._window_width * 0.45
            if CONTROL_WIDTH > 0:
                panel_width = CONTROL_WIDTH
            if CONTROL_HEIGHT > 0:
                panel_height = CONTROL_HEIGHT
            return panel_width, panel_height
        elif p == self.defaultPanel:
            return self._window_width, panel_height
        return panel_width, panel_height
    
    def _load_panels(self):
        """
        Load all panels in the panels directory
        """
        # Look for plug-in panels
        panels = []
        if wx.VERSION_STRING >= '3.0.0.0':
            mac_pos_y = 85
        else:
            mac_pos_y = 40
        for item in self.plugins:
            if hasattr(item, "get_panels"):
                ps = item.get_panels(self)
                panels.extend(ps)
        
        # Set up welcome panel
        #TODO: this needs serious simplification
        if self.welcome_panel_class is not None:
            welcome_panel = MDIFrame(self, None, 'None', (100, 200))
            self.defaultPanel = self.welcome_panel_class(welcome_panel, -1, style=wx.RAISED_BORDER)
            welcome_panel.set_panel(self.defaultPanel)
            self.defaultPanel.set_frame(welcome_panel)
            welcome_panel.Show(False)
        
        self.panels["default"] = self.defaultPanel
        size_t_bar = 70
        if IS_LINUX:
            size_t_bar = 115
        if self.defaultPanel is not None:
            w, h = self._get_panels_size(self.defaultPanel)
            frame = self.defaultPanel.get_frame()
            frame.SetSize((self._window_width, self._window_height))
            if not IS_WIN:
                frame.SetPosition((0, mac_pos_y + size_t_bar))
            frame.Show(True)
        #add data panel 
        win = MDIFrame(self, None, 'None', (100, 200))
        data_panel = DataPanel(parent=win,  id=-1)
        win.set_panel(data_panel)
        self.panels["data_panel"] = data_panel
        self._data_panel = data_panel
        d_panel_width, h = self._get_panels_size(self._data_panel)
        win.SetSize((d_panel_width, h))
        is_visible = self.__gui_style & GUIFRAME.MANAGER_ON == GUIFRAME.MANAGER_ON
        if IS_WIN:
            win.SetPosition((0, 0))
        else:
            win.SetPosition((0, mac_pos_y + size_t_bar))
        win.Show(is_visible)
        # Add the panels to the AUI manager
        for panel_class in panels:
            frame = panel_class.get_frame()
            id = wx.NewId()
            # Check whether we need to put this panel in the center pane
            if hasattr(panel_class, "CENTER_PANE") and panel_class.CENTER_PANE:
                w, h = self._get_panels_size(panel_class)
                if panel_class.CENTER_PANE:
                    self.panels[str(id)] = panel_class
                    _, pos_y = frame.GetPositionTuple()
                    frame.SetPosition((d_panel_width + 1, pos_y))
                    frame.SetSize((w, h))
                    frame.Show(False)
            elif panel_class == self._data_panel:
                panel_class.frame.Show(is_visible)
                continue
            else:
                self.panels[str(id)] = panel_class
                frame.SetSize((w, h))
                frame.Show(False)
            if IS_WIN:
                frame.SetPosition((d_panel_width + 1, 0))
            else:
                frame.SetPosition((d_panel_width + 1, mac_pos_y + size_t_bar))

        if not IS_WIN:
            win_height = mac_pos_y
            if IS_LINUX:
                if wx.VERSION_STRING >= '3.0.0.0':
                    win_height = mac_pos_y + 10
                else:
                    win_height = mac_pos_y + 55
                self.SetMaxSize((-1, win_height))
            else:
                self.SetSize((self._window_width, win_height))
        
    def update_data(self, prev_data, new_data):
        """
        Update the data.
        """
        prev_id, data_state = self._data_manager.update_data(
                              prev_data=prev_data, new_data=new_data)
        
        self._data_panel.remove_by_id(prev_id)
        self._data_panel.load_data_list(data_state)
        
    def update_theory(self, data_id, theory, state=None):
        """
        Update the theory
        """ 
        data_state = self._data_manager.update_theory(data_id=data_id, 
                                         theory=theory,
                                         state=state)  
        wx.CallAfter(self._data_panel.load_data_list, data_state)
        
    def onfreeze(self, theory_id):
        """
        """
        data_state_list = self._data_manager.freeze(theory_id)
        self._data_panel.load_data_list(list=data_state_list)
        for data_state in data_state_list.values():
            new_plot = data_state.get_data()
            
            wx.PostEvent(self, NewPlotEvent(plot=new_plot,
                                             title=new_plot.title))
        
    def freeze(self, data_id, theory_id):
        """
        """
        data_state_list = self._data_manager.freeze_theory(data_id=data_id, 
                                                theory_id=theory_id)
        self._data_panel.load_data_list(list=data_state_list)
        for data_state in data_state_list.values():
            new_plot = data_state.get_data()
            wx.PostEvent(self, NewPlotEvent(plot=new_plot,
                                             title=new_plot.title))
        
    def delete_data(self, data):
        """
        Delete the data.
        """
        self._current_perspective.delete_data(data)
        
    
    def get_context_menu(self, plotpanel=None):
        """
        Get the context menu items made available 
        by the different plug-ins. 
        This function is used by the plotting module
        """
        if plotpanel is None:
            return
        menu_list = []
        for item in self.plugins:
            menu_list.extend(item.get_context_menu(plotpanel=plotpanel))
        return menu_list
        
    def get_current_context_menu(self, plotpanel=None):
        """
        Get the context menu items made available 
        by the current plug-in. 
        This function is used by the plotting module
        """
        if plotpanel is None:
            return
        menu_list = []
        item = self._current_perspective
        if item != None:
            menu_list.extend(item.get_context_menu(plotpanel=plotpanel))
        return menu_list
            
    def on_panel_close(self, event):
        """
        Gets called when the close event for a panel runs.
        This will check which panel has been closed and
        delete it.
        """
        frame = event.GetEventObject()
        for ID in self.plot_panels.keys():
            if self.plot_panels[ID].window_name == frame.name:
                self.disable_app_menu(self.plot_panels[ID])
                self.delete_panel(ID)
                break
        self.cpanel_on_focus.SetFocus()
    
    
    def popup_panel(self, p):
        """
        Add a panel object to the AUI manager
        
        :param p: panel object to add to the AUI manager
        
        :return: ID of the event associated with the new panel [int]
        
        """
        ID = wx.NewId()
        self.panels[str(ID)] = p
        ## Check and set the size
        if PLOPANEL_WIDTH < 0:
            p_panel_width = int(self._window_width * 0.45)
        else:
            p_panel_width = PLOPANEL_WIDTH
        p_panel_height = int(p_panel_width * 0.76)
        p.frame.SetSize((p_panel_width, p_panel_height))
        self.graph_num += 1
        if p.window_caption.split()[0] in NOT_SO_GRAPH_LIST:
            windowcaption = p.window_caption
        else:
            windowcaption = 'Graph'
        windowname = p.window_name

        # Append nummber
        captions = self._get_plotpanel_captions()
        while (1):
            caption = windowcaption + '%s'% str(self.graph_num)
            if caption not in captions:
                break
            self.graph_num += 1
            # protection from forever-loop: max num = 1000
            if self.graph_num > 1000:
                break
        if p.window_caption.split()[0] not in NOT_SO_GRAPH_LIST:
            p.window_caption = caption 
        p.window_name = windowname + str(self.graph_num)
        
        p.frame.SetTitle(p.window_caption)
        p.frame.name = p.window_name
        if not IS_WIN:
            p.frame.Center()
            x_pos, _ = p.frame.GetPositionTuple()
            p.frame.SetPosition((x_pos, 112))
        p.frame.Show(True)

        # Register for showing/hiding the panel
        wx.EVT_MENU(self, ID, self.on_view)
        if p not in self.plot_panels.values() and p.group_id != None:
            self.plot_panels[ID] = p
            if len(self.plot_panels) == 1:
                self.panel_on_focus = p
                self.set_panel_on_focus(None)
            if self._data_panel is not None and \
                self._plotting_plugin is not None:
                ind = self._data_panel.cb_plotpanel.FindString('None')
                if ind != wx.NOT_FOUND:
                    self._data_panel.cb_plotpanel.Delete(ind)
                if caption not in self._data_panel.cb_plotpanel.GetItems():
                    self._data_panel.cb_plotpanel.Append(str(caption), p)
        return ID
    
    def _get_plotpanel_captions(self):
        """
        Get all the plotpanel cations
        
        : return: list of captions
        """
        captions = []
        for Id in self.plot_panels.keys():
            captions.append(self.plot_panels[Id].window_caption)
        
        return captions
        
    def _setup_tool_bar(self):
        """
        add toolbar to the frame
        """
        self._toolbar = GUIToolBar(self)
        # The legacy code doesn't work well for wx 3.0
        # but the old code produces better results with wx 2.8
        if not IS_WIN and wx.VERSION_STRING >= '3.0.0.0':
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(self._toolbar, 0, wx.EXPAND)
            self.SetSizer(sizer)
        else:
            self.SetToolBar(self._toolbar)
        self._update_toolbar_helper()
        self._on_toggle_toolbar(event=None)
    
    def _update_toolbar_helper(self):
        """
        Helping to update the toolbar
        """
        application_name = 'No Selected Analysis'
        panel_name = 'No Panel on Focus'
        c_panel = self.cpanel_on_focus        
        if self._toolbar is  None:
            return
        if c_panel is not None:
            self.reset_bookmark_menu(self.cpanel_on_focus)
        if self._current_perspective is not None:
            application_name = self._current_perspective.sub_menu
        c_panel_state = c_panel
        if c_panel is not None:
            panel_name = c_panel.window_caption
            if not c_panel.IsShownOnScreen():
                c_panel_state = None
        self._toolbar.update_toolbar(c_panel_state)
        self._toolbar.update_button(application_name=application_name, 
                                        panel_name=panel_name)
        self._toolbar.Realize()
        
    def _add_menu_tool(self):
        """
        Tools menu
        Go through plug-ins and find tools to populate the tools menu
        """
        style = self.__gui_style & GUIFRAME.CALCULATOR_ON
        if style == GUIFRAME.CALCULATOR_ON:
            self._tool_menu = None
            for item in self.plugins:
                if hasattr(item, "get_tools"):
                    for tool in item.get_tools():
                        # Only create a menu if we have at least one tool
                        if self._tool_menu is None:
                            self._tool_menu = wx.Menu()
                        if tool[0].lower().count('python') > 0:
                            self._tool_menu.AppendSeparator()
                        id = wx.NewId()
                        self._tool_menu.Append(id, tool[0], tool[1])
                        wx.EVT_MENU(self, id, tool[2])
            if self._tool_menu is not None:
                self._menubar.Append(self._tool_menu, '&Tool')
                
    def _add_current_plugin_menu(self):
        """
        add current plugin menu
        Look for plug-in menus
        Add available plug-in sub-menus. 
        """
        if self._menubar is None or self._current_perspective is None \
            or self._menubar.GetMenuCount()==0:
            return
        #replace or add a new menu for the current plugin
       
        pos = self._menubar.FindMenu(str(self._applications_menu_name))
        if pos != -1:
            menu_list = self._current_perspective.populate_menu(self)
            if menu_list:
                for (menu, name) in menu_list:
                    hidden_menu = self._menubar.Replace(pos, menu, name) 
                    self._applications_menu_name = name 
                #self._applications_menu_pos = pos
            else:
                hidden_menu = self._menubar.Remove(pos)
                self._applications_menu_name = None
            #get the position of the menu when it first added
            self._applications_menu_pos = pos 
            
        else:
            menu_list = self._current_perspective.populate_menu(self)
            if menu_list:
                for (menu, name) in menu_list:
                    if self._applications_menu_pos == -1:
                        self._menubar.Append(menu, name)
                    else:
                        self._menubar.Insert(self._applications_menu_pos, 
                                             menu, name)
                    self._applications_menu_name = name
                  
    def _add_help_menu(self):
        """
        add help menu
        """
        # Help menu
        self._help_menu = wx.Menu()
        style = self.__gui_style & GUIFRAME.WELCOME_PANEL_ON
        if style == GUIFRAME.WELCOME_PANEL_ON or custom_config != None:
            # add the welcome panel menu item
            if config.WELCOME_PANEL_ON and self.defaultPanel is not None:
                id = wx.NewId()
                self._help_menu.Append(id, '&Welcome', '')
                self._help_menu.AppendSeparator()
                wx.EVT_MENU(self, id, self.show_welcome_panel)
        # Look for help item in plug-ins 
        for item in self.plugins:
            if hasattr(item, "help"):
                id = wx.NewId()
                self._help_menu.Append(id,'&%s Help' % item.sub_menu, '')
                wx.EVT_MENU(self, id, item.help)
        if config._do_tutorial and (IS_WIN or sys.platform =='darwin'):
            self._help_menu.AppendSeparator()
            id = wx.NewId()
            self._help_menu.Append(id, '&Tutorial', 'Software tutorial')
            wx.EVT_MENU(self, id, self._onTutorial)
            
        if config._do_aboutbox:
            self._help_menu.AppendSeparator()
            id = wx.NewId()
            self._help_menu.Append(id, '&About', 'Software information')
            wx.EVT_MENU(self, id, self._onAbout)
        
        # Checking for updates
        id = wx.NewId()
        self._help_menu.Append(id,'&Check for update', 
         'Check for the latest version of %s' % config.__appname__)
        wx.EVT_MENU(self, id, self._check_update)
        self._menubar.Append(self._help_menu, '&Help')
            
    def _add_menu_view(self):
        """
        add menu items under view menu
        """
        if not VIEW_MENU:
            return
        self._view_menu = wx.Menu()
        
        id = wx.NewId()
        hint = "Display the Grid Window for batch results etc."
        self._view_menu.Append(id, '&Show Grid Window', hint) 
        wx.EVT_MENU(self, id, self.show_batch_frame)
        
        self._view_menu.AppendSeparator()
        style = self.__gui_style & GUIFRAME.MANAGER_ON
        id = wx.NewId()
        self._data_panel_menu = self._view_menu.Append(id,
                                                '&Show Data Explorer', '')
        wx.EVT_MENU(self, id, self.show_data_panel)
        if style == GUIFRAME.MANAGER_ON:
            self._data_panel_menu.SetText('Hide Data Explorer')
        else:
            self._data_panel_menu.SetText('Show Data Explorer')
  
        self._view_menu.AppendSeparator()
        id = wx.NewId()
        style1 = self.__gui_style & GUIFRAME.TOOLBAR_ON
        if style1 == GUIFRAME.TOOLBAR_ON:
            self._toolbar_menu = self._view_menu.Append(id, '&Hide Toolbar', '')
        else:
            self._toolbar_menu = self._view_menu.Append(id, '&Show Toolbar', '')
        wx.EVT_MENU(self, id, self._on_toggle_toolbar)

        if custom_config != None:
            self._view_menu.AppendSeparator()
            id = wx.NewId()
            hint_ss = "Select the current/default configuration "
            hint_ss += "as a startup setting"
            preference_menu = self._view_menu.Append(id, 'Startup Setting', 
                                                     hint_ss)
            wx.EVT_MENU(self, id, self._on_preference_menu)
            
        id = wx.NewId()
        self._view_menu.AppendSeparator()
        self._view_menu.Append(id, 'Category Manager', 'Edit model categories')
        wx.EVT_MENU(self, id, self._on_category_manager)

        self._menubar.Append(self._view_menu, '&View')   
         
    def show_batch_frame(self, event=None):
        """
        show the grid of result
        """
        # Show(False) before Show(True) in order to bring it to the front
        self.batch_frame.Show(False)
        self.batch_frame.Show(True)
    
    def  on_category_panel(self, event):  
        """
        On cat panel
        """
        self._on_category_manager(event)
          
    def _on_category_manager(self, event):
        """
        Category manager frame
        """
        frame = CategoryManager(self, -1, 'Model Category Manager')
        icon = self.GetIcon()
        frame.SetIcon(icon)

    def _on_preference_menu(self, event):     
        """
        Build a panel to allow to edit Mask
        """
        from sans.guiframe.startup_configuration \
        import StartupConfiguration as ConfDialog
        
        dialog = ConfDialog(parent=self, gui=self.__gui_style)
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            dialog.write_custom_config()
            # post event for info
            wx.PostEvent(self, StatusEvent(status="Wrote custom configuration", info='info'))
        dialog.Destroy()
        
    def _add_menu_application(self):
        """
        # Attach a menu item for each defined perspective or application.
        # Only add the perspective menu if there are more than one perspectives
        add menu application
        """
        if self._num_perspectives  > 1:
            plug_data_count = False
            plug_no_data_count = False
            self._applications_menu = wx.Menu()
            pos = 0
            separator = self._applications_menu.AppendSeparator()
            for plug in self.plugins:
                if len(plug.get_perspective()) > 0:
                    id = wx.NewId()
                    if plug.use_data():
                        
                        self._applications_menu.InsertCheckItem(pos, id, plug.sub_menu,
                                      "Switch to analysis: %s" % plug.sub_menu)
                        plug_data_count = True
                        pos += 1
                    else:
                        plug_no_data_count = True
                        self._applications_menu.AppendCheckItem(id, plug.sub_menu,
                                      "Switch to analysis: %s" % plug.sub_menu)
                    wx.EVT_MENU(self, id, plug.on_perspective)

            if (not plug_data_count or not plug_no_data_count):
                self._applications_menu.RemoveItem(separator)
            self._menubar.Append(self._applications_menu, '&Analysis')
            self._check_applications_menu()
            
    def _populate_file_menu(self):
        """
        Insert menu item under file menu
        """
        for plugin in self.plugins:
            if len(plugin.populate_file_menu()) > 0:
                for item in plugin.populate_file_menu():
                    m_name, m_hint, m_handler = item
                    id = wx.NewId()
                    self._file_menu.Append(id, m_name, m_hint)
                    wx.EVT_MENU(self, id, m_handler)
                self._file_menu.AppendSeparator()
                
    def _add_menu_file(self):
        """
        add menu file
        """
        
        # File menu
        self._file_menu = wx.Menu()
        style1 = self.__gui_style & GUIFRAME.MULTIPLE_APPLICATIONS
        if OPEN_SAVE_MENU:
            id = wx.NewId()
            hint_load_file = "read all analysis states saved previously"
            self._save_appl_menu = self._file_menu.Append(id, 
                                    '&Open Project', hint_load_file)
            wx.EVT_MENU(self, id, self._on_open_state_project)
            
        if style1 == GUIFRAME.MULTIPLE_APPLICATIONS:
            # some menu of plugin to be seen under file menu
            hint_load_file = "Read a status files and load"
            hint_load_file += " them into the analysis"
            id = wx.NewId()
            self._save_appl_menu = self._file_menu.Append(id, 
                                    '&Open Analysis', hint_load_file)
            wx.EVT_MENU(self, id, self._on_open_state_application)
        if OPEN_SAVE_MENU:        
            self._file_menu.AppendSeparator()
            id = wx.NewId()
            self._file_menu.Append(id, '&Save Project',
                                 'Save the state of the whole analysis')
            wx.EVT_MENU(self, id, self._on_save_project)
        if style1 == GUIFRAME.MULTIPLE_APPLICATIONS:
            id = wx.NewId()
            self._save_appl_menu = self._file_menu.Append(id, 
                                                      '&Save Analysis',
                        'Save state of the current active analysis panel')
            wx.EVT_MENU(self, id, self._on_save_application)
            self._file_menu.AppendSeparator()
       
        id = wx.NewId()
        self._file_menu.Append(id, '&Quit', 'Exit') 
        wx.EVT_MENU(self, id, self.Close)
        # Add sub menus
        self._menubar.Append(self._file_menu, '&File')
        
    def _add_menu_edit(self):
        """
        add menu edit
        """
        if not EDIT_MENU:
            return
        # Edit Menu
        self._edit_menu = wx.Menu()
        self._edit_menu.Append(GUIFRAME_ID.UNDO_ID, '&Undo', 
                               'Undo the previous action')
        wx.EVT_MENU(self, GUIFRAME_ID.UNDO_ID, self.on_undo_panel)
        self._edit_menu.Append(GUIFRAME_ID.REDO_ID, '&Redo', 
                               'Redo the previous action')
        wx.EVT_MENU(self, GUIFRAME_ID.REDO_ID, self.on_redo_panel)
        self._edit_menu.AppendSeparator()
        self._edit_menu.Append(GUIFRAME_ID.COPY_ID, '&Copy Params', 
                               'Copy parameter values')
        wx.EVT_MENU(self, GUIFRAME_ID.COPY_ID, self.on_copy_panel)
        self._edit_menu.Append(GUIFRAME_ID.PASTE_ID, '&Paste Params', 
                               'Paste parameter values')
        wx.EVT_MENU(self, GUIFRAME_ID.PASTE_ID, self.on_paste_panel)

        self._edit_menu.AppendSeparator()

        self._edit_menu_copyas = wx.Menu()
        #Sub menu for Copy As...
        self._edit_menu_copyas.Append(GUIFRAME_ID.COPYEX_ID, 'Copy current tab to Excel',
                               'Copy parameter values in tabular format')
        wx.EVT_MENU(self, GUIFRAME_ID.COPYEX_ID, self.on_copy_panel)

        self._edit_menu_copyas.Append(GUIFRAME_ID.COPYLAT_ID, 'Copy current tab to LaTeX',
                               'Copy parameter values in tabular format')
        wx.EVT_MENU(self, GUIFRAME_ID.COPYLAT_ID, self.on_copy_panel)


        self._edit_menu.AppendMenu(GUIFRAME_ID.COPYAS_ID, 'Copy Params as...', self._edit_menu_copyas,
                               'Copy parameter values in various formats')


        self._edit_menu.AppendSeparator()
        
        self._edit_menu.Append(GUIFRAME_ID.PREVIEW_ID, '&Report Results',
                               'Preview current panel')
        wx.EVT_MENU(self, GUIFRAME_ID.PREVIEW_ID, self.on_preview_panel)

        self._edit_menu.Append(GUIFRAME_ID.RESET_ID, '&Reset Page', 
                               'Reset current panel')
        wx.EVT_MENU(self, GUIFRAME_ID.RESET_ID, self.on_reset_panel)
    
        self._menubar.Append(self._edit_menu,  '&Edit')
        self.enable_edit_menu()
        
    def get_style(self):
        """
        Return the gui style
        """
        return  self.__gui_style
    
    def _add_menu_data(self):
        """
        Add menu item item data to menu bar
        """
        if self._data_plugin is not None:
            menu_list = self._data_plugin.populate_menu(self)
            if menu_list:
                for (menu, name) in menu_list:
                    self._menubar.Append(menu, name)
        
                        
    def _on_toggle_toolbar(self, event=None):
        """
        hide or show toolbar
        """
        if self._toolbar is None:
            return
        if self._toolbar.IsShown():
            if self._toolbar_menu is not None:
                self._toolbar_menu.SetItemLabel('Show Toolbar')
            self._toolbar.Hide()
        else:
            if self._toolbar_menu is not None:
                self._toolbar_menu.SetItemLabel('Hide Toolbar')
            self._toolbar.Show()
        self._toolbar.Realize()
        
    def _on_status_event(self, evt):
        """
        Display status message
        """
        # This CallAfter fixes many crashes on MAC.
        wx.CallAfter(self.sb.set_status, evt)
       
    def on_view(self, evt):
        """
        A panel was selected to be shown. If it's not already
        shown, display it.
        
        :param evt: menu event
        
        """
        panel_id = str(evt.GetId())
        self.on_set_plot_focus(self.panels[panel_id])
        wx.CallLater(5*TIME_FACTOR, self.set_schedule(True))
        self.set_plot_unfocus()
 
    def show_welcome_panel(self, event):
        """    
        Display the welcome panel
        """
        if self.defaultPanel is None:
            return 
        frame = self.panels['default'].get_frame()
        if frame == None:
            return
        # Show default panel
        if not frame.IsShown():
            frame.Show(True)
            
    def on_close_welcome_panel(self):
        """
        Close the welcome panel
        """
        if self.defaultPanel is None:
            return 
        default_panel = self.panels["default"].frame
        if default_panel.IsShown():
            default_panel.Show(False) 
                
    def delete_panel(self, uid):
        """
        delete panel given uid
        """
        ID = str(uid)
        config.printEVT("delete_panel: %s" % ID)
        try:
            caption = self.panels[ID].window_caption
        except:
            logging.error("delete_panel: No such plot id as %s" % ID)
            return
        if ID in self.panels.keys():
            self.panel_on_focus = None
            panel = self.panels[ID]

            if hasattr(panel, "connect"):
                panel.connect.disconnect()
            self._plotting_plugin.delete_panel(panel.group_id)

            if panel in self.schedule_full_draw_list:
                self.schedule_full_draw_list.remove(panel) 
            
            #delete uid number not str(uid)
            if ID in self.plot_panels.keys():
                del self.plot_panels[ID]
            if ID in self.panels.keys():
                del self.panels[ID]
            return 
            
    def create_gui_data(self, data, path=None):
        """
        """
        return self._data_manager.create_gui_data(data, path)
    
    def get_data(self, path):
        """
        """
        message = ""
        log_msg = ''
        output = []
        error_message = ""
        basename  = os.path.basename(path)
        root, extension = os.path.splitext(basename)
        if extension.lower() not in EXTENSIONS:
            log_msg = "File Loader cannot "
            log_msg += "load: %s\n" % str(basename)
            log_msg += "Try Data opening...."
            logging.error(log_msg)
            return
        
        #reading a state file
        for plug in self.plugins:
            reader, ext = plug.get_extensions()
            if reader is not None:
                #read the state of the single plugin
                if extension == ext:
                    reader.read(path)
                    return
                elif extension == APPLICATION_STATE_EXTENSION:
                    try:
                        reader.read(path)
                    except:
                        msg = "DataLoader Error: Encounted Non-ASCII character"
                        msg += "\n(%s)"% sys.exc_value
                        wx.PostEvent(self, StatusEvent(status=msg, 
                                                info="error", type="stop"))
                        return
        
        style = self.__gui_style & GUIFRAME.MANAGER_ON
        if style == GUIFRAME.MANAGER_ON:
            if self._data_panel is not None:
                self._data_panel.frame.Show(True)
      
    def load_from_cmd(self,  path):   
        """
        load data from cmd or application
        """ 
        if path is None:
            return
        else:
            path = os.path.abspath(path)
            if not os.path.isfile(path) and not os.path.isdir(path):
                return
            
            if os.path.isdir(path):
                self.load_folder(path)
                return

        basename  = os.path.basename(path)
        root, extension = os.path.splitext(basename)
        if extension.lower() not in EXTENSIONS:
            self.load_data(path)
        else:
            self.load_state(path)

        self._default_save_location = os.path.dirname(path)
        
    def load_state(self, path, is_project=False):   
        """
        load data from command line or application
        """
        if path and (path is not None) and os.path.isfile(path):
            basename  = os.path.basename(path)
            if APPLICATION_STATE_EXTENSION is not None \
                and basename.endswith(APPLICATION_STATE_EXTENSION):
                if is_project:
                    for ID in self.plot_panels.keys():
                        panel = self.plot_panels[ID]
                        panel.on_close(None)
            self.get_data(path)
            wx.PostEvent(self, StatusEvent(status="Completed loading."))
        else:
            wx.PostEvent(self, StatusEvent(status=" "))
            
    def load_data(self, path):
        """
        load data from command line
        """
        if not os.path.isfile(path):
            return
        basename  = os.path.basename(path)
        root, extension = os.path.splitext(basename)
        if extension.lower() in EXTENSIONS:
            log_msg = "Data Loader cannot "
            log_msg += "load: %s\n" % str(path)
            log_msg += "Try File opening ...."
            logging.error(log_msg)
            return
        log_msg = ''
        output = {}
        error_message = ""
        try:
            logging.info("Loading Data...:\n" + str(path) + "\n")
            temp =  self.loader.load(path)
            if temp.__class__.__name__ == "list":
                for item in temp:
                    data = self.create_gui_data(item, path)
                    output[data.id] = data
            else:
                data = self.create_gui_data(temp, path)
                output[data.id] = data
            
            self.add_data(data_list=output)
        except:
            error_message = "Error while loading"
            error_message += " Data from cmd:\n %s\n" % str(path)
            error_message += str(sys.exc_value) + "\n"
            logging.error(error_message)
 
    def load_folder(self, path):
        """
        Load entire folder
        """   
        if not os.path.isdir(path):
            return
        if self._data_plugin is None:
            return
        try:
            if path is not None:
                self._default_save_location = os.path.dirname(path)
                file_list = self._data_plugin.get_file_path(path)
                self._data_plugin.get_data(file_list)
            else:
                return 
        except:
            error_message = "Error while loading"
            error_message += " Data folder from cmd:\n %s\n" % str(path)
            error_message += str(sys.exc_value) + "\n"
            logging.error(error_message)
            
    def _on_open_state_application(self, event):
        """
        """
        path = None
        if self._default_save_location == None:
            self._default_save_location = os.getcwd()
        wx.PostEvent(self, StatusEvent(status="Loading Analysis file..."))
        plug_wlist = self._on_open_state_app_helper()
        dlg = wx.FileDialog(self, 
                            "Choose a file", 
                            self._default_save_location, "",
                            plug_wlist)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if path is not None:
                self._default_save_location = os.path.dirname(path)
        dlg.Destroy()
        self.load_state(path=path)  
    
    def _on_open_state_app_helper(self):
        """
        Helps '_on_open_state_application()' to find the extension of 
        the current perspective/application
        """
        # No current perspective or no extension attr
        if self._current_perspective is None:
            return PLUGINS_WLIST 
        try:
            # Find the extension of the perspective 
            # and get that as 1st item in list
            ind = None
            app_ext = self._current_perspective._extensions
            plug_wlist = config.PLUGINS_WLIST
            for ext in set(plug_wlist):
                if ext.count(app_ext) > 0:
                    ind = ext
                    break
            # Found the extension
            if ind != None:
                plug_wlist.remove(ind)
                plug_wlist.insert(0, ind)
                try:
                    plug_wlist = '|'.join(plug_wlist)
                except:
                    plug_wlist = ''

        except:
            plug_wlist = PLUGINS_WLIST 
            
        return plug_wlist
            
    def _on_open_state_project(self, event):
        """
        """
        path = None
        if self._default_save_location == None:
            self._default_save_location = os.getcwd()
        wx.PostEvent(self, StatusEvent(status="Loading Project file..."))
        dlg = wx.FileDialog(self, 
                            "Choose a file", 
                            self._default_save_location, "",
                             APPLICATION_WLIST)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if path is not None:
                self._default_save_location = os.path.dirname(path)
        dlg.Destroy()
        
        self.load_state(path=path, is_project=True)
        
    def _on_save_application(self, event):
        """
        save the state of the current active application
        """
        if self.cpanel_on_focus is not None:
            try:
                wx.PostEvent(self, 
                             StatusEvent(status="Saving Analysis file..."))
                self.cpanel_on_focus.on_save(event)
                wx.PostEvent(self, 
                             StatusEvent(status="Completed saving."))
            except:
                msg = "Error occurred while saving: "
                msg += "To save, the application panel should have a data set.."
                wx.PostEvent(self, StatusEvent(status=msg))  
            
    def _on_save_project(self, event):
        """
        save the state of the SasView as *.svs
        """
        if self._current_perspective is  None:
            return
        wx.PostEvent(self, StatusEvent(status="Saving Project file..."))
        reader, ext = self._current_perspective.get_extensions()
        path = None
        extension = '*' + APPLICATION_STATE_EXTENSION
        dlg = wx.FileDialog(self, "Save Project file",
                            self._default_save_location, "sasview_proj",
                             extension, 
                             wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self._default_save_location = os.path.dirname(path)
        else:
            return None
        dlg.Destroy()
        try:
            if path is None:
                return
            # default cansas xml doc
            doc = None
            for panel in self.panels.values():
                temp = panel.save_project(doc)
                if temp is not None:
                    doc = temp
              
            # Write the XML document
            extens = APPLICATION_STATE_EXTENSION
            fName = os.path.splitext(path)[0] + extens
            if doc != None:
                fd = open(fName, 'w')
                fd.write(doc.toprettyxml())
                fd.close()
                wx.PostEvent(self, StatusEvent(status="Completed Saving."))
            else:
                msg = "%s cannot read %s\n" % (str(APPLICATION_NAME), str(path))
                logging.error(msg)
        except:
            msg = "Error occurred while saving: "
            msg += "To save, at leat one application panel "
            msg += "should have a data set.."
            wx.PostEvent(self, StatusEvent(status=msg))    
                    
    def on_save_helper(self, doc, reader, panel, path):
        """
        Save state into a file
        """
        try:
            if reader is not None:
                # case of a panel with multi-pages
                if hasattr(panel, "opened_pages"):
                    for uid, page in panel.opened_pages.iteritems():
                        data = page.get_data()
                        # state must be cloned
                        state = page.get_state().clone()
                        if data is not None:
                            new_doc = reader.write_toXML(data, state)
                            if doc != None and hasattr(doc, "firstChild"):
                                child = new_doc.firstChild.firstChild
                                doc.firstChild.appendChild(child)  
                            else:
                                doc = new_doc 
                # case of only a panel
                else:
                    data = panel.get_data()
                    state = panel.get_state()
                    if data is not None:
                        new_doc = reader.write_toXML(data, state)
                        if doc != None and hasattr(doc, "firstChild"):
                            child = new_doc.firstChild.firstChild
                            doc.firstChild.appendChild(child)  
                        else:
                            doc = new_doc 
        except: 
            raise
            #pass

        return doc

    def quit_guiframe(self):
        """
        Pop up message to make sure the user wants to quit the application
        """
        message = "\nDo you really want to exit this application?        \n\n"
        dial = wx.MessageDialog(self, message, 'Confirm Exit',
                           wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if dial.ShowModal() == wx.ID_YES:
            return True
        else:
            return False    
        
    def WindowClose(self, event=None):
        """
        Quit the application from x icon
        """
        flag = self.quit_guiframe()
        if flag:
            _pylab_helpers.Gcf.figs = {}
            self.Close()
            
    def Close(self, event=None):
        """
        Quit the application
        """
        wx.Exit()
        sys.exit()
            
    def _check_update(self, event=None): 
        """
        Check with the deployment server whether a new version
        of the application is available.
        A thread is started for the connecting with the server. The thread calls
        a call-back method when the current version number has been obtained.
        """
        try:
            conn = httplib.HTTPConnection(config.__update_URL__[0], 
                              timeout=3.0)
            conn.request("GET", config.__update_URL__[1])
            res = conn.getresponse()
            content = res.read()
            conn.close()
        except:
            content = "0.0.0"
       
        version = content.strip()
        if len(re.findall('\d+\.\d+\.\d+$', version)) < 0:
            content = "0.0.0"
        self._process_version(content, standalone=event==None)
    
    def _process_version(self, version, standalone=True):
        """
        Call-back method for the process of checking for updates.
        This methods is called by a VersionThread object once the current
        version number has been obtained. If the check is being done in the
        background, the user will not be notified unless there's an update.
        
        :param version: version string
        :param standalone: True of the update is being checked in 
           the background, False otherwise.
           
        """
        try:
            if version == "0.0.0":
                msg = "Could not connect to the application server."
                msg += " Please try again later."
                self.SetStatusText(msg)
            elif cmp(version, config.__version__) > 0:
                msg = "Version %s is available! " % str(version)
                if not standalone:
                    import webbrowser
                    webbrowser.open(config.__download_page__)
                else:
                    msg +=  "See the help menu to download it." 
                self.SetStatusText(msg)
            else:
                if not standalone:
                    msg = "You have the latest version"
                    msg += " of %s" % str(config.__appname__)
                    self.SetStatusText(msg)
        except:
            msg = "guiframe: could not get latest application"
            msg += " version number\n  %s" % sys.exc_value
            logging.error(msg)
            if not standalone:
                msg = "Could not connect to the application server."
                msg += " Please try again later."
                self.SetStatusText(msg)
                    
    def _onAbout(self, evt):
        """
        Pop up the about dialog
        
        :param evt: menu event
        
        """
        if config._do_aboutbox:
            import sans.guiframe.aboutbox as AboutBox 
            dialog = AboutBox.DialogAbout(None, -1, "")
            dialog.ShowModal()   
                     
    def _onTutorial(self, evt):
        """
        Pop up the tutorial dialog
        
        :param evt: menu event
        
        """
        if config._do_tutorial:   
            path = config.TUTORIAL_PATH
            if IS_WIN:
                try:
                    from sans.guiframe.pdfview import PDFFrame
                    dialog = PDFFrame(None, -1, "Tutorial", path)
                    # put icon
                    self.put_icon(dialog)  
                    dialog.Show(True) 
                except:
                    logging.error("Error in _onTutorial: %s" % sys.exc_value)
                    try:
                        #in case when the pdf default set other than acrobat
                        import ho.pisa as pisa
                        pisa.startViewer(path)
                    except:
                        msg = "This feature requires 'PDF Viewer'\n"
                        msg += "Please install it first (Free)..."
                        wx.MessageBox(msg, 'Error')
            else:
                try:
                    command = "open '%s'" % path
                    os.system(command)
                except:
                    try:
                        #in case when the pdf default set other than preview
                        import ho.pisa as pisa
                        pisa.startViewer(path)
                    except:
                        msg = "This feature requires 'Preview' Application\n"
                        msg += "Please install it first..."
                        wx.MessageBox(msg, 'Error')

                      
    def set_manager(self, manager):
        """
        Sets the application manager for this frame
        
        :param manager: frame manager
        """
        self.app_manager = manager
        
    def post_init(self):
        """
        This initialization method is called after the GUI 
        has been created and all plug-ins loaded. It calls
        the post_init() method of each plug-in (if it exists)
        so that final initialization can be done.
        """
        for item in self.plugins:
            if hasattr(item, "post_init"):
                item.post_init()
        
    def set_default_perspective(self):
        """
        Choose among the plugin the first plug-in that has 
        "set_default_perspective" method and its return value is True will be
        as a default perspective when the welcome page is closed
        """
        for item in self.plugins:
            if hasattr(item, "set_default_perspective"):
                if item.set_default_perspective():
                    item.on_perspective(event=None)
                    return 
        
    def set_perspective(self, panels):
        """
        Sets the perspective of the GUI.
        Opens all the panels in the list, and closes
        all the others.
        
        :param panels: list of panels
        """
        for item in self.panels.keys():
            # Check whether this is a sticky panel
            if hasattr(self.panels[item], "ALWAYS_ON"):
                if self.panels[item].ALWAYS_ON:
                    continue 
            if self.panels[item] == None:
                continue
            if self.panels[item].window_name in panels:
                frame = self.panels[item].get_frame()
                if not frame.IsShown():
                    frame.Show(True)
            else:
                # always show the data panel if enable
                style = self.__gui_style & GUIFRAME.MANAGER_ON
                if (style == GUIFRAME.MANAGER_ON) and self.panels[item] == self._data_panel:
                    if 'data_panel' in self.panels.keys():
                        frame = self.panels['data_panel'].get_frame()
                        if frame == None:
                            continue
                        flag = frame.IsShown()
                        frame.Show(flag)
                else:
                    frame = self.panels[item].get_frame()
                    if frame == None:
                        continue

                    if frame.IsShown():
                        frame.Show(False)
        
    def show_data_panel(self, event=None, action=True):
        """
        show the data panel
        """
        if self._data_panel_menu == None:
            return
        label = self._data_panel_menu.GetText()
        pane = self.panels["data_panel"]
        frame = pane.get_frame()
        if label == 'Show Data Explorer':
            if action: 
                frame.Show(True)
            self.__gui_style = self.__gui_style | GUIFRAME.MANAGER_ON
            self._data_panel_menu.SetText('Hide Data Explorer')
        else:
            if action:
                frame.Show(False)
            self.__gui_style = self.__gui_style & (~GUIFRAME.MANAGER_ON)
            self._data_panel_menu.SetText('Show Data Explorer')

    def add_data_helper(self, data_list):
        """
        """
        if self._data_manager is not None:
            self._data_manager.add_data(data_list)
        
    def add_data(self, data_list):
        """
        receive a dictionary of data from loader
        store them its data manager if possible
        send to data the current active perspective if the data panel 
        is not active. 
        :param data_list: dictionary of data's ID and value Data
        """
        #Store data into manager
        self.add_data_helper(data_list)
        # set data in the data panel
        if self._data_panel is not None:
            data_state = self._data_manager.get_data_state(data_list.keys())
            self._data_panel.load_data_list(data_state)
        #if the data panel is shown wait for the user to press a button 
        #to send data to the current perspective. if the panel is not
        #show  automatically send the data to the current perspective
        style = self.__gui_style & GUIFRAME.MANAGER_ON
        if style == GUIFRAME.MANAGER_ON:
            #wait for button press from the data panel to set_data 
            if self._data_panel is not None:
                self._data_panel.frame.Show(True)
        else:
            #automatically send that to the current perspective
            self.set_data(data_id=data_list.keys())
       
    def set_data(self, data_id, theory_id=None): 
        """
        set data to current perspective
        """
        list_data, _ = self._data_manager.get_by_id(data_id)
        if self._current_perspective is not None:
            self._current_perspective.set_data(list_data.values())

        else:
            msg = "Guiframe does not have a current perspective"
            logging.info(msg)
            
    def set_theory(self, state_id, theory_id=None):
        """
        """
        _, list_theory = self._data_manager.get_by_id(theory_id)
        if self._current_perspective is not None:
            try:
                self._current_perspective.set_theory(list_theory.values())
            except:
                msg = "Guiframe set_theory: \n" + str(sys.exc_value)
                logging.info(msg)
                wx.PostEvent(self, StatusEvent(status=msg, info="error"))
        else:
            msg = "Guiframe does not have a current perspective"
            logging.info(msg)
            
    def plot_data(self,  state_id, data_id=None,
                  theory_id=None, append=False):
        """
        send a list of data to plot
        """
        total_plot_list = []
        data_list, _ = self._data_manager.get_by_id(data_id)
        _, temp_list_theory = self._data_manager.get_by_id(theory_id)
        total_plot_list = data_list.values()
        for item in temp_list_theory.values():
            theory_data, theory_state = item
            total_plot_list.append(theory_data)
        GROUP_ID = wx.NewId()
        for new_plot in total_plot_list:
            if append:
                if self.panel_on_focus is None:
                    message = "cannot append plot. No plot panel on focus!"
                    message += "please click on any available plot to set focus"
                    wx.PostEvent(self, StatusEvent(status=message, 
                                                   info='warning'))
                    return 
                else:
                    if self.enable_add_data(new_plot):
                        new_plot.group_id = self.panel_on_focus.group_id
                    else:
                        message = "Only 1D Data can be append to"
                        message += " plot panel containing 1D data.\n"
                        message += "%s not be appended.\n" %str(new_plot.name)
                        message += "try new plot option.\n"
                        wx.PostEvent(self, StatusEvent(status=message, 
                                                   info='warning'))
            else:
                #if not append then new plot
                from sans.guiframe.dataFitting import Data2D
                if issubclass(Data2D, new_plot.__class__):
                    #for 2 D always plot in a separated new plot
                    new_plot.group_id = wx.NewId()
                else:
                    # plot all 1D in a new plot
                    new_plot.group_id = GROUP_ID
            title = "PLOT " + str(new_plot.title)
            wx.PostEvent(self, NewPlotEvent(plot=new_plot,
                                                  title=title,
                                                  group_id = new_plot.group_id))
            
    def remove_data(self, data_id, theory_id=None):
        """
        Delete data state if data_id is provide
        delete theory created with data of id data_id if theory_id is provide
        if delete all true: delete the all state
        else delete theory
        """
        temp = data_id + theory_id
        for plug in self.plugins:
            plug.delete_data(temp)
        total_plot_list = []
        data_list, _ = self._data_manager.get_by_id(data_id)
        _, temp_list_theory = self._data_manager.get_by_id(theory_id)
        total_plot_list = data_list.values()
        for item in temp_list_theory.values():
            theory_data, theory_state = item
            total_plot_list.append(theory_data)
        for new_plot in total_plot_list:
            id = new_plot.id
            for group_id in new_plot.list_group_id:
                wx.PostEvent(self, NewPlotEvent(id=id,
                                                   group_id=group_id,
                                                   action='remove'))
                #remove res plot: Todo: improve
                wx.CallAfter(self._remove_res_plot, id)
        self._data_manager.delete_data(data_id=data_id, 
                                       theory_id=theory_id)
        
    def _remove_res_plot(self, id):
        """
        Try to remove corresponding res plot
        
        : param id: id of the data
        """
        try:
            wx.PostEvent(self, NewPlotEvent(id=("res"+str(id)),
                                           group_id=("res"+str(id)),
                                           action='remove'))
        except:
            pass
    
    def save_data1d(self, data, fname):
        """
        Save data dialog
        """
        default_name = fname
        wildcard = "Text files (*.txt)|*.txt|"\
                    "CanSAS 1D files(*.xml)|*.xml" 
        path = None
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
            format = ".txt"
            if os.path.splitext(mypath)[1].lower() == format:
                # Make sure the ext included in the file name
                # especially on MAC
                fName = os.path.splitext(path)[0] + format
                self._onsaveTXT(data, fName)
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
        
        
    def _onsaveTXT(self, data, path):
        """
        Save file as txt  
        :TODO: Refactor and remove this method. See TODO in _onSave.
        """
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
                if data.dx != None and data.dx != []:
                    out.write("<X>   <Y>   <dY>   <dX>\n")
                else:
                    out.write("<X>   <Y>   <dY>\n")
            else:
                out.write("<X>   <Y>\n")
                
            for i in range(len(data.x)):
                if has_errors:
                    if data.dx != None and data.dx != []:
                        if  data.dx[i] != None:
                            out.write("%g  %g  %g  %g\n" % (data.x[i], 
                                                        data.y[i],
                                                        data.dy[i],
                                                        data.dx[i]))
                        else:
                            out.write("%g  %g  %g\n" % (data.x[i], 
                                                        data.y[i],
                                                        data.dy[i]))
                    else:
                        out.write("%g  %g  %g\n" % (data.x[i], 
                                                    data.y[i],
                                                    data.dy[i]))
                else:
                    out.write("%g  %g\n" % (data.x[i], 
                                            data.y[i]))
            out.close()  
                             
    def show_data1d(self, data, name):
        """
        Show data dialog
        """   
        try:
            xmin = min(data.x)
            ymin = min(data.y)
        except:
            msg = "Unable to find min/max of \n data named %s"% \
                        data.filename  
            wx.PostEvent(self, StatusEvent(status=msg,
                                       info="error"))
            raise ValueError, msg
        ## text = str(data)
        text = data.__str__()
        text += 'Data Min Max:\n'
        text += 'X_min = %s:  X_max = %s\n'% (xmin, max(data.x))
        text += 'Y_min = %s:  Y_max = %s\n'% (ymin, max(data.y))
        if data.dy != None:
            text += 'dY_min = %s:  dY_max = %s\n'% (min(data.dy), max(data.dy))
        text += '\nData Points:\n'
        x_st = "X"
        for index in range(len(data.x)):
            if data.dy != None and len(data.dy) > index:
                dy_val = data.dy[index]
            else:
                dy_val = 0.0
            if data.dx != None and len(data.dx) > index:
                dx_val = data.dx[index]
            else:
                dx_val = 0.0
            if data.dxl != None and len(data.dxl) > index:
                if index == 0: 
                    x_st = "Xl"
                dx_val = data.dxl[index]
            elif data.dxw != None and len(data.dxw) > index:
                if index == 0: 
                    x_st = "Xw"
                dx_val = data.dxw[index]
            
            if index == 0:
                text += "<index> \t<X> \t<Y> \t<dY> \t<d%s>\n"% x_st
            text += "%s \t%s \t%s \t%s \t%s\n" % (index,
                                            data.x[index], 
                                            data.y[index],
                                            dy_val,
                                            dx_val)
        from pdfview import TextFrame
        frame = TextFrame(None, -1, "Data Info: %s"% data.name, text) 
        # put icon
        self.put_icon(frame) 
        frame.Show(True) 
            
    def save_data2d(self, data, fname):    
        """
        Save data2d dialog
        """
        default_name = fname
        wildcard = "IGOR/DAT 2D file in Q_map (*.dat)|*.DAT"
        dlg = wx.FileDialog(self, "Choose a file",
                            self._default_save_location,
                            default_name, wildcard , wx.SAVE)
       
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            # ext_num = 0 for .txt, ext_num = 1 for .xml
            # This is MAC Fix
            ext_num = dlg.GetFilterIndex()
            if ext_num == 0:
                format = '.dat'
            else:
                format = ''
            path = os.path.splitext(path)[0] + format
            mypath = os.path.basename(path)
            
            #TODO: This is bad design. The DataLoader is designed 
            #to recognize extensions.
            # It should be a simple matter of calling the .
            #save(file, data, '.xml') method
            # of the DataLoader.loader.Loader class.
            from sans.dataloader.loader import  Loader
            #Instantiate a loader 
            loader = Loader() 

            format = ".dat"
            if os.path.splitext(mypath)[1].lower() == format:
                # Make sure the ext included in the file name
                # especially on MAC
                fileName = os.path.splitext(path)[0] + format
                loader.save(fileName, data, format)
            try:
                self._default_save_location = os.path.dirname(path)
            except:
                pass    
        dlg.Destroy() 
                             
    def show_data2d(self, data, name):
        """
        Show data dialog
        """   

        wx.PostEvent(self, StatusEvent(status = "Gathering Data2D Info.", 
                                       type = 'start' ))
        text = data.__str__() 
        text += 'Data Min Max:\n'
        text += 'I_min = %s\n'% min(data.data)
        text += 'I_max = %s\n\n'% max(data.data)
        text += 'Data (First 2501) Points:\n'
        text += 'Data columns include err(I).\n'
        text += 'ASCII data starts here.\n'
        text += "<index> \t<Qx> \t<Qy> \t<I> \t<dI> \t<dQparal> \t<dQperp>\n"
        di_val = 0.0
        dx_val = 0.0
        dy_val = 0.0
        #mask_val = True
        len_data = len(data.qx_data)
        for index in xrange(0, len_data):
            x_val = data.qx_data[index]
            y_val = data.qy_data[index]
            i_val = data.data[index]
            if data.err_data != None: 
                di_val = data.err_data[index]
            if data.dqx_data != None: 
                dx_val = data.dqx_data[index]
            if data.dqy_data != None: 
                dy_val = data.dqy_data[index]
  
            text += "%s \t%s \t%s \t%s \t%s \t%s \t%s\n" % (index,
                                            x_val, 
                                            y_val,
                                            i_val,
                                            di_val,
                                            dx_val,
                                            dy_val)
            # Takes too long time for typical data2d: Break here
            if index >= 2500:
                text += ".............\n"
                break

        from pdfview import TextFrame
        frame = TextFrame(None, -1, "Data Info: %s"% data.name, text) 
        # put icon
        self.put_icon(frame)
        frame.Show(True) 
        wx.PostEvent(self, StatusEvent(status = "Data2D Info Displayed", 
                                       type = 'stop' ))
                                  
    def set_current_perspective(self, perspective):
        """
        set the current active perspective 
        """
        self._current_perspective = perspective
        name = "No current analysis selected"
        if self._current_perspective is not None:
            self._add_current_plugin_menu()
            for panel in self.panels.values():
                if hasattr(panel, 'CENTER_PANE') and panel.CENTER_PANE:
                    for name in self._current_perspective.get_perspective():
                        frame = panel.get_frame()
                        if frame != None:
                            if name == panel.window_name:
                                panel.on_set_focus(event=None)
                                frame.Show(True)
                            else:
                                frame.Show(False)
                            #break               
            name = self._current_perspective.sub_menu
            if self._data_panel is not None:
                self._data_panel.set_active_perspective(name)
                self._check_applications_menu()
            #Set the SasView title
            self._set_title_name(name)
            
    def _set_title_name(self, name):
        """
        Set the SasView title w/ the current application name
        
        : param name: application name [string]
        """
        # Set SanView Window title w/ application anme
        title = self.title + "  - " + name + " -"
        self.SetTitle(title)
            
    def _check_applications_menu(self):
        """
        check the menu of the current application
        """
        if self._applications_menu is not None:
            for menu in self._applications_menu.GetMenuItems():
                if self._current_perspective is not None:
                    name = self._current_perspective.sub_menu
                    if menu.IsCheckable():
                        if menu.GetLabel() == name:
                            menu.Check(True)
                        else:
                            menu.Check(False) 
            
    def enable_add_data(self, new_plot):
        """
        Enable append data on a plot panel
        """

        if self.panel_on_focus not in self._plotting_plugin.plot_panels.values():
            return
        is_theory = len(self.panel_on_focus.plots) <= 1 and \
            self.panel_on_focus.plots.values()[0].__class__.__name__ == "Theory1D"
            
        is_data2d = hasattr(new_plot, 'data')
        
        is_data1d = self.panel_on_focus.__class__.__name__ == "ModelPanel1D"\
            and self.panel_on_focus.group_id is not None
        has_meta_data = hasattr(new_plot, 'meta_data')
        
        #disable_add_data if the data is being recovered from  a saved state file.
        is_state_data = False
        if has_meta_data:
            if 'invstate' in new_plot.meta_data: 
                is_state_data = True
            if  'prstate' in new_plot.meta_data: 
                is_state_data = True
            if  'fitstate' in new_plot.meta_data: 
                is_state_data = True
    
        return is_data1d and not is_data2d and not is_theory and not is_state_data
    
    def check_multimode(self, perspective=None):
        """
        Check the perspective have batch mode capablitity
        """
        if perspective == None or self._data_panel == None:
            return
        flag = perspective.get_batch_capable()
        flag_on = perspective.batch_on
        if flag:
            self._data_panel.rb_single_mode.SetValue(not flag_on)
            self._data_panel.rb_batch_mode.SetValue(flag_on)
        else:
            self._data_panel.rb_single_mode.SetValue(True)
            self._data_panel.rb_batch_mode.SetValue(False)
        self._data_panel.rb_single_mode.Enable(flag)
        self._data_panel.rb_batch_mode.Enable(flag)
                

    
    def enable_edit_menu(self):
        """
        enable menu item under edit menu depending on the panel on focus
        """
        if self.cpanel_on_focus is not None and self._edit_menu is not None:
            flag = self.cpanel_on_focus.get_undo_flag()
            self._edit_menu.Enable(GUIFRAME_ID.UNDO_ID, flag)
            flag = self.cpanel_on_focus.get_redo_flag()
            self._edit_menu.Enable(GUIFRAME_ID.REDO_ID, flag)
            flag = self.cpanel_on_focus.get_copy_flag()
            self._edit_menu.Enable(GUIFRAME_ID.COPY_ID, flag)
            flag = self.cpanel_on_focus.get_paste_flag()
            self._edit_menu.Enable(GUIFRAME_ID.PASTE_ID, flag)

            #Copy menu
            flag = self.cpanel_on_focus.get_copy_flag()
            #self._edit_menu.ENABLE(GUIFRAME_ID.COPYAS_ID,flag)
            self._edit_menu_copyas.Enable(GUIFRAME_ID.COPYEX_ID, flag)
            self._edit_menu_copyas.Enable(GUIFRAME_ID.COPYLAT_ID, flag)

            flag = self.cpanel_on_focus.get_preview_flag()
            self._edit_menu.Enable(GUIFRAME_ID.PREVIEW_ID, flag)
            flag = self.cpanel_on_focus.get_reset_flag()
            self._edit_menu.Enable(GUIFRAME_ID.RESET_ID, flag)
        else:
            flag = False
            self._edit_menu.Enable(GUIFRAME_ID.UNDO_ID, flag)
            self._edit_menu.Enable(GUIFRAME_ID.REDO_ID, flag)
            self._edit_menu.Enable(GUIFRAME_ID.COPY_ID, flag)
            self._edit_menu.Enable(GUIFRAME_ID.PASTE_ID, flag)
            #self._edit_menu.Enable(GUIFRAME_ID.COPYEX_ID, flag)
            #self._edit_menu.Enable(GUIFRAME_ID.COPYLAT_ID, flag)
            #self._edit_menu.Enable(GUIFRAME_ID.COPYAS_ID, flag)
            self._edit_menu.Enable(GUIFRAME_ID.PREVIEW_ID, flag)
            self._edit_menu.Enable(GUIFRAME_ID.RESET_ID, flag)
            
    def on_undo_panel(self, event=None):
        """
        undo previous action of the last panel on focus if possible
        """
        if self.cpanel_on_focus is not None:
            self.cpanel_on_focus.on_undo(event)
            
    def on_redo_panel(self, event=None):
        """
        redo the last cancel action done on the last panel on focus
        """
        if self.cpanel_on_focus is not None:
            self.cpanel_on_focus.on_redo(event)
            
    def on_copy_panel(self, event=None):
        """
        copy the last panel on focus if possible
        """
        if self.cpanel_on_focus is not None:
            self.cpanel_on_focus.on_copy(event)
            
    def on_paste_panel(self, event=None):
        """
        paste clipboard to the last panel on focus
        """
        if self.cpanel_on_focus is not None:
            self.cpanel_on_focus.on_paste(event)
                    
    def on_bookmark_panel(self, event=None):
        """
        bookmark panel
        """
        if self.cpanel_on_focus is not None:
            self.cpanel_on_focus.on_bookmark(event)
            
    def append_bookmark(self, event=None):
        """
        Bookmark available information of the panel on focus
        """
        self._toolbar.append_bookmark(event)
            
    def on_save_panel(self, event=None):
        """
        save possible information on the current panel
        """
        if self.cpanel_on_focus is not None:
            self.cpanel_on_focus.on_save(event)
            
    def on_preview_panel(self, event=None):
        """
        preview information on the panel on focus
        """
        if self.cpanel_on_focus is not None:
            self.cpanel_on_focus.on_preview(event)
            
    def on_print_panel(self, event=None):
        """
        print available information on the last panel on focus
        """
        if self.cpanel_on_focus is not None:
            self.cpanel_on_focus.on_print(event)
            
    def on_zoom_panel(self, event=None):
        """
        zoom on the current panel if possible
        """
        if self.cpanel_on_focus is not None:
            self.cpanel_on_focus.on_zoom(event)
            
    def on_zoom_in_panel(self, event=None):
        """
        zoom in of the panel on focus
        """
        if self.cpanel_on_focus is not None:
            self.cpanel_on_focus.on_zoom_in(event)
            
    def on_zoom_out_panel(self, event=None):
        """
        zoom out on the panel on focus
        """
        if self.cpanel_on_focus is not None:
            self.cpanel_on_focus.on_zoom_out(event)
            
    def on_drag_panel(self, event=None):
        """
        drag apply to the panel on focus
        """
        if self.cpanel_on_focus is not None:
            self.cpanel_on_focus.on_drag(event)
            
    def on_reset_panel(self, event=None):
        """
        reset the current panel
        """
        if self.cpanel_on_focus is not None:
            self.cpanel_on_focus.on_reset(event)
            
    def on_change_caption(self, name, old_caption, new_caption):     
        """
        Change the panel caption
        
        :param name: window_name of the pane
        :param old_caption: current caption [string]
        :param new_caption: new caption [string]
        """
        # wx.aui.AuiPaneInfo
        pane_info = self.get_paneinfo(old_caption) 
        # update the data_panel.cb_plotpanel
        if 'data_panel' in self.panels.keys():
            # remove from data_panel combobox
            data_panel = self.panels["data_panel"]
            if data_panel.cb_plotpanel is not None:
                # Check if any panel has the same caption
                has_newstring = data_panel.cb_plotpanel.FindString\
                                                            (str(new_caption)) 
                caption = new_caption
                if has_newstring != wx.NOT_FOUND:
                    captions = self._get_plotpanel_captions()
                    # Append nummber
                    inc = 1
                    while (1):
                        caption = new_caption + '_%s'% str(inc)
                        if caption not in captions:
                            break
                        inc += 1
                    # notify to users
                    msg = "Found Same Title: Added '_%s'"% str(inc)
                    wx.PostEvent(self, StatusEvent(status=msg))
                # update data_panel cb
                pos = data_panel.cb_plotpanel.FindString(str(old_caption)) 
                if pos != wx.NOT_FOUND:
                    data_panel.cb_plotpanel.SetString(pos, caption)
                    data_panel.cb_plotpanel.SetStringSelection(caption)
        # New Caption
        pane_info.SetTitle(caption)
        return caption
        
    def get_paneinfo(self, name):
        """
        Get pane Caption from window_name
        
        :param name: window_name in AuiPaneInfo
        : return: AuiPaneInfo of the name
        """
        for panel in self.plot_panels.values():
            if panel.frame.GetTitle() == name:
                return panel.frame
        return None
    
    def enable_undo(self):
        """
        enable undo related control
        """
        if self.cpanel_on_focus is not None:
            self._toolbar.enable_undo(self.cpanel_on_focus)
            
    def enable_redo(self):
        """
        enable redo 
        """
        if self.cpanel_on_focus is not None:
            self._toolbar.enable_redo(self.cpanel_on_focus)
            
    def enable_copy(self):
        """
        enable copy related control
        """
        if self.cpanel_on_focus is not None:
            self._toolbar.enable_copy(self.cpanel_on_focus)
            
    def enable_paste(self):
        """
        enable paste 
        """
        if self.cpanel_on_focus is not None:
            self._toolbar.enable_paste(self.cpanel_on_focus)
                       
    def enable_bookmark(self):
        """
        Bookmark 
        """
        if self.cpanel_on_focus is not None:
            self._toolbar.enable_bookmark(self.cpanel_on_focus)
            
    def enable_save(self):
        """
        save 
        """
        if self.cpanel_on_focus is not None:
            self._toolbar.enable_save(self.cpanel_on_focus)
            
    def enable_preview(self):
        """
        preview 
        """
        if self.cpanel_on_focus is not None:
            self._toolbar.enable_preview(self.cpanel_on_focus)
            
    def enable_print(self):
        """
        print 
        """
        if self.cpanel_on_focus is not None:
            self._toolbar.enable_print(self.cpanel_on_focus)
            
    def enable_zoom(self):
        """
        zoom 
        """
        if self.cpanel_on_focus is not None:
            self._toolbar.enable_zoom(self.panel_on_focus)
            
    def enable_zoom_in(self):
        """
        zoom in 
        """
        if self.cpanel_on_focus is not None:
            self._toolbar.enable_zoom_in(self.panel_on_focus)
            
    def enable_zoom_out(self):
        """
        zoom out 
        """
        if self.cpanel_on_focus is not None:
            self._toolbar.enable_zoom_out(self.panel_on_focus)
            
    def enable_drag(self, event=None):
        """
        drag 
        """
        #Not implemeted
            
    def enable_reset(self):
        """
        reset the current panel
        """
        if self.cpanel_on_focus is not None:
            self._toolbar.enable_reset(self.panel_on_focus)
            
    def get_toolbar_height(self):
        """
        """
        size_y = 0
        if self.GetToolBar() != None and self.GetToolBar().IsShown():
            if not IS_LINUX:
                _, size_y = self.GetToolBar().GetSizeTuple()
        return size_y
    
    def set_schedule_full_draw(self, panel=None, func='del'):
        """
        Add/subtract the schedule full draw list with the panel given
        
        :param panel: plot panel
        :param func: append or del [string]
        """

        # append this panel in the schedule list if not in yet
        if func == 'append':
            if not panel in self.schedule_full_draw_list:
                self.schedule_full_draw_list.append(panel) 
        # remove this panel from schedule list
        elif func == 'del':
            if len(self.schedule_full_draw_list) > 0:
                if panel in self.schedule_full_draw_list:
                    self.schedule_full_draw_list.remove(panel)

        # reset the schdule
        if len(self.schedule_full_draw_list) == 0:
            self.schedule = False
        else:
            self.schedule = True    
        
    def full_draw(self):
        """
        Draw the panels with axes in the schedule to full dwar list
        """
        
        count = len(self.schedule_full_draw_list)
        #if not self.schedule:
        if count < 1:
            self.set_schedule(False)
            return

        else:
            ind = 0
            # if any of the panel is shown do full_draw
            for panel in self.schedule_full_draw_list:
                ind += 1
                if panel.frame.IsShown():
                    break
                # otherwise, return
                if ind == count:
                    return
        #Simple redraw only for a panel shown
        def f_draw(panel):
            """
            Draw A panel in the full draw list
            """
            try:
                # This checking of GetCapture is to stop redrawing
                # while any panel is capture.
                frame = panel.frame
                
                if not frame.GetCapture():
                    # draw if possible
                    panel.set_resizing(False)
                    #panel.Show(True)
                    panel.draw_plot()
                # Check if the panel is not shown
                flag = frame.IsShown()
                frame.Show(flag)  
            except:
                pass
     
        # Draw all panels 
        if count == 1:
            f_draw(self.schedule_full_draw_list[0])  
        else:
            map(f_draw, self.schedule_full_draw_list)
        # Reset the attr  
        if len(self.schedule_full_draw_list) == 0:
            self.set_schedule(False)
        else:
            self.set_schedule(True)
        
    def set_schedule(self, schedule=False):  
        """
        Set schedule
        """
        self.schedule = schedule
                
    def get_schedule(self):  
        """
        Get schedule
        """
        return self.schedule
    
    def on_set_plot_focus(self, panel):
        """
        Set focus on a plot panel
        """
        if panel == None:
            return
        #self.set_plot_unfocus()
        panel.on_set_focus(None)  
        # set focusing panel
        self.panel_on_focus = panel  
        self.set_panel_on_focus(None)

    def set_plot_unfocus(self): 
        """
        Un focus all plot panels
        """
        for plot in self.plot_panels.values():
            plot.on_kill_focus(None)
    
    def get_window_size(self):
        """
        Get window size 
        
        :return size: tuple
        """
        width, height = self.GetSizeTuple()
        if not IS_WIN:
            # Subtract toolbar height to get real window side
            if self._toolbar.IsShown():
                height -= 45
        return (width, height)
            
    def _onDrawIdle(self, *args, **kwargs):
        """
        ReDraw with axes
        """
        try:
            # check if it is time to redraw
            if self.GetCapture() == None:
                # Draw plot, changes resizing too
                self.full_draw()
        except:
            pass
            
        # restart idle        
        self._redraw_idle(*args, **kwargs)

            
    def _redraw_idle(self, *args, **kwargs):
        """
        Restart Idle
        """
        # restart idle   
        self.idletimer.Restart(100*TIME_FACTOR, *args, **kwargs)

        
class DefaultPanel(wx.Panel, PanelBase):
    """
    Defines the API for a panels to work with
    the GUI manager
    """
    ## Internal nickname for the window, used by the AUI manager
    window_name = "default"
    ## Name to appear on the window title bar
    window_caption = "Welcome panel"
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = True
    def __init__(self, parent, *args, **kwds):
        wx.Panel.__init__(self, parent, *args, **kwds)
        PanelBase.__init__(self, parent)
    


class ViewApp(wx.App):
    """
    Toy application to test this Frame
    """
    def OnInit(self):
        """
        When initialised
        """
        pos, size, self.is_max = self.window_placement((GUIFRAME_WIDTH, 
                                           GUIFRAME_HEIGHT))     
        self.frame = ViewerFrame(parent=None, 
                             title=APPLICATION_NAME, 
                             pos=pos, 
                             gui_style = DEFAULT_STYLE,
                             size=size)
        self.frame.Hide()
        if not IS_WIN:
            self.frame.EnableCloseButton(False)
        self.s_screen = None

        try:
            self.open_file()
        except:
            msg = "%s Could not load " % str(APPLICATION_NAME)
            msg += "input file from command line.\n"
            logging.error(msg)
        # Display a splash screen on top of the frame.
        try:
            if os.path.isfile(SPLASH_SCREEN_PATH):
                self.s_screen = self.display_splash_screen(parent=self.frame, 
                                        path=SPLASH_SCREEN_PATH)
            else:
                self.frame.Show()   
        except:
            if self.s_screen is not None:
                self.s_screen.Close()
            msg = "Cannot display splash screen\n"
            msg += str (sys.exc_value)
            logging.error(msg)
            self.frame.Show()

        self.SetTopWindow(self.frame)
  
        return True
    
    def maximize_win(self):
        """
        Maximize the window after the frame shown
        """
        if self.is_max:
            if self.frame.IsShown():
                # Max window size
                self.frame.Maximize(self.is_max)

    def open_file(self):
        """
        open a state file at the start of the application
        """
        input_file = None
        if len(sys.argv) >= 2:
            cmd = sys.argv[0].lower()
            basename  = os.path.basename(cmd)
            app_base = str(APPLICATION_NAME).lower()
            if os.path.isfile(cmd) or basename.lower() == app_base:
                app_py = app_base + '.py'
                app_exe = app_base + '.exe'
                app_app = app_base + '.app'
                if basename.lower() in [app_py, app_exe, app_app, app_base]:
                    data_base = sys.argv[1]
                    input_file = os.path.normpath(os.path.join(DATAPATH, 
                                                               data_base))
        if input_file is None:
            return
        if self.frame is not None:
            self.frame.set_input_file(input_file=input_file)
         
    def clean_plugin_models(self, path): 
        """
        Delete plugin models  in app folder
        
        :param path: path of the plugin_models folder in app
        """
        # do it only the first time app loaded
        # delete unused model folder    
        model_folder = os.path.join(PATH_APP, path)
        if os.path.exists(model_folder) and os.path.isdir(model_folder):
            if len(os.listdir(model_folder)) > 0:
                try:
                    for file in os.listdir(model_folder):
                        file_path = os.path.join(model_folder, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                except:
                    logging.error("gui_manager.clean_plugin_models:\n  %s" \
                                  % sys.exc_value)
              
    def set_manager(self, manager):
        """
        Sets a reference to the application manager
        of the GUI manager (Frame) 
        """
        self.frame.set_manager(manager)
        
    def build_gui(self):
        """
        Build the GUI
        """
        #try to load file at the start
        try:
            self.open_file()
        except:
            raise
        self.frame.build_gui()
        
    def set_welcome_panel(self, panel_class):
        """
        Set the welcome panel
        
        :param panel_class: class of the welcome panel to be instantiated
        
        """
        self.frame.welcome_panel_class = panel_class
        
    def add_perspective(self, perspective):
        """
        Manually add a perspective to the application GUI
        """
        self.frame.add_perspective(perspective)
    
    def window_placement(self, size):
        """
        Determines the position and size of the application frame such that it
        fits on the user's screen without obstructing (or being obstructed by)
        the Windows task bar.  The maximum initial size in pixels is bounded by
        WIDTH x HEIGHT.  For most monitors, the application
        will be centered on the screen; for very large monitors it will be
        placed on the left side of the screen.
        """
        is_maximized = False
        # Get size of screen without 
        for screenCount in range(wx.Display().GetCount()):
            screen = wx.Display(screenCount)
            if screen.IsPrimary():
                displayRect = screen.GetClientArea()
                break
        
        posX, posY, displayWidth, displayHeight = displayRect        
        customWidth, customHeight = size
        
        # If the custom size is default, set 90% of the screen size
        if customWidth <= 0 and customHeight <= 0:
            if customWidth == 0 and customHeight == 0:
                is_maximized = True
            customWidth = displayWidth * 0.9
            customHeight = displayHeight * 0.9
        else:
            # If the custom screen is bigger than the 
            # window screen than make maximum size
            if customWidth > displayWidth:
                customWidth = displayWidth
            if customHeight > displayHeight:
                customHeight = displayHeight
            
        # Note that when running Linux and using an Xming (X11) server on a PC
        # with a dual  monitor configuration, the reported display size may be
        # that of both monitors combined with an incorrect display count of 1.
        # To avoid displaying this app across both monitors, we check for
        # screen 'too big'.  If so, we assume a smaller width which means the
        # application will be placed towards the left hand side of the screen.
        
        # If dual screen registered as 1 screen. Make width half.
        # MAC just follows the default behavior of pos
        if IS_WIN:
            if displayWidth > (displayHeight*2):
                if (customWidth == displayWidth):
                    customWidth = displayWidth/2
                # and set the position to be the corner of the screen.
                posX = 0
                posY = 0
                
            # Make the position the middle of the screen. (Not 0,0)
            else:
                posX = (displayWidth - customWidth)/2
                posY = (displayHeight - customHeight)/2
        # Return the suggested position and size for the application frame.    
        return (posX, posY), (customWidth, customHeight), is_maximized

    
    def display_splash_screen(self, parent, 
                              path=SPLASH_SCREEN_PATH):
        """Displays the splash screen.  It will exactly cover the main frame."""
       
        # Prepare the picture.  On a 2GHz intel cpu, this takes about a second.
        image = wx.Image(path, wx.BITMAP_TYPE_PNG)
        image.Rescale(SPLASH_SCREEN_WIDTH, 
                      SPLASH_SCREEN_HEIGHT, wx.IMAGE_QUALITY_HIGH)
        bm = image.ConvertToBitmap()

        # Create and show the splash screen.  It will disappear only when the
        # program has entered the event loop AND either the timeout has expired
        # or the user has left clicked on the screen.  Thus any processing
        # performed in this routine (including sleeping) or processing in the
        # calling routine (including doing imports) will prevent the splash
        # screen from disappearing.
        #
        # Note that on Linux, the timeout appears to occur immediately in which
        # case the splash screen disappears upon entering the event loop.
        s_screen = wx.SplashScreen(bitmap=bm,
                                   splashStyle=(wx.SPLASH_TIMEOUT|
                                                wx.SPLASH_CENTRE_ON_SCREEN),
                                   style=(wx.SIMPLE_BORDER|
                                          wx.FRAME_NO_TASKBAR|
                                          wx.FRAME_FLOAT_ON_PARENT),
                                   milliseconds=SS_MAX_DISPLAY_TIME,
                                   parent=parent,
                                   id=wx.ID_ANY)
        from sans.guiframe.gui_statusbar import SPageStatusbar
        statusBar = SPageStatusbar(s_screen)
        s_screen.SetStatusBar(statusBar)
        s_screen.Bind(wx.EVT_CLOSE, self.on_close_splash_screen)
        s_screen.Show()
        return s_screen
        
        
    def on_close_splash_screen(self, event):
        """
        When the splash screen is closed.
        """
        self.frame.Show(True)
        event.Skip()
        self.maximize_win()


class MDIFrame(CHILD_FRAME):
    """
    Frame for panels
    """
    def __init__(self, parent, panel, title="Untitled", size=(300,200)):
        """
        comment
        :param parent: parent panel/container
        """
        # Initialize the Frame object
        CHILD_FRAME.__init__(self, parent=parent, id=wx.ID_ANY, title=title, size=size)
        self.parent = parent
        self.name = "Untitled"
        self.batch_on = self.parent.batch_on
        self.panel = panel
        if panel != None:
            self.set_panel(panel)
        self.Show(False)
    
    def show_data_panel(self, action):
        """
        """
        self.parent.show_data_panel(action)
        
    def set_panel(self, panel):
        """
        """
        self.panel = panel
        self.name = panel.window_name
        self.SetTitle(panel.window_caption)
        self.SetHelpText(panel.help_string)
        width, height = self.parent._get_panels_size(panel)
        if hasattr(panel, "CENTER_PANE") and panel.CENTER_PANE:
            width *= 0.6  
        self.SetSize((width, height))
        self.parent.put_icon(self)
        self.Bind(wx.EVT_SET_FOCUS, self.set_panel_focus)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Show(False)
    
    def set_panel_focus(self, event):
        """
        """
        if self.parent.panel_on_focus != self.panel:
            self.panel.SetFocus()
            self.parent.panel_on_focus = self.panel
        
    def OnClose(self, event):
        """
        On Close event
        """
        self.panel.on_close(event)
        
if __name__ == "__main__": 
    app = ViewApp(0)
    app.MainLoop()
