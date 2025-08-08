"""
    Validation tests for real-space simulation of I(q)

    @copyright: University of Tennessee, 2007
    @license: This software is provided as part of the DANSE project
"""

import math
import time

import pylab

try:
    import VolumeCanvas
    print("Testing local version")
except ImportError:
    print("Testing installed version")
    import sas.sascalc.realspace.VolumeCanvas as VolumeCanvas

class Validator:

    def __init__(self):
        self.density = 0.1
        self.canvas  = None
        self.ana     = None
        self.create()

    def create(self):
        pass

    def run_sim2D(self, qx, qy, density=None):
        """
            Calculate the mean and error of the simulation
            @param q: q-value to calculate at
            @param density: point density of simulation
            #return: mean, error
        """
        if density is not None:
            self.density = density
            self.create()

        return self.canvas.getIq2DError(qx, qy)

    def run_sim(self, q, density=None):
        """
            Calculate the mean and error of the simulation
            @param q: q-value to calculate at
            @param density: point density of simulation
            #return: mean, error
        """
        if density is not None:
            self.density = density
            self.create()

        return self.canvas.getIqError(q)

    def run_ana2D(self, qx, qy):
        """
            Return analytical value
            @param q: q-value to evaluate at [float]
            @return: analytical output [float]
        """
        return self.ana.runXY([qx, qy])

    def run_ana(self, q):
        """
            Return analytical value
            @param q: q-value to evaluate at [float]
            @return: analytical output [float]
        """
        return self.ana.run(q)

class SphereValidator(Validator):

    def __init__(self, radius=15, density = 0.01):
        from sas.models.SphereModel import SphereModel

        self.name = 'sphere'
        self.radius = radius
        self.density = density

        self.ana = SphereModel()
        self.ana.setParam('scale', 1.0)
        self.ana.setParam('contrast', 1.0)
        self.ana.setParam('background', 0.0)
        self.ana.setParam('radius', radius)
        self.create()

    def create(self):
        canvas = VolumeCanvas.VolumeCanvas()
        canvas.setParam('lores_density', self.density)
        handle = canvas.add('sphere')
        canvas.setParam('%s.radius' % handle, self.radius)
        canvas.setParam('scale' , 1.0)
        canvas.setParam('%s.contrast' % handle, 1.0)
        canvas.setParam('background' , 0.0)
        self.canvas = canvas

class CylinderValidator(Validator):

    def __init__(self, radius=15, length=100, density = 0.01):
        from sas.models.CylinderModel import CylinderModel

        self.name = 'cylinder'
        self.radius = radius
        self.length = length
        self.density = density

        self.ana = CylinderModel()
        self.ana.setParam('scale', 1.0)
        self.ana.setParam('contrast', 1.0)
        self.ana.setParam('background', 0.0)
        self.ana.setParam('radius', radius)
        self.ana.setParam('length', length)
        self.ana.setParam('cyl_theta', math.pi/2.0)
        self.ana.setParam('cyl_phi', math.pi/2.0)
        self.create()

    def create(self):
        canvas = VolumeCanvas.VolumeCanvas()
        canvas.setParam('lores_density', self.density)
        handle = canvas.add('cylinder')
        canvas.setParam('%s.radius' % handle, self.radius)
        canvas.setParam('%s.length' % handle, self.length)
        canvas.setParam('scale' , 1.0)
        canvas.setParam('%s.contrast' % handle, 1.0)
        canvas.setParam('background' , 0.0)
        self.canvas = canvas

class EllipsoidValidator(Validator):

    def __init__(self, radius_a=60, radius_b=10, density = 0.01):
        from sas.models.EllipsoidModel import EllipsoidModel
        #from sas.models.SphereModel import SphereModel

        self.name = 'ellipsoid'
        self.radius_a = radius_a
        self.radius_b = radius_b
        self.density = density

        self.ana = EllipsoidModel()
        #self.ana = SphereModel()
        self.ana.setParam('scale', 1.0)
        self.ana.setParam('contrast', 1.0)
        self.ana.setParam('background', 0.0)
        self.ana.setParam('radius_a', radius_a)
        self.ana.setParam('radius_b', radius_b)
        #self.ana.setParam('radius', radius_a)

        # Default orientation is there=1.57, phi=0
        # Radius_a is along the x direction

        self.create()

    def create(self):
        canvas = VolumeCanvas.VolumeCanvas()
        canvas.setParam('lores_density', self.density)
        handle = canvas.add('ellipsoid')
        canvas.setParam('%s.radius_x' % handle, self.radius_a)
        canvas.setParam('%s.radius_y' % handle, self.radius_b)
        canvas.setParam('%s.radius_z' % handle, self.radius_b)
        canvas.setParam('scale' , 1.0)
        canvas.setParam('%s.contrast' % handle, 1.0)
        canvas.setParam('background' , 0.0)
        self.canvas = canvas

class HelixValidator(Validator):

    def __init__(self, density = 0.01):
        self.name = 'helix'
        self.density = density
        self.create()

    def create(self):
        canvas = VolumeCanvas.VolumeCanvas()
        canvas.setParam('lores_density', self.density)
        handle = canvas.add('singlehelix')
        canvas.setParam('scale' , 1.0)
        canvas.setParam('%s.contrast' % handle, 1.0)
        canvas.setParam('background' , 0.0)
        self.canvas = canvas
        # just to write the parameters to the output file
        self.ana = canvas

    def run_ana(self, q):
        return 1


class CoreShellValidator(Validator):

    def __init__(self, radius=15, thickness=5, density = 0.01):
        from sas.models.CoreShellModel import CoreShellModel

        self.name = 'coreshell'
        self.radius = radius

        core_vol = 4.0/3.0*math.pi*radius*radius*radius
        self.outer_radius = radius+thickness
        shell_vol = 4.0/3.0*math.pi*self.outer_radius*self.outer_radius*self.outer_radius - core_vol
        self.shell_sld = -1.0*core_vol/shell_vol

        self.density = density

        # Core-shell
        sphere = CoreShellModel()
        # Core radius
        sphere.setParam('radius', self.radius)
        # Shell thickness
        sphere.setParam('thickness', thickness)
        sphere.setParam('core_sld', 1.0)
        sphere.setParam('shell_sld', self.shell_sld)
        sphere.setParam('solvent_sld', 0.0)
        sphere.setParam('background', 0.0)
        sphere.setParam('scale', 1.0)
        self.ana = sphere
        self.create()

    def create(self):
        canvas = VolumeCanvas.VolumeCanvas()
        canvas.setParam('lores_density', self.density)

        handle = canvas.add('sphere')
        canvas.setParam('%s.radius' % handle, self.outer_radius)
        canvas.setParam('%s.contrast' % handle, self.shell_sld)

        handle2 = canvas.add('sphere')
        canvas.setParam('%s.radius' % handle2, self.radius)
        canvas.setParam('%s.contrast' % handle2, 1.0)

        canvas.setParam('scale' , 1.0)
        canvas.setParam('background' , 0.0)
        self.canvas = canvas

def validate_model(validator, q_min, q_max, n_q):
    """
         Validate a model
         An output file containing a comparison between
         simulation and the analytical solution will be
         produced.

         @param validator: validator object
         @param q_min: minimum q
         @param q_max: maximum q
         @param n_q: number of q points
         @param N: number of times to evaluate each simulation point
    """

    q_list = pylab.arange(q_min, q_max*1.0001, (q_max-q_min)/(n_q-1))

    output = open('%s_d=%g_Iq.txt' % (validator.name, validator.density), 'w')
    output.write("PARS: %s\n" % validator.ana.params)
    output.write("<q>  <ana>  <sim>  <err>\n")
    for q in q_list:
        ana = validator.run_ana(q)
        sim, err = validator.run_sim(q)
        print("q=%-g  ana=%-g  sim=%-g  err=%-g  diff=%-g (%-g) %s" % (q, ana, sim, err,
                        (sim-ana), sim/ana, str(math.fabs(sim-ana)>err)))
        output.write("%g  %g  %g  %g\n" % (q, ana, sim, err))
    output.close()

def validate_model_2D(validator, q_min, q_max, phi, n_q):
    """
         Validate a model
         An output file containing a comparison between
         simulation and the analytical solution will be
         produced.

         @param validator: validator object
         @param q_min: minimum q
         @param q_max: maximum q
         @param n_q: number of q points
         @param N: number of times to evaluate each simulation point
    """

    q_list = pylab.arange(q_min, q_max*1.0001, (q_max-q_min)/(n_q-1))

    output = open('%s_d=%g_Iq2D.txt' % (validator.name, validator.density), 'w')
    output.write("PARS: %s\n" % validator.ana.params)
    output.write("<q>  <ana>  <sim>  <err>\n")
    t_0 = time.time()
    for q in q_list:
        ana = validator.run_ana2D(q*math.cos(phi), q*math.sin(phi))
        sim, err = validator.run_sim2D(q*math.cos(phi), q*math.sin(phi))
        print("q=%-g  ana=%-g  sim=%-g  err=%-g  diff=%-g (%-g) %s" % (q, ana, sim, err,
                        (sim-ana), sim/ana, str(math.fabs(sim-ana)>err)))
        output.write("%g  %g  %g  %g\n" % (q, ana, sim, err))
    print("Time elapsed: ", time.time()-t_0)
    output.close()

def check_density(validator, q, d_min, d_max, n_d):
    """
       Check simulation output as a function of the density
       An output file containing a comparison between
       simulation and the analytical solution will be
       produced.

       @param validator: validator object
       @param q: q-value to evaluate at
       @param d_min: minimum density
       @param d_max: maximum density
       @param n_d: number of density points
       @param N: number of times to evaluate each simulation point
    """
    d_list = pylab.arange(d_min, d_max*1.0001, (d_max-d_min)/(n_d-1.0))

    output = open('%s_%g_density.txt' % (validator.name, q), 'w')
    output.write("PARS: %s\n" % validator.ana.params)
    output.write("<density>  <ana_d>  <sim_d>  <err_d>\n")
    ana = validator.run_ana(q)
    for d in d_list:
        sim, err = validator.run_sim(q, density=d)
        print("d=%-g  ana=%-g  sim=%-g  err=%-g  diff=%-g (%g) %s" % \
            (d, ana, sim, err, (sim-ana), (sim-ana)/ana,
             str(math.fabs(sim-ana)>err)))
        output.write("%g  %g  %g  %g \n" % (d, ana, sim, err))
    output.close()


if __name__ == '__main__':

    # 2D: Density=5, 71.2 secs for 50 points
    #vali = CoreShellValidator(radius = 15, thickness=5, density = 5.0)
    #validate_model(vali, q_min=0.001, q_max=1, n_q=50)
    #validate_model_2D(vali, q_min=0.001, q_max=1, phi=1.0, n_q=50)

    # 2D: Density=2, 11.1 secs for 25 points
    #vali = SphereValidator(radius = 20, density = 0.02)
    #validate_model(vali, q_min=0.001, q_max=0.5, n_q=25)
    #vali = SphereValidator(radius = 20, density = 2.0)
    #validate_model_2D(vali, q_min=0.001, q_max=0.5, phi=1.0, n_q=25)

    # 2D: Density=1, 19.4 secs for 25 points
    # 2D: Density=0.5, 9.8 secs for 25 points
    #vali = CylinderValidator(radius = 20, length=100, density = 0.1)
    #validate_model(vali, q_min=0.001, q_max=0.5, n_q=25)
    vali = CylinderValidator(radius = 20, length=100, density = 0.5)
    validate_model_2D(vali, q_min=0.001, q_max=0.2, phi=1.0, n_q=25)

    # 2D: Density=0.5, 2.26 secs for 25 points
    #vali = EllipsoidValidator(radius_a = 20, radius_b=15, density = 0.05)
    #validate_model(vali, q_min=0.001, q_max=0.5, n_q=25)
    #vali = EllipsoidValidator(radius_a = 20, radius_b=15, density = 0.5)
    #validate_model_2D(vali, q_min=0.001, q_max=0.5, phi=1.0, n_q=25)

    #vali = HelixValidator(density = 0.05)
    #validate_model(vali, q_min=0.001, q_max=0.5, n_q=25)


