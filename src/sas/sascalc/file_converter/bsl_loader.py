from sas.sascalc.file_converter.core.bsl_loader import CLoader
from copy import deepcopy
import os
import numpy as np

class BSLParsingError(Exception):
    pass

class BSLLoader(CLoader):
    """
    Loads 2D SAS data from a BSL file.
    CLoader is a C extension (found in c_ext/bsl_loader.c)

    See http://www.diamond.ac.uk/Beamlines/Soft-Condensed-Matter/small-angle/SAXS-Software/CCP13/BSL.html
    for more info on the BSL file format.
    """

    def __init__(self, filename):
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
        if sasdata_filename == filename:
            err_msg = ("Invalid header filename {}.\nShould be of the format "
                "Xnn000.XXX where X is any alphanumeric character and n is any"
                " digit.").format(filename)
            raise BSLParsingError(err_msg)

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
            except:
                is_valid = False
                err_msg = "Invalid metadata in header file for {}"
                err_msg = err_msg.format(sasdata_filename)
            break

        if not is_valid:
            raise BSLParsingError(err_msg)

        CLoader.__init__(self, data_info['filename'], data_info['frames'],
            data_info['pixels'], data_info['rasters'], data_info['swap_bytes'])

    def __setattr__(self, name, value):
        if name == 'filename':
            return self.set_filename(value)
        elif name == 'n_frames':
            return self.set_n_frames(value)
        elif name == 'frame':
            return self.set_frame(value)
        elif name == 'n_pixels':
            return self.set_n_pixels(value)
        elif name == 'n_rasters':
            return self.set_n_rasters(value)
        elif name == 'swap_bytes':
            return self.set_swap_bytes(value)
        return CLoader.__setattr__(self, name, value)

    def __getattr__(self, name):
        if name == 'filename':
            return self.get_filename()
        elif name == 'n_frames':
            return self.get_n_frames()
        elif name == 'frame':
            return self.get_frame()
        elif name == 'n_pixels':
            return self.get_n_pixels()
        elif name == 'n_rasters':
            return self.get_n_rasters()
        elif name == 'swap_bytes':
            return self.get_swap_bytes()
        return CLoader.__getattr__(self, name)
