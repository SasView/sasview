
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
import wx.aui
import os
import sys
import xml
import time
import py_compile
# Try to find a local config
import imp
import warnings
warnings.simplefilter("ignore")
import logging


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
from sans.guiframe.data_processor import BatchOutputFrame
from sans.guiframe.events import EVT_NEW_BATCH
from sans.dataloader.loader import Loader

DATAPATH = os.getcwd()
def _change_current_dir():
    """
    Get the path of the current ran file and change the application current
    directory to the directory of that file
    """
    tem_path = sys.path[0]
    if os.path.isfile(tem_path):
        tem_path = os.path.dirname(tem_path)
    
    os.chdir(os.path.abspath(tem_path))
    
    
_change_current_dir()    
PATH_APP = os.getcwd()

def _find_local_config(file, path):
    """
    Find configuration file for the current application
    """
    
    file_path = os.path.abspath(os.path.join(path, "%s.py" % file))
    if(os.path.isfile(file_path)):
        py_compile.compile(file=file_path)
        fObj, path_config, descr = imp.find_module(file, [path])
        try:
            return imp.load_module(file, fObj, path_config, descr) 
        except:
            raise
        finally:
            if fObj:
                fObj.close()
        
              
try:
    path = PATH_APP
    config = _find_local_config('local_config', path)
    if config is None:
        path, _ = os.path.split(PATH_APP)
        config = _find_local_config('local_config', path)
except:
    # Didn't find local config, load the default 
    import sans.guiframe.config as config
custom_config = None
try:
    path = PATH_APP
    custom_config = _find_local_config('custom_config', path)
    if custom_config is None:
        path, _ = os.path.split(PATH_APP)
        custom_config = _find_local_config('custom_config', path)
except:
    msg = "Custom_config file was not imported"
    logging.info(msg)
    

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
    DEFAULT_PERSPECTIVE = None
    CLEANUP_PLOT = False
    DEFAULT_OPEN_FOLDER = PATH_APP

DEFAULT_STYLE = config.DEFAULT_STYLE


PLOPANEL_HEIGTH = config.PLOPANEL_HEIGTH
DATAPANEL_HEIGHT = config.DATAPANEL_HEIGHT
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
if sys.platform.count("win32")==0:
    IS_WIN = False

    
class ViewerFrame(wx.Frame):
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
        
        wx.Frame.__init__(self, parent=parent, title=title, pos=pos,size=size)
        # title
        self.title = title
        # Preferred window size
        self._window_width, self._window_height = size
        self.__gui_style = gui_style
        # Logging info
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='sans_app.log',
                    filemode='w')        
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
        self._window_menu = None
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
        # number of plugins
        self._num_perspectives = 0
        # plot duck cleanup option
        self.cleanup_plots = CLEANUP_PLOT
        # (un)-focus color
        #self.color = '#b3b3b3'
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
        #panel on focus
        self.panel_on_focus = None
        #control_panel on focus
        self.cpanel_on_focus = None
        self.loader = Loader()   
        #data manager
        from data_manager import DataManager
        self._data_manager = DataManager()
        self._data_panel = DataPanel(parent=self)
        if self.panel_on_focus is not None:
            self._data_panel.set_panel_on_focus(self.panel_on_focus.window_caption)
        # list of plot panels in schedule to full redraw
        self.schedule = False
        #self.callback = True
        self._idle_count = 0
        self.schedule_full_draw_list = []
        self.idletimer = wx.CallLater(1, self._onDrawIdle)
        
        self.batch_frame = GridFrame(parent=self)
        self.batch_frame.Hide()
        # Check for update
        #self._check_update(None)
        # Register the close event so it calls our own method
        wx.EVT_CLOSE(self, self.Close)
        # Register to status events
        self.Bind(EVT_STATUS, self._on_status_event)
        #Register add extra data on the same panel event on load
        self.Bind(EVT_PANEL_ON_FOCUS, self.set_panel_on_focus)
        self.Bind(EVT_APPEND_BOOKMARK, self.append_bookmark)
        self.Bind(EVT_NEW_LOAD_DATA, self.on_load_data)
        self.Bind(EVT_NEW_BATCH, self.on_batch_selection)
        self.Bind(EVT_NEW_COLOR, self.on_color_selection)
        self.setup_custom_conf()
    
    def on_set_batch_result(self, data_outputs, data_inputs=None,
                             plugin_name=""):
        """
        Display data into a grid in batch mode and show the grid
        """
        t = time.localtime(time.time())
        time_str = time.strftime("%b %d %H;%M of %Y", t)
        name = "Batch"  +  time_str
        details = "File Generated by %s : %s" % (APPLICATION_NAME,
                                                     str(plugin_name))
        details += "on %s.\n" % time_str 
        ext = ".csv"
        file_name = "Batch_" + str(plugin_name)+ "_" + time_str + ext
        file_name = self._default_save_location + str(file_name)
        #Need to save configuration for later 
        frame = BatchOutputFrame(parent=self, data_outputs=data_outputs, 
                                 data_inputs=data_inputs,
                                file_name=file_name,
                                details=details)
        frame.Show(True)
    
    def open_with_localapp(self, data_inputs, data_outputs):
        """
        Display value of data into the application grid
        :param data: dictionary of string and list of items
        """
        self.batch_frame.set_data(data_inputs, data_outputs)
        self.batch_frame.Show(True)
        
    def on_read_batch_tofile(self, event):
        """
        Open a file dialog , extract the file to read and display values
        into a grid
        """
        path = None
        if self._default_save_location == None:
            self._default_save_location = os.getcwd()
        
        dlg = wx.FileDialog(self, 
                            "Choose a file", 
                            self._default_save_location, "",
                             "(*.csv)|*.csv| Text Files (*.txt)|*.txt")
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if path is not None:
                self._default_save_location = os.path.dirname(path)
        dlg.Destroy()
        
        self.read_batch_tofile(file_name=path)
        
    def read_batch_tofile(self, file_name):
        """
        Extract value from file name and Display them into a grid
        """
        if file_name is None or file_name.strip() == "":
            return
        data = {}
        fd = open(file_name, 'r')
        _, ext = os.path.splitext(file_name)
        separator = "\t"
        if ext.lower() == ".csv":
            separator = ","
        buffer = fd.read()
        lines = buffer.split('\n')
        fd.close()
        column_names_line  = ""
        index = None
        for index in range(len(lines)):
            line = lines[index]
            if line.find(separator) != -1:
                #found the first line containing the label
                column_names_line = line
                first_data_index = index
                break 
        if column_names_line.strip() == "" or index is None:
            return 
        col_name_toks = column_names_line.split(separator)
        c_index = 0
        for col_index in range(len(col_name_toks)):
            c_name = col_name_toks[col_index]
            if c_name.strip() != "":
                data[c_name] = [ lines[row].split(separator)[c_index]
                                for row in range(index + 1, len(lines)-1)]
                c_index += 1
        self.open_with_localapp(data=data)
        
    def write_batch_tofile(self, data, file_name, details=""):
        """
        Helper to write result from batch into cvs file
        """
        self._default_save_location = os.path.dirname(file_name)
        file_name = os.path.basename(file_name)
        if data is None or file_name is None or file_name.strip() == "":
            return
        _, ext = os.path.splitext(file_name)
        
        fd = open(file_name, 'w')
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
            msg = "Error occured when calling Excel\n"
            msg += "Check that Excel in installed in this machine or \n"
            msg += "Check that %s really exists.\n" % str(file_name)
            wx.PostEvent(self, StatusEvent(status=msg,
                                             info="error"))
            
         
    def on_batch_selection(self, event):
        """
        :param event: contains parameter enable . when enable is set to True
        the application is in Batch mode
        else the application is default mode(single mode)
        """
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
                    #self._check_applications_menu()
                    break
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
    
    def set_input_file(self, input_file):
        """
        :param input_file: file to read
        """
        self._input_file = input_file
        
    def get_data_manager(self):
        """
        """
        return self._data_manager
    
    def get_toolbar(self):
        """
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
        panel_name = 'No panel on focus'
        application_name = 'No Selected Analysis'
        if self.panel_on_focus is not None:
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
    
    def set_panel_on_focus_helper(self):
        """
        Helper for panel on focus with data_panel
        """
        panel_name = self.panel_on_focus.window_caption
        ID = self.panel_on_focus.uid
        self._data_panel.set_panel_on_focus(ID)
        #update combo
        if self.panel_on_focus in self.plot_panels.values():
            combo = self._data_panel.cb_plotpanel
            combo_title = str(self.panel_on_focus.window_caption)
            combo.SetStringSelection(combo_title)
            combo.SetToolTip( wx.ToolTip(combo_title )) 
        elif self.panel_on_focus != self._data_panel:
            cpanel = self.panel_on_focus
            if self.cpanel_on_focus != cpanel:
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
        """
        # set tool bar
        self._setup_tool_bar()
        # Set up the layout
        self._setup_layout()
        
        # Set up the menu
        self._setup_menus()
        
        try:
            self.load_from_cmd(self._input_file)
        except:
            msg = "%s Cannot load file %s\n" %(str(APPLICATION_NAME), 
                                             str(self._input_file))
            msg += str(sys.exc_value) + '\n'
            print msg
        if self._data_panel is not None and len(self.plugins) > 0:
            self._data_panel.fill_cbox_analysis(self.plugins)
        self.post_init()
        # Set Custom default
        self.set_custom_default_perspective()
        # Set up extra custom tool menu
        self._setup_extra_custom()
        #self.Show(True)
        #self._check_update(None)
    
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
        from gui_statusbar import StatusBar
        self.sb = StatusBar(self, wx.ID_ANY)
        self.SetStatusBar(self.sb)
        # Add panel
        default_flag = wx.aui.AUI_MGR_DEFAULT#| wx.aui.AUI_MGR_ALLOW_ACTIVE_PANE
        self._mgr = wx.aui.AuiManager(self, flags=default_flag)
        self._mgr.SetDockSizeConstraint(0.5, 0.5)
        # border color
        #self.b_color = wx.aui.AUI_DOCKART_BORDER_COLOUR  
        #self._mgr.GetArtProvider().SetColor(self.b_color, self.color)
        #self._mgr.SetArtProvider(wx.aui.AuiDockArt(wx.AuiDefaultDockArt))
        #print "set", self._dockart.GetColour(13)
        # Load panels
        self._load_panels()
        self.set_default_perspective()
        self._mgr.Update()
        
    def SetStatusText(self, *args, **kwds):
        """
        """
        number = self.sb.get_msg_position()
        wx.Frame.SetStatusText(number=number, *args, **kwds)
        
    def PopStatusText(self, *args, **kwds):
        """
        """
        field = self.sb.get_msg_position()
        wx.Frame.PopStatusText(field=field)
        
    def PushStatusText(self, *args, **kwds):
        """
        """
        field = self.sb.get_msg_position()
        wx.Frame.PushStatusText(self, field=field, string=string)

    def add_perspective(self, plugin):
        """
        Add a perspective if it doesn't already
        exist.
        """
        self._num_perspectives += 1
        is_loaded = False
        for item in self.plugins:
            if plugin.__class__ == item.__class__:
                msg = "Plugin %s already loaded" % plugin.sub_menu
                logging.info(msg)
                is_loaded = True  
        if not is_loaded:
            
            self.plugins.append(plugin)
             
      
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
        import imp
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
                    file = ''
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
                        #print msg
                        logging.error(msg)
                    finally:
                        if not file == None:
                            file.close()
        except:
            # Should raise and catch at a higher level and 
            # display error on status bar
            pass  

        return plugins
    
    def set_welcome_panel(self, panel_class):
        """
        Sets the default panel as the given welcome panel 
        
        :param panel_class: class of the welcome panel to be instantiated
        
        """
        self.defaultPanel = panel_class(self, -1, style=wx.RAISED_BORDER)
        
    def _get_panels_size(self, p):
        """
        find the proper size of the current panel
        get the proper panel width and height
        """
        panel_height_min = self._window_height
        panel_width_min = self._window_width 
        style = self.__gui_style & (GUIFRAME.MANAGER_ON)
        if self._data_panel is not None  and (p == self._data_panel):
            panel_width_min = DATAPANEL_WIDTH
            panel_height_min = self._window_height * 0.8
            return panel_width_min, panel_height_min
        if hasattr(p, "CENTER_PANE") and p.CENTER_PANE:
            style = self.__gui_style & (GUIFRAME.PLOTTING_ON|GUIFRAME.MANAGER_ON)
            if style == (GUIFRAME.PLOTTING_ON|GUIFRAME.MANAGER_ON):
                panel_width_min = self._window_width -\
                            (DATAPANEL_WIDTH +config.PLOPANEL_WIDTH)
            return panel_width_min, panel_height_min
        return panel_width_min, panel_height_min
    
    def _load_panels(self):
        """
        Load all panels in the panels directory
        """
        
        # Look for plug-in panels
        panels = []    
        for item in self.plugins:
            if hasattr(item, "get_panels"):
                ps = item.get_panels(self)
                panels.extend(ps)
       
        # Show a default panel with some help information
        # It also sets the size of the application windows
        #TODO: Use this for slpash screen
        if self.defaultPanel is None:
            self.defaultPanel = DefaultPanel(self, -1, style=wx.RAISED_BORDER)
        # add a blank default panel always present 
        self.panels["default"] = self.defaultPanel
        self._mgr.AddPane(self.defaultPanel, wx.aui.AuiPaneInfo().
                              Name("default").
                              CenterPane().
                              #CloseButton(False).
                              #MinimizeButton(False).
                              # This is where we set the size of
                              # the application window
                              BestSize(wx.Size(self._window_width, 
                                               self._window_height)).
                              Show())

        #add data panel 
        self.panels["data_panel"] = self._data_panel
        w, h = self._get_panels_size(self._data_panel)
        self._mgr.AddPane(self._data_panel, wx.aui.AuiPaneInfo().
                              Name(self._data_panel.window_name).
                              Caption(self._data_panel.window_caption).
                              Left().
                              MinimizeButton().
                              CloseButton(True).
                              TopDockable(False).
                              BottomDockable(False).
                              LeftDockable(True).
                              RightDockable(False).
                              BestSize(wx.Size(w, h)).
                              Hide())

        style = self.__gui_style & GUIFRAME.MANAGER_ON
        data_pane = self._mgr.GetPane(self.panels["data_panel"].window_name)
        if style != GUIFRAME.MANAGER_ON:
            self._mgr.GetPane(self.panels["data_panel"].window_name).Hide()
        else:
            self._mgr.GetPane(self.panels["data_panel"].window_name).Show()
            
        # Add the panels to the AUI manager
        for panel_class in panels:
            p = panel_class
            id = wx.NewId()
            #w, h = self._get_panels_size(p)
            # Check whether we need to put this panel
            # in the center pane
            if hasattr(p, "CENTER_PANE") and p.CENTER_PANE:
                w, h = self._get_panels_size(p)
                if p.CENTER_PANE:
                    self.panels[str(id)] = p
                    self._mgr.AddPane(p, wx.aui.AuiPaneInfo().
                                          Name(p.window_name).
                                          CenterPane().
                                          Center().
                                          CloseButton(False).
                                          Hide())
            else:
                self.panels[str(id)] = p
                self._mgr.AddPane(p, wx.aui.AuiPaneInfo().
                                  Name(p.window_name).Caption(p.window_caption).
                                  Right().
                                  Dock().
                                  TopDockable().
                                  BottomDockable().
                                  LeftDockable().
                                  RightDockable().
                                  MinimizeButton().
                                  Hide())        
      
    def update_data(self, prev_data, new_data):
        """
        """
        prev_id, data_state = self._data_manager.update_data(prev_data=prev_data, 
                                       new_data=new_data)
        
        self._data_panel.remove_by_id(prev_id)
        self._data_panel.load_data_list(data_state)
        
    def update_theory(self, data_id, theory, state=None):
        """
        """ 
        data_state = self._data_manager.update_theory(data_id=data_id, 
                                         theory=theory,
                                         state=state)  
        self._data_panel.load_data_list(data_state)
        
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
        
    def popup_panel(self, p):
        """
        Add a panel object to the AUI manager
        
        :param p: panel object to add to the AUI manager
        
        :return: ID of the event associated with the new panel [int]
        
        """
        ID = wx.NewId()
        self.panels[str(ID)] = p
        count = 0
        for item in self.panels:
            if self.panels[item].window_name.startswith(p.window_name): 
                count += 1
        windowname = p.window_name
        windowcaption = 'Graph'#p.window_caption
        if count > 0:
            windowname += str(count+1)
            #caption += (' '+str(count))
        p.window_name = windowname

        # Append nummber
        captions = self._get_plotpanel_captions()
        while (1):
            self.graph_num += 1
            caption = windowcaption + '%s'% str(self.graph_num)
            if caption not in captions:
                break

        p.window_caption = caption
            
        style1 = self.__gui_style & GUIFRAME.FIXED_PANEL
        style2 = self.__gui_style & GUIFRAME.FLOATING_PANEL
        if style1 == GUIFRAME.FIXED_PANEL:
            self._mgr.AddPane(p, wx.aui.AuiPaneInfo().
                              Name(windowname).
                              Caption(caption).
                              Position(10).
                              Floatable().
                              Right().
                              Dock().
                              MinimizeButton().
                              Resizable(True).
                              # Use a large best size to make sure the AUI 
                              # manager takes all the available space
                              BestSize(wx.Size(PLOPANEL_WIDTH, 
                                               PLOPANEL_HEIGTH)))
        
            self._popup_fixed_panel(p)
    
        elif style2 == GUIFRAME.FLOATING_PANEL:
            self._mgr.AddPane(p, wx.aui.AuiPaneInfo().
                              Name(windowname).Caption(caption).
                              MinimizeButton().
                              Resizable(True).
                              # Use a large best size to make sure the AUI
                              #  manager takes all the available space
                              BestSize(wx.Size(PLOPANEL_WIDTH, 
                                               PLOPANEL_HEIGTH)))

            self._popup_floating_panel(p)
  
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
          
    def _setup_menus(self):
        """
        Set up the application menus
        """
        # Menu
        self._menubar = wx.MenuBar()
        self._add_menu_file()
        self._add_menu_edit()
        self._add_menu_view()
        #self._add_menu_data()
        self._add_menu_application()
        self._add_menu_tool()
        self._add_current_plugin_menu()
        self._add_menu_window()
        self._add_help_menu()
        self.SetMenuBar(self._menubar)
        
    def _setup_tool_bar(self):
        """
        add toolbar to the frame
        """
        #set toolbar
        self._toolbar = GUIToolBar(self, -1)
        self.SetToolBar(self._toolbar)
        self._update_toolbar_helper()
        self._on_toggle_toolbar(event=None)
    
    def _update_toolbar_helper(self):
        """
        """
        application_name = 'No Selected Analysis'
        panel_name = 'No Panel on Focus'
        if self._toolbar is  None:
            return
        if self.cpanel_on_focus is not None:
            self.reset_bookmark_menu(self.cpanel_on_focus)
        self._toolbar.update_toolbar(self.cpanel_on_focus)
        if self._current_perspective is not None:
            application_name = self._current_perspective.sub_menu
        if self.cpanel_on_focus is not None:
            panel_name = self.cpanel_on_focus.window_caption
            
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
        if (self._menubar is None) or (self._current_perspective is None):
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
                for (menu,name) in menu_list:
                    if self._applications_menu_pos == -1:
                        self._menubar.Append(menu, name)
                    else:
                        self._menubar.Insert(self._applications_menu_pos, menu, name)
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
        if config._do_tutorial:
            self._help_menu.AppendSeparator()
            id = wx.NewId()
            self._help_menu.Append(id,'&Tutorial', 'Software tutorial')
            wx.EVT_MENU(self, id, self._onTutorial)
            
        if config._do_aboutbox:
            self._help_menu.AppendSeparator()
            id = wx.NewId()
            self._help_menu.Append(id,'&About', 'Software information')
            wx.EVT_MENU(self, id, self._onAbout)
        
        # Checking for updates needs major refactoring to work with py2exe
        # We need to make sure it doesn't hang the application if the server
        # is not up. We also need to make sure there's a proper executable to
        # run if we spawn a new background process.
        #id = wx.NewId()
        #self._help_menu.Append(id,'&Check for update', 
        #'Check for the latest version of %s' % config.__appname__)
        #wx.EVT_MENU(self, id, self._check_update)
        self._menubar.Append(self._help_menu, '&Help')
            
    def _add_menu_view(self):
        """
        add menu items under view menu
        """
        if not VIEW_MENU:
            return
        self._view_menu = wx.Menu()
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
            self._toolbar_menu = self._view_menu.Append(id,'&Hide Toolbar', '')
        else:
            self._toolbar_menu = self._view_menu.Append(id,'&Show Toolbar', '')
        wx.EVT_MENU(self, id, self._on_toggle_toolbar)
        
        if custom_config != None:
            self._view_menu.AppendSeparator()
            id = wx.NewId()
            preference_menu = self._view_menu.Append(id,'Startup Setting', '')
            wx.EVT_MENU(self, id, self._on_preference_menu)
            
        self._menubar.Append(self._view_menu, '&View')   
         
    def _on_preference_menu(self, event):     
        """
        Build a panel to allow to edit Mask
        """
        
        from sans.guiframe.startup_configuration \
        import StartupConfiguration as ConfDialog
        
        self.panel = ConfDialog(parent=self, gui=self.__gui_style)
        self.panel.ShowModal()
        #wx.PostEvent(self.parent, event)
        

    def _add_menu_window(self):
        """
        add a menu window to the menu bar
        Window menu
        Attach a menu item for each panel in our
        panel list that also appears in a plug-in.
        
        Only add the panel menu if there is only one perspective and
        it has more than two panels.
        Note: the first plug-in is always the plotting plug-in. 
        The first application
        #plug-in is always the second one in the list.
        """
        self._window_menu = wx.Menu()
        if self._plotting_plugin is not None:
            for (menu, name) in self._plotting_plugin.populate_menu(self):
                self._window_menu.AppendSubMenu(menu, name)
        self._menubar.Append(self._window_menu, '&Graph')

        style = self.__gui_style & GUIFRAME.PLOTTING_ON
        if style == GUIFRAME.PLOTTING_ON:
            self._window_menu.AppendSeparator()
            id = wx.NewId()
            preferences_menu = wx.Menu()
            hint = "All plot panels will floating"
            preferences_menu.AppendRadioItem(id, '&Float All', hint)
            wx.EVT_MENU(self, id, self.set_plotpanel_floating)
            style = self.__gui_style & GUIFRAME.FLOATING_PANEL
            f_menu = preferences_menu.FindItemById(id)
            if style == GUIFRAME.FLOATING_PANEL: 
                f_checked = True
            else:
                f_checked = False
            f_menu.Check(f_checked)

            id = wx.NewId()
            hint = "All plot panels will displayed within the frame"
            preferences_menu.AppendRadioItem(id, '&Dock All', hint)
            wx.EVT_MENU(self, id, self.set_plotpanel_fixed) 
            if not f_checked:
                d_menu = preferences_menu.FindItemById(id)
                d_menu.Check(True)
            preferences_menu.AppendSeparator()
            id = wx.NewId()
            hint = "Clean up the dock area for plots on new-plot"
            preferences_menu.AppendCheckItem(id, '&CleanUp Dock on NewPlot', hint)
            wx.EVT_MENU(self, id, self.on_cleanup_dock)
            flag = self.cleanup_plots
            if self.cleanup_plots:
                c_menu = preferences_menu.FindItemById(id)
                c_menu.Check(True)  
            self._window_menu.AppendSubMenu(preferences_menu,'&Preferences')
        if self._window_menu.GetMenuItemCount() == 0:
            pos = self._menubar.FindMenu('Graph')
            self._menubar.Remove(pos)
        #wx.EVT_MENU(self, id, self.show_preferences_panel)   
        """
        if len(self.plugins) == 2:
            plug = self.plugins[1]
            pers = plug.get_perspective()
       
            if len(pers) > 1:
                self._window_menu = wx.Menu()
                for item in self.panels:
                    if item == 'default':
                        continue
                    panel = self.panels[item]
                    if panel.window_name in pers:
                        self._window_menu.Append(int(item),
                                                  panel.window_caption,
                                        "Show %s window" % panel.window_caption)
                        wx.EVT_MENU(self, int(item), self.on_view)
                self._menubar.Append(self._window_menu, '&Window')
                """

                
    def _add_menu_application(self):
        """
        
        # Attach a menu item for each defined perspective or application.
        # Only add the perspective menu if there are more than one perspectives
        add menu application
        """
        #style = self.__gui_style & GUIFRAME.MULTIPLE_APPLICATIONS
        #if style == GUIFRAME.MULTIPLE_APPLICATIONS:
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
            #self._applications_menu.
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
        #append item from plugin under menu file if necessary
        self._populate_file_menu()
        style = self.__gui_style & GUIFRAME.DATALOADER_ON
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
            #self._file_menu.AppendSeparator()
            id = wx.NewId()
            self._save_appl_menu = self._file_menu.Append(id, 
                                                      '&Save Analysis',
                        'Save state of the current active analysis panel')
            wx.EVT_MENU(self, id, self._on_save_application)
            self._file_menu.AppendSeparator()
        self._file_menu.AppendSeparator()
        id = wx.NewId()
        hint = "Display content of the file into a grid"
        self._file_menu.Append(id, '&Open Batch Result', hint) 
        wx.EVT_MENU(self, id, self.on_read_batch_tofile)
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
        
        self._edit_menu.Append(GUIFRAME_ID.PREVIEW_ID, '&Report Results',
                               'Preview current panel')
        wx.EVT_MENU(self, GUIFRAME_ID.PREVIEW_ID, self.on_preview_panel)
        #self._edit_menu.Append(GUIFRAME_ID.PRINT_ID, '&Print',
        #                       'Print current panel')
        #wx.EVT_MENU(self, GUIFRAME_ID.PRINT_ID, self.on_print_panel)
        self._edit_menu.Append(GUIFRAME_ID.RESET_ID, '&Reset Page', 
                               'Reset current panel')
        wx.EVT_MENU(self, GUIFRAME_ID.RESET_ID, self.on_reset_panel)
    
        self._menubar.Append(self._edit_menu,  '&Edit')
        self.enable_edit_menu()
        
    def get_style(self):
        """
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
        self.show_panel(evt.GetId(), 'on')      
        wx.CallLater(5, self.set_schedule(True))
        self.set_plot_unfocus()
        
    def on_close_welcome_panel(self):
        """
        Close the welcome panel
        """
        if self.defaultPanel is None:
            return 
        default_panel = self._mgr.GetPane(self.panels["default"].window_name)
        if default_panel.IsShown():
            default_panel.Hide()
            # Recover current perspective
            perspective = self._current_perspective
            perspective.on_perspective(event=None)
            self._mgr.Update()
            # Show toolbar
            #style = self.__gui_style & GUIFRAME.TOOLBAR_ON
            #if (style == GUIFRAME.TOOLBAR_ON) & (not self._toolbar.IsShown()):
            #    self._on_toggle_toolbar()
            
    def show_welcome_panel(self, event):
        """    
        Display the welcome panel
        """
        if self.defaultPanel is None:
            return 
        for id, panel in self.panels.iteritems():
            if id  ==  'default':
                # Show default panel
                if not self._mgr.GetPane(self.panels["default"].window_name).IsShown():
                    self._mgr.GetPane(self.panels["default"].window_name).Show(True)
            elif id == "data_panel":
                flag = self._mgr.GetPane(self.panels["data_panel"].window_name).IsShown()
                self._mgr.GetPane(self.panels["data_panel"].window_name).Show(flag)
            elif panel not in self.plot_panels.values() :
                self._mgr.GetPane(self.panels[id].window_name).IsShown()
                self._mgr.GetPane(self.panels[id].window_name).Hide()
        #style = self.__gui_style & GUIFRAME.TOOLBAR_ON
        #if (style == GUIFRAME.TOOLBAR_ON) & (self._toolbar.IsShown()):
        #    #    self._toolbar.Show(True)
        #    self._on_toggle_toolbar()

        self._mgr.Update()
       
    def show_panel(self, uid, show=None):
        """
        Shows the panel with the given id
        
        :param uid: unique ID number of the panel to show
        
        """
        ID = str(uid)
        config.printEVT("show_panel: %s" % ID)
        if ID in self.panels.keys():
            if not self._mgr.GetPane(self.panels[ID].window_name).IsShown(): 
                if show == 'on':
                    self._mgr.GetPane(self.panels[ID].window_name).Show()   
                elif self.panels[ID].window_caption.split(" ")[0] == \
                                                            "Residuals":
                    self._mgr.GetPane(self.panels[ID].window_name).Hide()
                else:
                    self._mgr.GetPane(self.panels[ID].window_name).Show()
                # Hide default panel
                self._mgr.GetPane(self.panels["default"].window_name).Hide()
        self._mgr.Update()     
        self._redraw_idle()
                    
    def hide_panel(self, uid):
        """
        hide panel except default panel
        """
        ID = str(uid)
        caption = self.panels[ID].window_caption
        config.printEVT("hide_panel: %s" % ID)
        if ID in self.panels.keys():
            if self._mgr.GetPane(self.panels[ID].window_name).IsShown():
                self._mgr.GetPane(self.panels[ID].window_name).Hide()
                if self._data_panel is not None and \
                            ID in self.plot_panels.keys():
                    self._data_panel.cb_plotpanel.Append(str(caption), p)
                # Do not Hide default panel here...
                #self._mgr.GetPane(self.panels["default"].window_name).Hide()
            self._mgr.Update()
                
    def delete_panel(self, uid):
        """
        delete panel given uid
        """
        ID = str(uid)
        config.printEVT("delete_panel: %s" % ID)
        caption = self.panels[ID].window_caption
        if ID in self.panels.keys():
            self.panel_on_focus = None
            panel = self.panels[ID]
            self._plotting_plugin.delete_panel(panel.group_id)
            self._mgr.DetachPane(panel)
            panel.Hide()
            panel.clear()
            panel.Close()
            #CallAfter: make sure panel is clear before updating mgr
            wx.CallAfter(self._mgr.Update)
            #delete uid number not str(uid)
            if uid in self.plot_panels.keys():
                del self.plot_panels[uid]
            return 
      
    def clear_panel(self):
        """
        """
        for item in self.panels:
            try:
                self.panels[item].clear_panel()
            except:
                pass
            
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
            logging.info(log_msg)
            self.load_complete(output=output, error_message=error_message,
                   message=log_msg, path=path)    
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
                    reader.read(path)
        
        style = self.__gui_style & GUIFRAME.MANAGER_ON
        if style == GUIFRAME.MANAGER_ON:
            if self._data_panel is not None:
                #data_state = self._data_manager.get_selected_data()
                #self._data_panel.load_data_list(data_state)
                self._mgr.GetPane(self._data_panel.window_name).Show(True)
      
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

    def load_state(self, path):   
        """
        load data from command line or application
        """
        if path and (path is not None) and os.path.isfile(path):
            basename  = os.path.basename(path)
            if APPLICATION_STATE_EXTENSION is not None \
                and basename.endswith(APPLICATION_STATE_EXTENSION):
                #Hide current plot_panels i
                for ID in self.plot_panels.keys():
                    panel = self._mgr.GetPane(self.plot_panels[ID].window_name)
                    if panel.IsShown():
                        panel.Hide()
            self.get_data(path)
        if self.defaultPanel is not None and \
            self._mgr.GetPane(self.panels["default"].window_name).IsShown():
            self.on_close_welcome_panel()
            
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
            print log_msg
            return
        message = ""
        log_msg = ''
        output = {}
        error_message = ""
        try:
            print "Loading Data...:\n" + str(path) + "\n"
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
            print error_message
 
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
            print error_message 
            
    def _on_open_state_application(self, event):
        """
        """
        path = None
        if self._default_save_location == None:
            self._default_save_location = os.getcwd()
        
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
            # Find the extension of the perspective and get that as 1st item in list
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
                    plug_wlist ='|'.join(plug_wlist)
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
        
        dlg = wx.FileDialog(self, 
                            "Choose a file", 
                            self._default_save_location, "",
                             APPLICATION_WLIST)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if path is not None:
                self._default_save_location = os.path.dirname(path)
        dlg.Destroy()
        
        #try:   
        #    os.popen(path)
        #    #self.Close()
        #except:
        self.load_state(path=path)
        
    def _on_save_application(self, event):
        """
        save the state of the current active application
        """
        if self.cpanel_on_focus is not None:
            try:
                self.cpanel_on_focus.on_save(event)
            except:
                msg = "Error occurred while saving: "
                msg += "To save, the application panel should have a data set.."
                wx.PostEvent(self, StatusEvent(status=msg))  
            
    def _on_save_project(self, event):
        """
        save the state of the SansView as *.svs
        """
        if self._current_perspective is  None:
            return
        reader, ext = self._current_perspective.get_extensions()
        path = None
        extension = '*' + APPLICATION_STATE_EXTENSION
        dlg = wx.FileDialog(self, "Save Project file",
                            self._default_save_location, "sansview_proj",
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
        
    def Close(self, event=None):
        """
        Quit the application
        """
        flag = self.quit_guiframe()
        if flag:
            wx.Exit()
            sys.exit()

    def _check_update(self, event=None): 
        """
        Check with the deployment server whether a new version
        of the application is available.
        A thread is started for the connecting with the server. The thread calls
        a call-back method when the current version number has been obtained.
        """
        if hasattr(config, "__update_URL__"):
            import version
            checker = version.VersionThread(config.__update_URL__,
                                            self._process_version,
                                            baggage=event==None)
            checker.start()  
    
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
            if cmp(version, config.__version__) > 0:
                msg = "Version %s is available! See the Help "
                msg += "menu to download it." % version
                self.SetStatusText(msg)
                if not standalone:
                    import webbrowser
                    webbrowser.open(config.__download_page__)
            else:
                if not standalone:
                    msg = "You have the latest version"
                    msg += " of %s" % config.__appname__
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
            import aboutbox 
            dialog = aboutbox.DialogAbout(None, -1, "")
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
                    #self.SetTopWindow(dialog)
                    dialog.Show(True) 
                except:
                    raise
                    msg = "This feature requires 'Adobe pdf Reader'\n"
                    msg += "Please install it first (Free)..."
                    wx.MessageBox(msg, 'Error')
            else:
                try:
                    command = "open "
                    command += path
                    os.system(command)
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
        #style = self.__gui_style & GUIFRAME.TOOLBAR_ON
        #if (style == GUIFRAME.TOOLBAR_ON) & (not self._toolbar.IsShown()):
        #    self._on_toggle_toolbar()
        for item in self.panels:
            # Check whether this is a sticky panel
            if hasattr(self.panels[item], "ALWAYS_ON"):
                if self.panels[item].ALWAYS_ON:
                    continue 
            
            if self.panels[item].window_name in panels:
                if not self._mgr.GetPane(self.panels[item].window_name).IsShown():
                    self._mgr.GetPane(self.panels[item].window_name).Show()
            else:
                # always show the data panel if enable
                style = self.__gui_style & GUIFRAME.MANAGER_ON
                if (style == GUIFRAME.MANAGER_ON) and self.panels[item] == self._data_panel:
                    if 'data_panel' in self.panels.keys():
                        flag = self._mgr.GetPane(self.panels['data_panel'].window_name).IsShown()
                        self._mgr.GetPane(self.panels['data_panel'].window_name).Show(flag)
                else:
                    if self._mgr.GetPane(self.panels[item].window_name).IsShown():
                        self._mgr.GetPane(self.panels[item].window_name).Hide()
                
        self._mgr.Update()
        
    def show_data_panel(self, event=None, action=True):
        """
        show the data panel
        """
        if self._data_panel_menu == None:
            return
        label = self._data_panel_menu.GetText()
        if label == 'Show Data Explorer':
            pane = self._mgr.GetPane(self.panels["data_panel"].window_name)
            #if not pane.IsShown():
            if action: 
                pane.Show(True)
                self._mgr.Update()
            self.__gui_style = self.__gui_style | GUIFRAME.MANAGER_ON
            
            self._data_panel_menu.SetText('Hide Data Explorer')
        else:
            pane = self._mgr.GetPane(self.panels["data_panel"].window_name)
            #if not pane.IsShown():
            if action:
                pane.Show(False)
                self._mgr.Update()
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
                self._mgr.GetPane(self._data_panel.window_name).Show(True)
                self._mgr.Update() 
        else:
            #automatically send that to the current perspective
            self.set_data(data_id=data_list.keys())
            self.on_close_welcome_panel()
       
    def set_data(self, data_id, theory_id=None): 
        """
        set data to current perspective
        """
        list_data, _ = self._data_manager.get_by_id(data_id)
        if self._current_perspective is not None:
            if self.cleanup_plots:
                for uid, panel in self.plot_panels.iteritems():
                    #panel = self.plot_panels[uid]
                    window = self._mgr.GetPane(panel.window_name)
                    # To hide all docked plot panels when set the data
                    if not window.IsFloating():
                        self.hide_panel(uid)
            self._current_perspective.set_data(list_data.values())
            self.on_close_welcome_panel()
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
                if self.cleanup_plots:
                    for id, panel in self.plot_panels.iteritems():
                        window = self._mgr.GetPane(panel.window_name)
                        # To hide all docked plot panels when set the data
                        if not window.IsFloating():
                            self.hide_panel(id)
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
        """
        value = [plug.is_in_use(temp) for plug in self.plugins]
        if len(value) > 0:
            print "value"
            return
            from data_panel import DataDialog
            dlg = DataDialog(data_list=data_list, nb_data=MAX_NBR_DATA)
            if dlg.ShowModal() == wx.ID_OK:
                selected_data_list = dlg.get_data()
            dlg.Destroy()
        """
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
                        if name == panel.window_name:
                            panel.on_set_focus(event=None)
                            break               
            name = self._current_perspective.sub_menu
            if self._data_panel is not None:
                self._data_panel.set_active_perspective(name)
                self._check_applications_menu()
            #Set the SansView title
            self._set_title_name(name)
          
            
    def _set_title_name(self, name):
        """
        Set the SansView title w/ the current application name
        
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
           
    def set_plotpanel_floating(self, event=None):
        """
        make the plot panel floatable
        """
        
        self.__gui_style &= (~GUIFRAME.FIXED_PANEL)
        self.__gui_style |= GUIFRAME.FLOATING_PANEL
        plot_panel = []
        id = event.GetId()
        menu = self._window_menu.FindItemById(id)
        if self._plotting_plugin is not None:
            plot_panel = self.plot_panels.values()
            for p in plot_panel:
                self._popup_floating_panel(p)
            menu.Check(True)
            
    def set_plotpanel_fixed(self, event=None):
        """
        make the plot panel fixed
        """
        self.__gui_style &= (~GUIFRAME.FLOATING_PANEL)
        self.__gui_style |= GUIFRAME.FIXED_PANEL
        plot_panel = []
        id = event.GetId()
        menu = self._window_menu.FindItemById(id)
        if self._plotting_plugin is not None:
            plot_panel = self.plot_panels.values()
            for p in plot_panel:
                self._popup_fixed_panel(p)
            menu.Check(True)
            
    def on_cleanup_dock(self, event=None):     
        """
        Set Cleanup Dock option
        """
        if event == None:
            return
        id = event.GetId()
        menu = self._window_menu.FindItemById(id)
        Flag = self.cleanup_plots
        if not Flag:
            menu.Check(True)
            self.cleanup_plots = True
            msg = "Cleanup-Dock option set to 'ON'."
        else:
            menu.Check(False)
            self.cleanup_plots = False
            msg = "Cleanup-Dock option set to 'OFF'."

        wx.PostEvent(self, StatusEvent(status= msg))
         
    def _popup_fixed_panel(self, p):
        """
        """
        style = self.__gui_style & GUIFRAME.FIXED_PANEL
        if style == GUIFRAME.FIXED_PANEL:
            self._mgr.GetPane(p.window_name).Dock()
            self._mgr.GetPane(p.window_name).Floatable()
            self._mgr.GetPane(p.window_name).Right()
            self._mgr.GetPane(p.window_name).TopDockable(False)
            self._mgr.GetPane(p.window_name).BottomDockable(False)
            self._mgr.GetPane(p.window_name).LeftDockable(False)
            self._mgr.GetPane(p.window_name).RightDockable(True)
            self._mgr.Update()
            
    def _popup_floating_panel(self, p):
        """
        """
        style = self.__gui_style &  GUIFRAME.FLOATING_PANEL
        if style == GUIFRAME.FLOATING_PANEL: 
            self._mgr.GetPane(p.window_name).Floatable(True)
            self._mgr.GetPane(p.window_name).Float()
            self._mgr.GetPane(p.window_name).Dockable(False)
            self._mgr.Update()
            
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
            if 'invstate' in new_plot.meta_data: is_state_data = True
            if  'prstate' in new_plot.meta_data: is_state_data = True
            if  'fitstate' in new_plot.meta_data: is_state_data = True
    
        return is_data1d and not is_data2d and not is_theory and not is_state_data
    
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
            #flag = self.cpanel_on_focus.get_print_flag()
            #self._edit_menu.Enable(GUIFRAME_ID.PRINT_ID, flag)
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
            #self._edit_menu.Enable(GUIFRAME_ID.PRINT_ID, flag)
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
        pane_info = self.get_paneinfo(name) 
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
        # update window Show menu
        if self._window_menu != None:
            for item in self._window_menu.GetMenuItems():
                pos = self._window_menu.FindItem(old_caption)
                if self._window_menu.GetLabel(pos) == str(old_caption):
                    self._window_menu.SetLabel(pos, caption)
                break
        # New Caption
        pane_info.Caption(caption)
        # update aui manager
        self._mgr.Update()
        return caption
        
    def get_paneinfo(self, name):
        """
        Get pane Caption from window_name
        
        :param name: window_name in AuiPaneInfo
        : return: AuiPaneInfo of the name
        """
        return self._mgr.GetPane(name) 
    
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
        if self.cpanel_on_focus is not None:
            self._toolbar.enable_drag(self.panel_on_focus)
            
    def enable_reset(self):
        """
        reset the current panel
        """
        if self.cpanel_on_focus is not None:
            self._toolbar.enable_reset(self.panel_on_focus)

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
                if self._mgr.GetPane(panel.window_name).IsShown():
                    break
                # otherwise, return
                if ind == count:
                    return

        #Simple redraw only for a panel shown
        def f_draw(panel):
            """
            Draw A panel in the full dwar list
            """
            try:
                # This checking of GetCapture is to stop redrawing
                # while any panel is capture.
                if self.GetCapture() == None:
                    # draw if possible
                    panel.set_resizing(False)
                    panel.Show(False)
                    panel.draw_plot()
                    
                    # Check if the panel is not shown
                    if not self._mgr.GetPane(panel.window_name).IsShown():
                        self._mgr.GetPane(panel.window_name).Hide()
                    else:
                        panel.Show(True)
            except:
                pass
        
        # Draw all panels        
        map(f_draw, self.schedule_full_draw_list)
        
        # Reset the attr  
        if len(self.schedule_full_draw_list) == 0:
            self.set_schedule(False)
        else:
            self.set_schedule(True)
        # do not update mgr
        #self._mgr.Update()
        
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
        self.set_plot_unfocus()
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
        self.idletimer.Restart(55, *args, **kwargs)

        
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
    


# Toy application to test this Frame
class ViewApp(wx.App):
    """
    """
    def OnInit(self):
        """
        """
        pos, size = self.window_placement((GUIFRAME_WIDTH, GUIFRAME_HEIGHT))
        self.frame = ViewerFrame(parent=None, 
                                 title=APPLICATION_NAME, 
                                 pos=pos, 
                                 gui_style = DEFAULT_STYLE,
                                 size=size) 
        self.frame.Hide()
        self.s_screen = None
        temp_path = None
        try:
            _change_current_dir()
        except:
            pass
        try:
            self.open_file()
        except:
            msg = "%s Could not load " % str(APPLICATION_NAME)
            msg += "input file from command line.\n"
            logging.error(msg)
        # Display a splash screen on top of the frame.
        if len(sys.argv) > 1 and '--time' in sys.argv[1:]:
            log_time("Starting to display the splash screen")
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
 
        if hasattr(self.frame, 'special'):
            self.frame.special.SetCurrent()
        self.SetTopWindow(self.frame)
  
        return True

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
        #if self.s_screen is not None and self.s_screen.IsShown():
        #    self.s_screen.Close()
        
    def set_welcome_panel(self, panel_class):
        """
        Set the welcome panel
        
        :param panel_class: class of the welcome panel to be instantiated
        
        """
        self.frame.set_welcome_panel(panel_class)
        
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
        window_width, window_height = size
        screen_size = wx.GetDisplaySize()
        window_height = window_height if screen_size[1]>window_height else screen_size[1]-10
        window_width  = window_width if screen_size[0]> window_width else screen_size[0]-10
        xpos = ypos = 0

        # Note that when running Linux and using an Xming (X11) server on a PC
        # with a dual  monitor configuration, the reported display size may be
        # that of both monitors combined with an incorrect display count of 1.
        # To avoid displaying this app across both monitors, we check for
        # screen 'too big'.  If so, we assume a smaller width which means the
        # application will be placed towards the left hand side of the screen.

        _, _, x, y = wx.Display().GetClientArea() # size excludes task bar
        if len(sys.argv) > 1 and '--platform' in sys.argv[1:]:
            w, h = wx.DisplaySize()  # size includes task bar area
        # display on left side, not centered on screen
        if x > 1920 and x > (2*y): x = x / 2  
        if x > window_width:  xpos = (x - window_width)/2
        if y > window_height: ypos = (y - window_height)/2

        # Return the suggested position and size for the application frame.
        return (xpos, ypos), (min(x, window_width), min(y, window_height))
    
    def display_splash_screen(self, parent, 
                              path=SPLASH_SCREEN_PATH):
        """Displays the splash screen.  It will exactly cover the main frame."""
       
        # Prepare the picture.  On a 2GHz intel cpu, this takes about a second.
        x, y = parent.GetSizeTuple()
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
                                        wx.STAY_ON_TOP),
                                        
                        milliseconds=SS_MAX_DISPLAY_TIME,
                        parent=parent,
                        id=wx.ID_ANY)
        from gui_statusbar import SPageStatusbar
        statusBar = SPageStatusbar(s_screen)
        s_screen.SetStatusBar(statusBar)
        s_screen.Bind(wx.EVT_CLOSE, self.on_close_splash_screen)
        s_screen.Show()
        return s_screen
        
        
    def on_close_splash_screen(self, event):
        """
        """
        self.frame.Show(True)
        event.Skip()
      
if __name__ == "__main__": 
    app = ViewApp(0)
    app.MainLoop()

             