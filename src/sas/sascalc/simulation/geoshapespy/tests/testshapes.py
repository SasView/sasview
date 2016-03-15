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

    from SASsimulation import geoshapespy

    print
    print "module information:"
    print "    file:", geoshapespy.__file__
    print "    doc:", geoshapespy.__doc__
    print "    contents:", dir(geoshapespy)

    sp = geoshapespy.new_sphere(10)
#    geoshapespy.set_orientation(sp,10,20,10)
    cy = geoshapespy.new_cylinder(2,6)

    el = geoshapespy.new_ellipsoid(25,15,10)

    hs = geoshapespy.new_hollowsphere(10,2)

    sh = geoshapespy.new_singlehelix(10,2,30,2)

# version
__id__ = "$Id$"

#  End of file 
