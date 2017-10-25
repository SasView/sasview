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

# TODO: Add udunits to NAPI rather than reimplementing it in python
# TODO: Alternatively, parse the udunits database directly
# UDUnits:
#  http://www.unidata.ucar.edu/software/udunits/udunits-1/udunits.txt

from __future__ import division
import math

__all__ = ['Converter']

# Limited form of units for returning objects of a specific type.
# Maybe want to do full units handling with e.g., pyre's
# unit class. For now lets keep it simple.  Note that
def _build_metric_units(unit,abbr):
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
    prefix = dict(peta=1e15,tera=1e12,giga=1e9,mega=1e6,kilo=1e3,
                  deci=1e-1,centi=1e-2,milli=1e-3,mili=1e-3,micro=1e-6,
                  nano=1e-9,pico=1e-12,femto=1e-15)
    short_prefix = dict(P=1e15,T=1e12,G=1e9,M=1e6,k=1e3,
                        d=1e-1,c=1e-2,m=1e-3,u=1e-6,
                        n=1e-9,p=1e-12,f=1e-15)
    map = {abbr:1}
    map.update([(P+abbr,scale) for (P,scale) in short_prefix.items()])
    for name in [unit,unit.capitalize()]:
        map.update({name:1,name+'s':1})
        map.update([(P+name,scale) for (P,scale) in prefix.items()])
        map.update([(P+'*'+name,scale) for (P,scale) in prefix.items()])
        map.update([(P+name+'s',scale) for (P,scale) in prefix.items()])
    return map

def _build_plural_units(**kw):
    """
    Construct names for the given units.  Builds singular and plural form.
    """
    map = {}
    map.update([(name,scale) for name,scale in kw.items()])
    map.update([(name+'s',scale) for name,scale in kw.items()])
    return map

def _caret_optional(s):
    """
    Strip '^' from unit names.

    * WARNING * this will incorrect transform 10^3 to 103.
    """
    s.update((k.replace('^',''),v)
             for k, v in list(s.items())
             if '^' in k)

def _build_all_units():
    distance = _build_metric_units('meter','m')
    distance.update(_build_metric_units('metre','m'))
    distance.update(_build_plural_units(micron=1e-6, Angstrom=1e-10))
    distance.update({'A':1e-10, 'Ang':1e-10})

    # Note: minutes are used for angle
    time = _build_metric_units('second','s')
    time.update(_build_plural_units(hour=3600,day=24*3600,week=7*24*3600))

    # Note: seconds are used for time
    angle = _build_plural_units(degree=1, minute=1/60.,
                  arcminute=1/60., arcsecond=1/3600., radian=180/math.pi)
    angle.update(deg=1, arcmin=1/60., arcsec=1/3600., rad=180/math.pi)

    frequency = _build_metric_units('hertz','Hz')
    frequency.update(_build_metric_units('Hertz','Hz'))
    frequency.update(_build_plural_units(rpm=1/60.))

    # Note: degrees are used for angle
    # Note: temperature needs an offset as well as a scale
    temperature = _build_metric_units('kelvin','K')
    temperature.update(_build_metric_units('Kelvin','K'))
    temperature.update(_build_metric_units('Celcius', 'C'))
    temperature.update(_build_metric_units('celcius', 'C'))

    charge = _build_metric_units('coulomb','C')
    charge.update({'microAmp*hour':0.0036})

    sld = { '10^-6 Angstrom^-2': 1e-6, 'Angstrom^-2': 1 }
    Q = { 'invA': 1, 'invAng': 1, 'invAngstroms': 1, '1/A': 1,
          '10^-3 Angstrom^-1': 1e-3, '1/cm': 1e-8, '1/m': 1e-10,
          'nm^-1': 0.1, '1/nm': 0.1, 'n_m^-1': 0.1 }

    _caret_optional(sld)
    _caret_optional(Q)

    dims = [distance, time, angle, frequency, temperature, charge, sld, Q]
    return dims

class Converter(object):
    """
    Unit converter for NeXus style units.
    """
    # Define the units, using both American and European spelling.
    scalemap = None
    scalebase = 1
    dims = _build_all_units()

    # Note: a.u. stands for arbitrary units, which should return the default
    # units for that particular dimension.
    # Note: don't have support for dimensionless units.
    unknown = {None:1, '???':1, '': 1, 'a.u.': 1}

    def __init__(self, name):
        self.base = name
        for map in self.dims:
            if name in map:
                self.scalemap = map
                self.scalebase = self.scalemap[name]
                return
        if name in self.unknown:
            return # default scalemap and scalebase correspond to unknown
        else:
            raise KeyError("Unknown unit %s"%name)

    def scale(self, units=""):
        if units == "" or self.scalemap is None: return 1
        return self.scalebase/self.scalemap[units]

    def __call__(self, value, units=""):
        # Note: calculating a*1 rather than simply returning a would produce
        # an unnecessary copy of the array, which in the case of the raw
        # counts array would be bad.  Sometimes copying and other times
        # not copying is also bad, but copy on modify semantics isn't
        # supported.
        if units == "" or self.scalemap is None: return value
        try:
            return value * (self.scalebase/self.scalemap[units])
        except KeyError:
            possible_units = ", ".join(str(k) for k in self.scalemap.keys())
            raise KeyError("%s not in %s"%(units,possible_units))

def _check(expect,get):
    if expect != get:
        raise ValueError("Expected %s but got %s"%(expect, get))
     #print expect,"==",get

def test():
    _check(1,Converter('n_m^-1')(10,'invA')) # 10 nm^-1 = 1 inv Angstroms
    _check(2,Converter('mm')(2000,'m')) # 2000 mm -> 2 m
    _check(2.011e10,Converter('1/A')(2.011,"1/m")) # 2.011 1/A -> 2.011 * 10^10 1/m
    _check(0.003,Converter('microseconds')(3,units='ms')) # 3 us -> 0.003 ms
    _check(45,Converter('nanokelvin')(45))  # 45 nK -> 45 nK
    _check(0.5,Converter('seconds')(1800,units='hours')) # 1800 s -> 0.5 hr
    _check(123,Converter('a.u.')(123,units='mm')) # arbitrary units always returns the same value
    _check(123,Converter('a.u.')(123,units='s')) # arbitrary units always returns the same value
    _check(123,Converter('a.u.')(123,units='')) # arbitrary units always returns the same value
    try:
        Converter('help')
    except KeyError:
        pass
    else:
        raise Exception("unknown unit did not raise an error")

    # TODO: more tests

if __name__ == "__main__":
    test()
