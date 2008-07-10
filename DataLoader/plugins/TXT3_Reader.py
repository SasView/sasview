# class Loader  to load any king of file
import wx
import string,numpy
import logging
class ReaderInfo:
    """
        This class is a container of data. It stores values read from files
    """
    ## Wavelength [A]
    wavelength = 0.0
    ## Number of x bins
    xbins = 128
    ## Number of y bins
    ybins = 128
    ## Beam center X [pixel number]
    center_x = 65
    ## Beam center Y [pixel number]
    center_y = 65
    ## Distance from sample to detector [m]
    distance = 11.0
    ## Qx values [A-1]
    x_vals = []
    ## Qy xalues [A-1]
    y_vals = []
    ## Qx min
    xmin = 0.0
    ## Qx max
    xmax = 1.0
    ## Qy min
    ymin = 0.0
    ## Qy max
    ymax = 1.0
    ## Image
    image = None
    ## Pixel size
    pixel_size = 0.5
    ## x coordinate
    x=[]
    ##y coordinate
    y=[]
    ##dx error on y
    dx=None
    ## dy error on y
    dy=None
    ## Error on each pixel
    error = None
    ##type of data
    type=""
    ##z
    Z=None
class Reader:
    """
        This class is loading values from given file or value giving by the user
    """
    ext=['.txt','.dat']  
    def _init_(self,filename=None,x=None,y=None,dx=None,dy=None):
        # variable to store loaded values
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.filename = filename
        
        
    def read(self,path, format=None):
        """ Store the values loaded from file in local variables 
            can read 3 columns of data
        """
        
        if not path == None:
            read_it = False
            
            for item in self.ext:
                if path.lower().find(item)>=0:
                    read_it = True
            #print "this is the flag",read_it, path.lower()
            if read_it==False:
                return None
            else:
                try:
                    input_f =  open(path,'r')
                except :
                    raise  RuntimeError,"TXT3_Reader cannot open %s"%(path)
                buff = input_f.read()
                lines = buff.split('\n')
                self.x=[]
                self.y=[]
                self.dx = [] 
                self.dy=[]
                for line in lines:
                    toks = line.split()
                    try:  
                        x = float(toks[0])
                        y = float(toks[1]) 
                        dy = float(toks[2])
                       
                        self.x.append(x)
                        self.y.append(y)
                        self.dy.append(dy)
                   
                    except:
                        pass
                        #print "READ ERROR", line
            
                    self.dx = numpy.zeros(len(self.x))
                    # Sanity check
                    if not len(self.x) == len(self.dx):
                        raise ValueError, "x and dx have different length"
                    if not len(self.y) == len(self.dy):
                        raise ValueError, "y and dy have different length"
               
                if (self.x==[] or self.y==[])and (self.dy==[]):
                    raise ValueError, "TXT3_Reader can't read %s"%path
                else:
                   
                    logging.info ("TXT3_Reader reading %s \n" %(path))
                      
                    output = ReaderInfo()
                    output.x    = self.x
                    output.y    = self.y
                    output.dy   = self.dy
                    output.type = "1D"
                    
                    return output
                
        return None
if __name__ == "__main__": 
    read= Reader()
    #read= Reader(filename="testdata_line.txt")
    print read.load("test.dat")
    
    
            