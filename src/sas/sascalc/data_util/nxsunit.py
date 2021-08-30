# This program is public domain
# Author: Paul Kienzle
"""
Define unit conversion support for NeXus style units.

The unit format is somewhat complicated.  There are variant spellings
and incorrect capitalization to worry about, as well as forms such as
"mili*metre" and "1e-7 seconds".

This is a minimal implementation of units including only what I happen to
need now.  It does not support the complete dimensional analysis provided
by the package udunits on which NeXus is based, or even the units used
in the NeXus definition files.

Unlike other units packages, this package does not carry the units along with
the value but merely provides a conversion function for transforming values.

Usage example::

    import nxsunit
    u = nxsunit.Converter('mili*metre')  # Units stored in mm
    v = u(3000,'m')  # Convert the value 3000 mm into meters

NeXus example::

    # Load sample orientation in radians regardless of how it is stored.
    # 1. Open the path
    file.openpath('/entry1/sample/sample_orientation')
    # 2. scan the attributes, retrieving 'units'
    units = [for attr,value in file.attrs() if attr == 'units']
    # 3. set up the converter (assumes that units actually exists)
    u = nxsunit.Converter(units[0])
    # 4. read the data and convert to the correct units
    v = u(file.read(),'radians')

This is a standalone module, not relying on either DANSE or NeXus, and
can be used for other unit conversion tasks.

Note: minutes are used for angle and seconds are used for time.  We
cannot tell what the correct interpretation is without knowing something
about the fields themselves.  If this becomes an issue, we will need to
allow the application to set the dimension for the unit rather than
inferring the dimension from an example unit.
"""

from __future__ import division
import math
import re


__all__ = ['Converter']
DIMENSIONS = {}  # type: Dict[str, Dict[str, ConversionType]]
AMBIGUITIES = {}  # type: Dict[str, str]
PREFIX = dict(peta=1e15, tera=1e12, giga=1e9, mega=1e6, kilo=1e3, deci=1e-1, centi=1e-2, milli=1e-3, mili=1e-3,
              micro=1e-6, nano=1e-9, pico=1e-12, femto=1e-15)
SHORT_PREFIX = dict(P=1e15, T=1e12, G=1e9, M=1e6, k=1e3, d=1e-1, c=1e-2, m=1e-3, u=1e-6, n=1e-9, p=1e-12, f=1e-15)


# Limited form of units for returning objects of a specific type.
# Maybe want to do full units handling with e.g., pyre's
# unit class. For now lets keep it simple.  Note that
def _build_metric_units(unit, abbr):
    # type: (str, str) -> dict[str, float]
    """
    Construct standard SI names for the given unit.
    Builds e.g.,
        s, ns, n*s, n_s
        second, nanosecond, nano*second, nano_second
        seconds, nanoseconds, nano*seconds, nano_seconds
    Includes prefixes for femto through peta.

    Ack! Allows, e.g., Coulomb and coulomb even though Coulomb is not
    a unit because some NeXus files store it that way!

    Returns a dictionary of names and scales.
    """
    map = {}
    for name in [unit, unit.capitalize(), unit.lower(), abbr]:
        for items in [PREFIX, SHORT_PREFIX]:
            names = {}
            names.update({name: 1})
            names.update([(P + name, scale) for (P, scale) in items.items()])
            names.update([(P + '*' + name, scale) for (P, scale) in items.items()])
            names.update([(P + '_' + name, scale) for (P, scale) in items.items()])
            # Exclude pluralized abbrevs., e.g. create m(illi)(?)(*|_)(?)meters, but not milli(*|_)(?)ms or m(*|_)(?)ms
            if name != abbr:
                names.update(_build_plural_units(**names))
            map.update(names)
    return map


def _build_plural_units(**kw):
    # type: (dict[str, float]) -> dict[str, float]
    """
    Construct names for the given units.  Builds singular and plural form.
    """
    map = {}
    map.update([(name, scale) for name, scale in kw.items()])
    map.update([(name + 's', scale) for name, scale in kw.items()])
    return map


def _build_degree_units(name, symbol, conversion):
    # type: (str, str, ConversionType) -> Dict[str, ConversionType]
    """
    Builds variations on the temperature unit name, including the degree
    symbol or the word degree.
    """
    map = {}  # type: Dict[str, ConversionType]
    map[symbol] = conversion
    for s in symbol, symbol.lower():
        map['deg' + s] = conversion
        map['deg_' + s] = conversion
        map['°' + s] = conversion
    for s in name, name.capitalize(), symbol, symbol.lower():
        map[s] = conversion
        map['degree_' + s] = conversion
        map['degree' + s] = conversion
        map['degrees' + s] = conversion
    return map


def _build_inv_n_units(names, conversion, n=2):
    # type: (Sequence[str], ConversionType, int) -> Dict[str, ConversionType]
    """
    Builds variations on inverse x to the nth power units, including 1/x^n, invx^n, x^-n and x^{-n}.
    """
    map = {}  # type: Dict[str, ConversionType]
    n = int(n)
    for s in names:
        map[f'1/{s}^{n}'] = conversion
        map[f'inv{s}^{n}'] = conversion
        map[f'{s}^-{n}'] = conversion
        map[s + '^{-' + str(n) + '}'] = conversion
    return map


def _build_inv_n_metric_units(unit, abbr, n=2):
    # type: (Sequence[str], ConversionType, int) -> Dict[str, ConversionType]
    """
    Using the return from _build_metric_units, build inverse to the nth power variations on all units
    (1/x^n, invx^n, x^{-n} and x^-n)
    """
    map = {}  # type: Dict[str, ConversionType]
    meter_map = _build_metric_units(unit, abbr)
    n = int(n)
    for s, c in meter_map.items():
        conversion = 1/(math.pow(float(c), n))
        map.update(_build_inv_n_units([s], conversion, n))
    return map


def _build_all_units():
    # type: () -> None
    """
    Fill in the global variables DIMENSIONS and AMBIGUITIES for all available
    dimensions.
    """
    # Gather all the ambiguities in one spot
    AMBIGUITIES['A'] = 'distance'  # distance, current
    AMBIGUITIES['second'] = 'time'  # time, angle
    AMBIGUITIES['seconds'] = 'time'
    AMBIGUITIES['sec'] = 'time'
    AMBIGUITIES['°'] = 'angle'  # temperature, angle
    AMBIGUITIES['minute'] = 'angle'  # time, angle
    AMBIGUITIES['minutes'] = 'angle'
    AMBIGUITIES['min'] = 'angle'
    AMBIGUITIES['C'] = 'charge'  # temperature, charge
    AMBIGUITIES['F'] = 'temperature'  # temperature
    AMBIGUITIES['R'] = 'radiation'  # temperature:rankines, radiation:roentgens

    # Distance measurements
    distance = _build_metric_units('meter', 'm')
    distance.update(_build_metric_units('metre', 'm'))
    distance.update(_build_plural_units(micron=1e-6, Angstrom=1e-10))
    distance.update({'Å': 1e-10, 'A': 1e-10, 'Ang': 1e-10,  'ang': 1e-10})
    DIMENSIONS['distance'] = distance

    # Time measurements
    time = _build_metric_units('second', 's')
    time.update(_build_plural_units(minute=60, hour=3600, day=24 * 3600, week=7 * 24 * 3600))
    time.update({'sec': 1., 'min': 60., 'hr': 3600.})
    time.update({'1e-7 s': 1e-7, '1e-7 second': 1e-7, '1e-7 seconds': 1e-7})
    DIMENSIONS['time'] = time

    # Various angle measures.
    angle = _build_plural_units(
        degree=1., minute=1 / 60., second=1 / 3600.,
        arcdegree=1., arcminute=1 / 60., arcsecond=1 / 3600.,
        radian=180 / math.pi)
    # Note: shouldn't need the extra dict() in the line below, but mypy is
    # confused if we don't.
    angle.update(dict(
        deg=1., min=1 / 60., sec=1 / 3600.,
        arcdeg=1., arcmin=1 / 60., arcsec=1 / 3600.,
        angular_degree=1., angular_minute=1 / 60., angular_second=1 / 3600.,
        rad=180. / math.pi,
    ))
    angle['°'] = 1.
    DIMENSIONS['angle'] = angle

    frequency = _build_metric_units('hertz', 'Hz')
    frequency.update(_build_metric_units('Hertz', 'Hz'))
    frequency.update(_build_plural_units(rpm=1 / 60.))
    frequency.update(_build_inv_n_metric_units('second', 's', 1))
    DIMENSIONS['frequency'] = frequency

    # Note: degrees are used for angle
    temperature = _build_metric_units('kelvin', 'K')
    for k, v in temperature.items():
        # add offset 0 to all kelvin temperatures
        temperature[k] = (v, 0.)  # type: ignore
    temperature.update(_build_degree_units('celcius', 'C', (1., 273.15)))
    temperature.update(_build_degree_units('centigrade', 'C', temperature['degC']))
    temperature.update(_build_degree_units('fahrenheit', 'F', (5. / 9., 491.67 - 32)))
    temperature.update(_build_degree_units('rankine', 'R', (5. / 9., 0)))
    # special unicode symbols for fahrenheit and celcius
    temperature['℃'] = temperature['degC']
    temperature['℉'] = temperature['degF']
    DIMENSIONS['temperature'] = temperature

    # Charge
    charge = _build_metric_units('coulomb', 'C')
    charge['microAmp*hour'] = 0.0036
    DIMENSIONS['charge'] = charge

    # Resistance Units
    resistance = _build_metric_units('ohm', 'Ω')
    DIMENSIONS['resistance'] = resistance

    # Scattering length densities and inverse area units
    sld = _build_inv_n_metric_units('meter', 'm', 2)
    sld.update(_build_inv_n_units(('Å', 'A', 'Ang', 'Angstrom', 'ang', 'angstrom'), 1.0e10, 2))
    sld['10^-6 Angstrom^-2'] = 1e-6
    DIMENSIONS['sld'] = sld

    # Q units (also inverse lengths)
    Q = _build_inv_n_metric_units('meter', 'm', 1)
    Q.update(_build_inv_n_units(('Å', 'A', 'Ang', 'Angstrom', 'ang', 'angstrom'), 1.0e10, 1))
    Q['10^-3 Angstrom^-1'] = 1e-3
    DIMENSIONS['Q'] = Q

    # Inverse volume units
    scattering_volume = _build_inv_n_metric_units('meter', 'm', 3)
    scattering_volume.update(_build_inv_n_units(('Å', 'A', 'Ang', 'Angstrom', 'ang', 'angstrom'), 1.0e10, 3))
    DIMENSIONS['scattering_volume'] = scattering_volume

    # TODO: break into separate dimension blocks to allow scaling of complex units
    #  SANS units => ['A^{-2}']
    #  SESANS units => ['A^{-2}', 'cm^{-1}']
    #  Will require more complexity to scale calculations
    DIMENSIONS['SESANS'] = {'Å^{-2} cm^{-1}': 1, 'A^{-2} cm^{-1}': 1}

    # Energy units
    energy = _build_metric_units('electronvolt', 'eV')
    DIMENSIONS['energy'] = energy
    # Note: energy <=> wavelength <=> velocity requires a probe type

    # Magnetic moment units
    magnetism = _build_metric_units('tesla', 'T')
    gauss = _build_metric_units('gauss', 'G')
    gauss = dict((k, v * 1e-4) for k, v in gauss.items())
    magnetism.update(gauss)
    DIMENSIONS['magnetism'] = magnetism

    # APS files may be using 'a.u.' for 'arbitrary units'.  Other
    # facilities are leaving the units blank, using ??? or not even
    # writing the units attributes.
    unknown = {}  # type: Dict[str, ConversionType]
    unknown.update(
        {'None': 1, '???': 1, '': 1, 'A.U.': 1,  'a.u.': 1, 'arbitrary': 1, 'arbitrary units': 1,
         'Counts': 1, 'counts': 1, 'Cts': 1, 'cts': 1, 'unitless': 1, 'unknown': 1, 'Unknown': 1, 'Unk': 1}
    )
    DIMENSIONS['dimensionless'] = unknown


def standardize_units(unit):
    # type: (str) -> str
    """
    Convert supplied units to a standard format for maintainability
    :param unit: Raw unit as supplied
    :return: Unit with known, reduced values
    """
    # Convert value to a string -> Sets None to 'None'
    # Useful for GUI elements that require string values
    unit = str(unit)
    # Catch ang, angstrom, ANG, ANGSTROM, and any capitalization in between
    # Replace with 'Å'
    unit = re.sub(r'[ÅAa]ng(str[oö]m)?(s)?', 'Å', unit, flags=re.IGNORECASE)
    # Catch meter, metre, METER, METRE, and any capitalization in between
    # Replace with 'm'
    unit = re.sub(r'(met(er|re)(s)?)', 'm', unit, flags=re.IGNORECASE)
    # Catch second, sec, SECOND, SEC, and any capitalization in between
    # Replace with 's'
    unit = re.sub(r'sec(ond)?(s)?', 's', unit, flags=re.IGNORECASE)
    # Catch kelvin, KELVIN, and any capitalization in between
    # Replace with 'K'
    unit = re.sub(r'kel(vin)?(s)?', 'K', unit, flags=re.IGNORECASE)
    # Catch celcius, CELCIUS, and any capitalization in between
    # Replace with '℃'
    unit = re.sub(r'cel(cius)?', '℃', unit)
    # Catch hertz, HERTZ, hz, HZ, and any capitalization in between
    # Replace with 'Hz'
    unit = re.sub(r'h(ert)?z', 'Hz', unit)
    # Catch arbitrary units, arbitrary, and any capitalization
    # Replace with 'a.u.'
    unit = re.sub(r'(arb(itrary|[.]|)?( )?(units)?|a[.] ?u[.]|au[.]?|aus[.]?)',
                  'a.u.', unit, flags=re.IGNORECASE)
    unit = re.sub(r'(unk)(nown)?', 'Unk', unit, flags=re.IGNORECASE)
    unit = re.sub(r'(c)(oun)?(t)(s)?', 'cts', unit, flags=re.IGNORECASE)
    return _format_unit_structure(unit)


def _format_unit_structure(unit=None):
    """
    Format units a common way
    :param unit: Unit string to be formatted
    :return: Formatted unit string
    """
    # Convert value to a string -> Sets None to 'None'
    # Useful for GUI elements that require string values
    unit = str(unit)
    # a-m[ /?]b-n ... -> a^m b^-n
    unit = re.sub('([℃ÅA-Za-z_ ]+)([-0-9]+)', r"\1^\2", unit)
    # centi*metre -> centimetre (before converting * -> ' ')
    all_prefixes = list(PREFIX.keys())
    all_prefixes.extend(list(SHORT_PREFIX.keys()))
    for prefix in all_prefixes:
        unit = unit.replace(prefix + "*", prefix)
    # a^-m*b^-n -> a^-m b^-n
    unit = unit.replace('*', ' ')
    # invUnit or 1/unit -> /unit
    for x in ['inv', '1/']:
        unit = re.sub(x, '/', unit, flags=re.IGNORECASE)
    # (a_m^2 b_n^-3) -> am^2 bn^-3
    for x in ['_', '(', ')']:
        unit = unit.replace(x, '')
    final = ''
    factors = unit.split('/')
    # am^2/bn^2 c -> am^{{2}} bn^{{-2}} c^{{-1}}
    for i in range(len(factors)):
        sign = '-' if i > 0 else ''
        for item in factors[i].split():
            if item == '':
                continue
            ct_split = item.split('^')
            final += f"{ct_split[0]}"
            number = 1 if len(ct_split) == 1 else ct_split[1]
            final += (f"^{{{sign}{number}}} "
                      if len(ct_split) > 1 or sign == '-'
                      else " ")
    # ' am^{{2}} bn^{{-2}} c^{{-1}} ' -> 'am^{2} bn^{-2} c^{-1}'
    return final.strip().replace('{{', '{').replace('}}', '}')


# Initialize DIMENSIONS and AMBIGUITIES
_build_all_units()


class Converter(object):
    """
    Unit converter for NeXus style units.

    The converter is initialized with the units of the source value.  Various
    source values can then be converted to target values based on target
    value name.
    """
    #: Name of the source units (km, Ang, us, ...)
    units = None  # type: str
    #: Type of the source units (distance, time, frequency, ...)
    dimension = None  # type: str
    #: Scale converter, mapping unit name to scale factor or (scale, offset)
    #: for temperature units.
    scalemap = None  # type: Dict[str, ConversionType]
    #: Scale base for the source units
    scalebase = None  # type: ConversionType

    def __init__(self, units=None, dimension=None):
        # type: (Optional[str], Optional[str]) -> self
        self.units = standardize_units(units) if units is not None else ''  # type: str

        # Lookup dimension if not given
        if dimension:
            self.dimension = dimension
        elif self.units in AMBIGUITIES:
            self.dimension = AMBIGUITIES[self.units]
        else:
            for k, v in DIMENSIONS.items():
                if self.units in v:
                    self.dimension = k
                    break
            else:
                self.dimension = 'unknown'

        # Find the scale for the given units
        try:
            self.scalemap = DIMENSIONS[self.dimension]
            self.scalebase = self.scalemap[self.units]
        except KeyError:
            exc = ValueError('Unable to find %s in dimension %s'
                             % (self.units, self.dimension))
            exc.__cause__ = None
            raise exc

    def scale(self, units="", value=None):
        # type: (str, T) -> T
        """Scale the given value using the units string supplied"""
        if not units or self.scalemap is None or value is None:
            return value
        units = standardize_units(units)
        if isinstance(value, list):
            return [self.scale(units, i) for i in value]
        return value * self.scalebase / self.scalemap[units]

    def scale_with_offset(self, units="", value=None):
        # type: (str, T) -> T
        """Scale the given value and add the offset using the units string supplied"""
        if not units or self.scalemap is None or value is None:
            return value
        units = standardize_units(units)
        if isinstance(value, list):
            return [self.scale_with_offset(units, i) for i in value]
        inscale, inoffset = self.scalebase
        outscale, outoffset = self.scalemap[units]
        return (value + inoffset) * inscale / outscale - outoffset

    def get_compatible_units(self):
        # type: () -> [str]
        """Return a list of compatible units for the current Convertor object"""
        unique_units = []
        conv_list = []
        for item, conv in self.scalemap.items():
            unit = standardize_units(item)
            if unit not in unique_units and unit is not None:
                unique_units.append(unit)
                conv_list.append(conv)
        unique_units = [x for _, x in sorted(zip(conv_list, unique_units))]
        return unique_units

    def __call__(self, value, units=""):
        # type: (T, str) -> T
        # Note: calculating a*1 rather than simply returning a would produce
        # an unnecessary copy of the array, which in the case of the raw
        # counts array would be bad.  Sometimes copying and other times
        # not copying is also bad, but copy on modify semantics isn't
        # supported.
        if not units or self.scalemap is None:
            return value
        try:
            return self.scale(units, value)  # type: ignore
        except KeyError:
            exc = KeyError("%s is not a %s" % (units, self.dimension))
            exc.__cause__ = None
            raise exc
        except TypeError:
            # For temperatures, a type error is raised because the conversion
            # factor is (scale, offset) rather than scale.
            return self.scale_with_offset(units, value)  # type: ignore
