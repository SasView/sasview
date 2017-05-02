"""
Module to associate default readers to file extensions.
The module reads an xml file to get the readers for each file extension.
The readers are tried in order they appear when reading a file.
"""
############################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#If you use DANSE applications to do scientific research that leads to
#publication, we ask that you acknowledge the use of the software with the
#following sentence:
#This work benefited from DANSE software developed under NSF award DMR-0520547.
#copyright 2009, University of Tennessee
#############################################################################
from __future__ import print_function

import os
import sys
import logging
import json

logger = logging.getLogger(__name__)

FILE_NAME = 'defaults.json'

def read_associations(loader, settings=FILE_NAME):
    """
    Read the specified settings file to associate
    default readers to file extension.
    
    :param loader: Loader object
    :param settings: path to the json settings file [string]
    """
    reader_dir = os.path.dirname(__file__)
    path = os.path.join(reader_dir, settings)
    
    # If we can't find the file in the installation
    # directory, look into the execution directory.
    if not os.path.isfile(path):
        path = os.path.join(os.getcwd(), settings)
    if not os.path.isfile(path):
        path = os.path.join(sys.path[0], settings)
    if not os.path.isfile(path):
        path = settings
    if not os.path.isfile(path):
        path = "./%s" % settings
    if os.path.isfile(path):
        with open(path) as fh:
            json_tree = json.load(fh)
        
        # Read in the file extension associations
        entry_list = json_tree['SasLoader']['FileType']

        # For each FileType entry, get the associated reader and extension
        for entry in entry_list:
            reader = entry['-reader']
            ext = entry['-extension']
            
            if reader is not None and ext is not None:
                # Associate the extension with a particular reader
                # TODO: Modify the Register code to be case-insensitive
                # and remove the extra line below.
                try:
                    exec "import %s" % reader
                    exec "loader.associate_file_type('%s', %s)" % (ext.lower(),
                                                                    reader)
                    exec "loader.associate_file_type('%s', %s)" % (ext.upper(),
                                                                    reader)
                except:
                    msg = "read_associations: skipping association"
                    msg += " for %s\n  %s" % (ext.lower(), sys.exc_value)
                    logger.error(msg)
    else:
        print("Could not find reader association settings\n  %s [%s]" % (__file__, os.getcwd()))
         
         
def register_readers(registry_function):
    """
    Function called by the registry/loader object to register
    all default readers using a call back function.
    
    :WARNING: this method is now obsolete

    :param registry_function: function to be called to register each reader
    """
    logger.info("register_readers is now obsolete: use read_associations()")
    import abs_reader
    import ascii_reader
    import cansas_reader
    import danse_reader
    import hfir1d_reader
    import IgorReader
    import red2d_reader
    #import tiff_reader
    import nexus_reader
    import sesans_reader
    import cansas_reader_HDF5
    import anton_paar_saxs_reader
    registry_function(sesans_reader)
    registry_function(abs_reader)
    registry_function(ascii_reader)
    registry_function(cansas_reader)
    registry_function(danse_reader)
    registry_function(hfir1d_reader)
    registry_function(IgorReader)
    registry_function(red2d_reader)
    #registry_function(tiff_reader)
    registry_function(nexus_reader)
    registry_function(cansas_reader_HDF5)
    registry_function(anton_paar_saxs_reader)
    return True
