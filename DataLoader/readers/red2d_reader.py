"""
    TXT/IGOR 2D Q Map file reader
"""

"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

If you use DANSE applications to do scientific research that leads to 
publication, we ask that you acknowledge the use of the software with the 
following sentence:

"This work benefited from DANSE software developed under NSF award DMR-0520547." 

copyright 2008, University of Tennessee
"""

import os, sys
import numpy
import math, logging
from DataLoader.data_info import Data2D, Detector

# Look for unit converter
has_converter = True
try:
    from data_util.nxsunit import Converter
except:
    has_converter = False

class Reader:
    """ Simple data reader for Igor data files """
    ## File type
    type_name = "IGOR/DAT 2D Q_map"   
    ## Wildcards
    type = ["IGOR/DAT 2D file in Q_map (*.dat)|*.DAT"]
    ## Extension
    ext=['.DAT', '.dat']

    def read(self,filename=None):
        """ Read file """
        if not os.path.isfile(filename):
            raise ValueError, \
            "Specified file %s is not a regular file" % filename
        
        # Read file
        f = open(filename,'r')
        buf = f.read()
        
        # Instantiate data object
        output = Data2D()
        output.filename = os.path.basename(filename)
        detector = Detector()
        if len(output.detector)>0: print str(output.detector[0])
        output.detector.append(detector)
                
        # Get content
        dataStarted = False
        
        ## Defaults      
        lines = buf.split('\n')
        itot = 0
        x = []
        y = []
        
        ncounts = 0
        
        wavelength   = None
        distance     = None
        transmission = None
        
        pixel_x = None
        pixel_y = None
        
        i_x    = 0
        i_y    = -1
        pixels = 0
        
        isInfo   = False
        isCenter = False

        data_conv_q = None
        data_conv_i = None
        
        # Set units: This is the unit assumed for Q and I in the data file.
        if has_converter == True and output.Q_unit != '1/A':
            data_conv_q = Converter('1/A')
            # Test it
            data_conv_q(1.0, output.Q_unit)
            
        if has_converter == True and output.I_unit != '1/cm':
            data_conv_i = Converter('1/cm')
            # Test it
            data_conv_i(1.0, output.I_unit)            
        
        #Set the space for data
        data = numpy.zeros(0)
        qx_data = numpy.zeros(0)
        qy_data = numpy.zeros(0)
        q_data = numpy.zeros(0)
        dqx_data = numpy.zeros(0)
        dqy_data = numpy.zeros(0)
        mask = numpy.zeros(0,dtype=bool)
        
        #Read Header and 2D data
        for line in lines:      
            ## Reading the header applies only to IGOR/NIST 2D q_map data files
            # Find setup info line
            if isInfo:
                isInfo = False
                line_toks = line.split()
                # Wavelength in Angstrom
                try:
                    wavelength = float(line_toks[1])
                    # Units
                    if has_converter==True and output.source.wavelength_unit != 'A':
                        conv = Converter('A')
                        wavelength = conv(wavelength, units=output.source.wavelength_unit)
                except:
                    #Not required
                    pass
                # Distance in mm
                try:
                    distance = float(line_toks[3])
                    # Units
                    if has_converter==True and detector.distance_unit != 'm':
                        conv = Converter('m')
                        distance = conv(distance, units=detector.distance_unit)
                except:
                    #Not required
                    pass
                
                # Distance in meters
                try:
                    transmission = float(line_toks[4])
                except:
                    #Not required
                    pass
                                            
            if line.count("LAMBDA")>0:
                isInfo = True
                
            # Find center info line
            if isCenter:
                isCenter = False                
                line_toks = line.split()
                # Center in bin number
                center_x = float(line_toks[0])
                center_y = float(line_toks[1])

            if line.count("BCENT")>0:
                isCenter = True
                       
            # Find data start
            if line.count("Data columns") or line.count("ASCII data")>0:
                dataStarted = True
                continue

            ## Read and get data.   
            if dataStarted == True:
                line_toks = line.split()               
                if len(line_toks) == 0:
                    #empty line
                    continue
                elif len(line_toks) < 3: 
                    #Q-map 2d require 3 or more columns of data          
                    raise ValueError,"Igor_Qmap_Reader: Can't read this file: Not a proper file format"

                # defaults 
                dqx_value  = None
                dqy_value  = None
                qz_value   = None
                mask_value = 0
                
                ##Read and get data values
                qx_value =  float(line_toks[0])
                qy_value =  float(line_toks[1])
                value    =  float(line_toks[2])
                
                try:
                    #Read qz_value if exist on 4th column
                    qz_value = float(line_toks[3])                    
                except:
                    # Found a non-float entry, skip it: Not required.
                    pass                            
                try:
                    #Read qz_value if exist on 5th column
                    dqx_value = float(line_toks[4])
                except:
                    # Found a non-float entry, skip it: Not required.
                    pass
                try:
                    #Read qz_value if exist on 6th column
                    dqy_value = float(line_toks[5])
                except:
                    # Found a non-float entry, skip it: Not required.
                    pass                
                try:
                    #Read beam block mask if exist on 7th column
                    mask_value = float(line_toks[6])
                except:
                    # Found a non-float entry, skip it
                    pass 
                                             
                # get data  
                data    = numpy.append(data, value)
                qx_data = numpy.append(qx_data, qx_value)
                qy_data = numpy.append(qy_data, qy_value)
                
                # optional data
                if dqx_value != None and numpy.isfinite(dqx_value):               
                    dqx_data = numpy.append(dqx_data, dqx_value)
                if dqy_value != None and numpy.isfinite(dqy_value): 
                    dqy_data = numpy.append(dqy_data, dqy_value) 
                    
                # default data
                if qz_value == None or not numpy.isfinite(qz_value): 
                    qz_value = 0  
                if not numpy.isfinite(mask_value): 
                    mask_value = 1             
                q_data  = numpy.append(q_data,numpy.sqrt(qx_value**2+qy_value**2+qz_value**2))
                # Note: For convenience, mask = False stands for masked, while mask = True for unmasked
                mask    = numpy.append(mask,(mask_value>=1))
                
        # If all mask elements are False, put all True
        if not mask.any(): mask[mask==False] = True   
  
        # Store limits of the image in q space
        xmin    = numpy.min(qx_data)
        xmax    = numpy.max(qx_data)
        ymin    = numpy.min(qy_data)
        ymax    = numpy.max(qy_data)

        # units
        if has_converter == True and output.Q_unit != '1/A':
            xmin = data_conv_q(xmin, units=output.Q_unit)
            xmax = data_conv_q(xmax, units=output.Q_unit)
            ymin = data_conv_q(ymin, units=output.Q_unit)
            ymax = data_conv_q(ymax, units=output.Q_unit)
            
        ## calculate the range of the qx and qy_data
        x_size = math.fabs(xmax - xmin)
        y_size = math.fabs(ymax - ymin)
        
        # calculate the number of pixels in the each axes
        npix_y = math.floor(math.sqrt(len(data)))
        npix_x = math.floor(len(data)/npix_y)
        
        # calculate the size of bins      
        xstep = x_size/(npix_x-1)
        ystep = y_size/(npix_y-1)
        
        # store x and y axis bin centers in q space
        x_bins  = numpy.arange(xmin,xmax+xstep,xstep)
        y_bins  = numpy.arange(ymin,ymax+ystep,ystep)
       
        # get the limits of q values
        xmin = xmin - xstep/2
        xmax = xmax + xstep/2
        ymin = ymin - ystep/2
        ymax = ymax + ystep/2
        
        #Store data in outputs  
        #TODO: Check the lengths 
        output.data     = data
        output.err_data = numpy.sqrt(numpy.abs(data))
        output.qx_data  = qx_data
        output.qy_data  = qy_data             
        output.q_data   = q_data
        output.mask     = mask 
        
        output.x_bins = x_bins
        output.y_bins = y_bins
               
        output.xmin = xmin
        output.xmax = xmax
        output.ymin = ymin
        output.ymax = ymax
        
        output.source.wavelength = wavelength
        
        # Store pixel size in mm
        detector.pixel_size.x = pixel_x
        detector.pixel_size.y = pixel_y
        
        # Store the sample to detector distance
        detector.distance = distance
        
        # optional data: if any of dq data == 0, do not pass to output
        if len(dqx_data) == len(qx_data):
            output.dqx_data = dqx_data
        if len(dqy_data) == len(qy_data):
            output.dqy_data = dqy_data
        
        # Units of axes
        if data_conv_q is not None:
            output.xaxis("\\rm{Q_{x}}", output.Q_unit)
            output.yaxis("\\rm{Q_{y}}", output.Q_unit)
        else:
            output.xaxis("\\rm{Q_{x}}", 'A^{-1}')
            output.yaxis("\\rm{Q_{y}}", 'A^{-1}')            
        if data_conv_i is not None:
            output.zaxis("\\rm{Intensity}", output.I_unit)
        else:
            output.zaxis("\\rm{Intensity}","cm^{-1}")
    
        # Store loading process information
        output.meta_data['loader'] = self.type_name

        return output
    
if __name__ == "__main__": 
    reader = Reader()
    print reader.read("../test/exp18_14_igor_2dqxqy.dat") 
        