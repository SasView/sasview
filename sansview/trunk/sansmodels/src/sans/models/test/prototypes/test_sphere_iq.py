try:
    from sans.models.prototypes.SimSphereF import SimSphereF
except:
    print "This test uses the prototypes module."
from sans.models.SphereModel import SphereModel
import math, time



sim = SimSphereF()
sph = SphereModel()

sim.setParam('radius', 60)
sim.setParam('npoints', 50000)

sph.setParam('radius', 60)
sph.setParam('scale', 1)


f = open('sim_iq.txt', 'w')
f.write("<q>  <ana>  <sim> <err>\n")

t_0 = time.time()

#for i in range(60):
for i in range(100):
    #q = 0.01 * (i+1) /3.0
    q = 0.05 + 0.20*(i+1) /100
    
    ana_value = sph.run([q,0])
    sim_value = sim.run([q,0])
#    ana_value = sph.run(q)
#    sim_value = sim.run(q)
    ratio = 0
    if sim_value>0:
        ratio = sim_value/ana_value
    print q, ana_value, sim_value, ratio
    f.write("%10g %10g %10g %10g\n" % (q, ana_value, sim_value, (sim_value-ana_value)/ana_value))

t_f = time.time()
print "Time = ", t_f-t_0
f.close()

