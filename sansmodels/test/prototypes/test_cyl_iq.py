try:
    from sans.models.prototypes.TestSphere2 import TestSphere2
    from sans.models.prototypes.SimCylinderF import SimCylinderF
    from sans.models.prototypes.SimCylinder import SimCylinder
except:
    print "This test uses the prototypes module."
from sans.models.SphereModel import SphereModel
from sans.models.CylinderModel import CylinderModel
import math, time


def test_lores():

    lores = open('lores.iq', 'r')
    f = open('lores_check.txt', 'w')
    content = lores.read()
    lines = content.split('\n')
    inum = 0
    norma = 0.
    for line in lines:
        toks = line.split()
        if len(toks)==2:
            inum += 1
            q = float(toks[0])
            ana = sph.run(q)
            if inum==1:
                continue
            elif inum==2:
                norma = ana/float(toks[1])
            lor = float(toks[1])*norma
            f.write("%g %g %g\n" % (q, ana, lor))
    f.close()
            

#sim = TestSphere2()
#sph = SphereModel()
sim = SimCylinderF()
sph = CylinderModel()

sim.setParam('radius', 20)
sim.setParam('length', 200)
sim.setParam('phi', 1)
sim.setParam('theta', 1)
sim.setParam('npoints',2500)
#print sph.params

sph.setParam('radius', 20)
sph.setParam('scale', 1)
sph.setParam('contrast',1)
sph.setParam('length', 200)
sph.setParam('cyl_phi', 1)
sph.setParam('cyl_theta', 1)

#print "ANA", sph.run(0.1)
#print "SIM", sim.run(0.1)

f = open('sim_iq.txt', 'w')
f.write("<q>  <ana>  <sim>\n")

t_0 = time.time()

for i in range(60):
    q = 0.01 * (i+1) /3.0
    #ana_value = sph.run([q,0])
    #sim_value = sim.run([q,0])
    ana_value = sph.run(q)
    sim_value = sim.run(q)
    ratio = 0
    if sim_value>0:
        ratio = sim_value/ana_value
    print q, ana_value, sim_value, ratio
    f.write("%10g %10g %10g\n" % (q, ana_value, sim_value))

t_f = time.time()
print "Time = ", t_f-t_0
f.close()

