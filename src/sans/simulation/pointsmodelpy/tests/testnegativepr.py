if __name__ == "__main__":
  from sansModeling.pointsmodelpy import pointsmodelpy
  from sansModeling.iqPy import iqPy
  from sansModeling.geoshapespy import geoshapespy

  a = geoshapespy.new_sphere(10)
  lm = pointsmodelpy.new_loresmodel(0.0005)
  pointsmodelpy.lores_add(lm,a,1.0)
  b = geoshapespy.new_sphere(20)
  geoshapespy.set_center(b,20,20,20)
  pointsmodelpy.lores_add(lm,b,-1.0)

  vp = pointsmodelpy.new_point3dvec()
  pointsmodelpy.get_lorespoints(lm,vp)

  pointsmodelpy.get_lores_pr(lm,vp)