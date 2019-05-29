PLUGIN_ID = "Calculator plug-in 1.0"
import os
from distutils.filelist import findall
from .calculator import *
N_DIR = 12
def get_data_path(media):
    """
    """
    # Check for data path in the package
    path = os.path.join(os.path.dirname(__file__), media)
    if os.path.isdir(path):
        return path
    # Check for data path next to exe/zip file.
    # If we are inside a py2exe zip file, we need to go up
    # two levels to get to the directory containing the exe
    # We will check if the exe and the xsf are in the same
    # directory.
    path = os.path.dirname(__file__)
    #Look for maximum n_dir up of the current dir to find media

    #for i in range(n_dir):
    i = 0
    while(i < N_DIR):
        path, _ = os.path.split(path)
        media_path = os.path.join(path, media)
        if os.path.isdir(media_path):
             module_media_path = os.path.join(media_path,'calculator_%s'% media)
             if os.path.isdir(module_media_path):
                 return module_media_path
             return media_path
        i += 1

    raise RuntimeError('Could not find calculator media files')

def data_files():
    """
    Return the data files associated with media calculator.

    The format is a list of (directory, [files...]) pairs which can be
    used directly in setup(...,data_files=...) for setup.py.

    """
    data_files = []
    data_files.append(('media/calculator_media', findall(get_data_path("media"))))
    return data_files
