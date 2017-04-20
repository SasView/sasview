"""
"""
#####################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#See the license text in license.txt
#copyright 2008, University of Tennessee
######################################################################

import numpy as np
import os
from sas.sascalc.dataloader.data_info import Data1D
from sas.sascalc.dataloader.data_info import Detector

has_converter = True
try:
    from sas.sascalc.data_util.nxsunit import Converter
except:
    has_converter = False
    
    
class Reader:
    """
    Class to load IGOR reduced .ABS files
    """
    ## File type
    type_name = "IGOR 1D"
    ## Wildcards
    type = ["IGOR 1D files (*.abs)|*.abs"]
    ## List of allowed extensions
    ext = ['.abs', '.ABS']
    
    def read(self, path):
        """ 
        Load data file.
        
        :param path: file path
        
        :return: Data1D object, or None
        
        :raise RuntimeError: when the file can't be opened
        :raise ValueError: when the length of the data vectors are inconsistent
        """
        if os.path.isfile(path):
            basename = os.path.basename(path)
            root, extension = os.path.splitext(basename)
            if extension.lower() in self.ext:
                try:
                    input_f = open(path,'r')
                except:
                    raise  RuntimeError("abs_reader: cannot open %s" % path)
                buff = input_f.read()
                lines = buff.split('\n')
                x  = np.zeros(0)
                y  = np.zeros(0)
                dy = np.zeros(0)
                dx = np.zeros(0)
                output = Data1D(x, y, dy=dy, dx=dx)
                detector = Detector()
                output.detector.append(detector)
                output.filename = basename
                
                is_info = False
                is_center = False
                is_data_started = False
                
                data_conv_q = None
                data_conv_i = None
                
                if has_converter == True and output.x_unit != '1/A':
                    data_conv_q = Converter('1/A')
                    # Test it
                    data_conv_q(1.0, output.x_unit)
                    
                if has_converter == True and output.y_unit != '1/cm':
                    data_conv_i = Converter('1/cm')
                    # Test it
                    data_conv_i(1.0, output.y_unit)
                
                for line in lines:
                    
                    # Information line 1
                    if is_info == True:
                        is_info = False
                        line_toks = line.split()
                        
                        # Wavelength in Angstrom
                        try:
                            value = float(line_toks[1])
                            if has_converter == True and \
                                output.source.wavelength_unit != 'A':
                                conv = Converter('A')
                                output.source.wavelength = conv(value,
                                        units=output.source.wavelength_unit)
                            else:
                                output.source.wavelength = value
                        except:
                            #goes to ASC reader
                            msg = "abs_reader: cannot open %s" % path
                            raise  RuntimeError(msg)
                        
                        # Distance in meters
                        try:
                            value = float(line_toks[3])
                            if has_converter == True and \
                                detector.distance_unit != 'm':
                                conv = Converter('m')
                                detector.distance = conv(value,
                                                units=detector.distance_unit)
                            else:
                                detector.distance = value
                        except:
                            #goes to ASC reader
                            msg = "abs_reader: cannot open %s" % path
                            raise  RuntimeError(msg)
                        # Transmission
                        try:
                            output.sample.transmission = float(line_toks[4])
                        except:
                            # Transmission is not a mandatory entry
                            pass
                    
                        # Thickness in mm
                        try:
                            value = float(line_toks[5])
                            if has_converter == True and \
                                output.sample.thickness_unit != 'cm':
                                conv = Converter('cm')
                                output.sample.thickness = conv(value,
                                            units=output.sample.thickness_unit)
                            else:
                                output.sample.thickness = value
                        except:
                            # Thickness is not a mandatory entry
                            pass
                    
                    #MON CNT   LAMBDA   DET ANG   DET DIST   TRANS   THICK 
                    #  AVE   STEP
                    if line.count("LAMBDA") > 0:
                        is_info = True
                        
                    # Find center info line
                    if is_center == True:
                        is_center = False
                        line_toks = line.split()
                        # Center in bin number
                        center_x = float(line_toks[0])
                        center_y = float(line_toks[1])
                        
                        # Bin size
                        if has_converter == True and \
                            detector.pixel_size_unit != 'mm':
                            conv = Converter('mm')
                            detector.pixel_size.x = conv(5.0,
                                                units=detector.pixel_size_unit)
                            detector.pixel_size.y = conv(5.0,
                                                units=detector.pixel_size_unit)
                        else:
                            detector.pixel_size.x = 5.0
                            detector.pixel_size.y = 5.0
                        
                        # Store beam center in distance units
                        # Det 640 x 640 mm
                        if has_converter == True and \
                            detector.beam_center_unit != 'mm':
                            conv = Converter('mm')
                            detector.beam_center.x = conv(center_x * 5.0,
                                             units=detector.beam_center_unit)
                            detector.beam_center.y = conv(center_y * 5.0,
                                            units=detector.beam_center_unit)
                        else:
                            detector.beam_center.x = center_x * 5.0
                            detector.beam_center.y = center_y * 5.0
                        
                        # Detector type
                        try:
                            detector.name = line_toks[7]
                        except:
                            # Detector name is not a mandatory entry
                            pass
                    
                    #BCENT(X,Y)   A1(mm)   A2(mm)   A1A2DIST(m)   DL/L
                    #  BSTOP(mm)   DET_TYP
                    if line.count("BCENT") > 0:
                        is_center = True
                        
                    # Parse the data
                    if is_data_started == True:
                        toks = line.split()

                        try:
                            _x  = float(toks[0])
                            _y  = float(toks[1])
                            _dy = float(toks[2])
                            _dx = float(toks[3])
                            
                            if data_conv_q is not None:
                                _x = data_conv_q(_x, units=output.x_unit)
                                _dx = data_conv_i(_dx, units=output.x_unit)
                                
                            if data_conv_i is not None:
                                _y = data_conv_i(_y, units=output.y_unit)
                                _dy = data_conv_i(_dy, units=output.y_unit)
                           
                            x = np.append(x, _x)
                            y = np.append(y, _y)
                            dy = np.append(dy, _dy)
                            dx = np.append(dx, _dx)
                            
                        except:
                            # Could not read this data line. If we are here
                            # it is because we are in the data section. Just
                            # skip it.
                            pass
                            
                    #The 6 columns are | Q (1/A) | I(Q) (1/cm) | std. dev.
                    # I(Q) (1/cm) | sigmaQ | meanQ | ShadowFactor|
                    if line.count("The 6 columns") > 0:
                        is_data_started = True
            
                # Sanity check
                if not len(y) == len(dy):
                    msg = "abs_reader: y and dy have different length"
                    raise ValueError(msg)
                # If the data length is zero, consider this as
                # though we were not able to read the file.
                if len(x) == 0:
                    raise ValueError("ascii_reader: could not load file")
                
                output.x = x[x != 0]
                output.y = y[x != 0]
                output.dy = dy[x != 0]
                output.dx = dx[x != 0]
                if data_conv_q is not None:
                    output.xaxis("\\rm{Q}", output.x_unit)
                else:
                    output.xaxis("\\rm{Q}", 'A^{-1}')
                if data_conv_i is not None:
                    output.yaxis("\\rm{Intensity}", output.y_unit)
                else:
                    output.yaxis("\\rm{Intensity}", "cm^{-1}")
                    
                # Store loading process information
                output.meta_data['loader'] = self.type_name
                return output
        else:
            raise RuntimeError("%s is not a file" % path)
        return None
