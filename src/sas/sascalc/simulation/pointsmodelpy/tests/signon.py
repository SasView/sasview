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

if __name__ == "__main__":

    import pointsmodelpy
    from pointsmodelpy import pointsmodelpy as pointsmodelpymodule

    print("copyright information:")
    print("   ", pointsmodelpy.copyright())
    print("   ", pointsmodelpymodule.copyright())

    print()
    print("module information:")
    print("    file:", pointsmodelpymodule.__file__)
    print("    doc:", pointsmodelpymodule.__doc__)
    print("    contents:", dir(pointsmodelpymodule))

    print()
    print(pointsmodelpymodule.hello())

# version
__id__ = "$Id$"

#  End of file 
