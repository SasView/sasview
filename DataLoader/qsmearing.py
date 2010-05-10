"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2009, University of Tennessee
"""

import DataLoader.extensions.smearer as smearer
import numpy
import math
import logging, sys
from DataLoader.smearing_2d import Smearer2D

def smear_selection(data1D):
    """
        Creates the right type of smearer according 
        to the data.
    
        The canSAS format has a rule that either
        slit smearing data OR resolution smearing data
        is available. 
        
        For the present purpose, we choose the one that
        has none-zero data. If both slit and resolution
        smearing arrays are filled with good data 
        (which should not happen), then we choose the
        resolution smearing data. 
        
        @param data1D: Data1D object
    """
    # Sanity check. If we are not dealing with a SANS Data1D
    # object, just return None
    if  data1D.__class__.__name__ != 'Data1D':
        if data1D == None:
            return None
        elif data1D.dqx_data == None or data1D.dqy_data == None:
            return None
        return Smearer2D(data1D)
    
    if  not hasattr(data1D, "dx") and not hasattr(data1D, "dxl") and not hasattr(data1D, "dxw"):
        return None
    
    # Look for resolution smearing data
    _found_resolution = False
    if data1D.dx is not None and len(data1D.dx)==len(data1D.x):
        
        # Check that we have non-zero data
        if data1D.dx[0]>0.0:
            _found_resolution = True
            #print "_found_resolution",_found_resolution
            #print "data1D.dx[0]",data1D.dx[0],data1D.dxl[0]
    # If we found resolution smearing data, return a QSmearer
    if _found_resolution == True:
        return QSmearer(data1D)

    # Look for slit smearing data
    _found_slit = False
    if data1D.dxl is not None and len(data1D.dxl)==len(data1D.x) \
        and data1D.dxw is not None and len(data1D.dxw)==len(data1D.x):
        
        # Check that we have non-zero data
        if data1D.dxl[0]>0.0 or data1D.dxw[0]>0.0:
            _found_slit = True
        
        # Sanity check: all data should be the same as a function of Q
        for item in data1D.dxl:
            if data1D.dxl[0] != item:
                _found_resolution = False
                break
            
        for item in data1D.dxw:
            if data1D.dxw[0] != item:
                _found_resolution = False
                break
    # If we found slit smearing data, return a slit smearer
    if _found_slit == True:
        return SlitSmearer(data1D)
    
    return None
            

class _BaseSmearer(object):
    
    def __init__(self):
        self.nbins = 0
        self._weights = None
        ## Internal flag to keep track of C++ smearer initialization
        self._init_complete = False
        self._smearer = None
        
    def __deepcopy__(self, memo={}):
        """
            Return a valid copy of self.
            Avoid copying the _smearer C object and force a matrix recompute
            when the copy is used.  
        """
        result = _BaseSmearer()
        result.nbins = self.nbins
        return result

        
    def _compute_matrix(self): return NotImplemented

    def get_bin_range(self, q_min=None, q_max=None):
        """
            @param q_min: minimum q-value to smear
            @param q_max: maximum q-value to smear 
        """
        # If this is the first time we call for smearing,
        # initialize the C++ smearer object first
        if not self._init_complete:
            self._initialize_smearer()
            
        if q_min == None:
            q_min = self.min
        
        if q_max == None:
            q_max = self.max
        
        _qmin_unsmeared, _qmax_unsmeared = self.get_unsmeared_range(q_min, q_max)
        
        _first_bin = None
        _last_bin  = None

        step = (self.max-self.min)/(self.nbins-1.0)
        try:
            for i in range(self.nbins):
                q_i = smearer.get_q(self._smearer, i)
                if (q_i >= _qmin_unsmeared) and (q_i <= _qmax_unsmeared):
                    # Identify first and last bin
                    if _first_bin is None:
                        _first_bin = i
                    else:
                        _last_bin  = i
        except:
            raise RuntimeError, "_BaseSmearer.get_bin_range: error getting range\n  %s" % sys.exc_value
               
        return _first_bin, _last_bin

    def __call__(self, iq_in, first_bin=0, last_bin=None):
        """
            Perform smearing
        """
        # If this is the first time we call for smearing,
        # initialize the C++ smearer object first
        if not self._init_complete:
            self._initialize_smearer()
             
        # Get the max value for the last bin
        if last_bin is None or last_bin>=len(iq_in):
            last_bin = len(iq_in)-1
        # Check that the first bin is positive
        if first_bin<0:
            first_bin = 0
            
        # Sanity check
        if len(iq_in) != self.nbins:
            raise RuntimeError, "Invalid I(q) vector: inconsistent array length %d != %s" % (len(iq_in), str(self.nbins))
             
        # Storage for smeared I(q)   
        iq_out = numpy.zeros(self.nbins)
        smear_output = smearer.smear(self._smearer, iq_in, iq_out, first_bin, last_bin)
        if smear_output < 0:
            raise RuntimeError, "_BaseSmearer: could not smear, code = %g" % smear_output
        return iq_out
    
class _SlitSmearer(_BaseSmearer):
    """
        Slit smearing for I(q) array
    """
    
    def __init__(self, nbins=None, width=None, height=None, min=None, max=None):
        """
            Initialization
            
            @param iq: I(q) array [cm-1]
            @param width: slit width [A-1]
            @param height: slit height [A-1]
            @param min: Q_min [A-1]
            @param max: Q_max [A-1]
        """
        _BaseSmearer.__init__(self)
        ## Slit width in Q units
        self.width  = width
        ## Slit height in Q units
        self.height = height
        ## Q_min (Min Q-value for I(q))
        self.min    = min
        ## Q_max (Max Q_value for I(q))
        self.max    = max
        ## Number of Q bins 
        self.nbins  = nbins
        ## Number of points used in the smearing computation
        self.npts   = 1000
        ## Smearing matrix
        self._weights = None
        self.qvalues  = None
        
    def _initialize_smearer(self):
        """
            Initialize the C++ smearer object.
            This method HAS to be called before smearing
        """
        #self._smearer = smearer.new_slit_smearer(self.width, self.height, self.min, self.max, self.nbins)
        self._smearer = smearer.new_slit_smearer_with_q(self.width, self.height, self.qvalues)
        self._init_complete = True

    def get_unsmeared_range(self, q_min, q_max):
        """
            Determine the range needed in unsmeared-Q to cover
            the smeared Q range
        """
        # Range used for input to smearing
        _qmin_unsmeared = q_min
        _qmax_unsmeared = q_max 
        try:
            _qmin_unsmeared = self.min
            _qmax_unsmeared = self.max
        except:
            logging.error("_SlitSmearer.get_bin_range: %s" % sys.exc_value)
        return _qmin_unsmeared, _qmax_unsmeared

class SlitSmearer(_SlitSmearer):
    """
        Adaptor for slit smearing class and SANS data
    """
    def __init__(self, data1D):
        """
            Assumption: equally spaced bins of increasing q-values.
            
            @param data1D: data used to set the smearing parameters
        """
        # Initialization from parent class
        super(SlitSmearer, self).__init__()
        
        ## Slit width
        self.width = 0
        if data1D.dxw is not None and len(data1D.dxw)==len(data1D.x):
            self.width = data1D.dxw[0]
            # Sanity check
            for value in data1D.dxw:
                if value != self.width:
                    raise RuntimeError, "Slit smearing parameters must be the same for all data"
                
        ## Slit height
        self.height = 0
        if data1D.dxl is not None and len(data1D.dxl)==len(data1D.x):
            self.height = data1D.dxl[0]
            # Sanity check
            for value in data1D.dxl:
                if value != self.height:
                    raise RuntimeError, "Slit smearing parameters must be the same for all data"
        
        ## Number of Q bins
        self.nbins = len(data1D.x)
        ## Minimum Q 
        self.min = min(data1D.x)
        ## Maximum
        self.max = max(data1D.x)
        ## Q-values
        self.qvalues = data1D.x
        

class _QSmearer(_BaseSmearer):
    """
        Perform Gaussian Q smearing
    """
        
    def __init__(self, nbins=None, width=None, min=None, max=None):
        """
            Initialization
            
            @param nbins: number of Q bins
            @param width: array standard deviation in Q [A-1]
            @param min: Q_min [A-1]
            @param max: Q_max [A-1]
        """
        _BaseSmearer.__init__(self)
        ## Standard deviation in Q [A-1]
        self.width  = width
        ## Q_min (Min Q-value for I(q))
        self.min    = min
        ## Q_max (Max Q_value for I(q))
        self.max    = max
        ## Number of Q bins 
        self.nbins  = nbins
        ## Smearing matrix
        self._weights = None
        self.qvalues  = None
        
    def _initialize_smearer(self):
        """
            Initialize the C++ smearer object.
            This method HAS to be called before smearing
        """
        #self._smearer = smearer.new_q_smearer(numpy.asarray(self.width), self.min, self.max, self.nbins)
        self._smearer = smearer.new_q_smearer_with_q(numpy.asarray(self.width), self.qvalues)
        self._init_complete = True
        
    def get_unsmeared_range(self, q_min, q_max):
        """
            Determine the range needed in unsmeared-Q to cover
            the smeared Q range
            Take 3 sigmas as the offset between smeared and unsmeared space
        """
        # Range used for input to smearing
        _qmin_unsmeared = q_min
        _qmax_unsmeared = q_max 
        try:
            offset = 3.0*max(self.width)
            _qmin_unsmeared = max([self.min, q_min-offset])
            _qmax_unsmeared = min([self.max, q_max+offset])
        except:
            logging.error("_QSmearer.get_bin_range: %s" % sys.exc_value)
        return _qmin_unsmeared, _qmax_unsmeared
        
        
        
class QSmearer(_QSmearer):
    """
        Adaptor for Gaussian Q smearing class and SANS data
    """
    def __init__(self, data1D):
        """
            Assumption: equally spaced bins of increasing q-values.
            
            @param data1D: data used to set the smearing parameters
        """
        # Initialization from parent class
        super(QSmearer, self).__init__()
        
        ## Resolution
        self.width = numpy.zeros(len(data1D.x))
        if data1D.dx is not None and len(data1D.dx)==len(data1D.x):
            self.width = data1D.dx
        
        ## Number of Q bins
        self.nbins = len(data1D.x)
        ## Minimum Q 
        self.min = min(data1D.x)
        ## Maximum
        self.max = max(data1D.x)
        ## Q-values
        self.qvalues = data1D.x


if __name__ == '__main__':
    x = 0.001*numpy.arange(1,11)
    y = 12.0-numpy.arange(1,11)
    print x
    #for i in range(10): print i, 0.001 + i*0.008/9.0 
    #for i in range(100): print i, int(math.floor( (i/ (100/9.0)) )) 

    
    s = _SlitSmearer(nbins=10, width=0.0, height=0.005, min=0.001, max=0.010)
    #s = _QSmearer(nbins=10, width=0.001, min=0.001, max=0.010)
    s._compute_matrix()

    sy = s(y)
    print sy
    
    if True:
        for i in range(10):
            print x[i],y[i], sy[i]
            #print q, ' : ', s.weight(q), s._compute_iq(q) 
            #print q, ' : ', s(q), s._compute_iq(q) 
            #s._compute_iq(q) 




