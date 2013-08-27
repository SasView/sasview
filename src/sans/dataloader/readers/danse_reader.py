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
import sys
import numpy
import logging
from sans.dataloader.data_info import Data2D, Detector
from sans.dataloader.manipulations import reader2D_converter

# Look for unit converter
has_converter = True
try:
    from data_util.nxsunit import Converter
except:
    has_converter = False


class Reader:
    """
    Example data manipulation
    """
    ## File type
    type_name = "DANSE"
    ## Wildcards
    type = ["DANSE files (*.sans)|*.sans"]
    ## Extension
    ext  = ['.sans', '.SANS']
        
    def read(self, filename=None):
        """
        Open and read the data in a file
        @param file: path of the file
        """
        
        read_it = False
        for item in self.ext:
            if filename.lower().find(item) >= 0:
                read_it = True
                
        if read_it:
            try:
                datafile = open(filename, 'r')
            except:
                raise  RuntimeError,"danse_reader cannot open %s" % (filename)
        
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
            
            output = Data2D()
            output.filename = os.path.basename(filename)
            detector = Detector()
            output.detector.append(detector)
            
            output.data = numpy.zeros([size_x,size_y])
            output.err_data = numpy.zeros([size_x, size_y])
            
            data_conv_q = None
            data_conv_i = None
            
            if has_converter == True and output.Q_unit != '1/A':
                data_conv_q = Converter('1/A')
                # Test it
                data_conv_q(1.0, output.Q_unit)
                
            if has_converter == True and output.I_unit != '1/cm':
                data_conv_i = Converter('1/cm')
                # Test it
                data_conv_i(1.0, output.I_unit)
        
            read_on = True
            while read_on:
                line = datafile.readline()
                if line.find("DATA:") >= 0:
                    read_on = False
                    break
                toks = line.split(':')
                if toks[0] == "FORMATVERSION":
                    fversion = float(toks[1])
                if toks[0] == "WAVELENGTH":
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
            
            # Read the data
            data = []
            error = []
            if fversion == 1.0:
                data_str = datafile.readline()
                data = data_str.split(' ')
            else:
                read_on = True
                while read_on:
                    data_str = datafile.readline()
                    if len(data_str) == 0:
                        read_on = False
                    else:
                        toks = data_str.split()
                        try:
                            val = float(toks[0])
                            err = float(toks[1])
                            if data_conv_i is not None:
                                val = data_conv_i(val, units=output._yunit)
                                err = data_conv_i(err, units=output._yunit)
                            data.append(val)
                            error.append(err)
                        except:
                            logging.info("Skipping line:%s,%s" %(data_str,
                                                                sys.exc_value))
            
            # Initialize
            x_vals = []
            y_vals = []
            ymin = None
            ymax = None
            xmin = None
            xmax = None
            
            # Qx and Qy vectors
            theta = pixel / distance / 100.0
            stepq = 4.0 * math.pi / wavelength * math.sin(theta / 2.0)
            for i_x in range(size_x):
                theta = (i_x - center_x + 1) * pixel / distance / 100.0
                qx = 4.0 * math.pi / wavelength * math.sin(theta / 2.0)
                
                if has_converter == True and output.Q_unit != '1/A':
                    qx = data_conv_q(qx, units=output.Q_unit)
                
                x_vals.append(qx)
                if xmin == None or qx < xmin:
                    xmin = qx
                if xmax == None or qx > xmax:
                    xmax = qx
            
            ymin = None
            ymax = None
            for i_y in range(size_y):
                theta = (i_y - center_y + 1) * pixel / distance / 100.0
                qy = 4.0 * math.pi / wavelength * math.sin(theta/2.0)
                
                if has_converter == True and output.Q_unit != '1/A':
                    qy = data_conv_q(qy, units=output.Q_unit)
                
                y_vals.append(qy)
                if ymin == None or qy < ymin:
                    ymin = qy
                if ymax == None or qy > ymax:
                    ymax = qy
            
            # Store the data in the 2D array
            i_x = 0
            i_y = -1
            
            for i_pt in range(len(data)):
                try:
                    value = float(data[i_pt])
                except:
                    # For version 1.0, the data were still
                    # stored as strings at this point.
                    msg = "Skipping entry (v1.0):%s,%s" % (str(data[i_pt]),
                                                           sys.exc_value)
                    logging.info(msg)
                
                # Get bin number
                if math.fmod(i_pt, size_x) == 0:
                    i_x = 0
                    i_y += 1
                else:
                    i_x += 1
                    
                output.data[i_y][i_x] = value
                if fversion>1.0:
                    output.err_data[i_y][i_x] = error[i_pt]
                
            # Store all data
            # Store wavelength
            if has_converter == True and output.source.wavelength_unit != 'A':
                conv = Converter('A')
                wavelength = conv(wavelength,
                                  units=output.source.wavelength_unit)
            output.source.wavelength = wavelength
                
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
            
            # Store limits of the image (2D array)
            xmin = xmin - stepq / 2.0
            xmax = xmax + stepq / 2.0
            ymin = ymin - stepq /2.0
            ymax = ymax + stepq / 2.0
            
            if has_converter == True and output.Q_unit != '1/A':
                xmin = data_conv_q(xmin, units=output.Q_unit)
                xmax = data_conv_q(xmax, units=output.Q_unit)
                ymin = data_conv_q(ymin, units=output.Q_unit)
                ymax = data_conv_q(ymax, units=output.Q_unit)
            output.xmin = xmin
            output.xmax = xmax
            output.ymin = ymin
            output.ymax = ymax
            
            # Store x and y axis bin centers
            output.x_bins = x_vals
            output.y_bins = y_vals
           
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
           
            if not fversion >= 1.0:
                msg = "Danse_reader can't read this file %s" % filename
                raise ValueError, msg
            else:
                logging.info("Danse_reader Reading %s \n" % filename)
            
            # Store loading process information
            output.meta_data['loader'] = self.type_name
            output = reader2D_converter(output)
            return output
        
        return None
