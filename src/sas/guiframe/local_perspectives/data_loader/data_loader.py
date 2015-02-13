
"""
plugin DataLoader responsible of loading data
"""
import os
import sys
import wx
import logging

from sas.dataloader.loader import Loader
import sas.dataloader.data_info as DataInfo
from sas.guiframe.plugin_base import PluginBase
from sas.guiframe.events import StatusEvent
from sas.guiframe.events import NewPlotEvent
from sas.guiframe.dataFitting import Data1D
from sas.guiframe.dataFitting import Data2D
from sas.guiframe.utils import parse_name
from sas.guiframe.gui_style import GUIFRAME
from sas.guiframe.gui_manager import DEFAULT_OPEN_FOLDER
try:
    # Try to find a local config
    import imp
    path = os.getcwd()
    if(os.path.isfile("%s/%s.py" % (path, 'local_config'))) or \
        (os.path.isfile("%s/%s.pyc" % (path, 'local_config'))):
        fObj, path, descr = imp.find_module('local_config', [path])
        config = imp.load_module('local_config', fObj, path, descr)  
    else:
        # Try simply importing local_config
        import local_config as config
except:
    # Didn't find local config, load the default 
import sas.guiframe.config as config

if config is None:
import sas.guiframe.config as config
    
       
extension_list = []
if config.APPLICATION_STATE_EXTENSION is not None:
    extension_list.append(config.APPLICATION_STATE_EXTENSION)
EXTENSIONS = config.PLUGIN_STATE_EXTENSIONS + extension_list   
PLUGINS_WLIST = config.PLUGINS_WLIST
APPLICATION_WLIST = config.APPLICATION_WLIST

class Plugin(PluginBase):
    
    def __init__(self, standalone=False):
        PluginBase.__init__(self, name="DataLoader", standalone=standalone)
        #Default location
        self._default_save_location = DEFAULT_OPEN_FOLDER
        self.loader = Loader()  
        self._data_menu = None 
        
    def help(self, evt):
        """
        Show a general help dialog. 
        """
        from help_panel import  HelpWindow
        frame = HelpWindow(None, -1) 
        if hasattr(frame, "IsIconized"):
            if not frame.IsIconized():
                try:
                    icon = self.parent.GetIcon()
                    frame.SetIcon(icon)
                except:
                    pass  
        frame.Show(True)
        
    def populate_file_menu(self):
        """
        get a menu item and append it under file menu of the application
        add load file menu item and load folder item
        """
        #menu for data files
        menu_list = []
        data_file_hint = "load one or more data in the application"
        menu_list = [('&Load Data File(s)', data_file_hint, self.load_data)]
        gui_style = self.parent.get_style()
        style = gui_style & GUIFRAME.MULTIPLE_APPLICATIONS
        style1 = gui_style & GUIFRAME.DATALOADER_ON
        if style == GUIFRAME.MULTIPLE_APPLICATIONS:
            #menu for data from folder
            data_folder_hint = "load multiple data in the application"
            menu_list.append(('&Load Data Folder', data_folder_hint, 
                              self._load_folder))
        return menu_list
   

    def load_data(self, event):
        """
        Load data
        """
        path = None
        self._default_save_location = self.parent._default_save_location
        if self._default_save_location == None:
            self._default_save_location = os.getcwd()
        
        cards = self.loader.get_wildcards()
        temp = [APPLICATION_WLIST] + PLUGINS_WLIST
        for item in temp:
            if item in cards:
                cards.remove(item)
        wlist =  '|'.join(cards)
        style = wx.OPEN|wx.FD_MULTIPLE
        dlg = wx.FileDialog(self.parent, 
                            "Choose a file", 
                            self._default_save_location, "",
                             wlist,
                             style=style)
        if dlg.ShowModal() == wx.ID_OK:
            file_list = dlg.GetPaths()
            if len(file_list) >= 0 and not(file_list[0]is None):
                self._default_save_location = os.path.dirname(file_list[0])
                path = self._default_save_location
        dlg.Destroy()
        
        if path is None or not file_list or file_list[0] is None:
            return
        self.parent._default_save_location = self._default_save_location
        self.get_data(file_list)
        
        
    def can_load_data(self):
        """
        if return True, then call handler to laod data
        """
        return True
 
       
    def _load_folder(self, event):
        """
        Load entire folder
        """
        path = None
        self._default_save_location = self.parent._default_save_location
        if self._default_save_location == None:
            self._default_save_location = os.getcwd()
        dlg = wx.DirDialog(self.parent, "Choose a directory", 
                           self._default_save_location,
                            style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self._default_save_location = path
        dlg.Destroy()
        if path is not None:
            self._default_save_location = os.path.dirname(path)
        else:
            return    
        file_list = self.get_file_path(path)
        self.get_data(file_list)
        self.parent._default_save_location = self._default_save_location
        
    def load_error(self, error=None):
        """
        Pop up an error message.
        
        :param error: details error message to be displayed
        """
        if error is not None or str(error).strip() != "":
            dial = wx.MessageDialog(self.parent, str(error), 'Error Loading File',
                                wx.OK | wx.ICON_EXCLAMATION)
            dial.ShowModal()  
        
    def get_file_path(self, path):
        """
        Receive a list containing folder then return a list of file
        """
        if os.path.isdir(path):
            return [os.path.join(os.path.abspath(path),
                                  file) for file in os.listdir(path)]
   
    def get_data(self, path, format=None):
        """
        """
        message = ""
        log_msg = ''
        output = {}
        any_error = False
        error_message = ""
        for p_file in path:
            info = "info"
            basename  = os.path.basename(p_file)
            root, extension = os.path.splitext(basename)
            if extension.lower() in EXTENSIONS:
                any_error = True
                log_msg = "Data Loader cannot "
                log_msg += "load: %s\n" % str(p_file)
                log_msg += """Please try to open that file from "open project" """
                log_msg += """or "open analysis" menu\n"""
                error_message = log_msg + "\n"
                logging.info(log_msg)
                continue
        
            try:
                temp =  self.loader.load(p_file, format)
                if temp.__class__.__name__ == "list":
                    for item in temp:
                        data = self.parent.create_gui_data(item, p_file)
                        output[data.id] = data
                else:
                    data = self.parent.create_gui_data(temp, p_file)
                    output[data.id] = data
                message = "Loading Data..." + str(p_file) + "\n"
                self.load_update(output=output, message=message, info=info)
            except:
                any_error = True
                if error_message == "":
                     error = "Error: " + str(sys.exc_value) + "\n"
                     error += "while loading Data: \n%s\n" % str(p_file)
                     error_message = "The data file you selected could not be loaded.\n"
                     error_message += "Make sure the content of your file"
                     error_message += " is properly formatted.\n\n"
                     error_message += "When contacting the DANSE team, mention the"
                     error_message += " following:\n%s" % str(error)
                else:
                     error_message += "%s\n"% str(p_file)
                info = "error"
                self.load_update(output=output, message=error_message, 
                                  info=info)
                
        message = "Loading Data Complete! "
        message += log_msg
        if error_message != "":
            info = 'error'
        self.load_complete(output=output, error_message=error_message,
                       message=message, path=path, info=info)
            
    def load_update(self, output=None, message="", info="warning"):
        """
        print update on the status bar
        """
        if message != "":
            wx.PostEvent(self.parent, StatusEvent(status=message, info='info', 
                                                  type="progress"))
    def load_complete(self, output, message="", error_message="", path=None, 
                      info="warning"):
        """
         post message to  status bar and return list of data
        """
        wx.PostEvent(self.parent, StatusEvent(status=message, 
                                              info=info,
                                              type="stop"))
        #if error_message != "":
        #    self.load_error(error_message)
        self.parent.add_data(data_list=output)
   
    
        
   