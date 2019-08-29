"""
A class to load BSL files, loads as numpy 32-bit floats.
"""
import numpy as np

class Loader():

    def __init__(self, filename, frames, pixels, rasters, swap_bytes):




    def try_convert(self, type, value):
        """
        Attempts to cast value as type (type).

        :param: type object to cast to.
        :param: value to be cast.

        :return: value cast to type, type(value) or None if not possible.
        """
        return_val = None
        try:
            return_val = type(value)
        except:
            return_val = None

        return return_val

    def __str__(self):
        """
        Print the objects params.

        :return: string description of object parameters.
        """
        desc = "Filename: " + self.filename + "\n"
        desc += "n_frames: " + str(self.n_frames) + "\n"
        desc += "frame: " + str(self.frame) + "\n"
        desc += "n_pixels: " + str(self.n_pixels) + "\n"
        desc += "n_rasters: " + str(self.n_rasters) + "\n"
        desc += "swap_bytes: " + str(self.swap_bytes) + "\n"
        return desc


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

        try:
            input_file = open(self.filename, 'rb')
        except:
            raise RuntimeError("Unable to open file: ", self.filename)

        input_file.seek(offset)

        #With numpy 1.17, could use np.fromfile(self.filename, dtype=dtype, offset=offset).
        load = np.float64(np.fromfile(input_file, dtype=dtype))

        return load
