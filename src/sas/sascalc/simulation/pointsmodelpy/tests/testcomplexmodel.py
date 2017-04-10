from sasModeling.pointsmodelpy import pointsmodelpy
from sasModeling.iqPy import iqPy
from sasModeling.geoshapespy import geoshapespy

#First testing: a normal case, a lores model holds a sphere
#and a pdbmodel holds one pdb file. and merged into a complex
#model, then perform calculation
def test_complex():
    p = pointsmodelpy.new_pdbmodel()
    pointsmodelpy.pdbmodel_add(p,"ff0.pdb")

    vp = pointsmodelpy.new_point3dvec()
    pointsmodelpy.get_pdbpoints(p,vp);

    pointsmodelpy.get_pdb_pr(p,vp)
    pointsmodelpy.save_pdb_pr(p,"testcomplex.pr")

    iq = iqPy.new_iq(100,0.001, 0.3)
    pointsmodelpy.get_pdb_iq(p,iq)

    iqPy.OutputIQ(iq,"testcomplex.iq")

    a = geoshapespy.new_sphere(10)
    lm = pointsmodelpy.new_loresmodel(0.1)
    pointsmodelpy.lores_add(lm,a,1.0)

    vpcomplex = pointsmodelpy.new_point3dvec();
    complex = pointsmodelpy.new_complexmodel()
    pointsmodelpy.complexmodel_add(complex,p,"PDB");
    pointsmodelpy.complexmodel_add(complex,lm,"LORES");
    
    pointsmodelpy.get_complexpoints(complex,vpcomplex);
    pointsmodelpy.get_complex_pr(complex,vpcomplex);
    pointsmodelpy.save_complex_pr(complex,"testcomplex1.pr");

    iqcomplex = iqPy.new_iq(100,0.001, 0.3)
    pointsmodelpy.get_complex_iq(complex,iqcomplex);

    iqPy.OutputIQ(iq,"testcomplex1.iq")

#testing 2, insert one pdbmodel and one empty loresmodel
def test_complex2():
  pdb = pointsmodelpy.new_pdbmodel()
  pointsmodelpy.pdbmodel_add(pdb,"ff0.pdb")

  lores = pointsmodelpy.new_loresmodel(0.1)

  complex = pointsmodelpy.new_complexmodel()	
  pointsmodelpy.complexmodel_add(complex,pdb,"PDB");
  pointsmodelpy.complexmodel_add(complex,lores,"LORES")

  points = pointsmodelpy.new_point3dvec()
  pointsmodelpy.get_complexpoints(complex,points)

  pointsmodelpy.get_complex_pr(complex,points);
  pointsmodelpy.save_complex_pr(complex,"testcomplex2.pr")

  iqcomplex = iqPy.new_iq(100,0.001, 0.3)
  pointsmodelpy.get_complex_iq(complex,iqcomplex)

  iqPy.OutputIQ(iqcomplex,"testcomplex2.iq")

  print "p(r) is saved in testcomplex2.pr"
  print "I(Q) is saved in testcomplex2.iq"
  print "pass"

#testing 3, insert one empty pdbmodel and one loresmodel
def test_complex3():
  pdb = pointsmodelpy.new_pdbmodel()

  lores = pointsmodelpy.new_loresmodel(0.1)
  sph = geoshapespy.new_sphere(10)
  pointsmodelpy.lores_add(lores,sph,1.0)

  complex = pointsmodelpy.new_complexmodel()	
  pointsmodelpy.complexmodel_add(complex,pdb,"PDB");
  pointsmodelpy.complexmodel_add(complex,lores,"LORES")

  points = pointsmodelpy.new_point3dvec()
  pointsmodelpy.get_complexpoints(complex,points)

  pointsmodelpy.get_complex_pr(complex,points);
  pointsmodelpy.save_complex_pr(complex,"testcomplex3.pr")

  iqcomplex = iqPy.new_iq(100,0.001, 0.3)
  pointsmodelpy.get_complex_iq(complex,iqcomplex)

  iqPy.OutputIQ(iqcomplex,"testcomplex3.iq")

  print "p(r) is saved in testcomplex3.pr"
  print "I(Q) is saved in testcomplex3.iq"
  print "pass"

# Test 2D complex model
def test_complex4():


    a = geoshapespy.new_sphere(10)
    lm = pointsmodelpy.new_loresmodel(0.1)
    pointsmodelpy.lores_add(lm,a,1.0)

    vpcomplex = pointsmodelpy.new_point3dvec();
    complex = pointsmodelpy.new_complexmodel()
    pointsmodelpy.complexmodel_add(complex,lm,"LORES");
    
    pointsmodelpy.get_complexpoints(complex,vpcomplex);
 
    print pointsmodelpy.get_complex_iq_2D(complex,vpcomplex,0.1,0.1);
    print pointsmodelpy.get_complex_iq_2D(complex,vpcomplex,0.01,0.1);


if __name__ == "__main__":
    #print "test 1, adding one nonempty loresmodel and one nonempty pdbmodel to complex model"
    #test_complex()
    #print "test 2, adding a nonempty pdbmodel, and adding an empty loresmodel"
    #test_complex2()
    #print "test 3, adding an empty pdbmodel, and adding a nonempty loresmodel"
    #test_complex3()
    test_complex4()
