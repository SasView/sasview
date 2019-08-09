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
        #Placeholder value
        self.frame = 0

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
        Attempts to cast value as a type type.
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
        """
        desc = "Filename: " + self.filename + "\n"
        desc += "n_frames: " + str(self.n_frames) + "\n"
        desc += "frame: " + str(self.frame) + "\n"
        desc += "n_pixels: " + str(self.n_pixels) + "\n"
        desc += "n_rasters: " + str(self.n_rasters) + "\n"
        desc += "swap_bytes: " + str(self.swap_bytes) + "\n"
        return desc

    #May be irrelevant in final build.
    def reverse_float(self, in_float):
        """
        Reverses the order of the bytes of a float.
        :param: in_float, float to be reversed.
        :return: float value reversed.

        """
        in_float = self.try_convert(np.float64, in_float)
        bits = in_float.byteswap()
        # print(bits)
        return bits
    def load_data(self):
        """
        Load the data into a numpy array.
        """
        data = np.array([self.n_rasters, self.n_pixels], dtype = np.float64)

        #conditional little endian if swap_bytes true or big endian otherwise.
        #may be the other way around.
        dtype = ('>f8', '<f8')[self.swap_bytes]

        #Move the file to the position of the data we're interested in begins.
        frame_pos = self.n_pixels * self.n_rasters * self.frame

        offset = frame_pos #offset in float, np should

        float_size = 4 #assume float size is 4 bytes for now.

        #Read as numpy array of type float little/big endian, will not need
        #reverse_float explicitly.
        #May need to make a file pointer seek it then do -
        file = open(self.filename, 'rb')
        #error on opening file
        if(file == False):
            raise RuntimeError("Unable to open file", self.filename)

        file.seek(offset)
        #file object
        input_file = np.fromfile(file, dtype = dtype)
        #load to string.
        input_file = np.fromfile(self.filename, dtype = dtype)
        #seek to offset represented by starting from particular index?

        #something like
        data = input_file[offset:]
        #2d/1d indexing need.

        #Reading as python default file pointer each byte
        #return as file pointer and read bytes individually
        input_file = open(self.filename, 'rb')

        input_file.seek(offset)

        for raster in range(self.n_rasters):
            for pixel in range(self.n_pixels):
                input = 0
                try:
                    input = input_file.read(float_size)
                except:
                    raise RuntimeError("Error reading file or EOF reached")

                if(swap_bytes == 0):
                    input = self.reverse_float(input)

                data[raster, pixel] = input










        return data



if(__name__ == "__main__"):
    test = Loader("Name", 20, 20, 20, 20)
    test.filename = "ASDF"
    test.filename = 3
    test.filename = True

    test.frame = test.n_frames * test.n_pixels
    test.frame = "asdf"
    print(test)
    test_array = np.array([57.4, 16.7])
    print(test.reverse_float(np.array(test_array)))
    print(test.reverse_float(test.reverse_float(test_array)))
    print(test.reverse_float(test.reverse_float(test.reverse_float(test_array))))

##
## arr & traverse.each.filter (\x -> x != 0).toSpherical.radius %= sin
##