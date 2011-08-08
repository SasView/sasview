from sans.models.CylinderModel import CylinderModel
from sans.models.DisperseModel import DisperseModel
import math

cyl = CylinderModel()
cyl.setParam('scale', 1.0)
cyl.setParam('radius', 20.0)
cyl.setParam('length', 400.0)
cyl.setParam('contrast', 1.0)
cyl.setParam('background', 0.0)
cyl.setParam('cyl_theta', 1.57)
cyl.setParam('cyl_phi', 0.0)

q=0.025
phi=0.0

print "oriented output", cyl.run([q, phi])



name_list=['radius']
val_list = [3.0]
dispersed = DisperseModel(cyl, name_list, val_list)
dispersed.setParam('n_pts', 100)
print "disp output", dispersed.run([q, phi])



from Averager2D import Averager2D
avg = Averager2D()
avg.set_model(cyl)
#avg.set_dispersity([['radius', 3.0, 100]])
avg.setThetaFile('theta.txt')
print avg.runXY([q, 0])