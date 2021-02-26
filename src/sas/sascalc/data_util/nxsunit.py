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


# Limited form of units for returning objects of a specific type.
# Maybe want to do full units handling with e.g., pyre's
# unit class. For now lets keep it simple.  Note that
def _build_metric_units(unit, abbr):
    """
    Construct standard SI names for the given unit.
    Builds e.g.,
        s, ns
        second, nanosecond, nano*second
        seconds, nanoseconds
    Includes prefixes for femto through peta.

    Ack! Allows, e.g., Coulomb and coulomb even though Coulomb is not
    a unit because some NeXus files store it that way!

    Returns a dictionary of names and scales.
    """
    prefix = dict(peta=1e15, tera=1e12, giga=1e9, mega=1e6, kilo=1e3, deci=1e-1, centi=1e-2, milli=1e-3, mili=1e-3,
                  micro=1e-6, nano=1e-9, pico=1e-12, femto=1e-15)
    short_prefix = dict(P=1e15, T=1e12, G=1e9, M=1e6, k=1e3, d=1e-1, c=1e-2, m=1e-3, u=1e-6, n=1e-9, p=1e-12, f=1e-15)
    map = {abbr: 1}
    for name in [unit, unit.capitalize(), unit.lower(), abbr]:
        for items in [prefix, short_prefix]:
            map.update({name: 1, name+'s': 1})
            map.update([(P + name, scale) for (P, scale) in items.items()])
            map.update([(P + '*'+name, scale) for (P, scale) in items.items()])
            map.update([(P + name + 's', scale) for (P, scale) in items.items()])
    return map


def _build_plural_units(**kw):
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
        map['deg ' + s] = conversion
        map['°' + s] = conversion
    for s in name, name.capitalize(), symbol, symbol.lower():
        map[s] = conversion
        map['degree_' + s] = conversion
        map['degree ' + s] = conversion
        map['degrees ' + s] = conversion
    return map


def _build_inv_units(names, conversion):
    # type: (Sequence[str], ConversionType) -> Dict[str, ConversionType]
    """
    Builds variations on inverse units, including 1/x, invx and x^-1.
    """
    map = {}  # type: Dict[str, ConversionType]
    for s in names:
        map['1/' + s] = conversion
        map['inv' + s] = conversion
        map[s + '^-1'] = conversion
        map[s + '^{-1}'] = conversion
    return map


def _build_inv2_units(names, conversion):
    # type: (Sequence[str], ConversionType) -> Dict[str, ConversionType]
    """
    Builds variations on inverse square units, including 1/x^2, invx^-2 and x^-2.
    """
    map = {}  # type: Dict[str, ConversionType]
    for s in names:
        map['1/' + s + '^2'] = conversion
        map['inv' + s + '^2'] = conversion
        map[s + '^-2'] = conversion
        map[s + '^{-2}'] = conversion
    return map


def _caret_optional(s):
    """
    Strip '^' from unit names.
    * WARNING * this will incorrectly transform 10^3 to 103.
    """
    stripped = [(k.replace('^', ''), v) for k, v in s.items() if '^' in k]
    s.update(stripped)


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
    frequency.update(_build_inv_units(('s',), 1.))
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

    charge = _build_metric_units('coulomb', 'C')
    charge['microAmp*hour'] = 0.0036
    DIMENSIONS['charge'] = charge

    resistance = _build_metric_units('ohm', 'Ω')
    DIMENSIONS['resistance'] = resistance

    sld = _build_inv2_units(('Å', 'A', 'Ang', 'Angstrom', 'ang', 'angstrom'), 1.)
    sld.update(_build_inv2_units(('nm',), 100.))
    sld['10^-6 Angstrom^-2'] = 1e-6
    DIMENSIONS['sld'] = sld

    Q = _build_inv_units(('Å', 'A', 'Ang', 'Angstrom', 'ang', 'angstrom'), 1.)
    Q.update(_build_inv_units(('nanometer', 'nanometre', 'nm'), 10.))
    Q.update(_build_inv_units(('millimeter', 'millimetre', 'mm'), 1.0e8))
    Q.update(_build_inv_units(('centimeter', 'centimetre', 'cm'), 1.0e9))
    Q.update(_build_inv_units(('meter', 'metre', 'm'), 1.0e10))
    Q['10^-3 Angstrom^-1'] = 1e-3
    DIMENSIONS['Q'] = Q

    # TODO: break into separate dimension blocks to allow scaling of complex units
    #  SANS units => ['A^{-2}']
    #  SESANS units => ['A^{-2}', 'cm^{-1}']
    #  Will require more complexity to scale calculations
    DIMENSIONS['SESANS'] = {'Å^{-2} cm^{-1}': 1, 'A^{-2} cm^{-1}': 1}

    energy = _build_metric_units('electronvolt', 'eV')
    DIMENSIONS['energy'] = energy
    # Note: energy <=> wavelength <=> velocity requires a probe type

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
        {None: 1, '???': 1, '': 1, 'A.U.': 1,  'a.u.': 1, 'Counts': 1, 'counts': 1, 'arbitrary': 1, 'arbitrary units': 1,
         'unitless': 1, 'unknown': 1, 'Unknown': 1}
    )
    DIMENSIONS['dimensionless'] = unknown


def standardize_units(unit):
    """
    Convert supplied units to a standard format for maintainability
    :param unit: Raw unit as supplied
    :return: Unit with known, reduced values
    """
    if not unit:
        return None
    # Catch ang, angstrom, ANG, ANGSTROM, and any capitalization in between
    # Replace with 'Å'
    unit = re.sub(r'[Åa]ng(str[oö]m)?(s)?', 'Å', unit, flags=re.IGNORECASE)
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
    if not unit:
        return
    # a-m[ /?]b-n ... -> a^m b^-n
    unit = re.sub('([℃ÅA-Za-z_ ]+)([-0-9]+)', r"\1^\2", unit)
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

    def __init__(self, units, dimension=None):
        # type: (Optional[str], Optional[str]) -> None
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
        if not units or self.scalemap is None or value is None:
            return value
        units = standardize_units(units)
        return value * self.scalebase / self.scalemap[units]

    def scale_with_offset(self, units="", value=None):
        if not units or self.scalemap is None or value is None:
            return value
        units = standardize_units(units)
        inscale, inoffset = self.scalebase
        outscale, outoffset = self.scalemap[units]
        return (value + inoffset) * inscale / outscale - outoffset

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


def _check(expect,get):
    if expect != get:
        raise ValueError("Expected %s but got %s"%(expect, get))
     #print expect,"==",get


def test():
    _check(1,Converter('n_m^-1')(0.1,'invA')) # 10 nm^-1 = 1 inv Angstroms
    _check(2,Converter('mm')(2000,'m')) # 2000 mm -> 2 m
    _check(2.011e-10,Converter('1/A')(2.011,"1/m")) # 2.011 1/A -> 2.011 * 10^10 1/m
    _check(0.003,Converter('microseconds')(3,units='ms')) # 3 us -> 0.003 ms
    _check(45,Converter('nanokelvin')(45))  # 45 nK -> 45 nK
    _check(0.5,Converter('seconds')(1800,units='hours')) # 1800 s -> 0.5 hr\
    try:
        Converter('help')
    except ValueError:
        pass
    else:
        raise Exception("unknown unit did not raise an error")

    # TODO: move tests to their own unit test suite


if __name__ == "__main__":
    test()
