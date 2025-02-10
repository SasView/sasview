# NOTE: This module will probably be a lot more involved once how this is getting into the configuration will be sorted.

import sasdata.quantities.units as unit

# Based on the email Jeff sent me./
default_units = {
    'Q': [unit.per_nanometer, unit.per_angstrom, unit.per_meter],
    'I': [unit.per_centimeter, unit.per_meter]
}
