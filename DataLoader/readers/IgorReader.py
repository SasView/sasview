import os, sys
import pylab
from copy import deepcopy
import math
class Reader:
    """ Simple data reader for Igor data files """
    ext=['.ASC']
    def __init__(self, filename=None):
        """ Init
            @param filename: Name of Igor data file to read
        """
        self.file = filename
        self.x = []
        self.y = []
        self.image = []
        
        # Detector info
        self.wavelength = 0.0
        self.distance   = 0.0
        self.center_x   = 63.5
        self.center_y   = 63.5
        
    def read(self,filename=None):
        """ Read file """
        # Check if the file is there
        self.file=filename
        if not os.path.isfile(self.file):
            raise ValueError, \
            "Specified file %s is not a regular file" % self.file
        
        # Read file
        f = open(self.file,'r')
        buf = f.read()
        
        # Get content
        dataStarted = False
        
        
        lines = buf.split('\n')
        itot = 0
        self.x = []
        self.y = []
        self.image = []
        
        ncounts = 0
        
        #x = pylab.arange(0, 128, 1)
        #y = pylab.arange(0, 128, 1)
        x = pylab.arange(-.5, .5, 1.0/128)
        y = pylab.arange(-.5, .5, 1.0/128)
        X, Y = pylab.meshgrid(x, y)
        Z = deepcopy(X)
        
        xmin = None
        xmax = None
        ymin = None
        ymax = None
        
        i_x = 0
        i_y = -1
        
        isInfo = False
        isCenter = False
        for line in lines:
            
            # Find setup info line
            if isInfo:
                isInfo = False
                line_toks = line.split()
                # Wavelength in Angstrom
                try:
                    wavelength = float(line_toks[1])
                except:
                    raise ValueError,"IgorReader: can't read this file, missing wavelength"
                # Distance in meters
                try:
                    distance = float(line_toks[3])
                except:
                    raise ValueError,"IgorReader: can't read this file, missing distance"
                
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
            if line.count("***")>0:
                dataStarted = True
                
                # Check that we have all the info
                if wavelength == None \
                    or distance == None \
                    or center_x == None \
                    or center_y == None:
                    raise ValueError, "IgorReader:Missing information in data file"
                
            if dataStarted == True:
                try:
                    value = float(line)
                except:
                    continue
                
                # Get bin number
                if math.fmod(itot, 128)==0:
                    i_x = 0
                    i_y += 1
                else:
                    i_x += 1
                    
                Z[i_y][i_x] = value
                ncounts += 1 
                
                # Det 640 x 640 mm
                # Q = 4pi/lambda sin(theta/2)
                # Bin size is 0.5 cm
                theta = (i_x-center_x+1)*0.5 / distance / 100.0
                qx = 4.0*math.pi/wavelength * math.sin(theta/2.0)
                if xmin==None or qx<xmin:
                    xmin = qx
                if xmax==None or qx>xmax:
                    xmax = qx
                
                theta = (i_y-center_y+1)*0.5 / distance / 100.0
                qy = 4.0*math.pi/wavelength * math.sin(theta/2.0)
                if ymin==None or qy<ymin:
                    ymin = qy
                if ymax==None or qy>ymax:
                    ymax = qy
                
                
                if not qx in self.x:
                    self.x.append(qx)
                if not qy in self.y:
                    self.y.append(qy)
                
                itot += 1
                  
                  
        theta = 0.25 / distance / 100.0
        xstep = 4.0*math.pi/wavelength * math.sin(theta/2.0)
        
        theta = 0.25 / distance / 100.0
        ystep = 4.0*math.pi/wavelength * math.sin(theta/2.0)
        
        # Store q max 
        if xmax>ymax:
            self.qmax = xmax
        else:
            self.qmax = ymax
        
        #config.printEVT("Read %g points from file %s" % (ncounts, self.file))
  
        self.wavelength = wavelength
        self.distance   = distance*1000.0
        self.center_x = center_x
        self.center_y = center_y
        print "IgorReader reading %s"%self.file
        return Z, xmin-xstep/2.0, xmax+xstep/2.0, ymin-ystep/2.0, ymax+ystep/2.0
     