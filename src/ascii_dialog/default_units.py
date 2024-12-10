# NOTE: This module will probably be a lot more involved once how this is getting into the configuration will be sorted.

import sasdata.quantities.units as unit

# Based on the email Jeff sent me./
default_units = {
    'Q': [unit.per_nanometer, unit.per_angstrom],
    # TODO: I think the unit group for scattering intensity may be wrong. Defaulting to nanometers for now but I know
    # this isn't right
    'I': [unit.per_nanometer]
}

