"""
    Unit tests for specific oriented models
    @copyright: University of Tennessee, for the DANSE project
"""
from __future__ import print_function

import unittest, math, sys

# Disable "missing docstring" complaint
# pylint: disable-msg=C0111
# Disable "too many methods" complaint
# pylint: disable-msg=R0904
# Disable "could be a function" complaint
# pylint: disable-msg=R0201
# pylint: disable-msg=W0702

from sasmodels.sasview_model import _make_standard_model
EllipsoidModel = _make_standard_model('ellipsoid')
SphereModel = _make_standard_model('sphere')
CylinderModel = _make_standard_model('cylinder')
CoreShellModel = _make_standard_model('core_shell_sphere')

import sas.sascalc.realspace.VolumeCanvas as VolumeCanvas



class TestSphere(unittest.TestCase):
    """ Tests for oriented (2D) systems """

    def setUp(self):
        """
            Set up canvas
        """
        self.model = VolumeCanvas.VolumeCanvas()

        handle = self.model.add('sphere')

        radius = 10
        density = .1

        ana = SphereModel()
        ana.setParam('scale', 1.0)
        ana.setParam('background', 0.0)
        ana.setParam('sld', 1.0)
        ana.setParam('sld_solvent', 0.0)
        ana.setParam('radius', radius)
        self.ana = ana

        self.model.setParam('lores_density', density)
        self.model.setParam('scale' , 1.0)
        self.model.setParam('background' , 0.0)
        self.model.setParam('%s.contrast' % handle, 1.0)
        self.model.setParam('%s.radius' % handle, radius)


    def testdefault(self):
        """ Testing sphere """
        # Default orientation
        ana_val = self.ana.runXY([0.1, 0.1])
        sim_val = self.model.getIq2D(0.1, 0.1)
        self.assert_( math.fabs(sim_val/ana_val-1.0)<0.1 )

class TestCylinderAddObject(unittest.TestCase):
    """ Tests for oriented (2D) systems """

    def setUp(self):
        """ Set up cylinder model """
        radius = 5
        length = 40
        density = 20

        # Analytical model
        self.ana = CylinderModel()
        self.ana.setParam('scale', 1.0)
        self.ana.setParam('background', 0.0)
        self.ana.setParam('sld', 1.0)
        self.ana.setParam('sld_solvent', 0.0)
        self.ana.setParam('radius', radius)
        self.ana.setParam('length', length)

        # Simulation model
        self.model = VolumeCanvas.VolumeCanvas()
        cyl = VolumeCanvas.CylinderDescriptor()
        self.handle = self.model.addObject(cyl)
        self.model.setParam('lores_density', density)
        self.model.setParam('scale' , 1.0)
        self.model.setParam('background' , 0.0)
        self.model.setParam('%s.contrast' % self.handle, 1.0)
        self.model.setParam('%s.radius' % self.handle, radius)
        self.model.setParam('%s.length' % self.handle, length)

    def testalongY(self):
        """ Testing cylinder along Y axis """
        self.ana.setParam('theta', math.pi/2.0)
        self.ana.setParam('phi', math.pi/2.0)

        self.model.setParam('%s.orientation' % self.handle, [0,0,0])

        ana_val = self.ana.runXY([0.1, 0.2])
        sim_val = self.model.getIq2D(0.1, 0.2)
        #print ana_val, sim_val, sim_val/ana_val

        self.assert_( math.fabs(sim_val/ana_val-1.0)<0.05 )


class TestCylinder(unittest.TestCase):
    """ Tests for oriented (2D) systems """

    def setUp(self):
        """ Set up cylinder model """
        radius = 5
        length = 40
        density = 20

        # Analytical model
        self.ana = CylinderModel()
        self.ana.setParam('scale', 1.0)
        self.ana.setParam('background', 0.0)
        self.ana.setParam('sld', 1.0)
        self.ana.setParam('sld_solvent', 0.0)
        self.ana.setParam('radius', radius)
        self.ana.setParam('length', length)

        # Simulation model
        self.model = VolumeCanvas.VolumeCanvas()
        self.handle = self.model.add('cylinder')
        self.model.setParam('lores_density', density)
        self.model.setParam('scale' , 1.0)
        self.model.setParam('background' , 0.0)
        self.model.setParam('%s.radius' % self.handle, radius)
        self.model.setParam('%s.length' % self.handle, length)
        self.model.setParam('%s.contrast' % self.handle, 1.0)

    def testalongY(self):
        """ Testing cylinder along Y axis """
        self.ana.setParam('theta', math.pi/2.0)
        self.ana.setParam('phi', math.pi/2.0)

        self.model.setParam('%s.orientation' % self.handle, [0,0,0])

        ana_val = self.ana.runXY([0.1, 0.2])
        sim_val = self.model.getIq2D(0.1, 0.2)
        #print ana_val, sim_val, sim_val/ana_val

        self.assert_( math.fabs(sim_val/ana_val-1.0)<0.05 )

    def testalongZ(self):
        """ Testing cylinder along Z axis """
        self.ana.setParam('theta', 0)
        self.ana.setParam('phi', 0)

        self.model.setParam('%s.orientation' % self.handle, [90,0,0])

        ana_val = self.ana.runXY([0.1, 0.2])
        sim_val = self.model.getIq2D(0.1, 0.2)
        #print ana_val, sim_val, sim_val/ana_val

        self.assert_( math.fabs(sim_val/ana_val-1.0)<0.05 )

    def testalongX(self):
        """ Testing cylinder along X axis """
        self.ana.setParam('theta', 1.57)
        self.ana.setParam('phi', 0)

        self.model.setParam('%s.orientation' % self.handle, [0,0,90])

        ana_val = self.ana.runXY([0.1, 0.2])
        sim_val = self.model.getIq2D(0.1, 0.2)
        #print ana_val, sim_val, sim_val/ana_val

        self.assert_( math.fabs(sim_val/ana_val-1.0)<0.05 )

class TestEllipsoid(unittest.TestCase):
    """ Tests for oriented (2D) systems """

    def setUp(self):
        """ Set up ellipsoid """

        radius_a = 60
        radius_b = 10
        density = 30

        self.ana = EllipsoidModel()
        self.ana.setParam('scale', 1.0)
        self.ana.setParam('background', 0.0)
        self.ana.setParam('sld', 1.0)
        self.ana.setParam('sld_solvent', 0.0)
        self.ana.setParam('radius_polar', radius_a)
        self.ana.setParam('radius_equatorial', radius_b)
        # Default orientation is there=1.57, phi=0
        # Radius_a is along the x direction

        canvas = VolumeCanvas.VolumeCanvas()
        self.handle = canvas.add('ellipsoid')
        canvas.setParam('lores_density', density)
        canvas.setParam('scale' , 1.0)
        canvas.setParam('background' , 0.0)
        canvas.setParam('%s.radius_x' % self.handle, radius_a)
        canvas.setParam('%s.radius_y' % self.handle, radius_b)
        canvas.setParam('%s.radius_z' % self.handle, radius_b)
        canvas.setParam('%s.contrast' % self.handle, 1.0)
        self.canvas = canvas

    def testalongX(self):
        """ Testing ellipsoid along X """
        self.ana.setParam('theta', 1.57)
        self.ana.setParam('phi', 0)

        self.canvas.setParam('%s.orientation' % self.handle, [0,0,0])

        ana_val = self.ana.runXY([0.1, 0.2])
        sim_val = self.canvas.getIq2D(0.1, 0.2)
        #print ana_val, sim_val, sim_val/ana_val

        self.assert_( math.fabs(sim_val/ana_val-1.0)<0.05 )

    def testalongZ(self):
        """ Testing ellipsoid along Z """
        self.ana.setParam('theta', 0)
        self.ana.setParam('phi', 0)

        self.canvas.setParam('%s.orientation' % self.handle, [0,90,0])

        ana_val = self.ana.runXY([0.1, 0.2])
        sim_val = self.canvas.getIq2D(0.1, 0.2)
        #print ana_val, sim_val, sim_val/ana_val

        self.assert_( math.fabs(sim_val/ana_val-1.0)<0.05 )

    def testalongY(self):
        """ Testing ellipsoid along Y """
        self.ana.setParam('theta', math.pi/2.0)
        self.ana.setParam('phi', math.pi/2.0)

        self.canvas.setParam('%s.orientation' % self.handle, [0,0,90])

        ana_val = self.ana.runXY([0.05, 0.15])
        sim_val = self.canvas.getIq2D(0.05, 0.15)
        #print ana_val, sim_val, sim_val/ana_val

        try:
            self.assert_( math.fabs(sim_val/ana_val-1.0)<0.05 )
        except Exception:
            print("Error", ana_val, sim_val, sim_val/ana_val)
            raise

class TestCoreShell(unittest.TestCase):
    """ Tests for oriented (2D) systems """

    def setUp(self):
        """ Set up zero-SLD-average core-shell model """

        radius = 15
        thickness = 5
        density = 20

        core_vol = 4.0/3.0*math.pi*radius*radius*radius
        self.outer_radius = radius+thickness
        shell_vol = 4.0/3.0*math.pi*self.outer_radius*self.outer_radius*self.outer_radius - core_vol
        self.shell_sld = -1.0*core_vol/shell_vol

        self.density = density

        # Core-shell
        sphere = CoreShellModel()
        sphere.setParam('scale', 1.0)
        sphere.setParam('background', 0.0)
        # Core radius
        sphere.setParam('radius', radius)
        # Shell thickness
        sphere.setParam('thickness', thickness)
        sphere.setParam('sld_core', 1.0)
        sphere.setParam('sld_shell', self.shell_sld)
        sphere.setParam('sld_solvent', 0.0)
        self.ana = sphere

        canvas = VolumeCanvas.VolumeCanvas()
        canvas.setParam('lores_density', self.density)
        canvas.setParam('scale' , 1.0)
        canvas.setParam('background' , 0.0)

        handle = canvas.add('sphere')
        canvas.setParam('%s.radius' % handle, self.outer_radius)
        canvas.setParam('%s.contrast' % handle, self.shell_sld)

        handle2 = canvas.add('sphere')
        canvas.setParam('%s.radius' % handle2, radius)
        canvas.setParam('%s.contrast' % handle2, 1.0)

        self.canvas = canvas

    def testdefault(self):
        """ Testing default core-shell orientation """
        ana_val = self.ana.runXY([0.1, 0.2])
        sim_val, err = self.canvas.getIq2DError(0.1, 0.2)

        self.assert_( math.fabs(sim_val/ana_val-1.0)<0.05 )

class TestCoreShellError(unittest.TestCase):
    """ Tests for oriented (2D) systems """

    def setUp(self):
        """ Set up zero-SLD-average core-shell model """

        radius = 15
        thickness = 5
        density = 5

        core_vol = 4.0/3.0*math.pi*radius*radius*radius
        self.outer_radius = radius+thickness
        shell_vol = 4.0/3.0*math.pi*self.outer_radius*self.outer_radius*self.outer_radius - core_vol
        self.shell_sld = -1.0*core_vol/shell_vol

        self.density = density

        # Core-shell
        sphere = CoreShellModel()
        sphere.setParam('scale', 1.0)
        sphere.setParam('background', 0.0)
        # Core radius
        sphere.setParam('radius', radius)
        # Shell thickness
        sphere.setParam('thickness', thickness)
        sphere.setParam('sld_core', 1.0)
        sphere.setParam('sld_shell', self.shell_sld)
        sphere.setParam('sld_solvent', 0.0)
        self.ana = sphere

        canvas = VolumeCanvas.VolumeCanvas()
        canvas.setParam('lores_density', self.density)
        canvas.setParam('scale' , 1.0)
        canvas.setParam('background' , 0.0)

        handle = canvas.add('sphere')
        canvas.setParam('%s.radius' % handle, self.outer_radius)
        canvas.setParam('%s.contrast' % handle, self.shell_sld)

        handle2 = canvas.add('sphere')
        canvas.setParam('%s.radius' % handle2, radius)
        canvas.setParam('%s.contrast' % handle2, 1.0)

        self.canvas = canvas

    def testdefault(self):
        """ Testing default core-shell orientation """
        ana_val = self.ana.runXY([0.1, 0.2])
        sim_val, err = self.canvas.getIq2DError(0.1, 0.2)

        self.assert_( math.fabs(sim_val-ana_val) < 3.0 * err )

class TestRunMethods(unittest.TestCase):
    """ Tests run methods for oriented (2D) systems """

    def setUp(self):
        """ Set up ellipsoid """

        radius_a = 10
        radius_b = 15
        density = 5

        self.ana = EllipsoidModel()
        self.ana.setParam('scale', 1.0)
        self.ana.setParam('background', 0.0)
        self.ana.setParam('sld', 1.0)
        self.ana.setParam('sld_solvent', 1.0)
        self.ana.setParam('radius_polar', radius_a)
        self.ana.setParam('radius_equatorial', radius_b)


        canvas = VolumeCanvas.VolumeCanvas()
        self.handle = canvas.add('ellipsoid')
        canvas.setParam('lores_density', density)
        canvas.setParam('scale' , 1.0)
        canvas.setParam('background' , 0.0)
        canvas.setParam('%s.radius_x' % self.handle, radius_a)
        canvas.setParam('%s.radius_y' % self.handle, radius_b)
        canvas.setParam('%s.radius_z' % self.handle, radius_b)
        canvas.setParam('%s.contrast' % self.handle, 1.0)
        self.canvas = canvas

        self.ana.setParam('theta', 1.57)
        self.ana.setParam('phi', 0)

        self.canvas.setParam('%s.orientation' % self.handle, [0,0,0])


    def testRunXY_List(self):
        """ Testing ellipsoid along X """
        ana_val = self.ana.runXY([0.1, 0.2])
        sim_val = self.canvas.runXY([0.1, 0.2])
        #print ana_val, sim_val, sim_val/ana_val

        try:
            self.assert_( math.fabs(sim_val/ana_val-1.0)<0.05 )
        except Exception:
            print("Error", ana_val, sim_val, sim_val/ana_val)
            raise

    def testRunXY_float(self):
        """ Testing ellipsoid along X """
        ana_val = self.ana.runXY(0.1)
        sim_val = self.canvas.runXY(0.1)
        #print ana_val, sim_val, sim_val/ana_val

        try:
            self.assert_( math.fabs(sim_val/ana_val-1.0)<0.05 )
        except Exception:
            print("Error", ana_val, sim_val, sim_val/ana_val)
            raise

    def testRun_float(self):
        """ Testing ellipsoid along X """
        ana_val = self.ana.run(0.1)
        sim_val = self.canvas.run(0.1)
        #print ana_val, sim_val, sim_val/ana_val

        try:
            self.assert_( math.fabs(sim_val/ana_val-1.0)<0.05 )
        except Exception:
            print("Error", ana_val, sim_val, sim_val/ana_val)
            raise

    def testRun_list(self):
        """ Testing ellipsoid along X """
        ana_val = self.ana.run([0.1, 33.0])
        sim_val = self.canvas.run([0.1, 33.0])
        #print ana_val, sim_val, sim_val/ana_val

        try:
            self.assert_( math.fabs(sim_val/ana_val-1.0)<0.05 )
        except Exception:
            print("Error", ana_val, sim_val, sim_val/ana_val)
            raise

class TestParamChange(unittest.TestCase):
    """ Tests for oriented (2D) systems """

    def setUp(self):
        """ Set up cylinder model """
        radius = 5
        length = 40
        density = 20

        # Analytical model
        self.ana = CylinderModel()
        self.ana.setParam('scale', 1.0)
        self.ana.setParam('background', 0.0)
        self.ana.setParam('sld', 1.0)
        self.ana.setParam('sld_solvent', 0.0)
        self.ana.setParam('radius', radius)
        self.ana.setParam('length', length)
        self.ana.setParam('theta', math.pi/2.0)
        self.ana.setParam('phi', math.pi/2.0)

        # Simulation model
        self.model = VolumeCanvas.VolumeCanvas()
        self.handle = self.model.add('cylinder')
        self.model.setParam('lores_density', density)
        self.model.setParam('scale' , 1.0)
        self.model.setParam('background' , 0.0)
        self.model.setParam('%s.radius' % self.handle, radius)
        self.model.setParam('%s.length' % self.handle, length)
        self.model.setParam('%s.contrast' % self.handle, 1.0)
        self.model.setParam('%s.orientation' % self.handle, [0,0,0])

    def testalongY(self):
        """ Test that a parameter change forces the generation
            of new space points
        """
        ana_val = self.ana.runXY([0.1, 0.2])
        sim_val = self.model.getIq2D(0.1, 0.2)

        self.assert_( math.fabs(sim_val/ana_val-1.0)<0.05 )

        # Change the radius a re-evaluate
        self.ana.setParam('radius', 10)
        self.model.setParam('%s.radius' % self.handle, 10)

        ana_val = self.ana.runXY([0.1, 0.2])
        sim_val = self.model.getIq2D(0.1, 0.2)
        self.assert_( math.fabs(sim_val/ana_val-1.0)<0.05 )


if __name__ == '__main__':
    unittest.main()
