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
        is_bsl = False
        # Check if file is a BSL or OTOKO header file
        f = open(filename, 'r')
        f.readline()
        f.readline()
        bsl_metadata = f.readline().strip().split()
        f.close()
        if len(bsl_metadata) == 10:
            msg = ("Error parsing ASII data. {} looks like a BSL or OTOKO "
                "header file.")
            raise Exception(msg.format(os.path.split(filename)[-1]))

    if len(data.shape) != 1:
        msg = "Error reading {}: Only one column of data is allowed"
        raise Exception(msg.format(filename.split('\\')[-1]))

    is_float = True
    try:
        float(data[0])
    except:
        is_float = False

    if not is_float:
        end_char = data[0][-1]
        # If lines end with comma or semi-colon, trim the last character
        if end_char == ',' or end_char == ';':
            data = [s[0:-1] for s in data]
        else:
            msg = ("Error reading {}: Lines must end with a digit, comma "
                "or semi-colon").format(filename.split('\\')[-1])
            raise Exception(msg)

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
        raise Exception(msg)
        return
    else:
        qdata = qdata[0]
    return qdata, iqdata

def extract_bsl_data(filename):
    """
    Extracts data from a 2D BSL file

    :param filename: The header file to extract the data from
    :return x_data: A 1D array containing all the x coordinates of the data
    :return y_data: A 1D array containing all the y coordinates of the data
    :return frame_data: A dictionary of the form *{frame_number: data}*, where data is a 2D numpy array containing the intensity data
    """
    loader = BSLLoader(filename)
    frames = [0]
    should_continue = True

    if loader.n_frames > 1:
        params = ask_frame_range(loader.n_frames)
        frames = params['frames']
        if len(frames) == 0:
            should_continue = False
    elif loader.n_rasters == 1 and loader.n_frames == 1:
        message = ("The selected file is an OTOKO file. Please select the "
        "'OTOKO 1D' option if you wish to convert it.")
        raise Exception(message)
    else:
        message = ("The selected data file only has 1 frame, it might be"
            " a multi-frame OTOKO file.\nContinue conversion?")
        raise Exception(message)

    frame_data = loader.load_frames(frames)

    return frame_data

def convert_1d_data(qdata, iqdata, ofile, metadata):
    """
    Formats a 1D array of q_axis data and a 2D array of I axis data (where
    each row of iqdata is a separate row), into an array of Data1D objects
    """
    frames = []
    increment = 1
    single_file = True
    n_frames = iqdata.shape[0]
    # Standard file has 3 frames: SAS, calibration and WAS
    if n_frames > 3:
        # File has multiple frames - ask the user which ones they want to
        # export
        params = ask_frame_range(n_frames)
        frames = params['frames']
        increment = params['inc']
        single_file = params['file']
        if frames == []: return
    else: # Only interested in SAS data
        frames = [0]

    output_path = ofile

    frame_data = {}
    for i in frames:
        data = Data1D(x=qdata, y=iqdata[i])
        frame_data[i] = data
    if single_file:
        # Only need to set metadata on first Data1D object
        frame_data = list(frame_data.values()) # Don't need to know frame numbers
        frame_data[0].filename = output_path.split('\\')[-1]
        for key, value in metadata.items():
            setattr(frame_data[0], key, value)
    else:
        # Need to set metadata for all Data1D objects
        for datainfo in list(frame_data.values()):
            datainfo.filename = output_path.split('\\')[-1]
            for key, value in metadata.items():
                setattr(datainfo, key, value)

    _, ext = os.path.splitext(output_path)
    if ext == '.xml':
        run_name = metadata['run_name']
        convert_to_cansas(frame_data, output_path, run_name, single_file)
    else: # ext == '.h5'
        w = NXcanSASWriter()
        w.write(frame_data, output_path)

def convert_2d_data(dataset, output, metadata):
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
        entry_attrs = { 'name': run_name }
    if single_file:
        writer.write(filepath, frame_data,
            sasentry_attrs=entry_attrs)
    else:
        # Folder and base filename
        [group_path, group_name] = os.path.split(filepath)
        ext = "." + group_name.split('.')[-1] # File extension
        for frame_number, frame_data in frame_data.items():
            # Append frame number to base filename
            filename = group_name.replace(ext, str(frame_number)+ext)
            destination = os.path.join(group_path, filename)
            writer.write(destination, [frame_data],
                sasentry_attrs=entry_attrs)

