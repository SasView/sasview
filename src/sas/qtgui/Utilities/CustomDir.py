# Setup and find Custom config dir
import os.path
import shutil

CONF_DIR = 'config' 
APPLICATION_NAME = 'sasview'

def _find_usersasview_dir():
    """
    Find and return user/.sasview dir
    """
    return os.path.join(os.path.expanduser("~"), ("." + APPLICATION_NAME))

def _find_customconf_dir():
    """
    Find path of the config directory.
    The plugin directory is located in the user's home directory.
    """
    u_dir = _find_usersasview_dir()
    return os.path.join(u_dir, CONF_DIR)

def setup_conf_dir(path):
    """
    Setup the custom config dir and cat file
    """
    conf_dir = _find_customconf_dir()
    # If the plugin directory doesn't exist, create it
    if not os.path.isdir(conf_dir):
        os.makedirs(conf_dir)
    config_file = os.path.join(conf_dir, "custom_config.py")

    # Place example user models as needed
    try:
        if not os.path.isfile(config_file):
            shutil.copyfile(os.path.join(path, "custom_config.py"), config_file)

        #Adding SAS_OPENCL if it doesn't exist in the config file
        # - to support backcompability
        if not "SAS_OPENCL" in open(config_file).read():
            open(config_file,"a+").write("SAS_OPENCL = \"None\"\n")
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
                shutil.copyfile(temp_path, config_file)
                is_dir = True
                break
        if not is_dir:
            raise
    return conf_dir

