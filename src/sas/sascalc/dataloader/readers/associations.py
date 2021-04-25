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
import importlib
import logging

logger = logging.getLogger(__name__)

FILE_ASSOCIATIONS = {
    ".xml": "cansas_reader",
    ".ses": "sesans_reader",
    ".h5": "cansas_reader_HDF5",
    ".hdf": "cansas_reader_HDF5",
    ".hdf5": "cansas_reader_HDF5",
    ".nxs": "cansas_reader_HDF5",
    ".txt": "ascii_reader",
    ".csv": "csv_reader",
    ".dat": "red2d_reader",
    ".abs": "abs_reader",
    ".cor": "abs_reader",
    ".sans": "danse_reader",
    ".pdh": "anton_paar_saxs_reader"
}

GENERIC_ASSOCIATIONS = {
    ".xml": "cansas_reader",
    ".h5": "cansas_reader_HDF5",
    ".txt": "ascii_reader",
}


def read_associations(loader, settings=FILE_ASSOCIATIONS):
    """
    Read the specified settings file to associate
    default readers to file extension.
    :param loader: Loader object
    :param settings: path to the json settings file [string]
    """
    # For each FileType entry, get the associated reader and extension
    path = 'sas.sascalc.dataloader.readers.'
    for ext, reader in settings.items():
        if reader is not None and ext is not None:
            # Associate the extension with a particular reader
            try:
                local_reader = importlib.import_module(path + reader)
                loader.associate_file_type(ext.lower(), local_reader)
            except Exception as exc:
                msg = "read_associations: skipping association"
                msg += " for %s\n  %s" % (ext.lower(), exc)
                logger.error(msg)


def get_generic_readers(settings=GENERIC_ASSOCIATIONS):
    """
    Find and load the default loaders used by the program
    :param settings: path to the json settings file [string]
    :return: list of default loaders every file can potentially try to use
    """
    path = 'sas.sascalc.dataloader.readers.'
    defaults = [importlib.import_module(path + reader) for ext, reader in
                settings.items() if reader is not None]
    return defaults
