
import Image
import math,logging

    
class Reader:
    """
        Example data manipulation
    """
    ## File type
    type = []
    ## Extension
    ext  = ['tif', 'jpg', '.png', 'jpeg', '.tiff', 'gif', 'bmp']    
        
    def read(self, filename=None):
        print "in tiff"
        """
            Open and read the data in a file
            @param file: path of the file
        """
        
        read_it = False
        for item in self.ext:
            if filename.lower().find(item)>=0:
                read_it = True
                
        if read_it:
            import Image
            import pylab
            import copy
            import numpy
            
            wavelength, distance, center_x, center_y, pixel = 10.0, 11.0, 65, 65, 1.0
            
            
            
            # Initialize 
            x_vals = []
            y_vals = [] 
            ymin = None
            ymax = None
            xmin = None
            xmax = None
            Z = None
        
            try:
                im = Image.open(filename)
            except :
                raise  RuntimeError,"cannot open %s"%(filename)
            # Detector size should be 128x128, the file is 190x190
            print "-> Image size:", im.size, im.format, im.mode
            data = im.getdata()
            x = numpy.zeros(im.size[0])
            y = numpy.zeros(im.size[1])
            X, Y = pylab.meshgrid(x, y)
            Z = copy.deepcopy(X)
            itot = 0
            i_x = 0
            i_y = 0
            
            # Qx and Qy vectors
            for i_x in range(im.size[0]):
                theta = (i_x-center_x+1)*pixel / distance / 100.0
                qx = 4.0*math.pi/wavelength * math.sin(theta/2.0)
                x_vals.append(qx)
                if xmin==None or qx<xmin:
                    xmin = qx
                if xmax==None or qx>xmax:
                    xmax = qx
            
            ymin = None
            ymax = None
            for i_y in range(im.size[1]):
                theta = (i_y-center_y+1)*pixel / distance / 100.0
                qy = 4.0*math.pi/wavelength * math.sin(theta/2.0)
                y_vals.append(qy)
                if ymin==None or qy<ymin:
                    ymin = qy
                if ymax==None or qy>ymax:
                    ymax = qy
            
            for val in data:
                
                try:
                    value = float(val)
                except:
                    continue
                
                # Get bin number
                if math.fmod(itot, im.size[0])==0:
                    i_x = 0
                    i_y += 1
                else:
                    i_x += 1
                    
                Z[im.size[1]-1-i_y][i_x] = value
                
                itot += 1
            from readInfo import ReaderInfo      
            output = ReaderInfo()
            output.wavelength = wavelength
            output.xbins      = im.size[0]
            output.ybins      = im.size[1]
            output.center_x   = center_x
            output.center_y   = center_y
            output.distance   = distance
            output.x_vals     = x_vals
            output.y_vals     = y_vals
            output.xmin       = xmin
            output.xmax       = xmax
            output.ymin       = ymin
            output.ymax       = ymax
            output.image      = Z
            output.pixel_size = pixel
            output.type       ="2D"
            logging.info("tiff_reader reading %s"%(filename))
            
            return output
        
        return None


