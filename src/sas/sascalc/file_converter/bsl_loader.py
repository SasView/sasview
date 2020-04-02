import os

import numpy as np

from ..dataloader.data_info import Data2D

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
        [folder, filename] = os.path.split(filename)

        sasdata_filename = filename.replace('000.', '001.')
        if sasdata_filename == filename:
            err_msg = ("Invalid header filename {}.\nShould be of the format "
                       "Xnn000.XXX where X is any alphanumeric character and n is any"
                       " digit.").format(filename)
            raise BSLParsingError(err_msg)

        data_info = {}

        with open(os.path.join(folder, filename), 'r') as header_file:
            data_info = self._parse_header(header_file, filename, sasdata_filename, folder)

        self.filename = data_info['filename']
        self.n_frames = data_info['frames']
        self.n_pixels = data_info['pixels']
        self.n_rasters = data_info['rasters']
        self.swap_bytes = data_info['swap_bytes']

    def _parse_header(self, header_file, filename, sasdata_filename, folder):
        """
        Method that parses the header file and returns the metadata in data_info

        :param header_file: header file object.
        :return: metadata of header file.
        """
        data_info = {}
        # First 2 lines are headers
        header_file.readline()
        header_file.readline()

        metadata = header_file.readline().strip()
        metadata = metadata.split()
        data_filename = header_file.readline().strip()

        if len(metadata) != 10:
            err_msg = "Invalid header file: {}".format(filename)
            raise BSLParsingError(err_msg)

        if data_filename != sasdata_filename:
            last_file = (metadata[9] == '0')
            if last_file: # Reached last file we have metadata for
                err_msg = "No metadata for {} found in header file: {}"
                err_msg = err_msg.format(sasdata_filename, filename)
                raise BSLParsingError(err_msg)

        try:
            data_info = {
                'filename': os.path.join(folder, data_filename),
                'pixels': int(metadata[0]),
                'rasters': int(metadata[1]),
                'frames': int(metadata[2]),
                'swap_bytes': int(metadata[3])
            }
        except Exception:
            err_msg = "Invalid metadata in header file for {}"
            err_msg = err_msg.format(sasdata_filename)
            raise BSLParsingError(err_msg)

        return data_info

    @property
    def filename(self):
        """
        File to load.
        """
        return self._filename

    @filename.setter
    def filename(self, filename):
        self._filename = str(filename)

    @property
    def n_frames(self):
        """
        Number of frames in the file.
        """
        return self._n_frames

    @n_frames.setter
    def n_frames(self, n_frames):
        self._n_frames = int(n_frames)

    @property
    def n_pixels(self):
        """
        Number of pixels in the file.
        """
        return self._n_pixels

    @n_pixels.setter
    def n_pixels(self, n_pixels):
        self._n_pixels = int(n_pixels)

    @property
    def n_rasters(self):
        """
        Number of rasters in the file.
        """
        return self._n_rasters

    @n_rasters.setter
    def n_rasters(self, n_rasters):
        self._n_rasters = int(n_rasters)

    @property
    def swap_bytes(self):
        """
        Whether or not the bytes are in reverse order.
        """
        return self._swap_bytes

    @swap_bytes.setter
    def swap_bytes(self, swap_bytes):
        self._swap_bytes = bool(swap_bytes)


    def load_frames(self, frames):
        """
        Loads all frames of the BSl file into a Data2D object.

        :param frames: Number of frames.

        :return: Data2D frame_data.
        """
        frame_data = []
        # Prepare axis values (arbitrary scale)
        x = self.n_rasters * list(range(1, self.n_pixels+1))
        y = [self.n_pixels * [i] for i in list(range(1, self.n_rasters+1))]
        y = np.reshape(y, (1, self.n_pixels*self.n_rasters))[0]
        x_bins = x[:self.n_pixels]
        y_bins = y[0::self.n_pixels]

        for frame in frames:
            raw_frame_data = self.load_data(frame)
            data2d = Data2D(data=raw_frame_data, qx_data=x, qy_data=y)
            data2d.x_bins = x_bins
            data2d.y_bins = y_bins
            data2d.Q_unit = '' # Using arbitrary units
            frame_data.append(data2d)

        return frame_data

    def load_data(self, frame):
        """
        Loads the file named in filename in 4 byte float, in either
        little or big Endian depending on self.swap_bytes.

        :param frame: The frame to load.
        :return: np array of loaded floats.
        """
        # Set dtype to 4 byte float, big or little endian depending on swap_bytes.
        dtype = ('>f4', '<f4')[self.swap_bytes]

        # Size of float as stored in binary file should be 4 bytes.
        float_size = 4

        offset = self.n_pixels * self.n_rasters * frame * float_size

        with open(self.filename, 'rb') as input_file:
            input_file.seek(offset)
            # CRUFT: With numpy 1.17, could use np.fromfile(self.filename, dtype=dtype, offset=offset).
            data = np.float64(np.fromfile(input_file, dtype=dtype))

        return data

    def __str__(self):
        """
        Print the objects params.

        :return: string description of object parameters.
        """
        desc = "Filename: " + self.filename + "\n"
        desc += "n_frames: " + str(self.n_frames) + "\n"
        desc += "n_pixels: " + str(self.n_pixels) + "\n"
        desc += "n_rasters: " + str(self.n_rasters) + "\n"
        desc += "swap_bytes: " + str(self.swap_bytes) + "\n"
        return desc
