
#####################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#See the license text in license.txt
#copyright 2008, University of Tennessee
######################################################################
import numpy
import math
import logging
import sys
import sans.models.sans_extension.smearer as smearer 
from sans.models.smearing_2d import Smearer2D

def smear_selection(data1D, model = None):
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
    
    :param data1D: Data1D object
    :param model: sans.model instance
    """
    # Sanity check. If we are not dealing with a SANS Data1D
    # object, just return None
    if  data1D.__class__.__name__ not in ['Data1D', 'Theory1D']:
        if data1D == None:
            return None
        elif data1D.dqx_data == None or data1D.dqy_data == None:
            return None
        return Smearer2D(data1D)
    
    if  not hasattr(data1D, "dx") and not hasattr(data1D, "dxl")\
         and not hasattr(data1D, "dxw"):
        return None
    
    # Look for resolution smearing data
    _found_resolution = False
    if data1D.dx is not None and len(data1D.dx) == len(data1D.x):
        
        # Check that we have non-zero data
        if data1D.dx[0] > 0.0:
            _found_resolution = True
            #print "_found_resolution",_found_resolution
            #print "data1D.dx[0]",data1D.dx[0],data1D.dxl[0]
    # If we found resolution smearing data, return a QSmearer
    if _found_resolution == True:
        return QSmearer(data1D, model)

    # Look for slit smearing data
    _found_slit = False
    if data1D.dxl is not None and len(data1D.dxl) == len(data1D.x) \
        and data1D.dxw is not None and len(data1D.dxw) == len(data1D.x):
        
        # Check that we have non-zero data
        if data1D.dxl[0] > 0.0 or data1D.dxw[0] > 0.0:
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
        return SlitSmearer(data1D, model)
    return None
            

class _BaseSmearer(object):
    
    def __init__(self):
        self.nbins = 0
        self.nbins_low = 0
        self.nbins_high = 0
        self._weights = None
        ## Internal flag to keep track of C++ smearer initialization
        self._init_complete = False
        self._smearer = None
        self.model = None
        
    def __deepcopy__(self, memo={}):
        """
        Return a valid copy of self.
        Avoid copying the _smearer C object and force a matrix recompute
        when the copy is used.  
        """
        result = _BaseSmearer()
        result.nbins = self.nbins
        return result

    def _compute_matrix(self):
        """
        """
        return NotImplemented

    def get_bin_range(self, q_min=None, q_max=None):
        """
        
        :param q_min: minimum q-value to smear
        :param q_max: maximum q-value to smear
         
        """
        # If this is the first time we call for smearing,
        # initialize the C++ smearer object first
        if not self._init_complete:
            self._initialize_smearer()
        if q_min == None:
            q_min = self.min
        if q_max == None:
            q_max = self.max

        _qmin_unsmeared, _qmax_unsmeared = self.get_unsmeared_range(q_min,
                                                                     q_max)
        _first_bin = None
        _last_bin  = None

        #step = (self.max - self.min) / (self.nbins - 1.0)
        # Find the first and last bin number in all extrapolated and real data
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
            msg = "_BaseSmearer.get_bin_range: "
            msg += " error getting range\n  %s" % sys.exc_value
            raise RuntimeError, msg
   
        #  Find the first and last bin number only in the real data
        _first_bin, _last_bin = self._get_unextrapolated_bin( \
                                        _first_bin, _last_bin)

        return _first_bin, _last_bin

    def __call__(self, iq_in, first_bin = 0, last_bin = None):
        """
        Perform smearing
        """
        # If this is the first time we call for smearing,
        # initialize the C++ smearer object first
        if not self._init_complete:
            self._initialize_smearer()

        if last_bin is None or last_bin >= len(iq_in):
            last_bin = len(iq_in) - 1
        # Check that the first bin is positive
        if first_bin < 0:
            first_bin = 0

        # With a model given, compute I for the extrapolated points and append
        # to the iq_in
        iq_in_temp = iq_in
        if self.model != None:
            temp_first, temp_last = self._get_extrapolated_bin( \
                                                        first_bin, last_bin)
            if self.nbins_low > 0:
                iq_in_low = self.model.evalDistribution( \
                                    numpy.fabs(self.qvalues[0:self.nbins_low]))
            iq_in_high = self.model.evalDistribution( \
                                            self.qvalues[(len(self.qvalues) - \
                                            self.nbins_high - 1):])
            # Todo: find out who is sending iq[last_poin] = 0.
            if iq_in[len(iq_in) - 1] == 0:
                iq_in[len(iq_in) - 1] = iq_in_high[0]
            # Append the extrapolated points to the data points
            if self.nbins_low > 0:                             
                iq_in_temp = numpy.append(iq_in_low, iq_in)
            if self.nbins_high > 0:
                iq_in_temp = numpy.append(iq_in_temp, iq_in_high[1:])
        else:
            temp_first = first_bin
            temp_last = last_bin
            #iq_in_temp = iq_in

        # Sanity check
        if len(iq_in_temp) != self.nbins:
            msg = "Invalid I(q) vector: inconsistent array "
            msg += " length %d != %s" % (len(iq_in_temp), str(self.nbins))
            raise RuntimeError, msg

        # Storage for smeared I(q)   
        iq_out = numpy.zeros(self.nbins)

        smear_output = smearer.smear(self._smearer, iq_in_temp, iq_out,
                                      #0, self.nbins - 1)
                                      temp_first, temp_last)
                                      #first_bin, last_bin)
        if smear_output < 0:
            msg = "_BaseSmearer: could not smear, code = %g" % smear_output
            raise RuntimeError, msg

        temp_first = first_bin + self.nbins_low
        temp_last = self.nbins - self.nbins_high
        out = iq_out[temp_first: temp_last]

        return out
    
    def _initialize_smearer(self):
        """
        """
        return NotImplemented
            
    
    def _get_unextrapolated_bin(self, first_bin = 0, last_bin = 0):
        """
        Get unextrapolated first bin and the last bin
        
        : param first_bin: extrapolated first_bin
        : param last_bin: extrapolated last_bin
        
        : return fist_bin, last_bin: unextrapolated first and last bin
        """
        #  For first bin
        if first_bin <= self.nbins_low:
            first_bin = 0
        else:
            first_bin = first_bin - self.nbins_low
        # For last bin
        if last_bin >= (self.nbins - self.nbins_high):
            last_bin  = self.nbins - (self.nbins_high + self.nbins_low + 1)
        elif last_bin >= self.nbins_low:
            last_bin = last_bin - self.nbins_low
        else:
            last_bin = 0
        return first_bin, last_bin
    
    def _get_extrapolated_bin(self, first_bin = 0, last_bin = 0):
        """
        Get extrapolated first bin and the last bin
        
        : param first_bin: unextrapolated first_bin
        : param last_bin: unextrapolated last_bin
        
        : return first_bin, last_bin: extrapolated first and last bin
        """
        #  For the first bin
        # In the case that needs low extrapolation data
        first_bin = 0
        # For last bin
        if last_bin >= self.nbins - (self.nbins_high + self.nbins_low + 1):
            # In the case that needs higher q extrapolation data 
            last_bin = self.nbins - 1
        else:
            # In the case that doesn't need higher q extrapolation data 
             last_bin += self.nbins_low

        return first_bin, last_bin
        
class _SlitSmearer(_BaseSmearer):
    """
    Slit smearing for I(q) array
    """
    
    def __init__(self, nbins=None, width=None, height=None, min=None, max=None):
        """
        Initialization
            
        :param iq: I(q) array [cm-1]
        :param width: slit width [A-1]
        :param height: slit height [A-1]
        :param min: Q_min [A-1]
        :param max: Q_max [A-1]
        
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
        self.npts   = 3000
        ## Smearing matrix
        self._weights = None
        self.qvalues  = None
        
    def _initialize_smearer(self):
        """
        Initialize the C++ smearer object.
        This method HAS to be called before smearing
        """
        #self._smearer = smearer.new_slit_smearer(self.width,
        # self.height, self.min, self.max, self.nbins)
        self._smearer = smearer.new_slit_smearer_with_q(self.width, 
                                                    self.height, self.qvalues)
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
    def __init__(self, data1D, model = None):
        """
        Assumption: equally spaced bins of increasing q-values.
        
        :param data1D: data used to set the smearing parameters
        """
        # Initialization from parent class
        super(SlitSmearer, self).__init__()
        
        ## Slit width
        self.width = 0
        self.nbins_low = 0
        self.nbins_high = 0
        self.model = model
        if data1D.dxw is not None and len(data1D.dxw) == len(data1D.x):
            self.width = data1D.dxw[0]
            # Sanity check
            for value in data1D.dxw:
                if value != self.width:
                    msg = "Slit smearing parameters must "
                    msg += " be the same for all data"
                    raise RuntimeError, msg
        ## Slit height
        self.height = 0
        if data1D.dxl is not None and len(data1D.dxl) == len(data1D.x):
            self.height = data1D.dxl[0]
            # Sanity check
            for value in data1D.dxl:
                if value != self.height:
                    msg = "Slit smearing parameters must be"
                    msg += " the same for all data"
                    raise RuntimeError, msg
        # If a model is given, get the q extrapolation
        if self.model == None:
            data1d_x = data1D.x
        else:
            # Take larger sigma
            if self.height > self.width:
                # The denominator (2.0) covers all the possible w^2 + h^2 range
                sigma_in = data1D.dxl / 2.0
            elif self.width > 0:
                sigma_in = data1D.dxw / 2.0
            else:
                sigma_in = []

            self.nbins_low, self.nbins_high, _, data1d_x = \
                                get_qextrapolate(sigma_in, data1D.x)

        ## Number of Q bins
        self.nbins = len(data1d_x)
        ## Minimum Q 
        self.min = min(data1d_x)
        ## Maximum
        self.max = max(data1d_x)
        ## Q-values
        self.qvalues = data1d_x
        

class _QSmearer(_BaseSmearer):
    """
    Perform Gaussian Q smearing
    """
        
    def __init__(self, nbins=None, width=None, min=None, max=None):
        """
        Initialization
        
        :param nbins: number of Q bins
        :param width: array standard deviation in Q [A-1]
        :param min: Q_min [A-1]
        :param max: Q_max [A-1]
        """
        _BaseSmearer.__init__(self)
        ## Standard deviation in Q [A-1]
        self.width = width
        ## Q_min (Min Q-value for I(q))
        self.min = min
        ## Q_max (Max Q_value for I(q))
        self.max = max
        ## Number of Q bins 
        self.nbins = nbins
        ## Smearing matrix
        self._weights = None
        self.qvalues  = None
        
    def _initialize_smearer(self):
        """
        Initialize the C++ smearer object.
        This method HAS to be called before smearing
        """
        #self._smearer = smearer.new_q_smearer(numpy.asarray(self.width),
        # self.min, self.max, self.nbins)
        self._smearer = smearer.new_q_smearer_with_q(numpy.asarray(self.width),
                                                      self.qvalues)
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
            offset = 3.0 * max(self.width)
            _qmin_unsmeared = self.min#max([self.min, q_min - offset])
            _qmax_unsmeared = self.max#min([self.max, q_max + offset])
        except:
            logging.error("_QSmearer.get_bin_range: %s" % sys.exc_value)
        return _qmin_unsmeared, _qmax_unsmeared
        
    
class QSmearer(_QSmearer):
    """
    Adaptor for Gaussian Q smearing class and SANS data
    """
    def __init__(self, data1D, model = None):
        """
        Assumption: equally spaced bins of increasing q-values.
        
        :param data1D: data used to set the smearing parameters
        """
        # Initialization from parent class
        super(QSmearer, self).__init__()
        data1d_x = []
        self.nbins_low = 0
        self.nbins_high = 0
        self.model = model
        ## Resolution
        #self.width = numpy.zeros(len(data1D.x))
        if data1D.dx is not None and len(data1D.dx) == len(data1D.x):
            self.width = data1D.dx
        
        if self.model == None:
            data1d_x = data1D.x
        else:
            self.nbins_low, self.nbins_high, self.width, data1d_x = \
                                get_qextrapolate(self.width, data1D.x)

        ## Number of Q bins
        self.nbins = len(data1d_x)
        ## Minimum Q 
        self.min = min(data1d_x)
        ## Maximum
        self.max = max(data1d_x)
        ## Q-values
        self.qvalues = data1d_x

        
def get_qextrapolate(width, data_x):
    """
    Make fake data_x points extrapolated outside of the data_x points
    
    : param width: array of std of q resolution
    : param Data1D.x: Data1D.x array
    
    : return new_width, data_x_ext: extrapolated width array and x array
    
    : assumption1: data_x is ordered from lower q to higher q
    : assumption2: len(data) = len(width)
    : assumption3: the distance between the data points is more compact 
            than the size of width 
    : Todo1: Make sure that the assumptions are correct for Data1D
    : Todo2: This fixes the edge problem in Qsmearer but still needs to make 
            smearer interface 
    """
    # Length of the width
    length = len(width)
    width_low = math.fabs(width[0])   
    width_high = math.fabs(width[length -1])
    nbins_low = 0.0 
    nbins_high = 0.0
    # Compare width(dQ) to the data bin size and take smaller one as the bin 
    # size of the extrapolation; this will correct some weird behavior 
    # at the edge: This method was out (commented) 
    # because it becomes very expansive when
    # bin size is very small comparing to the width.
    # Now on, we will just give the bin size of the extrapolated points 
    # based on the width.
    # Find bin sizes
    #bin_size_low = math.fabs(data_x[1] - data_x[0])
    #bin_size_high = math.fabs(data_x[length - 1] - data_x[length - 2])
    # Let's set the bin size 1/3 of the width(sigma), it is good as long as
    # the scattering is monotonous.
    #if width_low < (bin_size_low):
    bin_size_low = width_low / 10.0
    #if width_high < (bin_size_high):
    bin_size_high = width_high / 10.0
        
    # Number of q points required below the 1st data point in order to extend
    # them 3 times of the width (std)
    if width_low > 0.0:
        nbins_low = math.ceil(3.0 * width_low / bin_size_low)
    # Number of q points required above the last data point
    if width_high > 0.0:
        nbins_high = math.ceil(3.0 * width_high / bin_size_high)
    # Make null q points        
    extra_low = numpy.zeros(nbins_low)
    extra_high = numpy.zeros(nbins_high)
    # Give extrapolated values
    ind = 0
    qvalue = data_x[0] - bin_size_low
    #if qvalue > 0:
    while(ind < nbins_low):
        extra_low[nbins_low - (ind + 1)] = qvalue
        qvalue -= bin_size_low
        ind += 1
        #if qvalue <= 0:
        #    break
    # Redefine nbins_low
    nbins_low = ind
    # Reset ind for another extrapolation
    ind = 0
    qvalue = data_x[length -1] + bin_size_high
    while(ind < nbins_high):
        extra_high[ind] = qvalue
        qvalue += bin_size_high
        ind += 1
    # Make a new qx array
    if nbins_low > 0:  
        data_x_ext = numpy.append(extra_low, data_x)
    else:
        data_x_ext = data_x
    data_x_ext = numpy.append(data_x_ext, extra_high)
    
    # Redefine extra_low and high based on corrected nbins  
    # And note that it is not necessary for extra_width to be a non-zero 
    if nbins_low > 0:     
        extra_low = numpy.zeros(nbins_low)
    extra_high = numpy.zeros(nbins_high) 
    # Make new width array
    new_width = numpy.append(extra_low, width)
    new_width = numpy.append(new_width, extra_high)
    
    # nbins corrections due to the negative q value
    nbins_low = nbins_low - len(data_x_ext[data_x_ext<=0])
    return  nbins_low, nbins_high, \
             new_width[data_x_ext>0], data_x_ext[data_x_ext>0]
    
if __name__ == '__main__':
    x = 0.001 * numpy.arange(1, 11)
    y = 12.0 - numpy.arange(1, 11)
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
            print x[i], y[i], sy[i]
            #print q, ' : ', s.weight(q), s._compute_iq(q) 
            #print q, ' : ', s(q), s._compute_iq(q) 
            #s._compute_iq(q) 




