
"""
plugin DataLoader responsible of loading data
"""
import os
import sys
import wx
import logging

from DataLoader.loader import Loader
import DataLoader.data_info as DataInfo
from sans.guiframe.plugin_base import PluginBase
from sans.guiframe.events import StatusEvent
from sans.guiframe.events import NewPlotEvent
from sans.guiframe.dataFitting import Data1D
from sans.guiframe.dataFitting import Data2D
from sans.guiframe.utils import parse_name
from sans.guiframe.gui_style import GUIFRAME
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
    import config
 
extension_list = []
if config.APPLICATION_STATE_EXTENSION is not None:
    extension_list.append(config.APPLICATION_STATE_EXTENSION)
EXTENSIONS = config.PLUGIN_STATE_EXTENSIONS + extension_list   

class Plugin(PluginBase):
    
    def __init__(self, standalone=False):
        PluginBase.__init__(self, name="DataLoader", standalone=standalone)
        #Default location
        self._default_save_location = None  
        self.loader = Loader()  
        self._data_menu = None 
        
    def populate_menu(self, parent):
        """
        """
         # Add menu data 
        self._data_menu = wx.Menu()
        #menu for data files
        data_file_id = wx.NewId()
        data_file_hint = "load one or more data in the application"
        self._data_menu.Append(data_file_id, 
                         '&Load Data File(s)', data_file_hint)
        wx.EVT_MENU(self.parent, data_file_id, self._load_data)
        gui_style = self.parent.get_style()
        style = gui_style & GUIFRAME.MULTIPLE_APPLICATIONS
        style1 = gui_style & GUIFRAME.DATALOADER_ON
        if style == GUIFRAME.MULTIPLE_APPLICATIONS:
            #menu for data from folder
            data_folder_id = wx.NewId()
            data_folder_hint = "load multiple data in the application"
            self._data_menu.Append(data_folder_id, 
                             '&Load Data Folder', data_folder_hint)
            wx.EVT_MENU(self.parent, data_folder_id, self._load_folder)
            
        return [(self._data_menu, 'Data')]

    def _load_data(self, event):
        """
        Load data
        """
        path = None
        if self._default_save_location == None:
            self._default_save_location = os.getcwd()
        
        cards = self.loader.get_wildcards()
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
        
    def load_error(self, error=None):
        """
        Pop up an error message.
        
        :param error: details error message to be displayed
        """
        message = "The data file you selected could not be loaded.\n"
        message += "Make sure the content of your file"
        message += " is properly formatted.\n\n"
        
        if error is not None:
            message += "When contacting the DANSE team, mention the"
            message += " following:\n%s" % str(error)
        dial = wx.MessageDialog(self.parent, message, 'Error Loading File',
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
        error_message = ""
        for p_file in path:
            basename  = os.path.basename(p_file)
            root, extension = os.path.splitext(basename)
            if extension.lower() in EXTENSIONS:
                log_msg = "Data Loader cannot "
                log_msg += "load: %s\n" % str(p_file)
                log_msg += "Try File opening ...."
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
                self.load_update(output=output, message=message)
            except:
                error_message = "Error while loading Data: %s\n" % str(p_file)
                error_message += str(sys.exc_value) + "\n"
                self.load_update(output=output, message=error_message)
                
        message = "Loading Data Complete! "
        message += log_msg
        self.load_complete(output=output, error_message=error_message,
                       message=message, path=path)
            
    def load_update(self, output=None, message=""):
        """
        print update on the status bar
        """
        if message != "":
            wx.PostEvent(self.parent, StatusEvent(status=message,
                                                  type="progress",
                                                   info="warning"))
    def load_complete(self, output, message="", error_message="", path=None):
        """
         post message to  status bar and return list of data
        """
        wx.PostEvent(self.parent, StatusEvent(status=message,
                                              info="warning",
                                              type="stop"))
        if error_message != "":
            self.load_error(error_message)
        self.parent.add_data(data_list=output)
   
    
        
   