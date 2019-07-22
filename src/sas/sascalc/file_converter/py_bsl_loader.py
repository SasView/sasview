"""
Python implementation of C extension bsl_loader.c
"""
import numpy as np

class PLoader():

    #File to load (string)
    @property
    def filename(self):
        return self._filename
    @filename.setter
    def filename(self, filename):
        self._filename = filename

    #Number of frames in the file (int)
    @property
    def n_frames(self):
        return self._n_frames
    @n_frames.setter
    def n_frames(self, n_frames):
        self._n_frames = n_frames

    #Frame to load (int)
    @property
    def frame(self):
        return self._frame
    @frame.setter
    def frame(self, frame):
        self._frame = frame

    #Number of pixels in the file (int)
    @property
    def n_pixels(self):
        return self._n_pixels
    @n_pixels.setter
    def n_pixels(self, n_pixels):
        self._n_pixels = n_pixels

    #Number of rasters in the file (int)
    @property
    def n_rasters(self):
        return self._n_rasters
    @n_rasters.setter
    def n_rasters(self, n_rasters):
        self._n_rasters = n_rasters

    #Whether or not the bytes are in reverse order (int)
    @property
    def swap_bytes(self):
        return self._swap_bytes
    @swap_bytes.setter
    def swap_bytes(self, swap_bytes):
        self._swap_bytes = swap_bytes

    def __init__(self, filename, frames, pixels, rasters, swap_bytes):
        self.filename = filename
        self.n_frames = frames
        self.n_pixels = pixels
        self.n_rasters = rasters
        self.swap_bytes = swap_bytes
        #Placeholder value
        self.frame = 0

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

    def load_data(self):
        """
        Load the data into a numpy array.
        """
        pass



if(__name__ == "__main__"):
    test = PLoader("Name", 20, 20, 20, 20)
    test.filename = "ASDF"
    test.frame = test.n_frames * test.n_pixels

    print(test)