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

If you use DANSE applications to do scientific research that leads to 
publication, we ask that you acknowledge the use of the software with the 
following sentence:

"This work benefited from DANSE software developed under NSF award DMR-0520547." 

copyright 2008, University of Tennessee
"""

#TODO: Keep track of data manipulation in the 'process' data structure.

from sans.guitools.plottables import Data1D as plottable_1D
from data_util.uncertainty import Uncertainty
import numpy
import math

class plottable_2D:
    """
        Data2D is a place holder for 2D plottables, which are 
        not yet implemented.
    """
    xmin = None
    xmax = None
    ymin = None
    ymax = None
    data = None
    err_data = None
    
    # Units
    _xaxis = ''
    _xunit = ''
    _yaxis = ''
    _yunit = ''
    _zaxis = ''
    _zunit = ''
    
    def __init__(self, data=None, err_data=None):
        self.data = data
        self.err_data = err_data
        
    def xaxis(self, label, unit):
        self._xaxis = label
        self._xunit = unit
        
    def yaxis(self, label, unit):
        self._yaxis = label
        self._yunit = unit
            
    def zaxis(self, label, unit):
        self._zaxis = label
        self._zunit = unit
            
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
    distance_unit = 'mm'
    ## Offset of this detector position in X, Y, (and Z if necessary) [Vector] [mm] 
    offset = Vector()
    offset_unit = 'm'
    ## Orientation (rotation) of this detector in roll, pitch, and yaw [Vector] [degrees]
    orientation = Vector()
    orientation_unit = 'degree'
    ## Center of the beam on the detector in X and Y (and Z if necessary) [Vector] [mm]
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
            
    def __init__(self):
        """
            Initialization
        """
        ## Title 
        self.title      = ''
        ## Run number
        self.run        = None
        ## File name
        self.filename   = ''
        ## Notes
        self.notes      = []
        ## Processes (Action on the data)
        self.process    = []
        ## Instrument name
        self.instrument = ''
        ## Detector information
        self.detector   = []
        ## Sample information
        self.sample     = Sample()
        ## Source information
        self.source     = Source()
        ## Collimation information
        self.collimation = []
        ## Additional meta-data
        self.meta_data  = {}
        ## Loading errors
        self.errors = []        
        
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

        return _str
            
    # Private method to perform operation. Not implemented for DataInfo,
    # but should be implemented for each data class inherited from DataInfo
    # that holds actual data (ex.: Data1D)
    def _perform_operation(self, other, operation): return NotImplemented

    def __add__(self, other):
        """
            Add two data sets
            
            @param other: data set to add to the current one
            @return: new data set
            @raise ValueError: raised when two data sets are incompatible
        """
        def operation(a, b): return a+b
        return self._perform_operation(other, operation)
        
    def __radd__(self, other):
        """
            Add two data sets
            
            @param other: data set to add to the current one
            @return: new data set
            @raise ValueError: raised when two data sets are incompatible
        """
        def operation(a, b): return b+a
        return self._perform_operation(other, operation)
        
    def __sub__(self, other):
        """
            Subtract two data sets
            
            @param other: data set to subtract from the current one
            @return: new data set
            @raise ValueError: raised when two data sets are incompatible
        """
        def operation(a, b): return a-b
        return self._perform_operation(other, operation)
        
    def __rsub__(self, other):
        """
            Subtract two data sets
            
            @param other: data set to subtract from the current one
            @return: new data set
            @raise ValueError: raised when two data sets are incompatible
        """
        def operation(a, b): return b-a
        return self._perform_operation(other, operation)
        
    def __mul__(self, other):
        """
            Multiply two data sets
            
            @param other: data set to subtract from the current one
            @return: new data set
            @raise ValueError: raised when two data sets are incompatible
        """
        def operation(a, b): return a*b
        return self._perform_operation(other, operation)
        
    def __rmul__(self, other):
        """
            Multiply two data sets
            
            @param other: data set to subtract from the current one
            @return: new data set
            @raise ValueError: raised when two data sets are incompatible
        """
        def operation(a, b): return b*a
        return self._perform_operation(other, operation)
        
    def __div__(self, other):
        """
            Divided a data set by another
            
            @param other: data set that the current one is divided by
            @return: new data set
            @raise ValueError: raised when two data sets are incompatible
        """
        def operation(a, b): return a/b
        return self._perform_operation(other, operation)
        
    def __rdiv__(self, other):
        """
            Divided a data set by another
            
            @param other: data set that the current one is divided by
            @return: new data set
            @raise ValueError: raised when two data sets are incompatible
        """
        def operation(a, b): return b/a
        return self._perform_operation(other, operation)            
            
class Data1D(plottable_1D, DataInfo):
    """
        1D data class
    """
    x_unit = '1/A'
    y_unit = '1/cm'
    
    def __init__(self, x, y, dx=None, dy=None):
        DataInfo.__init__(self)
        plottable_1D.__init__(self, x, y, dx, dy)
        if len(self.detector)>0:
            raise RuntimeError, "Data1D: Detector bank already filled at init"
        
        
    def __str__(self):
        """
            Nice printout
        """
        _str =  "%s\n" % DataInfo.__str__(self)
    
        _str += "Data:\n"
        _str += "   Type:         %s\n" % self.__class__.__name__
        _str += "   X-axis:       %s\t[%s]\n" % (self._xaxis, self._xunit)
        _str += "   Y-axis:       %s\t[%s]\n" % (self._yaxis, self._yunit)
        _str += "   Length:       %g\n" % len(self.x)

        return _str

    def clone_without_data(self, length=0):
        """
            Clone the current object, without copying the data (which
            will be filled out by a subsequent operation).
            The data arrays will be initialized to zero.
            
            @param length: length of the data array to be initialized
        """
        from copy import deepcopy
        
        x  = numpy.zeros(length) 
        dx = numpy.zeros(length) 
        y  = numpy.zeros(length) 
        dy = numpy.zeros(length) 
        
        clone = Data1D(x, y, dx=dx, dy=dy)
        clone.title       = self.title
        clone.run         = self.run
        clone.filename    = self.filename
        clone.notes       = deepcopy(self.notes) 
        clone.process     = deepcopy(self.process) 
        clone.detector    = deepcopy(self.detector) 
        clone.sample      = deepcopy(self.sample) 
        clone.source      = deepcopy(self.source) 
        clone.collimation = deepcopy(self.collimation) 
        clone.meta_data   = deepcopy(self.meta_data) 
        clone.errors      = deepcopy(self.errors) 
        
        return clone

    def _validity_check(self, other):
        """
            Checks that the data lengths are compatible.
            Checks that the x vectors are compatible.
            Returns errors vectors equal to original
            errors vectors if they were present or vectors
            of zeros when none was found.
            
            @param other: other data set for operation
            @return: dy for self, dy for other [numpy arrays]
            @raise ValueError: when lengths are not compatible
        """
        dy_other = None
        if isinstance(other, Data1D):
            # Check that data lengths are the same
            if len(self.x) != len(other.x) or \
                len(self.y) != len(other.y):
                raise ValueError, "Unable to perform operation: data length are not equal"
            
            # Here we could also extrapolate between data points
            for i in range(len(self.x)):
                if self.x[i] != other.x[i]:
                    raise ValueError, "Incompatible data sets: x-values do not match"
            
            # Check that the other data set has errors, otherwise
            # create zero vector
            dy_other = other.dy
            if other.dy==None or (len(other.dy) != len(other.y)):
                dy_other = numpy.zeros(len(other.y))
            
        # Check that we have errors, otherwise create zero vector
        dy = self.dy
        if self.dy==None or (len(self.dy) != len(self.y)):
            dy = numpy.zeros(len(self.y))            
            
        return dy, dy_other

    def _perform_operation(self, other, operation):
        """
        """
        # First, check the data compatibility
        dy, dy_other = self._validity_check(other)
        result = self.clone_without_data(len(self.x))
        
        for i in range(len(self.x)):
            result.x[i] = self.x[i]
            if self.dx is not None and len(self.x)==len(self.dx):
                result.dx[i] = self.dx[i]
            
            a = Uncertainty(self.y[i], dy[i]**2)
            if isinstance(other, Data1D):
                b = Uncertainty(other.y[i], dy_other[i]**2)
            else:
                b = other
            
            output = operation(a, b)
            result.y[i] = output.x
            result.dy[i] = math.sqrt(math.fabs(output.variance))
        return result
        
class Data2D(plottable_2D, DataInfo):
    """
        2D data class
    """
    ## Units for Q-values
    Q_unit = '1/A'
    
    ## Units for I(Q) values
    I_unit = '1/cm'
    
    ## Vector of Q-values at the center of each bin in x
    x_bins = []
    
    ## Vector of Q-values at the center of each bin in y
    y_bins = []
    
    
    def __init__(self, data=None, err_data=None):
        DataInfo.__init__(self)
        plottable_2D.__init__(self, data, err_data)
        if len(self.detector)>0:
            raise RuntimeError, "Data2D: Detector bank already filled at init"

    def __str__(self):
        _str =  "%s\n" % DataInfo.__str__(self)
        
        _str += "Data:\n"
        _str += "   Type:         %s\n" % self.__class__.__name__
        _str += "   X- & Y-axis:  %s\t[%s]\n" % (self._yaxis, self._yunit)
        _str += "   Z-axis:       %s\t[%s]\n" % (self._zaxis, self._zunit)
        leny = 0
        if len(self.data)>0:
            leny = len(self.data[0])
        _str += "   Length:       %g x %g\n" % (len(self.data), leny)
        
        return _str
  
