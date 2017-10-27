"""
    DANSE/SANS file reader
"""
############################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#If you use DANSE applications to do scientific research that leads to
#publication, we ask that you acknowledge the use of the software with the
#following sentence:
#This work benefited from DANSE software developed under NSF award DMR-0520547.
#copyright 2008, University of Tennessee
#############################################################################
import math
import os
import logging

import numpy as np

from ..data_info import plottable_2D, DataInfo, Detector
from ..manipulations import reader2D_converter
from ..file_reader_base_class import FileReader
from ..loader_exceptions import FileContentsException, DataReaderException

logger = logging.getLogger(__name__)

# Look for unit converter
has_converter = True
try:
    from sas.sascalc.data_util.nxsunit import Converter
except:
    has_converter = False


class Reader(FileReader):
    """
    Example data manipulation
    """
    ## File type
    type_name = "DANSE"
    ## Wildcards
    type = ["DANSE files (*.sans)|*.sans"]
    ## Extension
    ext  = ['.sans', '.SANS']

    def get_file_contents(self):
        self.current_datainfo = DataInfo()
        self.current_dataset = plottable_2D()
        self.output = []

        loaded_correctly = True
        error_message = ""

        # defaults
        # wavelength in Angstrom
        wavelength = 10.0
        # Distance in meter
        distance   = 11.0
        # Pixel number of center in x
        center_x   = 65
        # Pixel number of center in y
        center_y   = 65
        # Pixel size [mm]
        pixel      = 5.0
        # Size in x, in pixels
        size_x     = 128
        # Size in y, in pixels
        size_y     = 128
        # Format version
        fversion   = 1.0

        self.current_datainfo.filename = os.path.basename(self.f_open.name)
        detector = Detector()
        self.current_datainfo.detector.append(detector)

        self.current_dataset.data = np.zeros([size_x, size_y])
        self.current_dataset.err_data = np.zeros([size_x, size_y])

        read_on = True
        data_start_line = 1
        while read_on:
            line = self.nextline()
            data_start_line += 1
            if line.find("DATA:") >= 0:
                read_on = False
                break
            toks = line.split(':')
            try:
                if toks[0] == "FORMATVERSION":
                    fversion = float(toks[1])
                elif toks[0] == "WAVELENGTH":
                    wavelength = float(toks[1])
                elif toks[0] == "DISTANCE":
                    distance = float(toks[1])
                elif toks[0] == "CENTER_X":
                    center_x = float(toks[1])
                elif toks[0] == "CENTER_Y":
                    center_y = float(toks[1])
                elif toks[0] == "PIXELSIZE":
                    pixel = float(toks[1])
                elif toks[0] == "SIZE_X":
                    size_x = int(toks[1])
                elif toks[0] == "SIZE_Y":
                    size_y = int(toks[1])
            except ValueError as e:
                error_message += "Unable to parse {}. Default value used.\n".format(toks[0])
                loaded_correctly = False

        # Read the data
        data = []
        error = []
        if not fversion >= 1.0:
            msg = "danse_reader can't read this file {}".format(self.f_open.name)
            raise FileContentsException(msg)

        for line_num, data_str in enumerate(self.nextlines()):
            toks = data_str.split()
            try:
                val = float(toks[0])
                err = float(toks[1])
                data.append(val)
                error.append(err)
            except ValueError as exc:
                msg = "Unable to parse line {}: {}".format(line_num + data_start_line, data_str.strip())
                raise FileContentsException(msg)

        num_pts = size_x * size_y
        if len(data) < num_pts:
            msg = "Not enough data points provided. Expected {} but got {}".format(
                size_x * size_y, len(data))
            raise FileContentsException(msg)
        elif len(data) > num_pts:
            error_message += ("Too many data points provided. Expected {0} but"
                " got {1}. Only the first {0} will be used.\n").format(num_pts, len(data))
            loaded_correctly = False
            data = data[:num_pts]
            error = error[:num_pts]

        # Qx and Qy vectors
        theta = pixel / distance / 100.0
        i_x = np.arange(size_x)
        theta = (i_x - center_x + 1) * pixel / distance / 100.0
        x_vals = 4.0 * np.pi / wavelength * np.sin(theta / 2.0)
        xmin = x_vals.min()
        xmax = x_vals.max()

        i_y = np.arange(size_y)
        theta = (i_y - center_y + 1) * pixel / distance / 100.0
        y_vals = 4.0 * np.pi / wavelength * np.sin(theta / 2.0)
        ymin = y_vals.min()
        ymax = y_vals.max()

        self.current_dataset.data = np.array(data, dtype=np.float64).reshape((size_y, size_x))
        if fversion > 1.0:
            self.current_dataset.err_data = np.array(error, dtype=np.float64).reshape((size_y, size_x))

        # Store all data
        # Store wavelength
        if has_converter == True and self.current_datainfo.source.wavelength_unit != 'A':
            conv = Converter('A')
            wavelength = conv(wavelength,
                              units=self.current_datainfo.source.wavelength_unit)
        self.current_datainfo.source.wavelength = wavelength

        # Store distance
        if has_converter == True and detector.distance_unit != 'm':
            conv = Converter('m')
            distance = conv(distance, units=detector.distance_unit)
        detector.distance = distance

        # Store pixel size
        if has_converter == True and detector.pixel_size_unit != 'mm':
            conv = Converter('mm')
            pixel = conv(pixel, units=detector.pixel_size_unit)
        detector.pixel_size.x = pixel
        detector.pixel_size.y = pixel

        # Store beam center in distance units
        detector.beam_center.x = center_x * pixel
        detector.beam_center.y = center_y * pixel


        self.current_dataset.xaxis("\\rm{Q_{x}}", 'A^{-1}')
        self.current_dataset.yaxis("\\rm{Q_{y}}", 'A^{-1}')
        self.current_dataset.zaxis("\\rm{Intensity}", "cm^{-1}")

        self.current_dataset.x_bins = x_vals
        self.current_dataset.y_bins = y_vals

        # Reshape data
        x_vals = np.tile(x_vals, (size_y, 1)).flatten()
        y_vals = np.tile(y_vals, (size_x, 1)).T.flatten()
        if (np.all(self.current_dataset.err_data is None)
                or np.any(self.current_dataset.err_data <= 0)):
            new_err_data = np.sqrt(np.abs(self.current_dataset.data))
        else:
            new_err_data = self.current_dataset.err_data.flatten()

        self.current_dataset.err_data = new_err_data
        self.current_dataset.qx_data = x_vals
        self.current_dataset.qy_data = y_vals
        self.current_dataset.q_data = np.sqrt(x_vals**2 + y_vals**2)
        self.current_dataset.mask = np.ones(len(x_vals), dtype=bool)

        # Store loading process information
        self.current_datainfo.meta_data['loader'] = self.type_name

        self.send_to_output()

        if not loaded_correctly:
            raise DataReaderException(error_message)
