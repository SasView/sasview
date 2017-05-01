#!/usr/bin/env python
# 
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 
#                               Michael A.G. Aivazis
#                        California Institute of Technology
#                        (C) 1998-2005  All Rights Reserved
# 
#  <LicenseText>
# 
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 
from __future__ import print_function


if __name__ == "__main__":

    from SASsimulation import analmodelpy as analmodelpymodule
    from SASsimulation import iqPy
    from SASsimulation import geoshapespy

    print("copyright information:")
    print("   ", analmodelpymodule.copyright())

    print()
    print("module information:")
    print("    file:", analmodelpymodule.__file__)
    print("    doc:", analmodelpymodule.__doc__)
    print("    contents:", dir(analmodelpymodule))

    a = geoshapespy.new_sphere(1.0)
    iq = iqPy.new_iq(10,0.001, 0.3)
    anal = analmodelpymodule.new_analmodel(a)
    analmodelpymodule.CalculateIQ(anal,iq)
    iqPy.OutputIQ(iq,"out.iq")




# version
__id__ = "$Id$"

#  End of file 
