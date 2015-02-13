"""
    1D Modeling for SANS
"""
#from sas.models import *

import os
from distutils.filelist import findall

__version__ = "2.1.0"

def get_data_path(media):
    """
    """
    # Check for data path in the package
    path = os.path.join(os.path.dirname(__file__), media)
    if os.path.isdir(path):
        return path

    # Check for data path next to exe/zip file.
    # If we are inside a py2exe zip file, we need to go up
    # to get to the directory containing 
    # the media for this module
    path = os.path.dirname(__file__)
    #Look for maximum n_dir up of the current dir to find media
    n_dir = 12
    for i in range(n_dir):
        path, _ = os.path.split(path)
        media_path = os.path.join(path, media)
        if os.path.isdir(media_path):
            module_media_path = os.path.join(media_path, 'models_media')
            if os.path.isdir(module_media_path):
                return module_media_path
            return media_path
   
    raise RuntimeError('Could not find models media files')

def data_files():
    """
    Return the data files associated with media.
    
    The format is a list of (directory, [files...]) pairs which can be
    used directly in setup(...,data_files=...) for setup.py.

    """
    data_files = []
    path = get_data_path(media="media")
    path_img = get_data_path(media=os.path.join("media","img"))
    im_list = findall(path_img)
    for f in findall(path):
        if os.path.isfile(f) and f not in im_list:
            data_files.append(('media/models_media', [f]))
    
    for f in im_list:
        data_files.append(('media/models_media/img', [f]))
    return data_files
