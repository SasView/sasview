"""
    IGOR 2D reduced file reader
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
import os

from sas.sascalc.dataloader.data_info import Data2D
from sas.sascalc.dataloader.data_info import Detector
from sas.sascalc.dataloader.manipulations import reader2D_converter
import numpy as np

# Look for unit converter
has_converter = True
try:
    from sas.sascalc.data_util.nxsunit import Converter
except:
    has_converter = False


class Reader:
    """ Simple data reader for Igor data files """
    ## File type
    type_name = "IGOR 2D"
    ## Wildcards
    type = ["IGOR 2D files (*.ASC)|*.ASC"]
    ## Extension
    ext=['.ASC', '.asc']

    def read(self, filename=None):
        """ Read file """
        if not os.path.isfile(filename):
            raise ValueError("Specified file %s is not a regular "
                             "file" % filename)
        
        output = Data2D()

        output.filename = os.path.basename(filename)
        detector = Detector()
        if len(output.detector):
            print(str(output.detector[0]))
        output.detector.append(detector)

        data_conv_q = data_conv_i = None
        
        if has_converter and output.Q_unit != '1/A':
            data_conv_q = Converter('1/A')
            # Test it
            data_conv_q(1.0, output.Q_unit)
            
        if has_converter and output.I_unit != '1/cm':
            data_conv_i = Converter('1/cm')
            # Test it
            data_conv_i(1.0, output.I_unit)

        data_row = 0
        wavelength = distance = center_x = center_y = None
        dataStarted = isInfo = isCenter = False

        with open(filename, 'r') as f:
            for line in f:
                data_row += 1
                # Find setup info line
                if isInfo:
                    isInfo = False
                    line_toks = line.split()
                    # Wavelength in Angstrom
                    try:
                        wavelength = float(line_toks[1])
                    except ValueError:
                        msg = "IgorReader: can't read this file, missing wavelength"
                        raise ValueError(msg)
                    # Distance in meters
                    try:
                        distance = float(line_toks[3])
                    except ValueError:
                        msg = "IgorReader: can't read this file, missing distance"
                        raise ValueError(msg)

                    # Distance in meters
                    try:
                        transmission = float(line_toks[4])
                    except:
                        msg = "IgorReader: can't read this file, "
                        msg += "missing transmission"
                        raise ValueError(msg)

                if line.count("LAMBDA"):
                    isInfo = True

                # Find center info line
                if isCenter:
                    isCenter = False
                    line_toks = line.split()

                    # Center in bin number: Must subtract 1 because
                    # the index starts from 1
                    center_x = float(line_toks[0]) - 1
                    center_y = float(line_toks[1]) - 1

                if line.count("BCENT"):
                    isCenter = True

                # Find data start
                if line.count("***"):
                    # now have to continue to blank line
                    dataStarted = True

                    # Check that we have all the info
                    if (wavelength is None
                            or distance is None
                            or center_x is None
                            or center_y is None):
                        msg = "IgorReader:Missing information in data file"
                        raise ValueError(msg)

                if dataStarted:
                    if len(line.rstrip()):
                        continue
                    else:
                        break

        # The data is loaded in row major order (last index changing most
        # rapidly). However, the original data is in column major order (first
        # index changing most rapidly). The swap to column major order is done
        # in reader2D_converter at the end of this method.
        data = np.loadtxt(filename, skiprows=data_row)
        size_x = size_y = int(np.rint(np.sqrt(data.size)))
        output.data = np.reshape(data, (size_x, size_y))
        output.err_data = np.zeros_like(output.data)

        # Det 640 x 640 mm
        # Q = 4 * pi/lambda * sin(theta/2)
        # Bin size is 0.5 cm
        # Removed +1 from theta = (i_x - center_x + 1)*0.5 / distance
        # / 100.0 and
        # Removed +1 from theta = (i_y - center_y + 1)*0.5 /
        # distance / 100.0
        # ToDo: Need  complete check if the following
        # convert process is consistent with fitting.py.

        # calculate qx, qy bin centers of each pixel in the image
        theta = (np.arange(size_x) - center_x) * 0.5 / distance / 100.
        qx = 4 * np.pi / wavelength * np.sin(theta/2)

        theta = (np.arange(size_y) - center_y) * 0.5 / distance / 100.
        qy = 4 * np.pi / wavelength * np.sin(theta/2)

        if has_converter and output.Q_unit != '1/A':
            qx = data_conv_q(qx, units=output.Q_unit)
            qy = data_conv_q(qx, units=output.Q_unit)

        xmax = np.max(qx)
        xmin = np.min(qx)
        ymax = np.max(qy)
        ymin = np.min(qy)

        # calculate edge offset in q.
        theta = 0.25 / distance / 100.0
        xstep = 4.0 * np.pi / wavelength * np.sin(theta / 2.0)
        
        theta = 0.25 / distance / 100.0
        ystep = 4.0 * np.pi/ wavelength * np.sin(theta / 2.0)
        
        # Store all data ######################################
        # Store wavelength
        if has_converter and output.source.wavelength_unit != 'A':
            conv = Converter('A')
            wavelength = conv(wavelength, units=output.source.wavelength_unit)
        output.source.wavelength = wavelength

        # Store distance
        if has_converter and detector.distance_unit != 'm':
            conv = Converter('m')
            distance = conv(distance, units=detector.distance_unit)
        detector.distance = distance
  
        # Store transmission
        output.sample.transmission = transmission
        
        # Store pixel size (mm)
        pixel = 5.0
        if has_converter and detector.pixel_size_unit != 'mm':
            conv = Converter('mm')
            pixel = conv(pixel, units=detector.pixel_size_unit)
        detector.pixel_size.x = pixel
        detector.pixel_size.y = pixel
  
        # Store beam center in distance units
        detector.beam_center.x = center_x * pixel
        detector.beam_center.y = center_y * pixel
        
        # Store limits of the image (2D array)
        xmin -= xstep / 2.0
        xmax += xstep / 2.0
        ymin -= ystep / 2.0
        ymax += ystep / 2.0
        if has_converter and output.Q_unit != '1/A':
            xmin = data_conv_q(xmin, units=output.Q_unit)
            xmax = data_conv_q(xmax, units=output.Q_unit)
            ymin = data_conv_q(ymin, units=output.Q_unit)
            ymax = data_conv_q(ymax, units=output.Q_unit)
        output.xmin = xmin
        output.xmax = xmax
        output.ymin = ymin
        output.ymax = ymax
        
        # Store x and y axis bin centers
        output.x_bins = qx.tolist()
        output.y_bins = qy.tolist()
        
        # Units
        if data_conv_q is not None:
            output.xaxis("\\rm{Q_{x}}", output.Q_unit)
            output.yaxis("\\rm{Q_{y}}", output.Q_unit)
        else:
            output.xaxis("\\rm{Q_{x}}", 'A^{-1}')
            output.yaxis("\\rm{Q_{y}}", 'A^{-1}')
            
        if data_conv_i is not None:
            output.zaxis("\\rm{Intensity}", output.I_unit)
        else:
            output.zaxis("\\rm{Intensity}", "cm^{-1}")
    
        # Store loading process information
        output.meta_data['loader'] = self.type_name
        output = reader2D_converter(output)

        return output
