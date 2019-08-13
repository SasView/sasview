"""
Temporary class to run and load BSL files.
test.xml is the output from Sasview 4.x with input files
BSL 1D:
Q-Axis: Z83000.QAX and
Intesity Data: Z83000.IAD
"""
import os

import numpy as np
from loader import Loader

def parse_header(filename):
    """
    Parses the BSL header file and sets instance variables apropriately

    :param filename: Path to the BSL header file
    """
    header_file = open(filename, 'r')
    data_info = {}
    is_valid = True
    err_msg = ""

    [folder, filename] = os.path.split(filename)
    # SAS data will be in file Xnn001.mdd
    sasdata_filename = filename.replace('000.', '001.')

    # First 2 lines are headers
    header_file.readline()
    header_file.readline()

    while True:
        metadata = header_file.readline().strip()
        metadata = metadata.split()
        data_filename = header_file.readline().strip()

        if len(metadata) != 10:
            is_valid = False
            err_msg = "Invalid header file: {}".format(filename)
            break

        if data_filename != sasdata_filename:
            last_file = (metadata[9] == '0')
            if last_file: # Reached last file we have metadata for
                is_valid = False
                err_msg = "No metadata for {} found in header file: {}"
                err_msg = err_msg.format(sasdata_filename, filename)
                break
            continue
        try:
            data_info = {
                'filename': os.path.join(folder, data_filename),
                'pixels': int(metadata[0]),
                'rasters': int(metadata[1]),
                'frames': int(metadata[2]),
                'swap_bytes': int(metadata[3])
            }
        except Exception:
            is_valid = False
            err_msg = "Invalid metadata in header file for {}"
            err_msg = err_msg.format(sasdata_filename)
        break

    header_file.close()

    return data_info['filename'], data_info['frames'], data_info['pixels'], data_info['rasters'], data_info['swap_bytes']

if(__name__ == "__main__"):
    np.set_printoptions(precision = 14)

    q_params = parse_header("Z98000.QAX")
    print(q_params)
    q_loader = Loader(q_params[0], q_params[1], q_params[2], q_params[3], q_params[4])
    q_data = q_loader.load_data()
    print("Q params: ", q_data)

    i_params = parse_header("Z98000.I1D")
    print(i_params)
    i_loader = Loader(i_params[0], i_params[1], i_params[2], i_params[3], i_params[4])
    i_data = i_loader.load_data()
    print("I params: ", i_data)