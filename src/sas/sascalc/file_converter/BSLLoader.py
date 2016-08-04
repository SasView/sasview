from sas.sascalc.file_converter.core.bsl_loader import CLoader
import numpy as np

class BSLLoader(CLoader):

    # TODO: Change to __init__(self, filename, frame)
    # and parse n_(pixels/rasters) from header file
    def __init__(self, filename, frame, n_pixels, n_rasters):
        CLoader.__init__(self, filename, frame, n_pixels, n_rasters)

    # See invertor.py for implementation of pickling and setters/getters

    # def __setattr__(self, name, value):
    #     # if name == 'param':
    #     #     return self.set_param(value)
    #     return CBSLLoader.__set_attr__(self, name, value)

    def __getattr__(self, name):
        if name == 'filename':
            return self.get_filename()
        elif name == 'frame':
            return self.get_frame()
        elif name == 'n_pixels':
            return self.get_n_pixels()
        elif name == 'n_rasters':
            return self.get_n_rasters()
        return CBSLLoader.__getattr__(self, name)

    def create_arr(self):
        return np.zeros((self.n_rasters, self.n_pixels))
