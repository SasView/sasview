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
    DataReaderException, DefaultReaderException
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
            self.extension = extension.lower()
            # If the file type is not allowed, return nothing
            if self.extension in self.ext or self.allow_all:
                # Try to load the file, but raise an error if unable to.
                try:
                    self.f_open = open(filepath, 'rb')
                    self.get_file_contents()

                    if isinstance(self.output[0], Data1D):
                        self.sort_one_d_data()
                    elif isinstance(self.output[0], Data2D):
                        self.sort_two_d_data()

                except DataReaderException as e:
                    self.handle_error_message(e.message)
                except OSError as e:
                    # If the file cannot be opened
                    msg = "Unable to open file: {}\n".format(filepath)
                    msg += e.message
                    self.handle_error_message(msg)
                finally:
                    # Close the file handle if it is open
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

    def sort_one_d_data(self):
        """
        Sort 1D data along the X axis for consistency
        """
        final_list = []
        for data in self.output:
            if isinstance(data, Data1D):
                # Sort data by increasing x and remove 1st point
                ind = np.lexsort((data.y, data.x))
                data.x = np.asarray([data.x[i] for i in ind]).astype(np.float64)
                data.y = np.asarray([data.y[i] for i in ind]).astype(np.float64)
                if data.dx is not None:
                    data.dx = np.asarray([data.dx[i] for i in ind]).astype(np.float64)
                if data.dxl is not None:
                    data.dxl = np.asarray([data.dxl[i] for i in ind]).astype(np.float64)
                if data.dxw is not None:
                    data.dxw = np.asarray([data.dxw[i] for i in ind]).astype(np.float64)
                if data.dy is not None:
                    data.dy = np.asarray([data.dy[i] for i in ind]).astype(np.float64)
                if data.lam is not None:
                    data.lam = np.asarray([data.lam[i] for i in ind]).astype(np.float64)
                if data.dlam is not None:
                    data.dlam = np.asarray([data.dlam[i] for i in ind]).astype(np.float64)
                data.xmin = np.min(data.x)
                data.xmax = np.max(data.x)
                data.ymin = np.min(data.y)
                data.ymax = np.max(data.y)
            final_list.append(data)
        self.output = final_list
        self.remove_empty_q_values()

    def sort_two_d_data(self):
        final_list = []
        for dataset in self.output:
            if isinstance(dataset, Data2D):
                dataset.data = dataset.data.astype(np.float64)
                dataset.qx_data = dataset.qx_data.astype(np.float64)
                dataset.xmin = np.min(dataset.qx_data)
                dataset.xmax = np.max(dataset.qx_data)
                dataset.qy_data = dataset.qy_data.astype(np.float64)
                dataset.ymin = np.min(dataset.qy_data)
                dataset.ymax = np.max(dataset.qy_data)
                dataset.q_data = np.sqrt(dataset.qx_data * dataset.qx_data
                                         + dataset.qy_data * dataset.qy_data)
                if dataset.err_data is not None:
                    dataset.err_data = dataset.err_data.astype(np.float64)
                if dataset.dqx_data is not None:
                    dataset.dqx_data = dataset.dqx_data.astype(np.float64)
                if dataset.dqy_data is not None:
                    dataset.dqy_data = dataset.dqy_data.astype(np.float64)
                if dataset.mask is not None:
                    dataset.mask = dataset.mask.astype(dtype=bool)

                if len(dataset.data.shape) == 2:
                    n_rows, n_cols = dataset.data.shape
                    dataset.y_bins = dataset.qy_data[0::int(n_cols)]
                    dataset.x_bins = dataset.qx_data[:int(n_cols)]
                    dataset.data = dataset.data.flatten()
                else:
                    dataset.y_bins = []
                    dataset.x_bins = []
                    dataset.data = dataset.data.flatten()
                final_list.append(dataset)
        self.output = final_list

    def set_all_to_none(self):
        """
        Set all mutable values to None for error handling purposes
        """
        self.current_dataset = None
        self.current_datainfo = None
        self.output = []

    def remove_empty_q_values(self, has_error_dx=False, has_error_dy=False):
        """
        Remove any point where Q == 0
        """
        x = self.current_dataset.x
        self.current_dataset.x = self.current_dataset.x[x != 0]
        self.current_dataset.y = self.current_dataset.y[x != 0]
        self.current_dataset.dy = self.current_dataset.dy[x != 0] if \
            has_error_dy else np.zeros(len(self.current_dataset.y))
        self.current_dataset.dx = self.current_dataset.dx[x != 0] if \
            has_error_dx else np.zeros(len(self.current_dataset.x))

    def reset_data_list(self, no_lines=0):
        """
        Reset the plottable_1D object
        """
        # Initialize data sets with arrays the maximum possible size
        x = np.zeros(no_lines)
        y = np.zeros(no_lines)
        dy = np.zeros(no_lines)
        dx = np.zeros(no_lines)
        self.current_dataset = plottable_1D(x, y, dx, dy)

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
        Reader specific class to access the contents of the file
        All reader classes that inherit from FileReader must implement
        """
        pass
