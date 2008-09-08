from sans_extension.prototypes.c_models import CCanvas
from sans.models.SphereModel import SphereModel
from sans.models.CoreShellModel import CoreShellModel

import math

# Sphere ###############################
sphere = SphereModel()
sphere.setParam('radius',40.0)
sphere.setParam('contrast',1.0)
sphere.setParam('scale',1.0)
sphere.setParam('background',0.0)

can = CCanvas()

print "ID", can.add()
can.setParam(0,1,40.0)
 

for q in [1,0.1,0.05,0.02,0.01,0.001,0.0001]:
    ana = sphere.run([q,1.0])
    sim = can.evaluate([q,1.0])

    print "Sphere: ANA = %g   SIM = %g   (%g)" %(ana, sim, sim/ana)




# Core-shell ###########################
# This is a core shell model where the weight-average
# of the SLDs is zero. The I(q) should go to zero as q->0.

import time
t_0 = time.time()

sphere = CoreShellModel()
# Core radius
radius = 10.0
thickness = 5.0
sphere.setParam('radius', radius)
# Shell thickness
sphere.setParam('thickness', thickness)
sphere.setParam('core_sld', 1.0)

core_vol = 4.0/3.0*math.pi*radius*radius*radius
outer_radius = radius+thickness
shell_vol = 4.0/3.0*math.pi*outer_radius*outer_radius*outer_radius - core_vol
shell_sld = -1.0*core_vol/shell_vol
print "Shell SLD", shell_sld

sphere.setParam('shell_sld', shell_sld)
sphere.setParam('solvent_sld',0.0)
sphere.setParam('background',0.0)
sphere.setParam('scale',1.0)

can = CCanvas()

print "ID", can.add()
can.setParam(0,1, outer_radius)
can.setParam(0,2, shell_sld)


print "ID", can.add()
can.setParam(1,1, radius)
can.setParam(1,2, 1.0)

print "VOLS inner = %g, outer = %g, shell = %g" % (core_vol, shell_vol+core_vol, shell_vol)

f = open('core-shell.txt','w')
f.write("<q_cs>   <ans_cs>   <sim_cs>\n")
for q in [1,0.1,0.05,0.04,0.03,0.02,0.01,0.005,0.001,0.0001]:
#for i in range(400):
    #q = 0.0001+i*0.005
    ana = sphere.run([q,1.0])
    sim = can.evaluate([q,1.0])
    f.write("%g  %g  %g\n" %(q, ana, sim))
    print "Core-shell: q=%g  ANA = %g   SIM = %g   (%g)" %(q, ana, sim, sim/ana)

f.close()


print "Time: ", time.time()-t_0