"""
    Module that contains classes to hold information read from
    reduced data files.
    
    A good description of the data members can be found in
    the CanSAS 1D XML data format:
    
    http://www.smallangles.net/wgwiki/index.php/cansas1d_documentation
"""
#####################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#See the license text in license.txt
#copyright 2008, University of Tennessee
######################################################################


#TODO: Keep track of data manipulation in the 'process' data structure.
#TODO: This module should be independent of plottables. We should write
#        an adapter class for plottables when needed.

#from sans.guitools.plottables import Data1D as plottable_1D
from sans.data_util.uncertainty import Uncertainty
import numpy
import math


class plottable_1D:
    """
    Data1D is a place holder for 1D plottables.
    """
    # The presence of these should be mutually
    # exclusive with the presence of Qdev (dx)
    x = None
    y = None
    dx = None
    dy = None
    ## Slit smearing length
    dxl = None
    ## Slit smearing width
    dxw = None
    
    # Units
    _xaxis = ''
    _xunit = ''
    _yaxis = ''
    _yunit = ''
    
    def __init__(self, x, y, dx=None, dy=None, dxl=None, dxw=None):
        self.x = numpy.asarray(x)
        self.y = numpy.asarray(y)
        if dx is not None:
            self.dx = numpy.asarray(dx)
        if dy is not None:
            self.dy = numpy.asarray(dy)
        if dxl is not None:
            self.dxl = numpy.asarray(dxl)
        if dxw is not None: 
            self.dxw = numpy.asarray(dxw)

    def xaxis(self, label, unit):
        """
        set the x axis label and unit
        """
        self._xaxis = label
        self._xunit = unit
        
    def yaxis(self, label, unit):
        """
        set the y axis label and unit
        """
        self._yaxis = label
        self._yunit = unit


class plottable_2D:
    """
    Data2D is a place holder for 2D plottables.
    """
    xmin = None
    xmax = None
    ymin = None
    ymax = None
    data = None
    qx_data = None
    qy_data = None
    q_data = None
    err_data = None
    dqx_data = None
    dqy_data = None
    mask = None
    
    # Units
    _xaxis = ''
    _xunit = ''
    _yaxis = ''
    _yunit = ''
    _zaxis = ''
    _zunit = ''
    
    def __init__(self, data=None, err_data=None, qx_data=None,
                 qy_data=None, q_data=None, mask=None,
                 dqx_data=None, dqy_data=None):
        self.data = numpy.asarray(data)
        self.qx_data = numpy.asarray(qx_data)
        self.qy_data = numpy.asarray(qy_data)
        self.q_data = numpy.asarray(q_data)
        self.mask = numpy.asarray(mask)
        self.err_data = numpy.asarray(err_data)
        if dqx_data is not None:
            self.dqx_data = numpy.asarray(dqx_data) 
        if dqy_data is not None:
            self.dqy_data = numpy.asarray(dqy_data) 
               
    def xaxis(self, label, unit):
        """
        set the x axis label and unit
        """
        self._xaxis = label
        self._xunit = unit
        
    def yaxis(self, label, unit):
        """
        set the y axis label and unit
        """
        self._yaxis = label
        self._yunit = unit
            
    def zaxis(self, label, unit):
        """
        set the z axis label and unit
        """
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
        
        :param x: x component
        :param y: y component
        :param z: z component
        
        """
        self.x = x
        self.y = y
        self.z = z
        
    def __str__(self):
        msg = "x = %s\ty = %s\tz = %s" % (str(self.x), str(self.y), str(self.z))
        return msg
        

class Detector:
    """
    Class to hold detector information
    """
    ## Name of the instrument [string]
    name = None
    ## Sample to detector distance [float] [mm]
    distance = None
    distance_unit = 'mm'
    ## Offset of this detector position in X, Y,
    #(and Z if necessary) [Vector] [mm]
    offset = None
    offset_unit = 'm'
    ## Orientation (rotation) of this detector in roll,
    # pitch, and yaw [Vector] [degrees]
    orientation = None
    orientation_unit = 'degree'
    ## Center of the beam on the detector in X and Y
    #(and Z if necessary) [Vector] [mm]
    beam_center = None
    beam_center_unit = 'mm'
    ## Pixel size in X, Y, (and Z if necessary) [Vector] [mm]
    pixel_size = None
    pixel_size_unit = 'mm'
    ## Slit length of the instrument for this detector.[float] [mm]
    slit_length = None
    slit_length_unit = 'mm'
    
    def __init__(self):
        """
        
        Initialize class attribute that are objects...
        
        """
        self.offset      = Vector()
        self.orientation = Vector()
        self.beam_center = Vector()
        self.pixel_size  = Vector()
        
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


class Aperture:
    ## Name
    name = None
    ## Type
    type = None
    ## Size name
    size_name = None
    ## Aperture size [Vector]
    size = None
    size_unit = 'mm'
    ## Aperture distance [float]
    distance = None
    distance_unit = 'mm'
    
    def __init__(self):
        self.size = Vector()
    
    
class Collimation:
    """
    Class to hold collimation information
    """
    ## Name
    name = None
    ## Length [float] [mm]
    length = None
    length_unit = 'mm'
    ## Aperture
    aperture = None
    
    def __init__(self):
        self.aperture = []
    
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
    ## Name
    name = None
    ## Radiation type [string]
    radiation = None
    ## Beam size name
    beam_size_name = None
    ## Beam size [Vector] [mm]
    beam_size = None
    beam_size_unit = 'mm'
    ## Beam shape [string]
    beam_shape = None
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
    
    def __init__(self):
        self.beam_size = Vector()
        
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
    ## Short name for sample
    name = ''
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
    position = None
    position_unit = 'mm'
    ## Orientation [Vector] [degrees]
    orientation = None
    orientation_unit = 'degree'
    ## Details
    details = None
    
    def __init__(self):
        self.position    = Vector()
        self.orientation = Vector()
        self.details     = []
    
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
    description = ''
    term = None
    notes = None
    
    def __init__(self):
        self.term = []
        self.notes = []
    
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
    ## Run name
    run_name   = None
    ## File name
    filename   = ''
    ## Notes
    notes      = None
    ## Processes (Action on the data)
    process    = None
    ## Instrument name
    instrument = ''
    ## Detector information
    detector   = None
    ## Sample information
    sample     = None
    ## Source information
    source     = None
    ## Collimation information
    collimation = None
    ## Additional meta-data
    meta_data  = None
    ## Loading errors
    errors = None
            
    def __init__(self):
        """
        Initialization
        """
        ## Title 
        self.title      = ''
        ## Run number
        self.run        = []
        self.run_name   = {}
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
        
    def append_empty_process(self):
        """
        """
        self.process.append(Process())
        
    def add_notes(self, message=""):
        """
        Add notes to datainfo
        """
        self.notes.append(message)
        
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
    def _perform_operation(self, other, operation):
        """
        Private method to perform operation. Not implemented for DataInfo,
        but should be implemented for each data class inherited from DataInfo
        that holds actual data (ex.: Data1D)
        """
        return NotImplemented
    
    def _perform_union(self, other):
        """
        Private method to perform union operation. Not implemented for DataInfo,
        but should be implemented for each data class inherited from DataInfo
        that holds actual data (ex.: Data1D)
        """
        return NotImplemented

    def __add__(self, other):
        """
        Add two data sets
        
        :param other: data set to add to the current one
        :return: new data set
        :raise ValueError: raised when two data sets are incompatible
        """
        def operation(a, b):
            return a + b
        return self._perform_operation(other, operation)
        
    def __radd__(self, other):
        """
        Add two data sets
        
        :param other: data set to add to the current one
        
        :return: new data set
        
        :raise ValueError: raised when two data sets are incompatible
        
        """
        def operation(a, b):
            return b + a
        return self._perform_operation(other, operation)
        
    def __sub__(self, other):
        """
        Subtract two data sets
        
        :param other: data set to subtract from the current one
        
        :return: new data set
        
        :raise ValueError: raised when two data sets are incompatible
        
        """
        def operation(a, b):
            return a - b
        return self._perform_operation(other, operation)
        
    def __rsub__(self, other):
        """
        Subtract two data sets
        
        :param other: data set to subtract from the current one
        
        :return: new data set
        
        :raise ValueError: raised when two data sets are incompatible
        
        """
        def operation(a, b):
            return b - a
        return self._perform_operation(other, operation)
        
    def __mul__(self, other):
        """
        Multiply two data sets
        
        :param other: data set to subtract from the current one
        
        :return: new data set
        
        :raise ValueError: raised when two data sets are incompatible
        
        """
        def operation(a, b):
            return a * b
        return self._perform_operation(other, operation)
        
    def __rmul__(self, other):
        """
        Multiply two data sets
        
        :param other: data set to subtract from the current one
        
        :return: new data set
        
        :raise ValueError: raised when two data sets are incompatible
        """
        def operation(a, b):
            return b * a
        return self._perform_operation(other, operation)
        
    def __div__(self, other):
        """
        Divided a data set by another
        
        :param other: data set that the current one is divided by
        
        :return: new data set
        
        :raise ValueError: raised when two data sets are incompatible
        
        """
        def operation(a, b):
            return a/b
        return self._perform_operation(other, operation)
        
    def __rdiv__(self, other):
        """
        Divided a data set by another
        
        :param other: data set that the current one is divided by
        
        :return: new data set
        
        :raise ValueError: raised when two data sets are incompatible
        
        """
        def operation(a, b):
            return b/a
        return self._perform_operation(other, operation)
            
        
    def __or__(self, other):
        """
        Union a data set with another
        
        :param other: data set to be unified
        
        :return: new data set
        
        :raise ValueError: raised when two data sets are incompatible
        
        """
        return self._perform_union(other)
        
    def __ror__(self, other):
        """
        Union a data set with another
        
        :param other: data set to be unified
        
        :return: new data set
        
        :raise ValueError: raised when two data sets are incompatible
        
        """
        return self._perform_union(other)
                
class Data1D(plottable_1D, DataInfo):
    """
    1D data class
    """
    x_unit = '1/A'
    y_unit = '1/cm'
    
    def __init__(self, x, y, dx=None, dy=None):
        DataInfo.__init__(self)
        plottable_1D.__init__(self, x, y, dx, dy)
        
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

    def is_slit_smeared(self):
        """
        Check whether the data has slit smearing information
        
        :return: True is slit smearing info is present, False otherwise
        
        """
        def _check(v):
            if (v.__class__ == list or v.__class__ == numpy.ndarray) \
                and len(v) > 0 and min(v) > 0:
                return True
            
            return False
        
        return _check(self.dxl) or _check(self.dxw)
        
    def clone_without_data(self, length=0, clone=None):
        """
        Clone the current object, without copying the data (which
        will be filled out by a subsequent operation).
        The data arrays will be initialized to zero.
        
        :param length: length of the data array to be initialized
        :param clone: if provided, the data will be copied to clone
        """
        from copy import deepcopy
        
        if clone is None or not issubclass(clone.__class__, Data1D):
            x  = numpy.zeros(length)
            dx = numpy.zeros(length)
            y  = numpy.zeros(length)
            dy = numpy.zeros(length)
            clone = Data1D(x, y, dx=dx, dy=dy)
        
        clone.title       = self.title
        clone.run         = self.run
        clone.filename    = self.filename
        clone.instrument  = self.instrument
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
        
        :param other: other data set for operation
        
        :return: dy for self, dy for other [numpy arrays]
        
        :raise ValueError: when lengths are not compatible
        
        """
        dy_other = None
        if isinstance(other, Data1D):
            # Check that data lengths are the same
            if len(self.x) != len(other.x) or \
                len(self.y) != len(other.y):
                msg = "Unable to perform operation: data length are not equal"
                raise ValueError, msg
            
            # Here we could also extrapolate between data points
            ZERO = 1.0e-12
            for i in range(len(self.x)):
                if math.fabs(self.x[i] - other.x[i]) > ZERO:
                    msg = "Incompatible data sets: x-values do not match"
                    raise ValueError, msg
                """
                if self.dxl != None and other.dxl == None:
                    msg = "Incompatible data sets: dxl-values do not match"
                    raise ValueError, msg
                if self.dxl == None and other.dxl != None:
                    msg = "Incompatible data sets: dxl-values do not match"
                    raise ValueError, msg
                if self.dxw != None and other.dxw == None:
                    msg = "Incompatible data sets: dxw-values do not match"
                    raise ValueError, msg
                if self.dxw == None and other.dxw != None:
                    msg = "Incompatible data sets: dxw-values do not match"
                    raise ValueError, msg
                """
            # Check that the other data set has errors, otherwise
            # create zero vector
            dy_other = other.dy
            if other.dy == None or (len(other.dy) != len(other.y)):
                dy_other = numpy.zeros(len(other.y))
            
        # Check that we have errors, otherwise create zero vector
        dy = self.dy
        if self.dy == None or (len(self.dy) != len(self.y)):
            dy = numpy.zeros(len(self.y))
            
        return dy, dy_other

    def _perform_operation(self, other, operation):
        """
        """
        # First, check the data compatibility
        dy, dy_other = self._validity_check(other)
        result = self.clone_without_data(len(self.x))
        if self.dxw == None:
            result.dxw = None
        else:
            result.dxw = numpy.zeros(len(self.x))
        if self.dxl == None:
            result.dxl = None
        else:
            result.dxl = numpy.zeros(len(self.x))

        for i in range(len(self.x)):
            result.x[i] = self.x[i]
            if self.dx is not None and len(self.x) == len(self.dx):
                result.dx[i] = self.dx[i]
            if self.dxw is not None and len(self.x) == len(self.dxw):
                result.dxw[i] = self.dxw[i]
            if self.dxl is not None and len(self.x) == len(self.dxl):
                result.dxl[i] = self.dxl[i]
            
            a = Uncertainty(self.y[i], dy[i]**2)
            if isinstance(other, Data1D):
                b = Uncertainty(other.y[i], dy_other[i]**2)
                if other.dx is not None:
                    result.dx[i] *= self.dx[i]
                    result.dx[i] += (other.dx[i]**2)
                    result.dx[i] /= 2
                    result.dx[i] = math.sqrt(result.dx[i])
                if result.dxl is not None and other.dxl is not None:
                    result.dxl[i] *= self.dxl[i]
                    result.dxl[i] += (other.dxl[i]**2)
                    result.dxl[i] /= 2
                    result.dxl[i] = math.sqrt(result.dxl[i])
            else:
                b = other
            
            output = operation(a, b)
            result.y[i] = output.x
            result.dy[i] = math.sqrt(math.fabs(output.variance))
        return result
    
    def _validity_check_union(self, other):
        """
        Checks that the data lengths are compatible.
        Checks that the x vectors are compatible.
        Returns errors vectors equal to original
        errors vectors if they were present or vectors
        of zeros when none was found.
        
        :param other: other data set for operation
        
        :return: bool
        
        :raise ValueError: when data types are not compatible
        
        """
        if not isinstance(other, Data1D):
            msg = "Unable to perform operation: different types of data set"
            raise ValueError, msg   
        return True

    def _perform_union(self, other):
        """
        """
        # First, check the data compatibility
        self._validity_check_union(other)
        result = self.clone_without_data(len(self.x) + len(other.x))
        if self.dy == None or other.dy is None:
            result.dy = None
        else:
            result.dy = numpy.zeros(len(self.x) + len(other.x))
        if self.dx == None or other.dx is None:
            result.dx = None
        else:
            result.dx = numpy.zeros(len(self.x) + len(other.x))
        if self.dxw == None or other.dxw is None:
            result.dxw = None
        else:
            result.dxw = numpy.zeros(len(self.x) + len(other.x))
        if self.dxl == None or other.dxl is None:
            result.dxl = None
        else:
            result.dxl = numpy.zeros(len(self.x) + len(other.x))

        result.x = numpy.append(self.x, other.x)
        #argsorting
        ind = numpy.argsort(result.x)
        result.x = result.x[ind]
        result.y = numpy.append(self.y, other.y)
        result.y = result.y[ind]
        if result.dy != None:
            result.dy = numpy.append(self.dy, other.dy)
            result.dy = result.dy[ind]
        if result.dx is not None:
            result.dx = numpy.append(self.dx, other.dx)
            result.dx = result.dx[ind]
        if result.dxw is not None:
            result.dxw = numpy.append(self.dxw, other.dxw)
            result.dxw = result.dxw[ind]
        if result.dxl is not None:
            result.dxl = numpy.append(self.dxl, other.dxl)
            result.dxl = result.dxl[ind]
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
    x_bins = None
    
    ## Vector of Q-values at the center of each bin in y
    y_bins = None
    
    def __init__(self, data=None, err_data=None, qx_data=None,
                 qy_data=None, q_data=None, mask=None,
                 dqx_data=None, dqy_data=None):
        self.y_bins = []
        self.x_bins = []
        DataInfo.__init__(self)
        plottable_2D.__init__(self, data, err_data, qx_data,
                              qy_data, q_data, mask, dqx_data, dqy_data)
        if len(self.detector) > 0:
            raise RuntimeError, "Data2D: Detector bank already filled at init"

    def __str__(self):
        _str = "%s\n" % DataInfo.__str__(self)
        
        _str += "Data:\n"
        _str += "   Type:         %s\n" % self.__class__.__name__
        _str += "   X- & Y-axis:  %s\t[%s]\n" % (self._yaxis, self._yunit)
        _str += "   Z-axis:       %s\t[%s]\n" % (self._zaxis, self._zunit)
        #leny = 0
        #if len(self.data) > 0:
        #    leny = len(self.data)
        _str += "   Length:       %g \n" % (len(self.data))
        
        return _str
  
    def clone_without_data(self, length=0, clone=None):
        """
        Clone the current object, without copying the data (which
        will be filled out by a subsequent operation).
        The data arrays will be initialized to zero.
        
        :param length: length of the data array to be initialized
        :param clone: if provided, the data will be copied to clone
        """
        from copy import deepcopy
        
        if clone is None or not issubclass(clone.__class__, Data2D):
            data = numpy.zeros(length)
            err_data = numpy.zeros(length)
            qx_data = numpy.zeros(length)
            qy_data = numpy.zeros(length)
            q_data = numpy.zeros(length)
            mask = numpy.zeros(length)
            dqx_data = None
            dqy_data = None
            clone = Data2D(data=data, err_data=err_data, 
                           qx_data=qx_data, qy_data=qy_data, 
                           q_data=q_data, mask=mask)

        clone.title       = self.title
        clone.run         = self.run
        clone.filename    = self.filename
        clone.instrument  = self.instrument
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
        
        :param other: other data set for operation
        
        :return: dy for self, dy for other [numpy arrays]
        
        :raise ValueError: when lengths are not compatible
        
        """
        err_other = None
        if isinstance(other, Data2D):
            # Check that data lengths are the same
            if len(self.data) != len(other.data) or \
                len(self.qx_data) != len(other.qx_data) or \
                len(self.qy_data) != len(other.qy_data):
                msg = "Unable to perform operation: data length are not equal"
                raise ValueError, msg
            #if len(self.data) < 1:
            #    msg = "Incompatible data sets: I-values do not match"
            #    raise ValueError, msg 
            for ind in range(len(self.data)):
                if self.qx_data[ind] != other.qx_data[ind]:
                    msg = "Incompatible data sets: qx-values do not match"
                    raise ValueError, msg
                if self.qy_data[ind] != other.qy_data[ind]:
                    msg = "Incompatible data sets: qy-values do not match"
                    raise ValueError, msg
                   
            # Check that the scales match
            err_other = other.err_data
            if other.err_data == None or \
                (len(other.err_data) != len(other.data)):
                err_other = numpy.zeros(len(other.data))
            
        # Check that we have errors, otherwise create zero vector
        err = self.err_data
        if self.err_data == None or \
            (len(self.err_data) != len(self.data)):
            err = numpy.zeros(len(other.data))
            
        return err, err_other
  
    def _perform_operation(self, other, operation):
        """
        Perform 2D operations between data sets
        
        :param other: other data set
        :param operation: function defining the operation
        
        """
        # First, check the data compatibility
        dy, dy_other = self._validity_check(other)
        result = self.clone_without_data(numpy.size(self.data))
        if self.dqx_data == None or self.dqy_data == None:
            result.dqx_data = None
            result.dqy_data = None
        else:
            result.dqx_data = numpy.zeros(len(self.data))
            result.dqy_data = numpy.zeros(len(self.data))
        for i in range(numpy.size(self.data)):
            result.data[i] = self.data[i]
            if self.err_data is not None and \
                numpy.size(self.data) == numpy.size(self.err_data):
                result.err_data[i] = self.err_data[i]    
            if self.dqx_data is not None:
                result.dqx_data[i] = self.dqx_data[i]
            if self.dqy_data is not None:
                result.dqy_data[i] = self.dqy_data[i]
            result.qx_data[i] = self.qx_data[i]
            result.qy_data[i] = self.qy_data[i]
            result.q_data[i] = self.q_data[i]
            result.mask[i] = self.mask[i]
            
            a = Uncertainty(self.data[i], dy[i]**2)
            if isinstance(other, Data2D):
                b = Uncertainty(other.data[i], dy_other[i]**2)
                if other.dqx_data is not None and \
                        result.dqx_data is not None:
                    result.dqx_data[i] *= self.dqx_data[i]
                    result.dqx_data[i] += (other.dqx_data[i]**2)
                    result.dqx_data[i] /= 2
                    result.dqx_data[i] = math.sqrt(result.dqx_data[i])     
                if other.dqy_data is not None and \
                        result.dqy_data is not None:
                    result.dqy_data[i] *= self.dqy_data[i]
                    result.dqy_data[i] += (other.dqy_data[i]**2)
                    result.dqy_data[i] /= 2
                    result.dqy_data[i] = math.sqrt(result.dqy_data[i])
            else:
                b = other
            
            output = operation(a, b)
            result.data[i] = output.x
            result.err_data[i] = math.sqrt(math.fabs(output.variance))
        return result
    
    def _validity_check_union(self, other):
        """
        Checks that the data lengths are compatible.
        Checks that the x vectors are compatible.
        Returns errors vectors equal to original
        errors vectors if they were present or vectors
        of zeros when none was found.
        
        :param other: other data set for operation
        
        :return: bool
        
        :raise ValueError: when data types are not compatible
        
        """
        if not isinstance(other, Data2D):
            msg = "Unable to perform operation: different types of data set"
            raise ValueError, msg   
        return True
    
    def _perform_union(self, other):
        """
        Perform 2D operations between data sets
        
        :param other: other data set
        :param operation: function defining the operation
        
        """
        # First, check the data compatibility
        self._validity_check_union(other)
        result = self.clone_without_data(numpy.size(self.data) + \
                                         numpy.size(other.data))
        result.xmin = self.xmin
        result.xmax = self.xmax
        result.ymin = self.ymin
        result.ymax = self.ymax
        if self.dqx_data == None or self.dqy_data == None or \
                other.dqx_data == None or other.dqy_data == None :
            result.dqx_data = None
            result.dqy_data = None
        else:
            result.dqx_data = numpy.zeros(len(self.data) + \
                                         numpy.size(other.data))
            result.dqy_data = numpy.zeros(len(self.data) + \
                                         numpy.size(other.data))
        
        result.data = numpy.append(self.data, other.data)
        result.qx_data = numpy.append(self.qx_data, other.qx_data)
        result.qy_data = numpy.append(self.qy_data, other.qy_data)
        result.q_data = numpy.append(self.q_data, other.q_data)
        result.mask = numpy.append(self.mask, other.mask)
        if result.err_data is not None:
            result.err_data = numpy.append(self.err_data, other.err_data) 
        if self.dqx_data is not None:
            result.dqx_data = numpy.append(self.dqx_data, other.dqx_data)
        if self.dqy_data is not None:
            result.dqy_data = numpy.append(self.dqy_data, other.dqy_data)

        return result
