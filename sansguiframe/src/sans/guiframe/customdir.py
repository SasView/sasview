# Setup and find Custom config dir
import sys
import os.path
import shutil

CONF_DIR = 'config' 
APPLICATION_NAME = 'sasview'

def _find_customconf_dir():
    """
    Find path of the config directory.
    The plugin directory is located in the user's home directory.
    """
    dir = os.path.join(os.path.expanduser("~"), 
                       ("." + APPLICATION_NAME), CONF_DIR)
    
    return dir

def _setup_conf_dir(path):
    """
    Setup the custom config dir
    """
    dir = _find_customconf_dir()
    # If the plugin directory doesn't exist, create it
    if not os.path.isdir(dir):
        os.makedirs(dir)
    file = os.path.join(dir, "custom_config.py")
    # Place example user models as needed
    try:
        if not os.path.isfile(file):
         shutil.copyfile(os.path.join(path, "custom_config.py"), file)
    except:
        # Check for data path next to exe/zip file.
        #Look for maximum n_dir up of the current dir to find plugins dir
        n_dir = 12
        is_dir = False
        f_dir = path
        for i in range(n_dir):
            if i > 1:
                f_dir, _ = os.path.split(f_dir)
            temp_path = os.path.join(f_dir, "custom_config.py")
            if os.path.isfile(temp_path):
                shutil.copyfile(temp_path, file)
                is_dir = True
                break
        if not is_dir:
            raise
        
    return dir
  
        
class SetupCustom(object):
    """
    implement custom config dir
    """
    def find_dir(self):
        return _find_customconf_dir()
    
    def setup_dir(self, path):
        return _setup_conf_dir(path)
    

    
    
  