# Setup and find Custom config dir
import sys
import os.path
import shutil
from sas.sasgui.guiframe.CategoryInstaller import CategoryInstaller

CONF_DIR = 'config' 
APPLICATION_NAME = 'sasview'

def _find_usersasview_dir():
    """
    Find and return user/.sasview dir
    """
    dir = os.path.join(os.path.expanduser("~"), 
                       ("." + APPLICATION_NAME))
    return dir

def _find_customconf_dir():
    """
    Find path of the config directory.
    The plugin directory is located in the user's home directory.
    """
    u_dir = _find_usersasview_dir()
    dir = os.path.join(u_dir, CONF_DIR)
    
    return dir

def _setup_conf_dir(path):
    """
    Setup the custom config dir and cat file
    """
    dir = _find_customconf_dir()
    # If the plugin directory doesn't exist, create it
    if not os.path.isdir(dir):
        os.makedirs(dir)
    file = os.path.join(dir, "custom_config.py")
    cat_file = CategoryInstaller.get_user_file()
    # If the user category file doesn't exist copy the default to
    # the user directory
    if not os.path.isfile(cat_file):
        try:
            default_cat_file = CategoryInstaller.get_default_file()
            if os.path.isfile(default_cat_file):
                shutil.copyfile(default_cat_file, cat_file)
            else:
                print "Unable to find/copy default cat file"
        except:
            print "Unable to copy default cat file to the user dir."

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
    

    
    
  