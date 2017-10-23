"""
This module is a small tool to allow user to
control instrumental parameters
"""
import numpy as np

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
_MAX = 50.0
_INTENSITY = 368428
_WAVE_LENGTH = 6.0
_WAVE_SPREAD = 0.125
_MASS = 1.67492729E-24  # [gr]
_LAMBDA_ARRAY = [[0, 1e+16], [_INTENSITY, _INTENSITY]]


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

    def set_source_size(self, size=[]):
        """
        Set the source aperture size
        """
        if len(size) == 0:
            self.source_size = 0.0
        else:
            self.source_size = size
            validate(size[0])

    def set_sample_size(self, size=[]):
        """
        Set the sample aperture size
        """
        if len(size) == 0:
            self.sample_size = 0.0
        else:
            self.sample_size = size
            validate(size[0])

    def set_sample_distance(self, distance=[]):
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

    def set_size(self, size=[]):
        """
        Set the sample size
        """
        if len(size) == 0:
            self.size = 0.0
        else:
            self.size = size
            validate(size[0])

    def set_thickness(self, thickness=0.0):
        """
        Set the sample thickness
        """
        self.thickness = thickness
        validate(thickness)

    def set_distance(self, distance=[]):
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

    def set_size(self, size=[]):
        """
        Set the detector  size
        """
        if len(size) == 0:
            self.size = 0
        else:
            self.size = size
            validate(size[0])

    def set_pix_size(self, size=[]):
        """
        Set the detector pix_size
        """
        if len(size) == 0:
            self.pix_size = 0
        else:
            self.pix_size = size
            validate(size[0])

    def set_distance(self, distance=[]):
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

        # neutron mass in cgs unit
        self.mass = _MASS

        # wavelength
        self.wavelength = _WAVE_LENGTH
        # wavelength spread (FWHM)
        self.wavelength_spread = _WAVE_SPREAD
        # wavelength spectrum
        self.spectrum = self.get_default_spectrum()
        # intensity in counts/sec
        self.intensity = np.interp(self.wavelength,
                                      self.spectrum[0],
                                      self.spectrum[1],
                                      0.0,
                                      0.0)
        # min max range of the spectrum
        self.min = min(self.spectrum[0])
        self.max = max(self.spectrum[0])
        # wavelength band
        self.band = [self.min, self.max]

        # default unit of the thickness
        self.wavelength_unit = 'A'

    def set_full_band(self):
        """
        set band to default value
        """
        self.band = self.spectrum

    def set_spectrum(self, spectrum):
        """
        Set spectrum

        :param spectrum: numpy array
        """
        self.spectrum = spectrum
        self.setup_spectrum()

    def setup_spectrum(self):
        """
        To set the wavelength spectrum, and intensity, assumes
        wavelength is already within the spectrum
        """
        spectrum = self.spectrum
        intensity = np.interp(self.wavelength,
                                 spectrum[0],
                                 spectrum[1],
                                 0.0,
                                 0.0)
        self.set_intensity(intensity)
        # min max range of the spectrum
        self.min = min(self.spectrum[0])
        self.max = max(self.spectrum[0])
        # set default band
        self.set_band([self.min, self.max])

    def set_band(self, band=[]):
        """
        To set the wavelength band

        :param band: array of [min, max]
        """
        # check if the wavelength is in range
        if min(band) < self.min or max(band) > self.max:
            raise ValueError("band out of range")
        self.band = band

    def set_intensity(self, intensity=368428):
        """
        Sets the intensity in counts/sec
        """
        self.intensity = intensity
        validate(intensity)

    def set_wavelength(self, wavelength=_WAVE_LENGTH):
        """
        Sets the wavelength
        """
        # check if the wavelength is in range
        if wavelength < min(self.band) or wavelength > max(self.band):
            raise ValueError("wavelength out of range")
        self.wavelength = wavelength
        validate(wavelength)
        self.intensity = np.interp(self.wavelength,
                                      self.spectrum[0],
                                      self.spectrum[1],
                                      0.0,
                                      0.0)

    def set_mass(self, mass=_MASS):
        """
        Sets the wavelength
        """
        self.mass = mass
        validate(mass)

    def set_wavelength_spread(self, spread=_WAVE_SPREAD):
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

    def get_spectrum(self):
        """
        To get the wavelength spectrum
        """
        return self.spectrum

    def get_default_spectrum(self):
        """
        get default spectrum
        """
        return np.array(_LAMBDA_ARRAY)

    def get_band(self):
        """
        To get the wavelength band
        """
        return self.band

    def plot_spectrum(self):
        """
        To plot the wavelength spactrum
        : requirment: matplotlib.pyplot
        """
        try:
            import matplotlib.pyplot as plt
            plt.plot(self.spectrum[0], self.spectrum[1], linewidth=2, color='r')
            plt.legend(['Spectrum'], loc='best')
            plt.show()
        except:
            raise RuntimeError("Can't import matplotlib required to plot...")


class TOF(Neutron):
    """
    TOF: make list of wavelength and wave length spreads
    """
    def __init__(self):
        """
        Init
        """
        Neutron.__init__(self)
        #self.switch = switch
        self.wavelength_list = [self.wavelength]
        self.wavelength_spread_list = [self.wavelength_spread]
        self.intensity_list = self.get_intensity_list()

    def get_intensity_list(self):
        """
        get list of the intensity wrt wavelength_list
        """
        out = np.interp(self.wavelength_list,
                           self.spectrum[0],
                           self.spectrum[1],
                           0.0,
                           0.0)
        return out

    def get_wave_list(self):
        """
        Get wavelength and wavelength_spread list
        """
        return self.wavelength_list, self.wavelength_spread_list

    def set_wave_list(self, wavelength=[]):
        """
        Set wavelength list

        :param wavelength: list of wavelengths
        """
        self.wavelength_list = wavelength

    def set_wave_spread_list(self, wavelength_spread=[]):
        """
        Set wavelength_spread list

        :param wavelength_spread: list of wavelength spreads
        """
        self.wavelength_spread_list = wavelength_spread


def validate(value=None):
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
