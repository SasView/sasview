
"""
plugin DataLoader responsible of loading data
"""

from sans.guiframe.plugin_base import PluginBase

class Plugin(PluginBase):
    
    def __init__(self, standalone=False):
        PluginBase.__init__(self, name="DataLaoder", standalone=standalone)
        
    def populate_file_menu(self):
        """
        get a menu item and append it under file menu of the application
        add load file menu item and load folder item
        """
        hint_load_folder = "Read file(s) from a folder and load"
        hint_load_folder += " them into the application"
        hint_load_file = "Read files and load them into the application"
        return [["Load File", hint_load_file, self.parent._on_open]]
                 #["Load File", hint_load_file, self._load_file],
                #["Load Folder", hint_load_folder ,self._load_folder]]
  
    def _load_file(self, event):
        """
        Load file(s)
        """
    def _load_folder(self, event):
        """
        Load entire folder
        """
        