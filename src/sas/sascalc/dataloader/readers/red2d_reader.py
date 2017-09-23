"""
    TXT/IGOR 2D Q Map file reader
"""
#####################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#See the license text in license.txt
#copyright 2008, University of Tennessee
######################################################################
import os
import math
import time

import numpy as np

from sas.sascalc.data_util.nxsunit import Converter

from ..data_info import plottable_2D, DataInfo, Detector
from ..file_reader_base_class import FileReader
from ..loader_exceptions import FileContentsException


def check_point(x_point):
    """
    check point validity
    """
    # set zero for non_floats
    try:
        return float(x_point)
    except Exception:
        return 0


class Reader(FileReader):
    """ Simple data reader for Igor data files """
    ## File type
    type_name = "IGOR/DAT 2D Q_map"
    ## Wildcards
    type = ["IGOR/DAT 2D file in Q_map (*.dat)|*.DAT"]
    ## Extension
    ext = ['.DAT', '.dat']

    def write(self, filename, data):
        """
        Write to .dat

        :param filename: file name to write
        :param data: data2D
        """
        # Write the file
        try:
            fd = open(filename, 'w')
            t = time.localtime()
            time_str = time.strftime("%H:%M on %b %d %y", t)

            header_str = "Data columns are Qx - Qy - I(Qx,Qy)\n\nASCII data"
            header_str += " created at %s \n\n" % time_str
            # simple 2D header
            fd.write(header_str)
            # write qx qy I values
            for i in range(len(data.data)):
                fd.write("%g  %g  %g\n" % (data.qx_data[i],
                                            data.qy_data[i],
                                           data.data[i]))
        finally:
            fd.close()

    def get_file_contents(self):
        # Read file
        buf = self.readall()
        self.f_open.close()
        # Instantiate data object
        self.current_dataset = plottable_2D()
        self.current_datainfo = DataInfo()
        self.current_datainfo.filename = os.path.basename(self.f_open.name)
        self.current_datainfo.detector.append(Detector())

        # Get content
        data_started = False

        ## Defaults
        lines = buf.split('\n')
        x = []
        y = []

        wavelength = None
        distance = None
        transmission = None

        pixel_x = None
        pixel_y = None

        is_info = False
        is_center = False

        # Remove the last lines before the for loop if the lines are empty
        # to calculate the exact number of data points
        count = 0
        while (len(lines[len(lines) - (count + 1)].lstrip().rstrip()) < 1):
            del lines[len(lines) - (count + 1)]
            count = count + 1

        #Read Header and find the dimensions of 2D data
        line_num = 0
        # Old version NIST files: 0
        ver = 0
        for line in lines:
            line_num += 1
            ## Reading the header applies only to IGOR/NIST 2D q_map data files
            # Find setup info line
            if is_info:
                is_info = False
                line_toks = line.split()
                # Wavelength in Angstrom
                try:
                    wavelength = float(line_toks[1])
                    # Wavelength is stored in angstroms; convert if necessary
                    if self.current_datainfo.source.wavelength_unit != 'A':
                        conv = Converter('A')
                        wavelength = conv(wavelength,
                                          units=self.current_datainfo.source.wavelength_unit)
                except Exception:
                    pass  # Not required
                try:
                    distance = float(line_toks[3])
                    # Distance is stored in meters; convert if necessary
                    if self.current_datainfo.detector[0].distance_unit != 'm':
                        conv = Converter('m')
                        distance = conv(distance,
                            units=self.current_datainfo.detector[0].distance_unit)
                except Exception:
                    pass  # Not required

                try:
                    transmission = float(line_toks[4])
                except Exception:
                    pass  # Not required

            if line.count("LAMBDA") > 0:
                is_info = True

            # Find center info line
            if is_center:
                is_center = False
                line_toks = line.split()
                # Center in bin number
                center_x = float(line_toks[0])
                center_y = float(line_toks[1])

            if line.count("BCENT") > 0:
                is_center = True
            # Check version
            if line.count("Data columns") > 0:
                if line.count("err(I)") > 0:
                    ver = 1
            # Find data start
            if line.count("ASCII data") > 0:
                data_started = True
                continue

            ## Read and get data.
            if data_started:
                line_toks = line.split()
                if len(line_toks) == 0:
                    #empty line
                    continue
                # the number of columns must be stayed same
                col_num = len(line_toks)
                break

        # Make numpy array to remove header lines using index
        lines_array = np.array(lines)

        # index for lines_array
        lines_index = np.arange(len(lines))

        # get the data lines
        data_lines = lines_array[lines_index >= (line_num - 1)]
        # Now we get the total number of rows (i.e., # of data points)
        row_num = len(data_lines)
        # make it as list again to control the separators
        data_list = " ".join(data_lines.tolist())
        # split all data to one big list w/" "separator
        data_list = data_list.split()

        # Check if the size is consistent with data, otherwise
        #try the tab(\t) separator
        # (this may be removed once get the confidence
        #the former working all cases).
        if len(data_list) != (len(data_lines)) * col_num:
            data_list = "\t".join(data_lines.tolist())
            data_list = data_list.split()

        # Change it(string) into float
        #data_list = map(float,data_list)
        data_list1 = list(map(check_point, data_list))

        # numpy array form
        data_array = np.array(data_list1)
        # Redimesion based on the row_num and col_num,
        #otherwise raise an error.
        try:
            data_point = data_array.reshape(row_num, col_num).transpose()
        except Exception:
            msg = "red2d_reader can't read this file: Incorrect number of data points provided."
            raise FileContentsException(msg)
        ## Get the all data: Let's HARDcoding; Todo find better way
        # Defaults
        dqx_data = np.zeros(0)
        dqy_data = np.zeros(0)
        err_data = np.ones(row_num)
        qz_data = np.zeros(row_num)
        mask = np.ones(row_num, dtype=bool)
        # Get from the array
        qx_data = data_point[0]
        qy_data = data_point[1]
        data = data_point[2]
        if ver == 1:
            if col_num > (2 + ver):
                err_data = data_point[(2 + ver)]
        if col_num > (3 + ver):
            qz_data = data_point[(3 + ver)]
        if col_num > (4 + ver):
            dqx_data = data_point[(4 + ver)]
        if col_num > (5 + ver):
            dqy_data = data_point[(5 + ver)]
        #if col_num > (6 + ver): mask[data_point[(6 + ver)] < 1] = False
        q_data = np.sqrt(qx_data*qx_data+qy_data*qy_data+qz_data*qz_data)

        # Extra protection(it is needed for some data files):
        # If all mask elements are False, put all True
        if not mask.any():
            mask[mask == False] = True

        # Store limits of the image in q space
        xmin = np.min(qx_data)
        xmax = np.max(qx_data)
        ymin = np.min(qy_data)
        ymax = np.max(qy_data)

        ## calculate the range of the qx and qy_data
        x_size = math.fabs(xmax - xmin)
        y_size = math.fabs(ymax - ymin)

        # calculate the number of pixels in the each axes
        npix_y = math.floor(math.sqrt(len(data)))
        npix_x = math.floor(len(data) / npix_y)

        # calculate the size of bins
        xstep = x_size / (npix_x - 1)
        ystep = y_size / (npix_y - 1)

        # store x and y axis bin centers in q space
        x_bins = np.arange(xmin, xmax + xstep, xstep)
        y_bins = np.arange(ymin, ymax + ystep, ystep)

        # get the limits of q values
        xmin = xmin - xstep / 2
        xmax = xmax + xstep / 2
        ymin = ymin - ystep / 2
        ymax = ymax + ystep / 2

        #Store data in outputs
        #TODO: Check the lengths
        self.current_dataset.data = data
        if (err_data == 1).all():
            self.current_dataset.err_data = np.sqrt(np.abs(data))
            self.current_dataset.err_data[self.current_dataset.err_data == 0.0] = 1.0
        else:
            self.current_dataset.err_data = err_data

        self.current_dataset.qx_data = qx_data
        self.current_dataset.qy_data = qy_data
        self.current_dataset.q_data = q_data
        self.current_dataset.mask = mask

        self.current_dataset.x_bins = x_bins
        self.current_dataset.y_bins = y_bins

        self.current_dataset.xmin = xmin
        self.current_dataset.xmax = xmax
        self.current_dataset.ymin = ymin
        self.current_dataset.ymax = ymax

        self.current_datainfo.source.wavelength = wavelength

        # Store pixel size in mm
        self.current_datainfo.detector[0].pixel_size.x = pixel_x
        self.current_datainfo.detector[0].pixel_size.y = pixel_y

        # Store the sample to detector distance
        self.current_datainfo.detector[0].distance = distance

        # optional data: if all of dq data == 0, do not pass to output
        if len(dqx_data) == len(qx_data) and dqx_data.any() != 0:
            # if no dqx_data, do not pass dqy_data.
            #(1 axis dq is not supported yet).
            if len(dqy_data) == len(qy_data) and dqy_data.any() != 0:
                # Currently we do not support dq parr, perp.
                # tranfer the comp. to cartesian coord. for newer version.
                if ver != 1:
                    diag = np.sqrt(qx_data * qx_data + qy_data * qy_data)
                    cos_th = qx_data / diag
                    sin_th = qy_data / diag
                    self.current_dataset.dqx_data = np.sqrt((dqx_data * cos_th) * \
                                                 (dqx_data * cos_th) \
                                                 + (dqy_data * sin_th) * \
                                                  (dqy_data * sin_th))
                    self.current_dataset.dqy_data = np.sqrt((dqx_data * sin_th) * \
                                                 (dqx_data * sin_th) \
                                                 + (dqy_data * cos_th) * \
                                                  (dqy_data * cos_th))
                else:
                    self.current_dataset.dqx_data = dqx_data
                    self.current_dataset.dqy_data = dqy_data

        # Units of axes
        self.current_dataset.xaxis(r"\rm{Q_{x}}", 'A^{-1}')
        self.current_dataset.yaxis(r"\rm{Q_{y}}", 'A^{-1}')
        self.current_dataset.zaxis(r"\rm{Intensity}", "cm^{-1}")

        # Store loading process information
        self.current_datainfo.meta_data['loader'] = self.type_name

        self.send_to_output()
