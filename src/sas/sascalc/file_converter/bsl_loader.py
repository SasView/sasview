from sas.sascalc.file_converter.core.bsl_loader import CLoader
from copy import deepcopy
import os
import numpy as np

class BSLLoader(CLoader):

    # TODO: Change to __init__(self, filename, frame)
    # and parse n_(pixels/rasters) from header file
    def __init__(self, filename, frame):
        header_file = open(filename, 'r')
        data_info = {}
        is_valid = True
        err_msg = ""

        [folder, filename] = os.path.split(filename)

        # First 2 lines are headers
        header_file.readline()
        header_file.readline()

        while True:
            import pdb; pdb.set_trace()
            metadata = header_file.readline().strip()
            metadata = metadata.split()
            data_filename = header_file.readline().strip()

            if len(metadata) != 10:
                is_valid = False
                err_msg = "Invalid header file: {}".format(filename)
                break
            # SAS data will be in file Xnn001.mdd
            if data_filename != filename.replace('0.', '1.'):
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
                err_msg = "Invalid metadata in header file for {}".format(filename.replace('0.', '1.'))
            break

        if not is_valid:
            raise Exception(err_msg)

        if data_info['frames'] == 1:
            # File is actually in OTOKO (1D) format
            # Number of frames is 2nd indicator,
            data_info['frames'] = data_info['rasters']
            data_info['rasters'] = data_info['pixels']
            data_info['pixels'] = 1

        CLoader.__init__(self, data_info['filename'], frame,
            data_info['pixels'], data_info['rasters'], data_info['swap_bytes'])

    def __setattr__(self, name, value):
        if name == 'filename':
            return self.set_filename(value)
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
        elif name == 'frame':
            return self.get_frame()
        elif name == 'n_pixels':
            return self.get_n_pixels()
        elif name == 'n_rasters':
            return self.get_n_rasters()
        elif name == 'swap_bytes':
            return self.get_swap_bytes()
        return CLoader.__getattr__(self, name)

    def create_arr(self):
        return np.zeros((self.n_rasters, self.n_pixels))
