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
import numpy
import math
#import logging
from sas.dataloader.data_info import Data2D
from sas.dataloader.data_info import Detector
from sas.dataloader.manipulations import reader2D_converter

# Look for unit converter
has_converter = True
try:
    from sas.data_util.nxsunit import Converter
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
            raise ValueError, \
            "Specified file %s is not a regular file" % filename
        
        # Read file
        f = open(filename, 'r')
        buf = f.read()
        
        # Instantiate data object
        output = Data2D()
        output.filename = os.path.basename(filename)
        detector = Detector()
        if len(output.detector) > 0:
            print str(output.detector[0])
        output.detector.append(detector)
                
        # Get content
        dataStarted = False
        
        lines = buf.split('\n')
        itot = 0
        x = []
        y = []
        
        ncounts = 0
        
        xmin = None
        xmax = None
        ymin = None
        ymax = None
        
        i_x = 0
        i_y = -1
        i_tot_row = 0
        
        isInfo = False
        isCenter = False
       
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
         
        for line in lines:
            
            # Find setup info line
            if isInfo:
                isInfo = False
                line_toks = line.split()
                # Wavelength in Angstrom
                try:
                    wavelength = float(line_toks[1])
                except:
                    msg = "IgorReader: can't read this file, missing wavelength"
                    raise ValueError, msg
                
            #Find # of bins in a row assuming the detector is square.
            if dataStarted == True:
                try:
                    value = float(line)
                except:
                    # Found a non-float entry, skip it
                    continue
                
                # Get total bin number
                
            i_tot_row += 1
        i_tot_row = math.ceil(math.sqrt(i_tot_row)) - 1
        #print "i_tot", i_tot_row
        size_x = i_tot_row  # 192#128
        size_y = i_tot_row  # 192#128
        output.data = numpy.zeros([size_x, size_y])
        output.err_data = numpy.zeros([size_x, size_y])
     
        #Read Header and 2D data
        for line in lines:
            # Find setup info line
            if isInfo:
                isInfo = False
                line_toks = line.split()
                # Wavelength in Angstrom
                try:
                    wavelength = float(line_toks[1])
                except:
                    msg = "IgorReader: can't read this file, missing wavelength"
                    raise ValueError, msg
                # Distance in meters
                try:
                    distance = float(line_toks[3])
                except:
                    msg = "IgorReader: can't read this file, missing distance"
                    raise ValueError, msg
                
                # Distance in meters
                try:
                    transmission = float(line_toks[4])
                except:
                    msg = "IgorReader: can't read this file, "
                    msg += "missing transmission"
                    raise ValueError, msg
                                            
            if line.count("LAMBDA") > 0:
                isInfo = True
                
            # Find center info line
            if isCenter:
                isCenter = False
                line_toks = line.split()
                
                # Center in bin number: Must substrate 1 because
                #the index starts from 1
                center_x = float(line_toks[0]) - 1
                center_y = float(line_toks[1]) - 1

            if line.count("BCENT") > 0:
                isCenter = True
                
            # Find data start
            if line.count("***")>0:
                dataStarted = True
                
                # Check that we have all the info
                if wavelength == None \
                    or distance == None \
                    or center_x == None \
                    or center_y == None:
                    msg = "IgorReader:Missing information in data file"
                    raise ValueError, msg
                
            if dataStarted == True:
                try:
                    value = float(line)
                except:
                    # Found a non-float entry, skip it
                    continue
                
                # Get bin number
                if math.fmod(itot, i_tot_row) == 0:
                    i_x = 0
                    i_y += 1
                else:
                    i_x += 1
                    
                output.data[i_y][i_x] = value
                ncounts += 1
                
                # Det 640 x 640 mm
                # Q = 4pi/lambda sin(theta/2)
                # Bin size is 0.5 cm 
                #REmoved +1 from theta = (i_x-center_x+1)*0.5 / distance
                # / 100.0 and 
                #REmoved +1 from theta = (i_y-center_y+1)*0.5 /
                # distance / 100.0
                #ToDo: Need  complete check if the following
                # covert process is consistent with fitting.py.
                theta = (i_x - center_x) * 0.5 / distance / 100.0
                qx = 4.0 * math.pi / wavelength * math.sin(theta/2.0)

                if has_converter == True and output.Q_unit != '1/A':
                    qx = data_conv_q(qx, units=output.Q_unit)

                if xmin == None or qx < xmin:
                    xmin = qx
                if xmax == None or qx > xmax:
                    xmax = qx
                
                theta = (i_y - center_y) * 0.5 / distance / 100.0
                qy = 4.0 * math.pi / wavelength * math.sin(theta / 2.0)

                if has_converter == True and output.Q_unit != '1/A':
                    qy = data_conv_q(qy, units=output.Q_unit)
                
                if ymin == None or qy < ymin:
                    ymin = qy
                if ymax == None or qy > ymax:
                    ymax = qy
                
                if not qx in x:
                    x.append(qx)
                if not qy in y:
                    y.append(qy)
                
                itot += 1
                  
                  
        theta = 0.25 / distance / 100.0
        xstep = 4.0 * math.pi / wavelength * math.sin(theta / 2.0)
        
        theta = 0.25 / distance / 100.0
        ystep = 4.0 * math.pi/ wavelength * math.sin(theta / 2.0)
        
        # Store all data ######################################
        # Store wavelength
        if has_converter == True and output.source.wavelength_unit != 'A':
            conv = Converter('A')
            wavelength = conv(wavelength, units=output.source.wavelength_unit)
        output.source.wavelength = wavelength

        # Store distance
        if has_converter == True and detector.distance_unit != 'm':
            conv = Converter('m')
            distance = conv(distance, units=detector.distance_unit)
        detector.distance = distance
  
        # Store transmission
        output.sample.transmission = transmission
        
        # Store pixel size
        pixel = 5.0
        if has_converter == True and detector.pixel_size_unit != 'mm':
            conv = Converter('mm')
            pixel = conv(pixel, units=detector.pixel_size_unit)
        detector.pixel_size.x = pixel
        detector.pixel_size.y = pixel
  
        # Store beam center in distance units
        detector.beam_center.x = center_x * pixel
        detector.beam_center.y = center_y * pixel
        
        # Store limits of the image (2D array)
        xmin = xmin - xstep / 2.0
        xmax = xmax + xstep / 2.0
        ymin = ymin - ystep / 2.0
        ymax = ymax + ystep / 2.0
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
        output.x_bins = x
        output.y_bins = y
        
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
