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

    import analmodelpy
    from analmodelpy import analmodelpy as analmodelpymodule

    print("copyright information:")
    print("   ", analmodelpy.copyright())
    print("   ", analmodelpymodule.copyright())

    print()
    print("module information:")
    print("    file:", analmodelpymodule.__file__)
    print("    doc:", analmodelpymodule.__doc__)
    print("    contents:", dir(analmodelpymodule))

    print()
    print(analmodelpymodule.hello())

# version
__id__ = "$Id$"

#  End of file 
