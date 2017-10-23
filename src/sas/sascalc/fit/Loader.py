from __future__ import print_function

# class Loader  to load any king of file
#import wx
#import string
import numpy as np

class Load:
    """
    This class is loading values from given file or value giving by the user
    """
    def __init__(self, x=None, y=None, dx=None, dy=None):
        raise NotImplementedError("a code search shows that this code is not active, and you are not seeing this message")
        # variable to store loaded values
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.filename = None

    def set_filename(self, path=None):
        """
        Store path into a variable.If the user doesn't give
        a path as a parameter a pop-up
        window appears to select the file.

        :param path: the path given by the user

        """
        self.filename = path

    def get_filename(self):
        """ return the file's path"""
        return self.filename

    def set_values(self):
        """ Store the values loaded from file in local variables"""
        if self.filename is not None:
            input_f =  open(self.filename, 'r')
            buff = input_f.read()
            lines = buff.split('\n')
            self.x = []
            self.y = []
            self.dx = []
            self.dy = []
            for line in lines:
                try:
                    toks = line.split()
                    x = float(toks[0])
                    y = float(toks[1])
                    dy = float(toks[2])

                    self.x.append(x)
                    self.y.append(y)
                    self.dy.append(dy)
                    self.dx = np.zeros(len(self.x))
                except:
                    print("READ ERROR", line)
            # Sanity check
            if not len(self.x) == len(self.dx):
                raise ValueError("x and dx have different length")
            if not len(self.y) == len(self.dy):
                raise ValueError("y and dy have different length")


    def get_values(self):
        """ Return x, y, dx, dy"""
        return self.x, self.y, self.dx, self.dy

    def load_data(self, data):
        """ Return plottable"""
        #load data
        data.x = self.x
        data.y = self.y
        data.dx = self.dx
        data.dy = self.dy
        #Load its View class
        #plottable.reset_view()


if __name__ == "__main__":
    load = Load()
    load.set_filename("testdata_line.txt")
    print(load.get_filename())
    load.set_values()
    print(load.get_values())

