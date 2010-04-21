PLUGIN_ID = "Calculator plug-in 1.0"
from calculator import *

import os
from distutils.filelist import findall

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
    path= os.path.dirname(__file__)
    n_dir = 4
    for i in range(n_dir):
        path,_ = os.path.split(path)

    path = os.path.join(path, '', media,'calculator_media' )
    if os.path.isdir(path):
        return path
    path = os.path.join(path, '', media)
    if os.path.isdir(path):
        return path
    raise RuntimeError('Could not find calculator media files')

def data_files():
    """
    Return the data files associated with media calculator.
    
    The format is a list of (directory, [files...]) pairs which can be
    used directly in setup(...,data_files=...) for setup.py.

    """
    data_files =[]
    path = get_data_path(media="media")
    for f in findall(path):
        data_files.append(('media/calculator_media', [f]))
    return data_files