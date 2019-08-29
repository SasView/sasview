"""
Python implementation of C extension bsl_loader.c
"""
import numpy as np

class Loader():

    def __init__(self, filename, frames, pixels, rasters, swap_bytes):
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
        _filename = self.try_convert(str, filename)
        self._filename = _filename

    #Number of frames in the file.
    @property
    def n_frames(self):
        return self._n_frames

    @n_frames.setter
    def n_frames(self, n_frames):
        _n_frames = self.try_convert(int, n_frames)
        self._n_frames = _n_frames

    #Frame to load.
    @property
    def frame(self):
        return self._frame

    @frame.setter
    def frame(self, frame):
        _frame = self.try_convert(int, frame)
        self._frame = _frame

    #Number of pixels in the file.
    @property
    def n_pixels(self):
        return self._n_pixels

    @n_pixels.setter
    def n_pixels(self, n_pixels):
        _n_pixels = self.try_convert(int, n_pixels)
        self._n_pixels = _n_pixels

    #Number of rasters in the file (int)
    @property
    def n_rasters(self):
        return self._n_rasters

    @n_rasters.setter
    def n_rasters(self, n_rasters):
        _n_rasters = self.try_convert(int, n_rasters)
        self._n_rasters = _n_rasters

    #Whether or not the bytes are in reverse order (int)
    @property
    def swap_bytes(self):
        return self._swap_bytes

    @swap_bytes.setter
    def swap_bytes(self, swap_bytes):
        _swap_bytes = self.try_convert(bool, swap_bytes)
        self._swap_bytes = _swap_bytes


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
