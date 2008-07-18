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
    ## Offset of this detector position in X, Y, (and Z if necessary) [Vector] [mm] 
    offset = Vector()
    ## Orientation (rotation) of this detector in roll, pitch, and yaw [Vector] [degrees]
    orientation = Vector()
    ## Center of the beam on the detector in X and Y (and Z if necessary) [Vector] [pixel]
    beam_center = Vector()
    ## Pixel size in X, Y, (and Z if necessary) [Vector] [mm]
    pixel_size = Vector()
    ## Slit length of the instrument for this detector.[float] [mm]
    slit_length = None

class Collimation:
    """
        Class to hold collimation information
    """
    ## Length [float] [mm]
    length = None
    ## Aperture size [Vector] [mm]
    aperture_size = Vector()
    ## Aperture distance [float] [m]
    aperture_distance = None

class Source:
    """
        Class to hold source information
    """  
    ## Radiation type [string]
    radiation = ''
    ## Beam size [Vector] [mm]
    beam_size = Vector()
    ## Beam shape [string]
    beam_shape = ''
    ## Wavelength [float] [Angstrom]
    wavelength = None
    ## Minimum wavelength [float] [Angstrom]
    wavelength_min = None
    ## Maximum wavelength [float] [Angstrom]
    wavelength_max = None
    ## Wavelength spread [float] [Angstrom]
    wavelength_spread = None
    
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
    ## Transmission [float] [%]
    transmission = None
    ## Temperature [float] [C]
    temperature = None
    ## Position [Vector] [mm]
    position = Vector()
    ## Orientation [Vector] [degrees]
    orientation = Vector()
    ## Details
    details = ''
    
  
class DataInfo:
    """
        Class to hold the data read from a file.
        It includes four blocks of data for the
        instrument description, the sample description,
        the data itself and any other meta data.
    """
    ## Run number
    run        = None
    ## File name
    filename   = ''
    ## Notes
    notes      = ''
    ## Processes (Action on the data)
    process    = []
    ## Detector information
    detector   = Detector()
    ## Sample information
    sample     = Sample()
    ## Source information
    source     = Source()
    ## Additional meta-data
    meta_data  = {}
    
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
    def __init__(self, x, y, dx=None, dy=None):
        plottable_1D.__init__(self, x, y, dx, dy)
        
    def __str__(self):
        """
            Nice printout
        """
        _str = "File: %s\n" % self.filename
        
        _str += "Sample:\n"
        _str += "   Transmission: %s\n" % str(self.sample.transmission)
        _str += "   Thickness:    %s\n" % str(self.sample.thickness)
        
        _str += "Source:\n"
        _str += "   Wavelength:   %s [A]\n" % str(self.source.wavelength)

        _str += "Detector:\n"
        _str += "   Name:         %s\n" % self.detector.name
        _str += "   Distance:     %s [mm]\n" % str(self.detector.distance)
        _str += "   Beam_center:  %s [pixel]\n" % str(self.detector.beam_center)
        
        _str += "Data:\n"
        _str += "   Type:         %s\n" % self.__class__.__name__
        _str += "   X-axis:       %s\t[%s]\n" % (self._xaxis, self._xunit)
        _str += "   Y-axis:       %s\t[%s]\n" % (self._yaxis, self._yunit)
        _str += "   Length:       %g\n" % len(self.x)

        return _str




