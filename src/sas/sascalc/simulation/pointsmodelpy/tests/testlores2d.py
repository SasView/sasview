def test_lores2d(phi):
  from sasModeling.pointsmodelpy import pointsmodelpy 
  from sasModeling.iqPy import iqPy
  from sasModeling.geoshapespy import geoshapespy

  #lores model is to hold several geometric objects
  lm = pointsmodelpy.new_loresmodel(0.1)

  #generate single geometry shape
  c = geoshapespy.new_cylinder(10,40)
  geoshapespy.set_center(c,1,1,1)
  geoshapespy.set_orientation(c,0,0,0)

  #add single geometry shape to lores model
  pointsmodelpy.lores_add(lm,c,3.0)

  #retrieve the points from lores model for sas calculation
  vp = pointsmodelpy.new_point3dvec()
  pointsmodelpy.get_lorespoints(lm,vp)

  #Calculate I(Q) and P(r) 2D
  pointsmodelpy.distdistribution_xy(lm,vp)
  pointsmodelpy.outputPR_xy(lm,"out_xy.pr")
  iq = iqPy.new_iq(100,0.001, 0.3)
  pointsmodelpy.calculateIQ_2D(lm,iq,phi)
  iqPy.OutputIQ(iq, "out_xy.iq")

def get2d():
  from math import pi
  from Numeric import arange,zeros
  from enthought.util.numerix import Float,zeros
  from sasModeling.file2array import readfile2array
  from sasModeling.pointsmodelpy import pointsmodelpy
  from sasModeling.geoshapespy import geoshapespy

  lm = pointsmodelpy.new_loresmodel(0.1)
  sph = geoshapespy.new_sphere(20)
  pointsmodelpy.lores_add(lm,sph,1.0)

  vp = pointsmodelpy.new_point3dvec()
  pointsmodelpy.get_lorespoints(lm,vp)

  pointsmodelpy.distdistribution_xy(lm,vp)

  value_grid = zeros((100,100),Float)
  width, height = value_grid.shape
  print width,height

  I = pointsmodelpy.calculateI_Qxy(lm,0.00001,0.000002)
  print I

  Imax = 0
  for i in range(width):
    for j in range(height):
      qx = float(i-50)/200.0
      qy = float(j-50)/200.0
      value_grid[i,j] = pointsmodelpy.calculateI_Qxy(lm,qx,qy)
      if value_grid[i][j] > Imax:
        Imax = value_grid[i][j]

  for i in range(width):
    for j in range(height):
      value_grid[i][j] = value_grid[i][j]/Imax

  value_grid[50,50] = 1
  return value_grid

def get2d_2():
  from math import pi
  from Numeric import arange,zeros
  from enthought.util.numerix import Float,zeros
  from sasModeling.file2array import readfile2array
  from sasModeling.pointsmodelpy import pointsmodelpy
  from sasModeling.geoshapespy import geoshapespy

  lm = pointsmodelpy.new_loresmodel(0.1)
  cyn = geoshapespy.new_cylinder(5,20)
  geoshapespy.set_orientation(cyn,0,0,90)
  pointsmodelpy.lores_add(lm,cyn,1.0)

  vp = pointsmodelpy.new_point3dvec()
  pointsmodelpy.get_lorespoints(lm,vp)

  pointsmodelpy.distdistribution_xy(lm,vp)

  value_grid = zeros((100,100),Float)
  width, height = value_grid.shape
  print width,height

  I = pointsmodelpy.calculateI_Qxy(lm,0.00001,0.000002)
  print I

  Imax = 0
  for i in range(width):
    for j in range(height):
      qx = float(i-50)/200.0
      qy = float(j-50)/200.0
      value_grid[i,j] = pointsmodelpy.calculateI_Qxy(lm,qx,qy)
      if value_grid[i][j] > Imax:
        Imax = value_grid[i][j]

  for i in range(width):
    for j in range(height):
      value_grid[i][j] = value_grid[i][j]/Imax

  value_grid[50,50] = 1
  return value_grid
  
if __name__ == "__main__":

  print "start to test lores 2D"
#  test_lores2d(10)
  value_grid = get2d_2()
  print value_grid
  print "pass"
