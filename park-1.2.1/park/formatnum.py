# This program is public domain
# Author Paul Kienzle
"""
Format numbers nicely for printing.

Usage::

   >> from danse.common.util.formatnum import *
   >> v,dv = 757.2356,0.01032
   >> print format_uncertainty_pm(v,dv)
   757.235 +/- 0.010
   >> format_uncertainty_compact(v,dv)
   757.235(10)
   >> format_uncertainty(v,dv)
   757.235(10)

Set format_uncertainty.compact to False to use the +/-
format by default, otherwise leave it at True for compact
value(##) format.
"""
from __future__ import division

import math
import numpy
__all__ = ['format_uncertainty', 'format_uncertainty_pm', 
           'format_uncertainty_compact']

# These routines need work for +/- formatting::
# - pm formats are not rigorously tested
# - pm formats do not try to align the scale to multiples of 1000
# - pm formats do not try to align the value scale to uncertainty scale

# Coordinating scales across a set of numbers is not supported.  For easy
# comparison a set of numbers should be shown in the same scale.  One could
# force this from the outside by adding scale parameter (either 10**n, n, or
# a string representing the desired SI prefix) and having a separate routine
# which computes the scale given a set of values.

# Coordinating scales with units offers its own problems.  Again, the user
# may want to force particular units.  This can be done by outside of the
# formatting routines by scaling the numbers to the appropriate units then
# forcing them to print with scale 10**0.  If this is a common operation,
# however, it may want to happen inside.

# The value e<n> is currently formatted into the number.  Alternatively this
# scale factor could be returned so that the user can choose the appriate
# SI prefix when printing the units.  This gets tricky when talking about
# composite units such as 2.3e-3 m**2 -> 2300 mm**2, and with volumes
# such as 1 g/cm**3 -> 1 kg/L.

def format_uncertainty_pm(value, uncertainty=None):
    """
    Given *value* v and *uncertainty* dv, return a string v +/- dv.
    
    The returned string uses only the number of digits warranted by
    the uncertainty in the measurement.

    If the uncertainty is 0 or not otherwise provided, the simple
    %g floating point format option is used.

    Infinite and indefinite numbers are represented as inf and NaN.
    """
    return _format_uncertainty(value, uncertainty, compact=False)

def format_uncertainty_compact(value, uncertainty=None):
    """
    Given *value* v and *uncertainty* dv, return the compact
    representation v(##), where ## are the first two digits of 
    the uncertainty.
    
    The returned string uses only the number of digits warranted by
    the uncertainty in the measurement.

    If the uncertainty is 0 or not otherwise provided, the simple
    %g floating point format option is used.

    Infinite and indefinite numbers are represented as inf and NaN.
    """
    return _format_uncertainty(value, uncertainty, compact=True)

class FormatUncertainty:
    """
    Given *value* and *uncertainty*, return a concise string representation.

    This will either by the +/- form of :func:`format_uncertainty_pm` or
    the compact form of :func:`format_uncertainty_compact` depending on 
    whether *compact* is specified or whether *format_uncertainty.compact* 
    is True or False.
    """
    compact = True
    def __call__(self, value, uncertainty):
        return _format_uncertainty(value, uncertainty, self.compact)
format_uncertainty = FormatUncertainty()

def _format_uncertainty(value,uncertainty,compact):
    """
    Implementation of both the compact and the +/- formats.
    """
    if numpy.isinf(value):
        return "inf" if value > 0 else "-inf"
    
    if numpy.isnan(value):
        return "NaN"

    # Uncertainty check must come after indefinite check since the %g
    # format string doesn't handle indefinite numbers consistently
    # across platforms.
    if uncertainty == None or uncertainty <= 0 or numpy.isnan(uncertainty):
        return "%g"%value
    if numpy.isinf(uncertainty):
        if compact:
            return "%g(inf)"%value
        else:
            return "%g +/- inf"%value
    
    # Process sign
    sign = "-" if value < 0 else ""
    value = abs(value)
    
    # Determine the number of digits in the value and the error
    # Note that uncertainty <= 0 is handled above
    err_place = int(math.floor(math.log10(uncertainty)))
    if value == 0:
        val_place = err_place-1
    else:
        val_place = int(math.floor(math.log10(value)))

    # If pm, return a simple v +/- dv
    if not compact:
        scale = 10**(err_place-1)
        val_digits = val_place-err_place+2
        return "%s%.*g +/- %.2g"%(sign,val_digits,value,uncertainty)

    # The remainder is for the v(dv) case 
    err_str = "(%2d)"%int(uncertainty/10.**(err_place-1)+0.5)
    if err_place > val_place:
        # Degenerate case: error bigger than value
        # The mantissa is 0.#(##)e#, 0.0#(##)e# or 0.00#(##)e#
        if err_place - val_place > 2: value = 0
        val_place = int(math.floor((err_place+2)/3.))*3
        digits_after_decimal = val_place - err_place + 1
        val_str = "%.*f%s"%(digits_after_decimal,value/10.**val_place,err_str)
        if val_place != 0: val_str += "e%d"%val_place
    elif err_place == val_place:
        # Degenerate case: error and value the same order of magnitude
        # The value is ##(##)e#, #.#(##)e# or 0.##(##)e#
        val_place = int(math.floor((err_place+1)/3.))*3
        digits_after_decimal = val_place - err_place + 1
        val_str = "%.*f%s"%(digits_after_decimal,value/10.**val_place,err_str)
        if val_place != 0: val_str += "e%d"%val_place
    elif err_place <= 1 and val_place >= -3:
        # Normal case: nice numbers and errors
        # The value is ###.###(##)
        digits_after_decimal = abs(err_place-1)
        val_str = "%.*f%s"%(digits_after_decimal,value,err_str)
    else:
        # Extreme cases: zeros before value or after error
        # The value is ###.###(##)e#, ##.####(##)e# or #.#####(##)e#
        total_digits = val_place - err_place + 2
        val_place = int(math.floor(val_place/3.))*3
        val_str = "%.*g%se%d"%(total_digits,
                               value/10.**val_place,
                               err_str,val_place)

    return sign+val_str



def test():
    # Oops... renamed function after writing tests
    value_str = format_uncertainty_compact
    
    # val_place > err_place
    assert value_str(1235670,766000) == "1.24(77)e6"
    assert value_str(123567.,76600) == "124(77)e3"
    assert value_str(12356.7,7660) == "12.4(77)e3"
    assert value_str(1235.67,766) == "1.24(77)e3"
    assert value_str(123.567,76.6) == "124(77)"
    assert value_str(12.3567,7.66) == "12.4(77)"
    assert value_str(1.23567,.766) == "1.24(77)"
    assert value_str(.123567,.0766) == "0.124(77)"
    assert value_str(.0123567,.00766) == "0.0124(77)"
    assert value_str(.00123567,.000766) == "0.00124(77)"
    assert value_str(.000123567,.0000766) == "124(77)e-6"
    assert value_str(.0000123567,.00000766) == "12.4(77)e-6"
    assert value_str(.00000123567,.000000766) == "1.24(77)e-6"
    assert value_str(.000000123567,.0000000766) == "124(77)e-9"
    assert value_str(.00000123567,.0000000766) == "1.236(77)e-6"
    assert value_str(.0000123567,.0000000766) == "12.357(77)e-6"
    assert value_str(.000123567,.0000000766) == "123.567(77)e-6"
    assert value_str(.00123567,.000000766) == "0.00123567(77)"
    assert value_str(.0123567,.00000766) == "0.0123567(77)"
    assert value_str(.123567,.0000766) == "0.123567(77)"
    assert value_str(1.23567,.000766) == "1.23567(77)"
    assert value_str(12.3567,.00766) == "12.3567(77)"
    assert value_str(123.567,.0764) == "123.567(76)"
    assert value_str(1235.67,.764) == "1235.67(76)"
    assert value_str(12356.7,7.64) == "12356.7(76)"
    assert value_str(123567,76.4) == "123567(76)"
    assert value_str(1235670,764) == "1.23567(76)e6"
    assert value_str(12356700,764) == "12.3567(76)e6"
    assert value_str(123567000,7640) == "123.567(76)e6"
    assert value_str(1235670000,76400) == "1.23567(76)e9"
    
    # val_place == err_place
    assert value_str(123567,764000) == "0.12(76)e6"
    assert value_str(12356.7,76400) == "12(76)e3"
    assert value_str(1235.67,7640) == "1.2(76)e3"
    assert value_str(123.567,764) == "0.12(76)e3"
    assert value_str(12.3567,76.4) == "12(76)"
    assert value_str(1.23567,7.64) == "1.2(76)"
    assert value_str(.123567,.764) == "0.12(76)"
    assert value_str(.0123567,.0764) == "12(76)e-3"
    assert value_str(.00123567,.00764) == "1.2(76)e-3"
    assert value_str(.000123567,.000764) == "0.12(76)e-3"

    # val_place == err_place-1
    assert value_str(123567,7640000) == "0.1(76)e6"
    assert value_str(12356.7,764000) == "0.01(76)e6"
    assert value_str(1235.67,76400) == "0.001(76)e6"
    assert value_str(123.567,7640) == "0.1(76)e3"
    assert value_str(12.3567,764) == "0.01(76)e3"
    assert value_str(1.23567,76.4) == "0.001(76)e3"
    assert value_str(.123567,7.64) == "0.1(76)"
    assert value_str(.0123567,.764) == "0.01(76)"
    assert value_str(.00123567,.0764) == "0.001(76)"
    assert value_str(.000123567,.00764) == "0.1(76)e-3"

    # val_place == err_place-2
    assert value_str(12356700,7640000000) == "0.0(76)e9"
    assert value_str(1235670,764000000) == "0.00(76)e9"
    assert value_str(123567,76400000) == "0.000(76)e9"
    assert value_str(12356,7640000) == "0.0(76)e6"
    assert value_str(1235,764000) == "0.00(76)e6"
    assert value_str(123,76400) == "0.000(76)e6"
    assert value_str(12,7640) == "0.0(76)e3"
    assert value_str(1,764) == "0.00(76)e3"
    assert value_str(0.1,76.4) == "0.000(76)e3"
    assert value_str(0.01,7.64) == "0.0(76)"
    assert value_str(0.001,0.764) == "0.00(76)"
    assert value_str(0.0001,0.0764) == "0.000(76)"
    assert value_str(0.00001,0.00764) == "0.0(76)e-3"

    # val_place == err_place-3
    assert value_str(12356700,76400000000) == "0.000(76)e12"
    assert value_str(1235670,7640000000) == "0.0(76)e9"
    assert value_str(123567,764000000) == "0.00(76)e9"
    assert value_str(12356,76400000) == "0.000(76)e9"
    assert value_str(1235,7640000) == "0.0(76)e6"
    assert value_str(123,764000) == "0.00(76)e6"
    assert value_str(12,76400) == "0.000(76)e6"
    assert value_str(1,7640) == "0.0(76)e3"
    assert value_str(0.1,764) == "0.00(76)e3"
    assert value_str(0.01,76.4) == "0.000(76)e3"
    assert value_str(0.001,7.64) == "0.0(76)"
    assert value_str(0.0001,0.764) == "0.00(76)"
    assert value_str(0.00001,0.0764) == "0.000(76)"
    assert value_str(0.000001,0.00764) == "0.0(76)e-3"

    # negative values
    assert value_str(-1235670,765000) == "-1.24(77)e6"
    assert value_str(-1.23567,.765) == "-1.24(77)"
    assert value_str(-.00000123567,.0000000765) == "-1.236(77)e-6"
    assert value_str(-12356.7,7.64) == "-12356.7(76)"
    assert value_str(-123.567,764) == "-0.12(76)e3"
    assert value_str(-1235.67,76400) == "-0.001(76)e6"
    assert value_str(-.000123567,.00764) == "-0.1(76)e-3"
    assert value_str(-12356,7640000) == "-0.0(76)e6"
    assert value_str(-12,76400) == "-0.000(76)e6"
    assert value_str(-0.0001,0.764) == "-0.00(76)"

    # zero values
    assert value_str(0,0) == "0"
    assert value_str(-1.23567,0) == "-1.23567"
    assert value_str(0,765000) == "0.00(77)e6"
    assert value_str(0,.765) == "0.00(77)"
    assert value_str(0,.000000765) == "0.00(77)e-6"
    assert value_str(0,76400) == "0.000(76)e6"
    assert value_str(0,7640) == "0.0(76)e3"

    # marked values
    assert value_str(-numpy.inf,None) == "-inf"
    assert value_str(numpy.inf,None) == "inf"
    assert value_str(numpy.NaN,None) == "NaN"
    
    # plus/minus form
    assert format_uncertainty_pm(-1.23567,0.765) == "-1.24 +/- 0.77"
    assert format_uncertainty_compact(-1.23567,0.765) == "-1.24(77)"
    assert format_uncertainty_pm(752.3567,0.01) == "752.357 +/- 0.01"
    assert format_uncertainty(-1.23567,0.765) == "-1.24(77)"

    # bad uncertainty
    assert format_uncertainty_pm(-1.23567,numpy.NaN) == "-1.23567"
    assert format_uncertainty_pm(-1.23567,-numpy.inf) == "-1.23567"
    assert format_uncertainty_pm(-1.23567,-0.1) == "-1.23567"
    assert format_uncertainty_compact(-1.23567,numpy.NaN) == "-1.23567"
    assert format_uncertainty_compact(-1.23567,-numpy.inf) == "-1.23567"
    assert format_uncertainty_compact(-1.23567,-0.1) == "-1.23567"

    # no uncertainty
    assert format_uncertainty_pm(-1.23567,0) == "-1.23567"
    assert format_uncertainty_compact(-1.23567,0) == "-1.23567"
    assert format_uncertainty_pm(-1.23567,None) == "-1.23567"
    assert format_uncertainty_compact(-1.23567,None) == "-1.23567"

    # inf uncertainty
    assert format_uncertainty_pm(-1.23567,numpy.inf) == "-1.23567 +/- inf"
    assert format_uncertainty_compact(-1.23567,numpy.inf) == "-1.23567(inf)"


if __name__ == "__main__": test()
    
