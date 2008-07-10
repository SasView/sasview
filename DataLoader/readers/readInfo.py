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

  