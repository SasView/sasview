
import VolumeCanvas
from sas.models.SphereModel import SphereModel
from sas.models.CoreShellModel import CoreShellModel

import math, time
    
def form_factor(q, r):
    qr = q*r
    f = 3*( math.sin(qr) - qr*math.cos(qr) ) / (qr*qr*qr)
    return f*f
    
def test_1():
    
    radius = 15
    
    density = .1
    vol = 4/3*math.pi*radius*radius*radius
    npts = vol*density
     
    canvas = VolumeCanvas.VolumeCanvas()
    canvas.setParam('lores_density', density)
    handle = canvas.add('sphere')
    canvas.setParam('%s.radius' % handle, radius)
    canvas.setParam('%s.contrast' % handle, 1.0)
    
    
    if False:
        # Time test
        t_0 = time.time()
        value_1 = 1.0e8*canvas.getIq(0.1)
        print "density = 0.1:  output=%g  time=%g" % (value_1, time.time()-t_0)
        
        t_0 = time.time()
        canvas.setParam('lores_density', 1)
        value_1 = 1.0e8*canvas.getIq(0.1)
        print "density = 1000:  output=%g  time=%g" % (value_1, time.time()-t_0)
        
        t_0 = time.time()
        canvas.setParam('lores_density', 0.01)
        value_1 = 1.0e8*canvas.getIq(0.1)
        print "density = 0.00001:  output=%g  time=%g" % (value_1, time.time()-t_0)
        print
    
    
    sphere = SphereModel()
    sphere.setParam('radius', radius)
    sphere.setParam('scale', 1.0)
    sphere.setParam('contrast', 1.0)
        
        
    # Simple sphere sum(Pr) = (rho*V)^2    
    # each p(r) point has a volume of 1/density    
        
    for i in range(35):
        q = 0.001 + 0.01*i
        
        
        
        #sim_1 = 1.0e8*canvas.getIq(q)*4/3*math.pi/(density*density*density)
        sim_1 = canvas.getIq(q)
        ana_1 = sphere.run(q)
        #ana_1 = form_factor(q, radius)
        
        print "q=%g  sim=%g  ana=%g   ratio=%g" % (q, sim_1, ana_1, sim_1/ana_1)
    
def test_2():
    radius = 15.0
    thickness = 5.0
    
    core_vol = 4.0/3.0*math.pi*radius*radius*radius
    outer_radius = radius+thickness
    shell_vol = 4.0/3.0*math.pi*outer_radius*outer_radius*outer_radius - core_vol
    shell_sld = -1.0*core_vol/shell_vol
    print "Shell SLD", shell_sld

    
    density = .1
    vol = 4/3*math.pi*radius*radius*radius
    npts = vol*density
     
    canvas = VolumeCanvas.VolumeCanvas()
    canvas.setParam('lores_density', density)
    handle = canvas.add('sphere')
    canvas.setParam('%s.radius' % handle, outer_radius)
    canvas.setParam('%s.contrast' % handle, shell_sld)
   
    handle2 = canvas.add('sphere')
    canvas.setParam('%s.radius' % handle2, radius)
    canvas.setParam('%s.contrast' % handle2, 1.0)
   
   
   
    # Core-shell
    sphere = CoreShellModel()
    # Core radius
    sphere.setParam('radius', radius)
    # Shell thickness
    sphere.setParam('thickness', thickness)
    sphere.setParam('core_sld', 1.0)
    
    
    sphere.setParam('shell_sld', shell_sld)
    sphere.setParam('solvent_sld',0.0)
    sphere.setParam('background',0.0)
    sphere.setParam('scale',1.0)
   
    out = open("lores_test.txt",'w')
    out.write("<q> <sim> <ana>\n")
    
    for i in range(65):
        q = 0.001 + 0.01*i
        
        # For each volume integral that we change to a sum,
        # we must multiply by 1/density = V/N
        # Since we want P(r)/V, we will need to multiply
        # the sum by 1/(N*density), where N is the number of
        # points without overlap. Since we already divide
        # by N when calculating I(q), we only need to divide
        # by the density here. We divide by N in the 
        # calculation because it is difficult to estimate it here.
        
        
        # Put the factor 2 in the simulation two...
        sim_1 = canvas.getIq(q)
        ana_1 = sphere.run(q)
        
        print "q=%g  sim=%g  ana=%g   ratio=%g" % (q, sim_1, ana_1, sim_1/ana_1)
        out.write( "%g  %g  %g\n" % (q, sim_1, ana_1))

    out.close()

def test_4():
    radius = 15
    
    density = .1
    vol = 4/3*math.pi*radius*radius*radius
    npts = vol*density

    
    canvas = VolumeCanvas.VolumeCanvas()
    canvas.setParam('lores_density', density)
    #handle = canvas.add('sphere')
    #canvas.setParam('%s.radius' % handle, radius)
    #canvas.setParam('%s.contrast' % handle, 1.0)
    
    pdb = canvas.add('test.pdb')
    
    
    
    sphere = SphereModel()
    sphere.setParam('radius', radius)
    sphere.setParam('scale', 1.0)
    sphere.setParam('contrast', 1.0)
        
        
    # Simple sphere sum(Pr) = (rho*V)^2    
    # each p(r) point has a volume of 1/density    
        
    for i in range(35):
        q = 0.001 + 0.01*i
        
        
        
        #sim_1 = 1.0e8*canvas.getIq(q)*4/3*math.pi/(density*density*density)
        sim_1 = canvas.getIq(q)
        ana_1 = sphere.run(q)
        #ana_1 = form_factor(q, radius)
        
        print "q=%g  sim=%g  ana=%g   ratio=%g" % (q, sim_1, ana_1, sim_1/ana_1)

def test_5():
    from sas.models.SphereModel import SphereModel
    model = VolumeCanvas.VolumeCanvas()
    
    handle = model.add('sphere')
    
    radius = 10
    density = .1
    
    ana = SphereModel()
    ana.setParam('scale', 1.0)
    ana.setParam('contrast', 1.0)
    ana.setParam('background', 0.0)
    ana.setParam('radius', radius)
    
    model.setParam('lores_density', density)
    model.setParam('%s.radius' % handle, radius)
    model.setParam('scale' , 1.0)
    model.setParam('%s.contrast' % handle, 1.0)
    model.setParam('background' , 0.0)
    
    ana = ana.runXY([0.1, 0.1])
    sim = model.getIq2D(0.1, 0.1)
    print ana, sim, sim/ana, ana/sim

def test_6():
    from sas.models.CylinderModel import CylinderModel
    radius = 5
    length = 40
    density = 20
    
    ana = CylinderModel()
    ana.setParam('scale', 1.0)
    ana.setParam('contrast', 1.0)
    ana.setParam('background', 0.0)
    ana.setParam('radius', radius)
    ana.setParam('length', length)
    
    # Along Y
    ana.setParam('cyl_theta', 1.57)
    ana.setParam('cyl_phi', 1.57)
    
    # Along Z
    #ana.setParam('cyl_theta', 0)
    #ana.setParam('cyl_phi', 0)
    
    model = VolumeCanvas.VolumeCanvas()    
    handle = model.add('cylinder')
    model.setParam('lores_density', density)
    model.setParam('%s.radius' % handle, radius)
    model.setParam('%s.length' % handle, length)
    model.setParam('scale' , 1.0)
    model.setParam('%s.contrast' % handle, 1.0)
    model.setParam('background' , 0.0)
    
    # Along Y
    model.setParam('%s.orientation' % handle, [0,0,0])
    
    # Along Z
    #model.setParam('%s.orientation' % handle, [1.57,0,0])
    
    
    print model.npts
    for i in range(40):
        qmax = 0.5
        anaX = ana.runXY([qmax*i/40.0, 0.0])
        simX = model.getIq2D(qmax*i/40.0, 0.0)
        
        anaY = ana.runXY([0, qmax*i/40.0])
        simY = model.getIq2D(0, qmax*i/40.0)
        print anaX, simX, simX/anaX, '|', anaY, simY, simY/anaY
    
def test_7():
    from sas.models.CoreShellModel import CoreShellModel
    print "Testing core-shell"
    radius = 15
    thickness = 5
    density = 5
    
    core_vol = 4.0/3.0*math.pi*radius*radius*radius
    outer_radius = radius+thickness
    shell_vol = 4.0/3.0*math.pi*outer_radius*outer_radius*outer_radius - core_vol
    shell_sld = -1.0*core_vol/shell_vol

    # Core-shell
    sphere = CoreShellModel()
    # Core radius
    sphere.setParam('radius', radius)
    # Shell thickness
    sphere.setParam('thickness', thickness)
    sphere.setParam('core_sld', 1.0)
    sphere.setParam('shell_sld', shell_sld)
    sphere.setParam('solvent_sld', 0.0)
    sphere.setParam('background', 0.0)
    sphere.setParam('scale', 1.0)
    ana = sphere
   
    canvas = VolumeCanvas.VolumeCanvas()        
    canvas.setParam('lores_density', density)
    
    handle = canvas.add('sphere')
    canvas.setParam('%s.radius' % handle, outer_radius)
    canvas.setParam('%s.contrast' % handle, shell_sld)
   
    handle2 = canvas.add('sphere')
    canvas.setParam('%s.radius' % handle2, radius)
    canvas.setParam('%s.contrast' % handle2, 1.0)
           
    canvas.setParam('scale' , 1.0)
    canvas.setParam('background' , 0.0)
    
               
    """ Testing default core-shell orientation """
    qlist = [.0001, 0.002, .01, .1, 1.0, 5.]
    for q in qlist:
        ana_val = ana.runXY([q, 0.2])
        sim_val, err = canvas.getIq2DError(q, 0.2)
        print ana_val, sim_val, sim_val/ana_val, err, (sim_val-ana_val)/err
    
    
    
if __name__ == "__main__":
    test_6()
