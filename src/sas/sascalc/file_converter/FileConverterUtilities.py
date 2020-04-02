# pylint: disable=C0103, I1101
"""
Module with file loader specific static utilities.
"""
import os
import numpy as np

from sas.sascalc.dataloader.data_info import Data1D
from sas.sascalc.file_converter.nxcansas_writer import NXcanSASWriter
from sas.sascalc.file_converter.bsl_loader import BSLLoader
from sas.sascalc.file_converter.otoko_loader import OTOKOLoader
from sas.sascalc.file_converter.cansas_writer import CansasWriter

def extract_ascii_data(filename):
    """
    Extracts data from a single-column ASCII file

    :param filename: The file to load data from
    :return: A numpy array containing the extracted data
    """
    try:
        data = np.loadtxt(filename, dtype=str)
    except:
        # Check if file is a BSL or OTOKO header file
        f = open(filename, 'r')
        f.readline()
        f.readline()
        bsl_metadata = f.readline().strip().split()
        f.close()
        if len(bsl_metadata) == 10:
            msg = ("Error parsing ASII data. {} looks like a BSL or OTOKO "
                   "header file.")
            raise IOError(msg.format(os.path.split(filename)[-1]))

    if len(data.shape) != 1:
        msg = "Error reading {}: Only one column of data is allowed"
        raise IOError(msg.format(filename.split('\\')[-1]))

    is_float = True
    try:
        float(data[0])
    except:
        is_float = False

    if not is_float:
        end_char = data[0][-1]
        # If lines end with comma or semi-colon, trim the last character
        if end_char in (',', ';'):
            data = [s[0:-1] for s in data]
        else:
            msg = ("Error reading {}: Lines must end with a digit, comma "
                   "or semi-colon").format(filename.split('\\')[-1])
            raise IOError(msg)

    return np.array(data, dtype=np.float32)

def extract_otoko_data(qfile, ifile):
    """
    Extracts data from a 1D OTOKO file

    :param filename: The OTOKO file to load the data from
    :return: A numpy array containing the extracted data
    """
    loader = OTOKOLoader(qfile, ifile)
    otoko_data = loader.load_otoko_data()
    qdata = otoko_data.q_axis.data
    iqdata = otoko_data.data_axis.data
    if len(qdata) > 1:
        msg = ("Q-Axis file has multiple frames. Only 1 frame is "
               "allowed for the Q-Axis")
        raise IOError(msg)

    qdata = qdata[0]
    return qdata, iqdata

def convert_2d_data(dataset, output, metadata):
    """
    Wrapper for the NX SAS writer call
    Sets external metadata on the dataset first.
    """
    for key, value in metadata.items():
        setattr(dataset[0], key, value)

    w = NXcanSASWriter()
    w.write(dataset, output)

def convert_to_cansas(frame_data, filepath, run_name, single_file):
    """
    Saves an array of Data1D objects to a single CanSAS file with multiple
    <SasData> elements, or to multiple CanSAS files, each with one
    <SasData> element.

    :param frame_data: If single_file is true, an array of Data1D
        objects. If single_file is false, a dictionary of the
        form *{frame_number: Data1D}*.
    :param filepath: Where to save the CanSAS file
    :param single_file: If true, array is saved as a single file,
        if false, each item in the array is saved to it's own file
    """
    writer = CansasWriter()
    entry_attrs = None
    if run_name != '':
        entry_attrs = {'name': run_name}
    if single_file:
        writer.write(filepath, frame_data,
                     sasentry_attrs=entry_attrs)
    else:
        # Folder and base filename
        [group_path, group_name] = os.path.split(filepath)
        ext = "." + group_name.split('.')[-1] # File extension
        for frame_number, frame_d in frame_data.items():
            # Append frame number to base filename
            filename = group_name.replace(ext, str(frame_number)+ext)
            destination = os.path.join(group_path, filename)
            writer.write(destination, [frame_d],
                         sasentry_attrs=entry_attrs)

def toFloat(text):
    """
    Dumb string->float converter
    """
    value = None
    try:
        value = float(text) if text != "" else None
    except ValueError:
        pass
    return value
