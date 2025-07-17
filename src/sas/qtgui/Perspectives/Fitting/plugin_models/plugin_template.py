r"""
Definition
----------

This template can be used to develop your plugin model.

.. math::

    I(q) = mq+b

where *m* is the slope and *b* is the intercept.

Validation
----------


References
----------

#. A LastNameA and B. LastNameB, *Title*, Journal, MoreInfo, (YEAR)

Authorship and Verification
----------------------------

* **Author:** Your Name Here
* **Last Modified by:**
* **Last Reviewed by:** Reviewer Name Here **Date:** Date Here
"""

from numpy import inf

name = "plugin_template"
title = 'Template Plugin Model'
description = """\
I(q) = mq + b
    m: slope of line
    b: intercept of line
"""
category = "plugin"
structure_factor = False

#             ["name", "units", default, [lower, upper], "type","description"],
parameters = [["m", "Ang/cm", 2, [-inf, inf], "", "slope of the line"],
              ["b", "1/cm", 1, [-inf, inf], "", "intercept of the line"]
             ]

def Iq(q, m=2, b=1):
    """
    Parameters:
        q:      input scattering vectors, units 1/Ang
        m:      slope of line, units Ang/cm, default value=2
        b:      intercept of line, units 1/cm, default value=1
    Returns:
        I(q):   1D scattering intensity at q, units 1/cm
    """
    iq = m*q + b
    return iq

# include tests for your model
# tests = [
#     [{'m': 2.0, 'b' : 1.0}, [q1, q2], [expected_Iq1, expected_Iq2]],
#     [{'m': 3.0, 'b' : 5.0}, [q3, q4], [expected_Iq3, expected_Iq4]],
# ]
