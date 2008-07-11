"""
    Test plug-in
"""

import math
import pylab
import copy
import numpy
import logging

class Reader:
    """
        Example data manipulation
    """
    ## File type
    type = ["DANSE files (*.sans)|*.sans"]
    ## Extension
    ext  = ['.sans']    
        
    def read(self, filename=None):
        """
            Open and read the data in a file
            @param file: path of the file
        """
        
        read_it = False
        for item in self.ext:
            if filename.lower().find(item)>=0:
                read_it = True
                
        if read_it:
            try:
                 datafile = open(filename, 'r')
            except :
                raise  RuntimeError,"danse_reader cannot open %s"%(filename)
            
            
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
            
            read_on = True
            while read_on:
                line = datafile.readline()
                if line.find("DATA:")>=0:
                    read_on = False
                    break
                toks = line.split(':')
                if toks[0]=="FORMATVERSION":
                    fversion = float(toks[1])
                if toks[0]=="WAVELENGTH":
                    wavelength = float(toks[1])
                elif toks[0]=="DISTANCE":
                    distance = float(toks[1])
                elif toks[0]=="CENTER_X":
                    center_x = float(toks[1])
                elif toks[0]=="CENTER_Y":
                    center_y = float(toks[1])
                elif toks[0]=="PIXELSIZE":
                    pixel = float(toks[1])
                elif toks[0]=="SIZE_X":
                    size_x = int(toks[1])
                elif toks[0]=="SIZE_Y":
                    size_y = int(toks[1])
            
            # Read the data
            data = []
            error = []
            if fversion==1.0:
                data_str = datafile.readline()
                data = data_str.split(' ')
            else:
                read_on = True
                while read_on:
                    data_str = datafile.readline()
                    if len(data_str)==0:
                        read_on = False
                    else:
                        toks = data_str.split()
                        try:
                            val = float(toks[0])
                            err = float(toks[1])
                            data.append(val)
                            error.append(err)
                        except:
                            logging.info("Skipping line:%s,%s" %( data_str,sys.exc_value))
                            #print "Skipping line:%s" % data_str
                            #print sys.exc_value
            
            # Initialize 
            x_vals = []
            y_vals = [] 
            ymin = None
            ymax = None
            xmin = None
            xmax = None
            Z = None
        
            
            x = numpy.zeros(size_x)
            y = numpy.zeros(size_y)
            X, Y = pylab.meshgrid(x, y)
            Z = copy.deepcopy(X)
            E = copy.deepcopy(X)
            itot = 0
            i_x = 0
            i_y = 0
            
            # Qx and Qy vectors
            for i_x in range(size_x):
                theta = (i_x-center_x+1)*pixel / distance / 100.0
                qx = 4.0*math.pi/wavelength * math.sin(theta/2.0)
                x_vals.append(qx)
                if xmin==None or qx<xmin:
                    xmin = qx
                if xmax==None or qx>xmax:
                    xmax = qx
            
            ymin = None
            ymax = None
            for i_y in range(size_y):
                theta = (i_y-center_y+1)*pixel / distance / 100.0
                qy = 4.0*math.pi/wavelength * math.sin(theta/2.0)
                y_vals.append(qy)
                if ymin==None or qy<ymin:
                    ymin = qy
                if ymax==None or qy>ymax:
                    ymax = qy
            
            for i_pt in range(len(data)):
                val = data[i_pt]
                try:
                    value = float(val)
                except:
                    continue
                
                # Get bin number
                if math.fmod(itot, size_x)==0:
                    i_x = 0
                    i_y += 1
                else:
                    i_x += 1
                    
                Z[size_y-1-i_y][i_x] = value
                if fversion>1.0:
                    E[size_y-1-i_y][i_x] = error[i_pt]
                
                itot += 1
            from readInfo import ReaderInfo   
            output = ReaderInfo()
            output.wavelength = wavelength
            output.xbins      = size_x
            output.ybins      = size_y
            output.center_x   = center_x
            output.center_y   = center_y
            # Store the distance in [mm]
            output.distance   = distance*1000.0
            output.x_vals     = x_vals
            output.y_vals     = y_vals
            output.xmin       = xmin
            output.xmax       = xmax
            output.ymin       = ymin
            output.ymax       = ymax
            output.pixel_size = pixel
            output.image      = Z
            output.x          = x_vals
            output.y          = y_vals
            output.type       = "2D "
           
            if not fversion>=1.0:
                #output.error  = E
                raise ValueError,"Danse_reader can't read this file %s"%filename
            else:
                logging.info("Danse_reader Reading %s \n"%filename)
                return output
        
        return None
