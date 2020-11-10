"""
This is the base file reader class most file readers should inherit from.
All generic functionality required for a file loader/reader is built into this
class
"""

import os
import sys
import math
import logging
from abc import abstractmethod

import numpy as np
from .loader_exceptions import NoKnownLoaderException, FileContentsException,\
    DataReaderException, DefaultReaderException
from .data_info import Data1D, Data2D, DataInfo, plottable_1D, plottable_2D,\
    combine_data_info_with_plottable
from sas.sascalc.data_util.nxsunit import Converter

logger = logging.getLogger(__name__)

if sys.version_info[0] < 3:
    def decode(s):
        return s
else:
    def decode(s):
        return s.decode() if isinstance(s, bytes) else s

# Data 1D fields for iterative purposes
FIELDS_1D = ('x', 'y', 'dx', 'dy', 'dxl', 'dxw')
# Data 2D fields for iterative purposes
FIELDS_2D = ('data', 'qx_data', 'qy_data', 'q_data', 'err_data',
                 'dqx_data', 'dqy_data', 'mask')
DEPRECATION_MESSAGE = ("\rThe extension of this file suggests the data set migh"
                       "t not be fully reduced. Support for the reader associat"
                       "ed with this file type has been removed. An attempt to "
                       "load the file was made, but, should it be successful, "
                       "SasView cannot guarantee the accuracy of the data.")


class FileReader(object):
    # String to describe the type of data this reader can load
    type_name = "ASCII"
    # Wildcards to display
    type = ["Text files (*.txt|*.TXT)"]
    # List of allowed extensions
    ext = ['.txt']
    # Deprecated extensions
    deprecated_extensions = ['.asc']
    # Bypass extension check and try to load anyway
    allow_all = False
    # Able to import the unit converter
    has_converter = True
    # Default value of zero
    _ZERO = 1e-16

    def __init__(self):
        # List of Data1D and Data2D objects to be sent back to data_loader
        self.output = []
        # Current plottable_(1D/2D) object being loaded in
        self.current_dataset = None
        # Current DataInfo object being loaded in
        self.current_datainfo = None
        # File path sent to reader
        self.filepath = None
        # Open file handle
        self.f_open = None

    def read(self, filepath):
        """
        Basic file reader

        :param filepath: The full or relative path to a file to be loaded
        """
        self.filepath = filepath
        if os.path.isfile(filepath):
            basename, extension = os.path.splitext(os.path.basename(filepath))
            self.extension = extension.lower()
            # If the file type is not allowed, return nothing
            if self.extension in self.ext or self.allow_all:
                # Try to load the file, but raise an error if unable to.
                try:
                    self.f_open = open(filepath, 'rb')
                    self.get_file_contents()
                except DataReaderException as e:
                    self.handle_error_message(e.message)
                except FileContentsException as e:
                    raise
                except OSError as e:
                    # If the file cannot be opened
                    msg = "Unable to open file: {}\n".format(filepath)
                    msg += e.message
                    self.handle_error_message(msg)
                except Exception as e:
                    self.handle_error_message(e.message)
                finally:
                    # Close the file handle if it is open
                    if not self.f_open.closed:
                        self.f_open.close()
                    if any(filepath.lower().endswith(ext) for ext in
                           self.deprecated_extensions):
                        self.handle_error_message(DEPRECATION_MESSAGE)
                    if len(self.output) > 0:
                        # Sort the data that's been loaded
                        self.convert_data_units()
                        self.sort_data()
        else:
            msg = "Unable to find file at: {}\n".format(filepath)
            msg += "Please check your file path and try again."
            self.handle_error_message(msg)

        # Return a list of parsed entries that data_loader can manage
        final_data = self.output
        self.reset_state()
        return final_data

    def reset_state(self):
        """
        Resets the class state to a base case when loading a new data file so previous
        data files do not appear a second time
        """
        self.current_datainfo = None
        self.current_dataset = None
        self.filepath = None
        self.ind = None
        self.output = []

    def nextline(self):
        """
        Returns the next line in the file as a string.
        """
        #return self.f_open.readline()
        return decode(self.f_open.readline())

    def nextlines(self):
        """
        Returns the next line in the file as a string.
        """
        for line in self.f_open:
            #yield line
            yield decode(line)

    def readall(self):
        """
        Returns the entire file as a string.
        """
        return decode(self.f_open.read())

    def handle_error_message(self, msg):
        """
        Generic error handler to add an error to the current datainfo to
        propagate the error up the error chain.
        :param msg: Error message
        """
        if len(self.output) > 0:
            self.output[-1].errors.append(msg)
        elif isinstance(self.current_datainfo, DataInfo):
            self.current_datainfo.errors.append(msg)
        else:
            logger.warning(msg)
            raise NoKnownLoaderException(msg)

    def send_to_output(self):
        """
        Helper that automatically combines the info and set and then appends it
        to output
        """
        data_obj = combine_data_info_with_plottable(self.current_dataset,
                                                    self.current_datainfo)
        self.output.append(data_obj)

    def sort_data(self):
        """
        Sort 1D data along the X axis for consistency
        """
        for data in self.output:
            if isinstance(data, Data1D):
                # Normalize the units for
                data.x_unit = self.format_unit(data.x_unit)
                data._xunit = data.x_unit
                data.y_unit = self.format_unit(data.y_unit)
                data._yunit = data.y_unit
                # Sort data by increasing x and remove 1st point
                ind = np.lexsort((data.y, data.x))
                data.x = self._reorder_1d_array(data.x, ind)
                data.y = self._reorder_1d_array(data.y, ind)
                if data.dx is not None:
                    if len(data.dx) == 0:
                        data.dx = None
                        continue
                    data.dx = self._reorder_1d_array(data.dx, ind)
                if data.dxl is not None:
                    data.dxl = self._reorder_1d_array(data.dxl, ind)
                if data.dxw is not None:
                    data.dxw = self._reorder_1d_array(data.dxw, ind)
                if data.dy is not None:
                    if len(data.dy) == 0:
                        data.dy = None
                        continue
                    data.dy = self._reorder_1d_array(data.dy, ind)
                if data.lam is not None:
                    data.lam = self._reorder_1d_array(data.lam, ind)
                if data.dlam is not None:
                    data.dlam = self._reorder_1d_array(data.dlam, ind)
                data = self._remove_nans_in_data(data)
                if len(data.x) > 0:
                    data.xmin = np.min(data.x)
                    data.xmax = np.max(data.x)
                    data.ymin = np.min(data.y)
                    data.ymax = np.max(data.y)
            elif isinstance(data, Data2D):
                # Normalize the units for
                data.Q_unit = self.format_unit(data.Q_unit)
                data.I_unit = self.format_unit(data.I_unit)
                data._xunit = data.Q_unit
                data._yunit = data.Q_unit
                data._zunit = data.I_unit
                data.data = data.data.astype(np.float64)
                data.qx_data = data.qx_data.astype(np.float64)
                data.xmin = np.min(data.qx_data)
                data.xmax = np.max(data.qx_data)
                data.qy_data = data.qy_data.astype(np.float64)
                data.ymin = np.min(data.qy_data)
                data.ymax = np.max(data.qy_data)
                data.q_data = np.sqrt(data.qx_data * data.qx_data
                                         + data.qy_data * data.qy_data)
                if data.err_data is not None:
                    data.err_data = data.err_data.astype(np.float64)
                if data.dqx_data is not None:
                    data.dqx_data = data.dqx_data.astype(np.float64)
                if data.dqy_data is not None:
                    data.dqy_data = data.dqy_data.astype(np.float64)
                if data.mask is not None:
                    data.mask = data.mask.astype(dtype=bool)
                    # If all mask elements are False, give a warning to the user
                    if not data.mask.any():
                        error = "The entire dataset is masked and may not "
                        error += "produce usable fits."
                        data.errors.append(error)

                if len(data.data.shape) == 2:
                    n_rows, n_cols = data.data.shape
                    data.y_bins = data.qy_data[0::int(n_cols)]
                    data.x_bins = data.qx_data[:int(n_cols)]
                    data.data = data.data.flatten()
                data = self._remove_nans_in_data(data)
                if len(data.data) > 0:
                    data.xmin = np.min(data.qx_data)
                    data.xmax = np.max(data.qx_data)
                    data.ymin = np.min(data.qy_data)
                    data.ymax = np.max(data.qy_data)

    @staticmethod
    def _reorder_1d_array(array, ind):
        """
        Reorders a 1D array based on the indices passed as ind
        :param array: Array to be reordered
        :param ind: Indices used to reorder array
        :return: reordered array
        """
        array = np.asarray(array, dtype=np.float64)
        return array[ind]

    @staticmethod
    def _remove_nans_in_data(data):
        """
        Remove data points where nan is loaded
        :param data: 1D or 2D data object
        :return: data with nan points removed
        """
        if isinstance(data, Data1D):
            fields = FIELDS_1D
        elif isinstance(data, Data2D):
            fields = FIELDS_2D
        else:
            return data
        # Make array of good points - all others will be removed
        good = np.isfinite(getattr(data, fields[0]))
        for name in fields[1:]:
            array = getattr(data, name)
            if array is not None:
                # Update good points only if not already changed
                good &= np.isfinite(array)
        if not np.all(good):
            for name in fields:
                array = getattr(data, name)
                if array is not None:
                    setattr(data, name, array[good])
        return data

    @staticmethod
    def set_default_1d_units(data):
        """
        Set the x and y axes to the default 1D units
        :param data: 1D data set
        :return:
        """
        data.xaxis(r"\rm{Q}", '1/A')
        data.yaxis(r"\rm{Intensity}", "1/cm")
        return data

    @staticmethod
    def set_default_2d_units(data):
        """
        Set the x and y axes to the default 2D units
        :param data: 2D data set
        :return:
        """
        data.xaxis("\\rm{Q_{x}}", '1/A')
        data.yaxis("\\rm{Q_{y}}", '1/A')
        data.zaxis("\\rm{Intensity}", "1/cm")
        return data

    def convert_data_units(self, default_q_unit="1/A"):
        """
        Converts al; data to the sasview default of units of A^{-1} for Q and
        cm^{-1} for I.
        :param default_q_unit: The default Q unit used by Sasview
        """
        convert_q = True
        new_output = []
        for data in self.output:
            if data.isSesans:
                new_output.append(data)
                continue
            try:
                file_x_unit = data._xunit
                data_conv_x = Converter(file_x_unit)
            except KeyError:
                logger.info("Unrecognized Q units in data file. No data "
                            "conversion attempted")
                convert_q = False
            try:

                if isinstance(data, Data1D):
                        if convert_q:
                            data.x = data_conv_x(data.x, units=default_q_unit)
                            data._xunit = default_q_unit
                            data.x_unit = default_q_unit
                            if data.dx is not None:
                                data.dx = data_conv_x(data.dx,
                                                      units=default_q_unit)
                            if data.dxl is not None:
                                data.dxl = data_conv_x(data.dxl,
                                                       units=default_q_unit)
                            if data.dxw is not None:
                                data.dxw = data_conv_x(data.dxw,
                                                       units=default_q_unit)
                elif isinstance(data, Data2D):
                    if convert_q:
                        data.qx_data = data_conv_x(data.qx_data,
                                                   units=default_q_unit)
                        if data.dqx_data is not None:
                            data.dqx_data = data_conv_x(data.dqx_data,
                                                        units=default_q_unit)
                        try:
                            file_y_unit = data._yunit
                            data_conv_y = Converter(file_y_unit)
                            data.qy_data = data_conv_y(data.qy_data,
                                                       units=default_q_unit)
                            if data.dqy_data is not None:
                                data.dqy_data = data_conv_y(data.dqy_data,
                                                            units=default_q_unit)
                        except KeyError:
                            logger.info("Unrecognized Qy units in data file. No"
                                        " data conversion attempted")
            except KeyError:
                message = "Unable to convert Q units from {0} to 1/A."
                message.format(default_q_unit)
                data.errors.append(message)
            new_output.append(data)
        self.output = new_output

    def format_unit(self, unit=None):
        """
        Format units a common way
        :param unit:
        :return:
        """
        if unit:
            split = unit.split("/")
            if len(split) == 1:
                return unit
            elif split[0] == '1':
                return "{0}^".format(split[1]) + "{-1}"
            else:
                return "{0}*{1}^".format(split[0], split[1]) + "{-1}"

    def set_all_to_none(self):
        """
        Set all mutable values to None for error handling purposes
        """
        self.current_dataset = None
        self.current_datainfo = None
        self.output = []

    def data_cleanup(self):
        """
        Clean up the data sets and refresh everything
        :return: None
        """
        self.remove_empty_q_values()
        self.send_to_output()  # Combine datasets with DataInfo
        self.current_datainfo = DataInfo()  # Reset DataInfo

    def remove_empty_q_values(self):
        """
        Remove any point where Q == 0
        """
        if isinstance(self.current_dataset, plottable_1D):
            # Booleans for resolutions
            has_error_dx = self.current_dataset.dx is not None
            has_error_dxl = self.current_dataset.dxl is not None
            has_error_dxw = self.current_dataset.dxw is not None
            has_error_dy = self.current_dataset.dy is not None
            # Create arrays of zeros for non-existent resolutions
            if has_error_dxw and not has_error_dxl:
                array_size = self.current_dataset.dxw.size - 1
                self.current_dataset.dxl = np.append(self.current_dataset.dxl,
                                                    np.zeros([array_size]))
                has_error_dxl = True
            elif has_error_dxl and not has_error_dxw:
                array_size = self.current_dataset.dxl.size - 1
                self.current_dataset.dxw = np.append(self.current_dataset.dxw,
                                                    np.zeros([array_size]))
                has_error_dxw = True
            elif not has_error_dxl and not has_error_dxw and not has_error_dx:
                array_size = self.current_dataset.x.size - 1
                self.current_dataset.dx = np.append(self.current_dataset.dx,
                                                    np.zeros([array_size]))
                has_error_dx = True
            if not has_error_dy:
                array_size = self.current_dataset.y.size - 1
                self.current_dataset.dy = np.append(self.current_dataset.dy,
                                                    np.zeros([array_size]))
                has_error_dy = True

            # Remove points where q = 0
            x = self.current_dataset.x
            self.current_dataset.x = self.current_dataset.x[x != 0]
            self.current_dataset.y = self.current_dataset.y[x != 0]
            if has_error_dy:
                self.current_dataset.dy = self.current_dataset.dy[x != 0]
            if has_error_dx:
                self.current_dataset.dx = self.current_dataset.dx[x != 0]
            if has_error_dxl:
                self.current_dataset.dxl = self.current_dataset.dxl[x != 0]
            if has_error_dxw:
                self.current_dataset.dxw = self.current_dataset.dxw[x != 0]
        elif isinstance(self.current_dataset, plottable_2D):
            has_error_dqx = self.current_dataset.dqx_data is not None
            has_error_dqy = self.current_dataset.dqy_data is not None
            has_error_dy = self.current_dataset.err_data is not None
            has_mask = self.current_dataset.mask is not None
            x = self.current_dataset.qx_data
            self.current_dataset.data = self.current_dataset.data[x != 0]
            self.current_dataset.qx_data = self.current_dataset.qx_data[x != 0]
            self.current_dataset.qy_data = self.current_dataset.qy_data[x != 0]
            self.current_dataset.q_data = np.sqrt(
                np.square(self.current_dataset.qx_data) + np.square(
                    self.current_dataset.qy_data))
            if has_error_dy:
                self.current_dataset.err_data = self.current_dataset.err_data[
                    x != 0]
            if has_error_dqx:
                self.current_dataset.dqx_data = self.current_dataset.dqx_data[
                    x != 0]
            if has_error_dqy:
                self.current_dataset.dqy_data = self.current_dataset.dqy_data[
                    x != 0]
            if has_mask:
                self.current_dataset.mask = self.current_dataset.mask[x != 0]

    def reset_data_list(self, no_lines=0):
        """
        Reset the plottable_1D object
        """
        # Initialize data sets with arrays the maximum possible size
        x = np.zeros(no_lines)
        y = np.zeros(no_lines)
        dx = np.zeros(no_lines)
        dy = np.zeros(no_lines)
        self.current_dataset = plottable_1D(x, y, dx, dy)

    @staticmethod
    def splitline(line):
        """
        Splits a line into pieces based on common delimiters
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
