"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2008, University of Tennessee
"""


import numpy
import math
import scipy.special

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
    if data1D.__class__.__name__ != 'Data1D' \
        or not hasattr(data1D, "dxl") or not hasattr(data1D, "dxw"):
        return None
    
    # Look for resolution smearing data
    _found_resolution = False
    if data1D.dx is not None and len(data1D.dx)==len(data1D.x):
        
        # Check that we have non-zero data
        if data1D.dx[0]>0.0:
            _found_resolution = True
        
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
        
    def _compute_matrix(self): return NotImplemented

    def __call__(self, iq):
        """
            Return the smeared I(q) value at the given q.
            The smeared I(q) is computed using a predetermined 
            smearing matrix for a particular binning.
        
            @param q: I(q) array
            @return: smeared I(q)
        """
        # Sanity check
        if len(iq) != self.nbins:
            raise RuntimeError, "Invalid I(q) vector: inconsistent array length %s <> %s" % (len(iq), self.nbins)
        
        if self._weights == None:
            self._compute_matrix()
            
        iq_smeared = numpy.zeros(self.nbins)
        # Loop over q-values
        for q_i in range(self.nbins):
            sum = 0.0
            counts = 0.0    
            
            for i in range(self.nbins):
                if iq[i]!=0 and self._weights[q_i][i]!=0:
                    sum += iq[i] * self._weights[q_i][i] 
                    counts += self._weights[q_i][i]
                    #print "i,iq[i],self._weights[q_i][i] ",i,iq[i],self._weights[q_i][i]
            iq_smeared[q_i] = sum/counts 
            #print "q_i,iq_smeared[q_i]",q_i,iq[i],iq_smeared[q_i]
            #print "iq[i],iq_smeared[q_i],sum,counts,self.nbins",iq[i], iq_smeared[q_i],sum,counts,self.nbins
        return iq_smeared    
    
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
        
    def _compute_matrix(self):
        """
            Compute the smearing matrix for the current I(q) array
        """
        weights = numpy.zeros([self.nbins, self.nbins])
        
        # Loop over all q-values
        for i in range(self.nbins):
            q = self.min + i*(self.max-self.min)/float(self.nbins-1.0)
            
            # For each q-value, compute the weight of each other q-bin
            # in the I(q) array
            npts_h = self.nbins if self.height>0 else 1 #changed self.npts=>self.nbins
            npts_w = self.nbins if self.width>0 else 1 #changed self.npts=>self.nbins
            
            # If both height and width are great than zero,
            # modify the number of points in each direction so 
            # that the total number of points is still what 
            # the user would expect (downgrade resolution)
            if npts_h>1 and npts_w>1:
                npts_h = int(math.ceil(math.sqrt(self.npts)))
                npts_w = npts_h
                
            for k in range(npts_h):
                if npts_h==1:
                    shift_h = 0
                else:
                    shift_h = self.height/(float(npts_h-1.0)) * k
                for j in range(npts_w):
                    if npts_w==1:
                        shift_w = 0
                    else:
                        shift_w = self.width/(float(npts_w-1.0)) * j
                    q_shifted = math.sqrt( ((q-shift_w)*(q-shift_w) + shift_h*shift_h) )
                    q_i = int(math.floor( (q_shifted-self.min)/((self.max-self.min)/(self.nbins -1.0)) ))
                    
                    # Skip the entries outside our I(q) range
                    #TODO: be careful with edge effect
                    if q_i<self.nbins:
                        weights[i][q_i] = weights[i][q_i]+1.0

        self._weights = weights
        return self._weights

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
        self.min = data1D.x[0]
        ## Maximum
        self.max = data1D.x[len(data1D.x)-1]        


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
        
    def _compute_matrix(self):
        """
            Compute the smearing matrix for the current I(q) array
        """
        weights = numpy.zeros([self.nbins, self.nbins])
        
        # Loop over all q-values
        step = (self.max-self.min)/float(self.nbins-1.0)
        for i in range(self.nbins):
            q = self.min + i*step
            q_min = q - 0.5*step
            q_max = q + 0.5*step
            for j in range(self.nbins):
                q_j = self.min + j*step
                
                # Compute the fraction of the Gaussian contributing
                # to the q bin between q_min and q_max
                #value =  math.exp(-math.pow((q_max-q_j),2)/(2*math.pow(self.width[j],2) ))
                #value +=  math.exp(-math.pow((q_max-q_j),2)/(2*math.pow(self.width[j],2) )) 
                value =  scipy.special.erf( (q_max-q_j)/(math.sqrt(2.0)*self.width[j]) ) 
                value -=scipy.special.erf( (q_min-q_j)/(math.sqrt(2.0)*self.width[j]) ) 
                weights[i][j] += value
                                
        self._weights = weights
        return self._weights
        
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
        self.min = data1D.x[0]
        ## Maximum
        self.max = data1D.x[len(data1D.x)-1]        


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




