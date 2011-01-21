
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

STATE_FILE_EXT = ['P(r) files (*.prv)|*.prv',
                  'P(r) files (*.sav)|*.sav',
                  'P(r) files (*.svs)|*.svs',
                  'Fitting files (*.fitv)|*.fitv',
                  'Fitting files (*.svs)|*.svs',
                  'Invariant files (*.inv)|*.inv',
                  'Invariant files (*.svs)|*.svs']
EXTENSIONS = ['.svs', '.prv', '.inv', '.fitv']

class Plugin(PluginBase):
    
    def __init__(self, standalone=False):
        PluginBase.__init__(self, name="DataLoader", standalone=standalone)
        #Default location
        self._default_save_location = None  
        self.data_name_dict = {}
        self.loader = Loader()   
        
    def populate_menu(self, id, owner):
        """
        Create a menu for the Data plug-in
        
        :param id: id to create a menu
        :param owner: owner of menu
        
        :return: list of information to populate the main menu
        
        """
        #Menu for data loader
        self.menu = wx.Menu()
        #menu for data files
        data_file_id = wx.NewId()
        data_file_hint = "load one or more data in the application"
        self.menu.Append(data_file_id, 
                         '&Load Data File(s)', data_file_hint)
        wx.EVT_MENU(owner, data_file_id, self._load_data)
        #menu for data from folder
        data_folder_id = wx.NewId()
        data_folder_hint = "load multiple data in the application"
        self.menu.Append(data_folder_id, 
                         '&Load Data Folder', data_folder_hint)
        wx.EVT_MENU(owner, data_folder_id, self._load_folder)
        #create  menubar items
        return [(id, self.menu, "Data")]
    
    def populate_file_menu(self):
        """
        get a menu item and append it under file menu of the application
        add load file menu item and load folder item
        """
        
        hint_load_file = "Read state's files and load them into the application"
        return [["Open State from File", hint_load_file, self._load_file]]
  
    def _load_data(self, event):
        """
        Load data
        """
        flag = True
        file_list = self.choose_data_file(flag)
        if not file_list or file_list[0] is None:
            return
        self.get_data(file_list, flag=flag)
        
    def _load_file(self, event):
        """
        Load  sansview defined files
        """
        flag = False
        file_list = self.choose_data_file(flag)
        if not file_list or file_list[0] is None:
            return
        self.get_data(file_list, flag=flag)
       
    def _load_folder(self, event):
        """
        Load entire folder
        """
        flag = True
        path = self.choose_data_folder(flag)
        if path is None:
            return
        file_list = self.get_file_path(path)
        self.get_data(file_list, flag=flag)
    
    def get_wild_card(self, flag=True):
        """
        :param flag: is True load only data file, else load state file
         return wild cards
        """
        if flag:
            cards = self.loader.get_wildcards()
            for item in STATE_FILE_EXT:
                if item in cards:
                    cards.remove(item)
        else:
            cards = STATE_FILE_EXT
        return '|'.join(cards)
        
        
    def choose_data_file(self, flag=True):
        """
        Open the file dialog to load file(s)
        """
        path = None
        if self._default_save_location == None:
            self._default_save_location = os.getcwd()
        
        cards = self.loader.get_wildcards()
        wlist = self.get_wild_card(flag)
        if flag:
            style = wx.OPEN|wx.FD_MULTIPLE
        else:
            style = wx.OPEN|wx.FD_DEFAULT_STYLE
            
        dlg = wx.FileDialog(self.parent, 
                            "Choose a file", 
                            self._default_save_location, "",
                             wlist,
                             style=style)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPaths()
            if len(path) >= 0 and not(path[0]is None):
                self._default_save_location = os.path.dirname(path[0])
        dlg.Destroy()
        return path
    
    def choose_data_folder(self, flag=True):
        """
        :param flag: is True load only data file, else load state file
        return a list of folder to read
        """
        path = None
        if self._default_save_location == None:
            self._default_save_location = os.getcwd()
        
        wlist = self.get_wild_card(flag)
        
        dlg = wx.DirDialog(self.parent, "Choose a directory", 
                           self._default_save_location,
                            style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self._default_save_location = path
        dlg.Destroy()
        return path
    
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
    
    def get_data(self, path, format=None, flag=True):
        """
        """
        message = ""
        log_msg = ''
        output = []
        error_message = ""
        for p_file in path:
            basename  = os.path.basename(p_file)
            root, extension = os.path.splitext(basename)
            if flag:
                if extension.lower() in EXTENSIONS:
                    log_msg = "Data Loader cannot "
                    log_msg += "load: %s\n" % str(p_file)
                    log_msg += "Try File -> open ...."
                    logging.info(log_msg)
                    continue
            else:
                if extension.lower() not in EXTENSIONS:
                    log_msg = "File Loader cannot"
                    log_msg += " load: %s\n" % str(p_file)
                    log_msg += "Try Data -> Load ...."
                    logging.info(log_msg)
                    continue
            try:
                temp =  self.loader.load(p_file)
                if temp.__class__.__name__ == "list":
                    for item in temp:
                        data = self.create_data(item, p_file)
                        output.append(data)
                else:
                    data = self.create_data(temp, p_file)
                    output.append(data)
                message = "Loading ..." + str(p_file) + "\n"
                self.load_update(output=output, message=message)
            except:
                error_message = "Error while loading: %s\n" % str(p_file)
                error_message += str(sys.exc_value) + "\n"
                self.load_update(output=output, message=error_message)
                
        message = "Loading Complete! "
        message += log_msg
        self.load_complete(output=output, error_message=error_message,
                       message=message, path=path)
            
   
    def old_get_data(self, path, format=None, flag=True):
        """
        :param flag: is True load only data file, else load state file
        Receive a list of file paths and return a list of Data objects
        """
        from .load_thread import DataReader
        message = "Start Loading \n"
        wx.PostEvent(self.parent, StatusEvent(status=message,
                                              info="info", type="progress"))
        calc_load = DataReader(loader=self.loader,
                               path=path,
                               flag=flag,
                               transform_data=self.create_data,
                               updatefn=self.load_update,
                               completefn=self.load_complete)
        calc_load.queue()
        
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
        self.parent.add_data(output)
        if error_message != "":
            self.load_error(error_message)
            
    def create_data(self, data, path):
        """
        Receive data from loader and create a data to use for guiframe
        """
        
        if issubclass(DataInfo.Data2D, data.__class__):
            new_plot = Data2D(image=None, err_image=None) 
        else: 
            new_plot = Data1D(x=[], y=[], dx=None, dy=None)
           
        new_plot.copy_from_datainfo(data) 
        data.clone_without_data(clone=new_plot)  
        #creating a name for data
        name = ""
        title = ""
        file_name = ""
        if path is not None:
            file_name = os.path.basename(path)
        if data.run:
            name = data.run[0]
        if name == "":
            name = file_name
        ## name of the data allow to differentiate data when plotted
        name = parse_name(name=name, expression="_")
        
        max_char = name.find("[")
        if max_char < 0:
            max_char = len(name)
        name = name[0:max_char]
        
        if name not in self.data_name_dict:
            self.data_name_dict[name] = 0
        else:
            self.data_name_dict[name] += 1
            name = name + " [" + str(self.data_name_dict[name]) + "]"
        #find title
        if data.title.strip():
            title = data.title
        if title.strip() == "":
            title = file_name
        
        if new_plot.filename.strip() == "":
            new_plot.filename = file_name
        
        new_plot.name = name
        new_plot.title = title
        ## allow to highlight data when plotted
        new_plot.interactive = True
        ## when 2 data have the same id override the 1 st plotted
        new_plot.id = name
        ##group_id specify on which panel to plot this data
        new_plot.group_id = name
        new_plot.is_data = True
        new_plot.path = path
        ##post data to plot
        # plot data
        return new_plot
        
       