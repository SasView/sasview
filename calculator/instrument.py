"""
This module is a small tool to allow user to 
control instrumental parameters 
"""
import numpy

# defaults in cgs unit
_SAMPLE_A_SIZE = [1.27]
_SOURCE_A_SIZE = [3.81] 
_SAMPLE_DISTANCE = [1627, 0] 
_SAMPLE_OFFSET = [0, 0] 
_SAMPLE_SIZE = [2.54] 
_SAMPLE_THICKNESS = 0.2  
_D_DISTANCE = [1000, 0] 
_D_SIZE = [128, 128]
_D_PIX_SIZE = [0.5, 0.5]  

_MIN = 0.0
_MAX = 30.0
_INTENSITY = 368428
_WAVE_LENGTH = 6.0
_WAVE_SPREAD = 0.125
_MASS = 1.67492729E-24 #[gr]
X_VAL = numpy.linspace(0, 30, 310)
_LAMBDA_ARRAY = [[0, 5, 10, 15, 20, 25, 30], [1, 1, 1, 1, 1, 1, 1]]

class Aperture(object):
    """
    An object class that defines the aperture variables
    """
    def __init__(self):
        
        # assumes that all aligned at the centers
        # aperture_size [diameter] for pinhole, [dx, dy] for rectangular
        self.sample_size = _SAMPLE_A_SIZE
        self.source_size = _SOURCE_A_SIZE
        self.sample_distance = _SAMPLE_DISTANCE
        
    def set_source_size(self, size =[]):
        """
        Set the source aperture size
        """
        if len(size) == 0:
            self.source_size = 0.0 
        else:
            self.source_size = size
            validate(size[0])
    def set_sample_size(self, size =[]):
        """
        Set the sample aperture size
        """
        if len(size) == 0:
            self.sample_size = 0.0 
        else:
            self.sample_size = size
            validate(size[0])
            
    def set_sample_distance(self, distance = []):
        """
        Set the sample aperture distance
        """
        if len(distance) == 0:
            self.sample_distance = 0.0 
        else:
            self.sample_distance = distance
            validate(distance[0])
        
   
class Sample(object):
    """
    An object class that defines the sample variables
    """
    def __init__(self):
        
        # assumes that all aligned at the centers
        # source2sample or sample2detector distance
        self.distance = _SAMPLE_OFFSET
        self.size = _SAMPLE_SIZE
        self.thickness = _SAMPLE_THICKNESS

    
    def set_size(self, size =[]):
        """
        Set the sample size
        """
        if len(size) == 0:
            self.sample_size = 0.0 
        else:
            self.sample_size = size
            validate(size[0])
            
    def set_thickness(self, thickness = 0.0):
        """
        Set the sample thickness
        """
        self.thickness = thickness
        validate(thickness)
    
    def set_distance(self, distance = []):
        """
        Set the sample distance
        """
        if len(distance) == 0:
            self.distance = 0.0 
        else:
            self.distance = distance
            if distance[0] != 0.0:
                validate(distance[0])
        
 
class Detector(object):
    """
    An object class that defines the detector variables
    """
    def __init__(self):
        
        # assumes that all aligned at the centers
        # source2sample or sample2detector distance
        self.distance = _D_DISTANCE
        self.size = _D_SIZE
        self.pix_size = _D_PIX_SIZE

    
        
    def set_size(self, size =[]):
        """
        Set the detector  size
        """
        if len(size) == 0:
            self.size = 0
        else:
            self.size = size
            validate(size[0])
            
    def set_pix_size(self, size = []):
        """
        Set the detector pix_size
        """
        if len(size) == 0:
            self.pix_size = 0 
        else:
            self.pix_size = size
            validate(size[0])
    
    def set_distance(self, distance = []):
        """
        Set the detector distance
        """
        if len(distance) == 0:
            self.distance = 0
        else:
            self.distance = distance
            validate(distance[0])
    
        
class Neutron(object):
    """
    An object that defines the wavelength variables
    """
    def __init__(self):
        
        # intensity in counts/sec
        self.intensity = _INTENSITY
        # neutron mass in cgs unit
        self.mass = _MASS
        # wavelength spectrum 
        self.spectrum = []
        # wavelength
        self.wavelength = _WAVE_LENGTH
        # wavelength spread (FWHM)
        self.wavelength_spread = _WAVE_SPREAD
        # mean wavelength
        self.mean = _WAVE_LENGTH
        # wavelength = distribution after velocity selector
        self.peak = []
        # std of of the spectrum
        self.std = None
        # min max range of the spectrum
        self.min = _MIN
        self.max = _MAX
        # x-range of the spectrum
        self.x_val = X_VAL
        # default distribution function
        # ex., 'gaussian', or an array
        self.func = _LAMBDA_ARRAY
        # default unit of the thickness
        self.wavelength_unit = 'A'
        
    def set_intensity(self, intensity = 368428):
        """
        Sets the intensity in counts/sec
        """
        self.intensity = intensity  
        validate(intensity) 
            
    def set_wavelength(self, wavelength = _WAVE_LENGTH):
        """
        Sets the wavelength
        """
        self.wavelength = wavelength
        validate(wavelength)

    def set_mass(self, mass = _MASS):
        """
        Sets the wavelength
        """
        self.mass = mass
        validate(mass)
        
    def set_wavelength_spread(self, spread = _WAVE_SPREAD):
        """
        Sets the wavelength spread
        """
        self.wavelength_spread = spread
        if spread != 0.0:
            validate(spread)
        
    def get_intensity(self):
        """
        To get the value of intensity
        """
        return self.intensity
        
    def get_wavelength(self):
        """
        To get the value of wavelength
        """
        return self.wavelength

    def get_mass(self):
        """
        To get the neutron mass
        """
        return self.mass
    
    def get_wavelength_spread(self):
        """
        To get the value of wavelength spread
        """
        return self.wavelength_spread
    
    def get_ramdom_value(self):
        """
        To get the value of wave length
        """
        return self.wavelength
    
    def _set_mean(self):
        """
        To get mean value of wavelength
        """
        mean_value = numpy.mean(self.peak[0]*
                                self.peak[1])
        self.mean = mean_value

        
    def get_mean_peakvalue(self):
        """
        To get mean value of wavelength
        """
        mean_value = numpy.mean(self.peak[1])
        return mean_value
            
    def get_spectrum(self):
        """
        To get the wavelength spectrum
        """
        return self.spectrum
    
    def plot_spectrum(self):
        """
        To plot the wavelength spactrum
        : requirment: matplotlib.pyplot
        """
        try:
            import matplotlib.pyplot as plt
            plt.plot(self.x_val, self.spectrum, linewidth = 2, color = 'r')
            plt.legend(['Spectrum'], loc = 'best')
            plt.show()
        except:
            raise RuntimeError, "Can't import matplotlib required to plot..."
        
    def plot_peak(self):
        """
        To plot the wavelength peak spactrum
        : requirment: matplotlib.pyplot
        """
        try:
            min = self.mean * (1 - self.wavelength_spread)
            max = self.mean * (1 + self.wavelength_spread)
            x_val =   numpy.linspace(min, max, 310)
            import matplotlib.pyplot as plt
            plt.plot(x_val, self.peak, linewidth = 2, color = 'r')
            plt.legend(['peak'], loc = 'best')
            plt.show()
        except:
            raise RuntimeError, "Can't import matplotlib required to plot..."

def validate(value = None):
    """
    Check if the value is folat > 0.0
    
    :return value: True / False
    """
    try:
        val = float(value)
        if val >= 0:
            val = True
        else:
            val = False
    except:
        val = False
    #if not val:
    #    raise ValueError, "Got improper value..."