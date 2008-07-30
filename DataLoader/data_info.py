"""
    Module that contains classes to hold information read from 
    reduced data files.
    
    A good description of the data members can be found in 
    the CanSAS 1D XML data format:
    
    http://www.smallangles.net/wgwiki/index.php/cansas1d_documentation
"""

"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2008, University of Tennessee
"""

from sans.guitools.plottables import Data1D as plottable_1D

class Data2D:
    """
        Data2D is a place holder for 2D plottables, which are 
        not yet implemented.
    """
    xmin = None
    xmax = None
    ymin = None
    ymax = None
    image = None
  
class Vector:
    """
        Vector class to hold multi-dimensional objects
    """
    ## x component
    x = None
    ## y component
    y = None
    ## z component
    z = None
    
    def __init__(self, x=None, y=None, z=None):
        """
            Initialization. Components that are not
            set a set to None by default.
            
            @param x: x component
            @param y: y component
            @param z: z component
        """
        self.x = x
        self.y = y
        self.z = z
        
    def __str__(self):
        return "x = %s\ty = %s\tz = %s" % (str(self.x), str(self.y), str(self.z))
        

class Detector:
    """
        Class to hold detector information
    """
    ## Name of the instrument [string]
    name = ''
    ## Sample to detector distance [float] [mm]
    distance = None
    distance_unit = 'm'
    ## Offset of this detector position in X, Y, (and Z if necessary) [Vector] [mm] 
    offset = Vector()
    offset_unit = 'mm'
    ## Orientation (rotation) of this detector in roll, pitch, and yaw [Vector] [degrees]
    orientation = Vector()
    orientation_unit = 'degree'
    ## Center of the beam on the detector in X and Y (and Z if necessary) [Vector] [pixel]
    beam_center = Vector()
    beam_center_unit = 'mm'
    ## Pixel size in X, Y, (and Z if necessary) [Vector] [mm]
    pixel_size = Vector()
    pixel_size_unit = 'mm'
    ## Slit length of the instrument for this detector.[float] [mm]
    slit_length = None
    slit_length_unit = 'mm'
    
    def __str__(self):
        _str  = "Detector:\n"
        _str += "   Name:         %s\n" % self.name
        _str += "   Distance:     %s [%s]\n" % \
            (str(self.distance), str(self.distance_unit))
        _str += "   Offset:       %s [%s]\n" % \
            (str(self.offset), str(self.offset_unit))
        _str += "   Orientation:  %s [%s]\n" % \
            (str(self.orientation), str(self.orientation_unit))
        _str += "   Beam center:  %s [%s]\n" % \
            (str(self.beam_center), str(self.beam_center_unit))
        _str += "   Pixel size:   %s [%s]\n" % \
            (str(self.pixel_size), str(self.pixel_size_unit))
        _str += "   Slit length:  %s [%s]\n" % \
            (str(self.slit_length), str(self.slit_length_unit))
        return _str

class Collimation:
    """
        Class to hold collimation information
    """
    class Aperture:
        # Aperture size [Vector]
        size = Vector()
        size_unit = 'mm'
        # Aperture distance [float]
        distance = None
        distance_unit = 'mm'
    
    ## Length [float] [mm]
    length = None
    length_unit = 'mm'
    ## Aperture
    aperture = []
    
    def __str__(self):
        _str = "Collimation:\n"
        _str += "   Length:       %s [%s]\n" % \
            (str(self.length), str(self.length_unit))
        for item in self.aperture:
            _str += "   Aperture size:%s [%s]\n" % \
                (str(item.size), str(item.size_unit))
            _str += "   Aperture_dist:%s [%s]\n" % \
                (str(item.distance), str(item.distance_unit))
        return _str

class Source:
    """
        Class to hold source information
    """  
    ## Radiation type [string]
    radiation = ''
    ## Beam size [Vector] [mm]
    beam_size = Vector()
    beam_size_unit = 'mm'
    ## Beam shape [string]
    beam_shape = ''
    ## Wavelength [float] [Angstrom]
    wavelength = None
    wavelength_unit = 'A'
    ## Minimum wavelength [float] [Angstrom]
    wavelength_min = None
    wavelength_min_unit = 'nm'
    ## Maximum wavelength [float] [Angstrom]
    wavelength_max = None
    wavelength_max_unit = 'nm'
    ## Wavelength spread [float] [Angstrom]
    wavelength_spread = None
    wavelength_spread_unit = 'percent'
    
    def __str__(self):
        _str  = "Source:\n"
        _str += "   Radiation:    %s\n" % str(self.radiation)
        _str += "   Shape:        %s\n" % str(self.beam_shape)
        _str += "   Wavelength:   %s [%s]\n" % \
            (str(self.wavelength), str(self.wavelength_unit))
        _str += "   Waveln_min:   %s [%s]\n" % \
            (str(self.wavelength_min), str(self.wavelength_min_unit))
        _str += "   Waveln_max:   %s [%s]\n" % \
            (str(self.wavelength_max), str(self.wavelength_max_unit))
        _str += "   Waveln_spread:%s [%s]\n" % \
            (str(self.wavelength_spread), str(self.wavelength_spread_unit))
        _str += "   Beam_size:    %s [%s]\n" % \
            (str(self.beam_size), str(self.beam_size_unit))
        return _str
    
    
""" 
    Definitions of radiation types
"""
NEUTRON  = 'neutron'
XRAY     = 'x-ray'
MUON     = 'muon'
ELECTRON = 'electron'
    
class Sample:
    """
        Class to hold the sample description
    """
    ## ID
    ID = ''
    ## Thickness [float] [mm]
    thickness = None
    thickness_unit = 'mm'
    ## Transmission [float] [fraction]
    transmission = None
    ## Temperature [float] [C]
    temperature = None
    temperature_unit = 'C'
    ## Position [Vector] [mm]
    position = Vector()
    position_unit = 'mm'
    ## Orientation [Vector] [degrees]
    orientation = Vector()
    orientation_unit = 'degree'
    ## Details
    details = []
    
    def __str__(self):
        _str  = "Sample:\n"
        _str += "   ID:           %s\n" % str(self.ID)
        _str += "   Transmission: %s\n" % str(self.transmission)
        _str += "   Thickness:    %s [%s]\n" % \
            (str(self.thickness), str(self.thickness_unit))
        _str += "   Temperature:  %s [%s]\n" % \
            (str(self.temperature), str(self.temperature_unit))
        _str += "   Position:     %s [%s]\n" % \
            (str(self.position), str(self.position_unit))
        _str += "   Orientation:  %s [%s]\n" % \
            (str(self.orientation), str(self.orientation_unit))
        
        _str += "   Details:\n"
        for item in self.details:
            _str += "      %s\n" % item
            
        return _str
  
class Process:
    """
        Class that holds information about the processes
        performed on the data.
    """
    name = ''
    date = ''
    description= ''
    term = []
    notes = []
    
    def __str__(self):
        _str  = "Process:\n"
        _str += "   Name:         %s\n" % self.name
        _str += "   Date:         %s\n" % self.date
        _str += "   Description:  %s\n" % self.description
        for item in self.term:
            _str += "   Term:         %s\n" % item
        for item in self.notes:
            _str += "   Note:         %s\n" % item
        return _str
    
  
class DataInfo:
    """
        Class to hold the data read from a file.
        It includes four blocks of data for the
        instrument description, the sample description,
        the data itself and any other meta data.
    """
    ## Title 
    title      = ''
    ## Run number
    run        = None
    ## File name
    filename   = ''
    ## Notes
    notes      = []
    ## Processes (Action on the data)
    process    = []
    ## Instrument name
    instrument = ''
    ## Detector information
    detector   = []
    ## Sample information
    sample     = Sample()
    ## Source information
    source     = Source()
    ## Collimation information
    collimation = []
    ## Additional meta-data
    meta_data  = {}
    ## Loading errors
    errors = []
    
    def __add__(self, data):
        """
            Add two data sets
            
            @param data: data set to add to the current one
            @return: new data set
            @raise ValueError: raised when two data sets are incompatible
        """
        raise RuntimeError, "DataInfo addition is not implemented yet"
    
    def __sub__(self, data):
        """
            Subtract two data sets
            
            @param data: data set to subtract from the current one
            @return: new data set
            @raise ValueError: raised when two data sets are incompatible
        """
        raise RuntimeError, "DataInfo subtraction is not implemented yet"
    
    def __mul__(self, constant):
        """
            Multiply every entry of the current data set by a constant
            
            @param constant: constant to multiply the data by
            @return: new data set
            @raise ValueError: raised when the constant is not a float
        """
        raise RuntimeError, "DataInfo multiplication is not implemented yet"
    
    def __div__(self, constant):
        """
        """
        raise RuntimeError, "DataInfo division is not implemented yet"
    
        
class Data1D(plottable_1D, DataInfo):
    """
        1D data class
    """
    x_unit = '1/A'
    y_unit = '1/cm'
    
    def __init__(self, x, y, dx=None, dy=None):
        plottable_1D.__init__(self, x, y, dx, dy)
        
    def __str__(self):
        """
            Nice printout
        """
        _str =  "File:            %s\n" % self.filename
        _str += "Title:           %s\n" % self.title
        _str += "Run:             %s\n" % str(self.run)
        _str += "Instrument:      %s\n" % str(self.instrument)
        _str += "%s\n" % str(self.sample)
        _str += "%s\n" % str(self.source)
        for item in self.detector:
            _str += "%s\n" % str(item)
        for item in self.collimation:
            _str += "%s\n" % str(item)
        for item in self.process:
            _str += "%s\n" % str(item)
        for item in self.notes:
            _str += "%s\n" % str(item)
        
        
        _str += "Data:\n"
        _str += "   Type:         %s\n" % self.__class__.__name__
        _str += "   X-axis:       %s\t[%s]\n" % (self._xaxis, self._xunit)
        _str += "   Y-axis:       %s\t[%s]\n" % (self._yaxis, self._yunit)
        _str += "   Length:       %g\n" % len(self.x)

        return _str




