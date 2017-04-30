if __name__ == "__main__":

    from sasModeling.iqPy import iqPy
    #from sasModeling.analmodelpy import analmodelpy as analmodelpymodule
    from sasModeling.geoshapespy import geoshapespy
    from sasModeling.pointsmodelpy import pointsmodelpy

#    print "copyright information:"
#    print "   ", pointsmodelpy.copyright()
#    print "   ", pointsmodelpymodule.copyright()

    print()
    print("module information:")
    print("    file:", pointsmodelpy.__file__)
    print("    doc:", pointsmodelpy.__doc__)
    print("    contents:", dir(pointsmodelpy))
    print("    contents:", dir(geoshapespy))

#    a = geoshapespy.new_singlehelix(10,2,30,2)
    #a = geoshapespy.new_sphere(20)
    
    iq = iqPy.new_iq(100,0.001, 0.3)

#    geoshapespy.set_orientation(a,20,40,60)
#    geoshapespy.set_center(a,0,0,0)
    lm = pointsmodelpy.new_loresmodel(0.1)
#    pointsmodelpy.lores_add(lm,a,1.0)

#    b = geoshapespy.new_sphere(15)
#    geoshapespy.set_center(b,15,15,15)
#    pointsmodelpy.lores_add(lm,b,2.0)

    
    c = geoshapespy.new_cylinder(10,40)
    geoshapespy.set_center(c,1,1,1)
    geoshapespy.set_orientation(c,0,0,0)
    pointsmodelpy.lores_add(lm,c,3.0)
    
#    d = geoshapespy.new_ellipsoid(10,8,6)
#    geoshapespy.set_center(d,3,3,3)
#    geoshapespy.set_orientation(c,30,30,30)
#    pointsmodelpy.lores_add(lm,d,1.0)

    vp = pointsmodelpy.new_point3dvec()
    pointsmodelpy.get_lorespoints(lm,vp)
    pointsmodelpy.outputPDB(lm,vp,"modelpy.pseudo.pdb")

    print("calculating distance distribution")
    rmax = pointsmodelpy.get_lores_pr(lm,vp)
    print("finish calculating get_lores_pr, and rmax is:", rmax)
    pointsmodelpy.outputPR(lm,"testlores.pr")
    pointsmodelpy.get_lores_iq(lm,iq)

    iqPy.OutputIQ(iq, "testlores.iq")

    print("Testing get I from a single q")
    result = pointsmodelpy.get_lores_i(lm,0.1)
    print("The I(0.1) is: %s" % str(result)) 

# version
__id__ = "$Id$"

#  End of file 
