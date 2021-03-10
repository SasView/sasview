"""
    IGOR 1D data reader
"""
#####################################################################
# This software was developed by the University of Tennessee as part of the
# Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
# project funded by the US National Science Foundation.
# See the license text in license.txt
# copyright 2008, University of Tennessee
######################################################################

import logging

import numpy as np

from sas.sascalc.data_util.nxsunit import Converter
from ..file_reader_base_class import FileReader
from ..data_info import DataInfo, plottable_1D, Data1D, Detector
from ..loader_exceptions import FileContentsException, DefaultReaderException

logger = logging.getLogger(__name__)


class Reader(FileReader):
    """
    Class to load IGOR reduced .ABS files
    """
    # File type
    type_name = "IGOR 1D"
    # Wildcards
    type = ["IGOR 1D files (*.abs)|*.abs", "IGOR 1D USANS files (*.cor)|*.cor"]
    # List of allowed extensions
    ext = ['.abs', '.cor']

    def get_file_contents(self):
        """
        Get the contents of the file

        :raise RuntimeError: when the file can't be opened
        :raise ValueError: when the length of the data vectors are inconsistent
        """
        buff = self.readall()
        filepath = self.f_open.name
        lines = buff.splitlines()
        self.output = []
        self.current_datainfo = DataInfo()
        self.current_datainfo.filename = filepath
        detector = Detector()
        data_line = 0
        x_index = 4
        self.reset_data_list(len(lines))
        self.current_datainfo.detector.append(detector)
        self.current_datainfo.filename = filepath

        is_info = False
        is_center = False
        is_data_started = False

        for line in lines:
            # Information line 1
            if line.find(".bt5") > 0:
                x_index = 0
            if is_info:
                is_info = False
                line_toks = line.split()

                # Wavelength in Angstrom
                try:
                    value = float(line_toks[1])
                    if self.current_datainfo.source.wavelength_unit != 'A':
                        conv = Converter('A')
                        self.current_datainfo.source.wavelength = conv(value,
                            units=self.current_datainfo.source.wavelength_unit)
                    else:
                        self.current_datainfo.source.wavelength = value
                except KeyError:
                    msg = "ABSReader cannot read wavelength from %s" % filepath
                    self.current_datainfo.errors.append(msg)

                # Detector distance in meters
                try:
                    value = float(line_toks[3])
                    if detector.distance_unit != 'm':
                        conv = Converter('m')
                        detector.distance = conv(value,
                                        units=detector.distance_unit)
                    else:
                        detector.distance = value
                except Exception:
                    msg = "ABSReader cannot read SDD from %s" % filepath
                    self.current_datainfo.errors.append(msg)

                # Transmission
                try:
                    self.current_datainfo.sample.transmission = \
                        float(line_toks[4])
                except ValueError:
                    # Transmission isn't always in the header
                    pass

                # Sample thickness in mm
                try:
                    # ABS writer adds 'C' with no space to the end of the
                    # thickness column.  Remove it if it is there before
                    # converting the thickness.
                    if line_toks[5][-1] not in '012345679.':
                        value = float(line_toks[5][:-1])
                    else:
                        value = float(line_toks[5])
                    if self.current_datainfo.sample.thickness_unit != 'cm':
                        conv = Converter('cm')
                        self.current_datainfo.sample.thickness = conv(value,
                            units=self.current_datainfo.sample.thickness_unit)
                    else:
                        self.current_datainfo.sample.thickness = value
                except ValueError:
                    # Thickness is not a mandatory entry
                    pass

            # MON CNT  LAMBDA  DET ANG  DET DIST  TRANS  THICK  AVE   STEP
            if line.count("LAMBDA") > 0:
                is_info = True

            # Find center info line
            if is_center:
                is_center = False
                line_toks = line.split()
                # Center in bin number
                center_x = float(line_toks[0])
                center_y = float(line_toks[1])

                # Bin size
                if detector.pixel_size_unit != 'mm':
                    conv = Converter('mm')
                    detector.pixel_size.x = conv(5.08,
                                        units=detector.pixel_size_unit)
                    detector.pixel_size.y = conv(5.08,
                                        units=detector.pixel_size_unit)
                else:
                    detector.pixel_size.x = 5.08
                    detector.pixel_size.y = 5.08

                # Store beam center in distance units
                # Det 640 x 640 mm
                if detector.beam_center_unit != 'mm':
                    conv = Converter('mm')
                    detector.beam_center.x = conv(center_x * 5.08,
                                     units=detector.beam_center_unit)
                    detector.beam_center.y = conv(center_y * 5.08,
                                     units=detector.beam_center_unit)
                else:
                    detector.beam_center.x = center_x * 5.08
                    detector.beam_center.y = center_y * 5.08

                # Detector type
                try:
                    detector.name = line_toks[7]
                except:
                    # Detector name is not a mandatory entry
                    pass

            # BCENT(X,Y)  A1(mm)  A2(mm)  A1A2DIST(m)  DL/L  BSTOP(mm)  DET_TYP
            if line.count("BCENT") > 0:
                is_center = True

            # Parse the data
            if is_data_started:
                toks = line.split()

                try:
                    _x = float(toks[x_index])
                    _y = float(toks[1])
                    _dy = float(toks[2])
                    _dx = float(toks[3])

                    self.current_dataset.x[data_line] = _x
                    self.current_dataset.y[data_line] = _y
                    self.current_dataset.dy[data_line] = _dy
                    if _dx > 0:
                        self.current_dataset.dx[data_line] = _dx
                    else:
                        if data_line == 0:
                            self.current_dataset.dx = None
                            self.current_dataset.dxl = np.zeros(len(lines))
                            self.current_dataset.dxw = np.zeros(len(lines))
                        self.current_dataset.dxl[data_line] = abs(_dx)
                        self.current_dataset.dxw[data_line] = 0
                    data_line += 1

                except ValueError:
                    # Could not read this data line. If we are here
                    # it is because we are in the data section. Just
                    # skip it.
                    pass

            # SANS Data:
            # The 6 columns are | Q (1/A) | I(Q) (1/cm) | std. dev.
            # I(Q) (1/cm) | sigmaQ | meanQ | ShadowFactor|
            # USANS Data:
            # EMP LEVEL: <value> ; BKG LEVEL: <value>
            if line.startswith("The 6 columns") or line.startswith("EMP LEVEL"):
                is_data_started = True

        self.remove_empty_q_values()

        # Sanity check
        if not len(self.current_dataset.y) == len(self.current_dataset.dy):
            self.set_all_to_none()
            msg = "abs_reader: y and dy have different length"
            raise ValueError(msg)
        # If the data length is zero, consider this as
        # though we were not able to read the file.
        if len(self.current_dataset.x) == 0:
            self.set_all_to_none()
            raise ValueError("ascii_reader: could not load file")

        self.current_dataset = self.set_default_1d_units(self.current_dataset)

        # Store loading process information
        self.current_datainfo.meta_data['loader'] = self.type_name
        self.send_to_output()
