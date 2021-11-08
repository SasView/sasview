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
import logging

from sas.sascalc.dataloader.readers import abs_reader
from sas.sascalc.dataloader.readers import anton_paar_saxs_reader
from sas.sascalc.dataloader.readers import ascii_reader
from sas.sascalc.dataloader.readers import cansas_reader
from sas.sascalc.dataloader.readers import cansas_reader_HDF5
from sas.sascalc.dataloader.readers import csv_reader
from sas.sascalc.dataloader.readers import danse_reader
from sas.sascalc.dataloader.readers import red2d_reader
from sas.sascalc.dataloader.readers import sesans_reader

logger = logging.getLogger(__name__)

FILE_ASSOCIATIONS = {
    ".xml": cansas_reader,
    ".ses": sesans_reader,
    ".h5": cansas_reader_HDF5,
    ".hdf": cansas_reader_HDF5,
    ".hdf5": cansas_reader_HDF5,
    ".nxs": cansas_reader_HDF5,
    ".txt": ascii_reader,
    ".csv": csv_reader,
    ".dat": red2d_reader,
    ".abs": abs_reader,
    ".cor": abs_reader,
    ".sans": danse_reader,
    ".pdh": anton_paar_saxs_reader
}


def read_associations(loader, settings=None):
    """
    Read the specified settings file to associate
    default readers to file extension.
    :param loader: Loader object
    :param settings: path to the json settings file [string]
    """
    # For each FileType entry, get the associated reader and extension
    if not settings:
        settings = FILE_ASSOCIATIONS
    for ext, reader in settings.items():
        # Associate the extension with a particular reader
        try:
            loader.associate_file_type(ext.lower(), reader)
        except Exception as exc:
            msg = "read_associations: skipping association"
            msg += " for %s\n  %s" % (ext.lower(), exc)
            logger.error(msg)


def get_generic_readers(settings=None):
    """
    Find and load the default loaders used by the program
    :param settings: path to the json settings file [string]
    :return: list of default loaders every file can potentially try to use
    """
    return [ascii_reader, cansas_reader, cansas_reader_HDF5]
