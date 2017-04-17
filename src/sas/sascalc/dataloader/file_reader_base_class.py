"""
This is the base file reader class most file readers should inherit from.
All generic functionality required for a file loader/reader is built into this
class
"""

import os
import logging
import numpy as np
from abc import abstractmethod
from loader_exceptions import NoKnownLoaderException, FileContentsException,\
    DataReaderException
from data_info import Data1D, Data2D, DataInfo, plottable_1D, plottable_2D,\
    combine_data_info_with_plottable

logger = logging.getLogger(__name__)


class FileReader(object):
    # List of Data1D and Data2D objects to be sent back to data_loader
    output = []
    # Current plottable_(1D/2D) object being loaded in
    current_dataset = None
    # Current DataInfo object being loaded in
    current_datainfo = None
    # String to describe the type of data this reader can load
    type_name = "ASCII"
    # Wildcards to display
    type = ["Text files (*.txt|*.TXT)"]
    # List of allowed extensions
    ext = ['.txt']
    # Bypass extension check and try to load anyway
    allow_all = False
    # Able to import the unit converter
    has_converter = True
    # Open file handle
    f_open = None
    # Default value of zero
    _ZERO = 1e-16

    def read(self, filepath):
        """
        Basic file reader 
        
        :param filepath: The full or relative path to a file to be loaded
        """
        if os.path.isfile(filepath):
            basename, extension = os.path.splitext(os.path.basename(filepath))
            # If the file type is not allowed, return nothing
            if extension in self.ext or self.allow_all:
                # Try to load the file, but raise an error if unable to.
                try:
                    self.unit_converter()
                    self.f_open = open(filepath, 'rb')
                    self.get_file_contents()
                    self.sort_one_d_data()
                except RuntimeError:
                    # Reader specific errors
                    # TODO: Give a specific error.
                    pass
                except OSError as e:
                    # If the file cannot be opened
                    msg = "Unable to open file: {}\n".format(filepath)
                    msg += e.message
                    self.handle_error_message(msg)
                except Exception as e:
                    # Handle any other generic error
                    # TODO: raise or log?
                    raise
                finally:
                    if not self.f_open.closed:
                        self.f_open.close()
        else:
            msg = "Unable to find file at: {}\n".format(filepath)
            msg += "Please check your file path and try again."
            self.handle_error_message(msg)
        # Return a list of parsed entries that data_loader can manage
        return self.output

    def handle_error_message(self, msg):
        """
        Generic error handler to add an error to the current datainfo to
        propogate the error up the error chain.
        :param msg: Error message
        """
        if isinstance(self.current_datainfo, DataInfo):
            self.current_datainfo.errors.append(msg)
        else:
            logger.warning(msg)

    def send_to_output(self):
        """
        Helper that automatically combines the info and set and then appends it
        to output
        """
        data_obj = combine_data_info_with_plottable(self.current_dataset,
                                                    self.current_datainfo)
        self.output.append(data_obj)

    def unit_converter(self):
        """
        Generic unit conversion import 
        """
        # Check whether we have a converter available
        self.has_converter = True
        try:
            from sas.sascalc.data_util.nxsunit import Converter
        except:
            self.has_converter = False

    def sort_one_d_data(self):
        """
        Sort 1D data along the X axis for consistency
        """
        final_list = []
        for data in self.output:
            if isinstance(data, Data1D):
                ind = np.lexsort((data.y, data.x))
                data.x = np.asarray([data.x[i] for i in ind])
                data.y = np.asarray([data.y[i] for i in ind])
                if data.dx is not None:
                    data.dx = np.asarray([data.dx[i] for i in ind])
                if data.dxl is not None:
                    data.dxl = np.asarray([data.dxl[i] for i in ind])
                if data.dxw is not None:
                    data.dxw = np.asarray([data.dxw[i] for i in ind])
                if data.dy is not None:
                    data.dy = np.asarray([data.dy[i] for i in ind])
                if data.lam is not None:
                    data.lam = np.asarray([data.lam[i] for i in ind])
                if data.dlam is not None:
                    data.dlam = np.asarray([data.dlam[i] for i in ind])
            final_list.append(data)
        self.output = final_list

    @staticmethod
    def splitline(line):
        """
        Splits a line into pieces based on common delimeters
        :param line: A single line of text
        :return: list of values
        """
        # Initial try for CSV (split on ,)
        toks = line.split(',')
        # Now try SCSV (split on ;)
        if len(toks) < 2:
            toks = line.split(';')
        # Now go for whitespace
        if len(toks) < 2:
            toks = line.split()
        return toks

    @abstractmethod
    def get_file_contents(self):
        """
        All reader classes that inherit from FileReader must implement
        """
        pass
