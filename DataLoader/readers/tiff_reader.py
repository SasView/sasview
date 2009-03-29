"""
    Image reader. Untested. 
"""

"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2008, University of Tennessee
"""
#TODO: load and check data and orientation of the image (needs rendering)

import math, logging, os
import numpy
from DataLoader.data_info import Image2D
    
class Reader:
    """
        Example data manipulation
    """
    ## File type
    type = ["TIF files (*.tif)|*.tif",
            "JPG files (*.jpg)|*.jpg",
            "JPEG files (*.jpeg)|*.jpeg",
            "PNG files (*.png)|*.png",
            "TIFF files (*.tiff)|*.tiff",
            "BMP files (*.bmp)|*.bmp",
            "GIF files (*.gif)|*.gif",
            ]
    ## Extension
    ext  = ['.tif','.TIF',
             '.jpg','.JPG',
              '.png','.PNG',
               '.jpeg','.JPEG',
                '.tiff','.TIFF',
                 '.gif','.GIF',
                  '.bmp', '.BMP']    
        
    def read(self, filename=None):
        """
            Open and read the data in a file
            @param file: path of the file
        """
        try:
            import Image
        except:
            raise RuntimeError, "tiff_reader: could not load file. Missing Image module."
        
        # Instantiate data object
        output = Image2D()
        output.filename = os.path.basename(filename)
            
        # Read in the image
        try:
            im = Image.open(filename)
        except :
            raise  RuntimeError,"cannot open %s"%(filename)
        data = im.load()

        x_range = im.size[0]
        y_range = im.size[1]
        
        # Initiazed the output data object
        output.image = numpy.zeros([y_range,x_range])

        # Initialize 
        x_vals = []
        y_vals = [] 

        # x and y vectors
        for i_x in range(x_range):
            x_vals.append(i_x)
            
        
        for i_y in range(y_range):
            y_vals.append(i_y)
        
        for i_x in range(x_range):
            for i_y in range(y_range):
            
                try:
                    if data[i_x,i_y].__class__.__name__=="tuple":                     
                        
                        if len(data[i_x,i_y]) == 3:   
                            R,G,B= data[i_x,i_y]
                            #Converting to L Mode: uses the ITU-R 601-2 luma transform.
                            value = float(R * 299/1000 + G * 587/1000 + B * 114/1000) 
                         
                        elif len(data[i_x,i_y]) == 4:   
                            R,G,B,I = data[i_x,i_y]
                            #Take only I 
                            value = float(R * 299/1000 + G * 587/1000 + B * 114/1000)+float(I)
                    else:
                        #Take it as Intensity
                        value = float(data[i_x,i_y])
                except:
                    logging.error("tiff_reader: had to skip a non-float point")
                    continue
                
                  
                output.image[y_range-i_y-1,i_x] = value
        
        output.xbins      = x_range
        output.ybins      = y_range
        output.x_bins     = x_vals
        output.y_bins     = y_vals
        output.xmin       = 0
        output.xmax       = x_range
        output.ymin       = 0
        output.ymax       = y_range
        
        return output
        


