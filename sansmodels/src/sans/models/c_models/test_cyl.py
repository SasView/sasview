import sys, os, math
from sans.models.CylinderModel import CylinderModel
from sans.models.DisperseModel import DisperseModel

def old_cyl(q=0.001):

    cyl = CylinderModel()
    cyl.setParam('cyl_phi', 0.0)
    cyl.setParam('cyl_theta', 0.0)
    
    disp = DisperseModel(cyl, ['radius'], [5])
    disp.setParam('n_pts', 100)
    print "" 
    print "Old Cyl : ", cyl.run(q)
    print "Old Disp: ", disp.run(q)
    
    
    
#----------------------------------------------------------------------
    
cyl = CylinderModel()
print cyl.run(0.001)
print cyl.run([0.001, .7854])
print cyl.runXY([0.001,0.001])

print ""
print cyl.dispersion['disp_radius']

cyl.dispersion['disp_radius']['width'] = 9.345

q=0.001
print "\n q=", q
print "New Cyl : ", cyl.run(q)

cyl.dispersion['disp_radius']['width']=5
cyl.dispersion['disp_radius']['npts']=100
print "New Disp: ", cyl.run(q)

# Angular averaging
values_ph = []
values_th = []
weights   = []
for i in range(100):
    values_ph.append(2.0*math.pi/99.0*i)
    values_th.append(math.pi/99.0*i)
    weights.append(1.0)



old_cyl()
