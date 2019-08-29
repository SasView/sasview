from copy import deepcopy
import os
import numpy as np

from sas.sascalc.dataloader.data_info import Data2D

class BSLParsingError(Exception):
    pass

class BSLLoader:
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
            except Exception:
                is_valid = False
                err_msg = "Invalid metadata in header file for {}"
                err_msg = err_msg.format(sasdata_filename)
            break

        header_file.close()
        if not is_valid:
            raise BSLParsingError(err_msg)

        self.filename = filename
        self.n_frames = frames
        self.n_pixels = pixels
        self.n_rasters = rasters
        self.swap_bytes = swap_bytes
        self.frame = np.int()

    #File to load.
    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, filename):
        self._filename = str(filename)

    #Number of frames in the file.
    @property
    def n_frames(self):
        return self._n_frames

    @n_frames.setter
    def n_frames(self, n_frames):
        self._n_frames = int(n_frames)

    #Frame to load.
    @property
    def frame(self):
        return self._frame

    @frame.setter
    def frame(self, frame):
        self._frame = int(frame)

    #Number of pixels in the file.
    @property
    def n_pixels(self):
        return self._n_pixels

    @n_pixels.setter
    def n_pixels(self, n_pixels):
        self._n_pixels = int(n_pixels)

    #Number of rasters in the file (int)
    @property
    def n_rasters(self):
        return self._n_rasters

    @n_rasters.setter
    def n_rasters(self, n_rasters):
        self._n_rasters = int(n_rasters)

    #Whether or not the bytes are in reverse order (int)
    @property
    def swap_bytes(self):
        return self._swap_bytes

    @swap_bytes.setter
    def swap_bytes(self, swap_bytes):
        self._swap_bytes = bool(swap_bytes)


    def load_frames(self, frames):
        frame_data = []
        # Prepare axis values (arbitrary scale)
        x = self.n_rasters * range(1, self.n_pixels+1)
        y = [self.n_pixels * [i] for i in range(1, self.n_rasters+1)]
        y = np.reshape(y, (1, self.n_pixels*self.n_rasters))[0]
        x_bins = x[:self.n_pixels]
        y_bins = y[0::self.n_pixels]

        for frame in frames:
            self.frame = frame
            raw_frame_data = self.load_data()
            data2d = Data2D(data=raw_frame_data, qx_data=x, qy_data=y)
            data2d.x_bins = x_bins
            data2d.y_bins = y_bins
            data2d.Q_unit = '' # Using arbitrary units
            frame_data.append(data2d)

        return frame_data

    def load_data(self):
        """
        Loads the file named in filename in 4 byte float, in either
        little or big Endian depending on self.swap_bytes.

        :return: np array of loaded floats.
        """
        #Set dtype to 4 byte float, big or little endian depending on swap_bytes.
        dtype = ('>f4', '<f4')[self.swap_bytes]

        #Size of float as stored in binary file should be 4 bytes.
        float_size = 4

        offset = self.n_pixels * self.n_rasters * self.frame * float_size

        with open(self.filename, 'rb') as input_file:
            input_file.seek(offset)
            #With numpy 1.17, could use np.fromfile(self.filename, dtype=dtype, offset=offset).
            load = np.float64(np.fromfile(input_file, dtype=dtype))
        except Exception as e:
            raise e

        return load
