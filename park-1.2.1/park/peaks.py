# This program is public domain
"""  
A park model implementing a multipeak fitter.

*** WARNING *** this example was used to inform the design process,
and has not yet been updated to correspond to the current implementation.
Do not use this as a tutorial.

This is an example model showing how to put together a multi-part
fit objective function.

:group main: Peaks
:group peaks: Gaussian, Lorentzian, Voigt
:group backgrounds: Constant, Quadratic, Linear
"""
import numpy
import park

class Peaks(park.Model): 
    """Peak fitter"""
    # Increment the minor version when adding new functions
    # Increment the major version if refactoring the class
    __version__ = "0.9"
    peak_types = {}

    def __init__(self, datafile=None):
        """
        Create a new multipeak model.  If datafile is present it will
        be loaded directly.  If not, then it can be set later with
        self.data.load(datafile), or replaced with a specialized
        data loader for the particular instrument.
        """
        # The initializer creates self.parameterset which will hold
        # the set of fitting parameters for all models.  It will also
        # define self.data = park.data.Data1D() which computes the
        # residuals given an eval function.
        park.Model.__init__(self,filename=datafile)
        self.parameterset = park.ParameterSet()
        self.peaks = {}
        self.peaknum = 0

    def eval(self, x):
        """
        Returns the raw theory value at x, unconvoluted and unweighted.
        
        The residuals will be calculated by park.Model.residuals by
        calling 
        """
        x = self.data[0]
        y = numpy.empty(x.shape)
        for name,peak in self.peaks.itervalues():
            y += peak(x)
        return y
        
    def add_peak(self, type, name=None, **kw):
        """ 
        Add a peak to the model.
        
        The name of the peak is used to distinguish it from other peaks 
        in the model, and appears as part of the parameter name in
        constraint expressions.  For example, if name is 'P3' and this
        is part of model 'M1' then the sigma parameter of a gaussian
        peak would be 'M1.P3.sigma'.

        The peak can be specified either by peak type and initial arguments
        or by the peak itself, which is a function of x with a parameters 
        attribute.
        
        Available peak types include:
            gaussian(scale=1, center=0, sigma=1) 
                = scale exp ( -0.5 (x-center)**2 / sigma**2 )
            lorentzian(scale=1, center=0, gamma=1) 
                = scale/pi gamma / ((x-center)**2 + gamma**2))
            voigt(scale=1, center=0, sigma=1, gamma=1)
                = scale (lorentzian(mu,gamma) * gaussian(mu,sigma))(x-center)
                where * represents convolution
        
        Available background functions include:
            constant(C=0)
                = C
            slope(C=0, B=1)
                = B x + C
            quadratic(A=1, B=0, C=0)
                = A x**2 + B x + C

        Additional peak types can be registered.  The complete dictionary
        of available types is in Peaks.peak_types.
        """
        self.peaknum
        if name == None: name = 'P'+str(self.peaknum)
        if isinstance(type,basestring):
            peak = self.peak_types[type](**kw)
        else:
            type = peak
        self.peaks[name] = peak
        self.parameters[name] = peak.parameters
        setattr(self,name,peak)

    def remove_peak(self, name):
        """
        Remove the named peak from the model.
        """
        del self.peaks[name]
        del self.parameterset[name]

    @classmethod
    def register_peak_generator(cls, type, factory):
        """
        Register a new peak generator.  This will return a callable
        object with a parameter set that can be used in the peak
        fitting class.

        The individual peak functions a number of attributes:
        
        __name__
            the name to be displayed in the list of peaks; the
            default is __class__.__name__
        __factory__
            the name of a factory function in the python
            namespace which returns a new peak.  These parameters
            will be set from the stored parameter list when the
            peak model is reloaded.  This can be omitted if it
            is simply the module and name of the class.
        __doc__
            the tool tip to be displayed with the peak
        __call__(x)
            evaluate the peak function at x
        """
        cls.peak_types[type]=factory



# ================== Peaks and backgrounds ===================
class Gaussian(object):
    """Gaussian peak: scale exp ( -0.5 (x-center)**2 / sigma**2 )"""
    def __init__(self, name, scale=1., center=0, sigma=1):
        park.define_parameters(name, ['scale','center','sigma'],
                               scale=scale,center=center,sigma=sigma)
        self.parameters['scale'].deriv = self.dscale
        self.parameters['center'].deriv = self.dcenter
        self.parameters['sigma'].deriv = self.dsigma
    def __call__(self, x):
        return self.scale * numpy.exp(-((x-self.center)/self.sigma)**2)
    def dscale(self, x):
        return self(x)/self.scale
    def dcenter(self, x):
        return 2*(x-self.center)/self.sigma*self(x)
    def dsigma(self, x):
        return 2*(x-self.center)/self.sigma**3*self(x)

class Lorentzian(object):
    """Lorentzian peak (HWHM): scale/pi  gamma/((x-center)**2 + gamma**2)"""
    def __init__(self, name, scale=1., center=0, gamma=1):
        park.define_parameters(name, ['scale','center','gamma'],
                               scale=scale,center=center,gamma=gamma)
        self.parameters['scale'].deriv = self.dscale
        self.parameters['center'].deriv = self.dcenter
        self.parameters['gamma'].deriv = self.dgamma
    def __call__(self, x):
        return self.scale/numpy.pi * self.gamma/((x-self.center)**2 + self.gamma**2)
    def dscale(self, x):
        return self(x)/self.scale
    def dcenter(self, x):
        return 2*(x-self.center)/((x-self.center)**2+self.gamma**2)*self(x)
    def dgamma(self, x):
        return self(x)*(1/self.gamma - self.gamma/((x-self.center)**2 + self.gamma**2))

class Voigt(object):
    """Voigt peak (HWHM,sigma): A [G(sigma) * L(gamma)](x-center)"""
    def __init__(self, name, scale=1, center=0, sigma=1, gamma=1):
        park.define_parameters(name, ['scale','center','sigma','gamma'],
                               scale=scale, center=center, sigma=sigma,
                               gamma=gamma)
    def __call__(self, x):
        return self.scale*voigt(x-self.center, 
                                sigma=self.sigma, gamma=self.gamma)

class Quadratic(object):
    """Quadratic background: A x**2 + B x + C"""
    name = "Background: quadratic"
    def __init__(self, name, A=1, B=0, C=0):
        park.define_parameters(name, ['A', 'B', 'C'], A=A, B=B, C=C)
        self.parameters['A'].deriv = self.dA
        self.parameters['B'].deriv = self.dB
        self.parameters['C'].deriv = self.dC
    def __call__(self, x):
        return numpy.polyval([self.a.value, self.b.value, self.c.value],x)
    def dA(self, x): return x**2
    def dB(self, x): return x
    def dC(self, x): return numpy.ones(x.shape)

class Linear(object):
    """Linear background: B x**2 + C"""
    name = "Background: linear"
    def __init__(self, name, B=0, C=0):
        park.define_parameters(name, ['B', 'C'], B=B, C=C)
        self.parameters['B'].deriv = self.dB
        self.parameters['C'].deriv = self.dC
    def __call__(self, x):
        return numpy.polyval([self.a.value, self.b.value, self.c.value],x)
    def dB(self, x): return x
    def dC(self, x): return numpy.ones(x.shape)

class Constant(object):
    """Constant background: C"""
    name = "Background: constant"
    def __init__(self, name, C=0):
        park.define_parameters(name, ['C'], C=C)
        self.parameters['C'].deriv = self.dC
    def __call__(self, x):
        return numpy.polyval([self.a.value, self.b.value, self.c.value],x)
    def dC(self, x): return numpy.ones(x.shape)


def voigt(x, sigma, gamma):
    """
    Return the voigt function, which is the convolution of a Lorentz
    function with a Gaussian.
    
    :Parameters:
     gamma : real
      The half-width half-maximum of the Lorentzian
     sigma : real
      The 1-sigma width of the Gaussian, which is one standard deviation.

    Ref: W.I.F. David, J. Appl. Cryst. (1986). 19, 63-64
    
    Note: adjusted to use stddev and HWHM rather than FWHM parameters
    """
    # wofz function = w(z) = Fad[d][e][y]eva function = exp(-z**2)erfc(-iz)
    from scipy.special import wofz
    z = (x+1j*gamma)/(sigma*sqrt(2))
    V = wofz(z)/(sqrt(2*pi)*sigma)
    return V.real


def init():
    """
    Register peak types with the Peaks model.
    """
    for cls in [Gaussian, Lorentzian, Voigt, Quadratic, Linear, Constant]:
        Peaks.register_peak_generator(cls.__name__,cls)
init()

# ========================================

def test():
    x = numpy.linspace(-5,5,10)
    
    pass

if __name__ == "__main__": test()
