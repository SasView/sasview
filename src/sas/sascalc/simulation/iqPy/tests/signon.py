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

    import iqPy
    from iqPy import iqPy as iqPymodule

    print("copyright information:")
    print("   ", iqPy.copyright())
    print("   ", iqPymodule.copyright())

    print()
    print("module information:")
    print("    file:", iqPymodule.__file__)
    print("    doc:", iqPymodule.__doc__)
    print("    contents:", dir(iqPymodule))

    print()

# version
__id__ = "$Id$"

#  End of file
