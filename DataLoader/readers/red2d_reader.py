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
        f.close()     
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
        
              
        # Remove the last lines before the for loop if the lines are empty
        # to calculate the exact number of data points
        count = 0
        while (len(lines[len(lines)-(count+1)].lstrip().rstrip()) < 1):
            del lines[len(lines)-(count+1)]
            count = count + 1

        #Read Header and find the dimensions of 2D data
        line_num = 0
        for line in lines:      
            line_num += 1
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
                # the number of columns must be stayed same 
                col_num = len(line_toks)
                break

        
        # Make numpy array to remove header lines using index
        lines_array = numpy.array(lines)

        # index for lines_array
        lines_index = numpy.arange(len(lines))
        
        # get the data lines
        data_lines = lines_array[lines_index>=(line_num-1)]
        # Now we get the total number of rows (i.e., # of data points)
        row_num = len(data_lines)
        # make it as list again to control the separators
        data_list = " ".join(data_lines.tolist())
        # split all data to one big list w/" "separator
        data_list = data_list.split()
 
        # Check if the size is consistent with data, otherwise try the tab(\t) separator
        # (this may be removed once get the confidence the former working all cases).
        if len(data_list) != (len(data_lines)) * col_num:
            data_list = "\t".join(data_lines.tolist())
            data_list = data_list.split()
            
        # Change it(string) into float
        data_list = map(float,data_list)
        # numpy array form
        data_array = numpy.array(data_list)

        # Redimesion based on the row_num and col_num, otherwise raise an error.
        try:
            data_point = data_array.reshape(row_num,col_num).transpose()
        except:
            raise ValueError, "red2d_reader: Can't read this file: Not a proper file format"
        
        ## Get the all data: Let's HARDcoding; Todo find better way
        # Defaults
        dqx_data = numpy.zeros(0)
        dqy_data = numpy.zeros(0)
        qz_data = numpy.zeros(row_num)
        mask = numpy.ones(row_num,dtype=bool)
        # Get from the array
        qx_data = data_point[0]
        qy_data = data_point[1]
        data = data_point[2]
        if col_num >3: qz_data = data_point[3]
        if col_num >4: dqx_data = data_point[4]
        if col_num >5: dqy_data = data_point[5]
        if col_num >6: mask[data_point[6]<1] = False
        q_data = numpy.sqrt(qx_data*qx_data+qy_data*qy_data+qz_data*qz_data)
           
        # Extra protection(it is needed for some data files): 
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
        

