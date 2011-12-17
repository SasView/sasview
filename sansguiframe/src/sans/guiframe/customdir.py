# Setup and find Custom config dir
import sys
import os.path
import shutil
from sans import sansview
CONF_DIR = 'config' 
APPLICATION_NAME = 'sansview'

def _find_customconf_dir():
    """
    Find path of the config directory.
    The plugin directory is located in the user's home directory.
    """
    dir = os.path.join(os.path.expanduser("~"), ("." + APPLICATION_NAME), CONF_DIR)
    
    return dir

def _setup_conf_dir(path):
    """
    Setup the custom config dir
    """
    dir = _find_customconf_dir()
    # If the plugin directory doesn't exist, create it
    if not os.path.isdir(dir):
        os.makedirs(dir)
 
    # Place example user models as needed
    if not os.path.isfile(os.path.join(dir,"custom_config.py")):
        shutil.copy(os.path.join(path, "custom_config.py"), dir)
        
    return dir
  
        
class SetupCustom(object):
    """
    implement custom config dir
    """
    def find_dir(self):
        return _find_customconf_dir()
    
    def setup_dir(self, path):
        return _setup_conf_dir(path)
    

    
    
  