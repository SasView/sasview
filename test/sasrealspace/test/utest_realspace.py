"""
    Unit tests for specific models
    @author: Mathieu Doucet / UTK
"""
from __future__ import print_function

import unittest, math, time

# Disable "missing docstring" complaint
# pylint: disable-msg=C0111
# Disable "too many methods" complaint
# pylint: disable-msg=R0904
# Disable "could be a function" complaint
# pylint: disable-msg=R0201

from sasmodels.sasview_model import _make_standard_model
EllipsoidModel = _make_standard_model('ellipsoid')
SphereModel = _make_standard_model('sphere')
CylinderModel = _make_standard_model('cylinder')
CoreShellModel = _make_standard_model('core_shell_sphere')

import sas.sascalc.realspace.VolumeCanvas as VolumeCanvas

class TestRealSpaceModel(unittest.TestCase):
    """ Unit tests for sphere model """

    def setUp(self):
        self.model = VolumeCanvas.VolumeCanvas()
        self.model.add('cylinder', 'cyl')
        self.model.add('sphere', 'sph')
        self.model.add('ellipsoid', 'elli')
        self.model.add('singlehelix', 'shelix')

    def testAdding(self):
        self.assertEqual('cyl', self.model.add('cylinder', 'cyl'))

    def testDeleting(self):
        self.model.add('ellipsoid','elli2')
        self.model.delete('elli2')
        self.assert_('elli2' not in self.model.getShapeList())

    def testsetParam(self):
        self.model.setParam('q_max', 0.2)
        self.model.setParam('shelix.radius_helix', 12)

    def testgetParamList(self):
        #print self.model.getParamList()
        #print self.model.getParamList('shelix')
        pass

    def testPr_Iq(self):
        self.model.getPr()
        #print "pr is calculated", self.model.hasPr
        result = self.model.getIq(0.1)
        #print "I(0.1) is calculated: ", result

class TestSphere(unittest.TestCase):
    """ Unit tests for sphere model """

    def setUp(self):
        self.canvas = VolumeCanvas.VolumeCanvas()


    def testSetQmax(self):
        old_value = self.canvas.getParam('q_max')
        new_value = old_value + 0.1
        self.canvas.setParam('q_max', new_value)
        self.assertEqual(self.canvas.getParam("Q_MAx"), new_value)

    def testSetDensity(self):
        self.canvas.setParam('lores_density', 0.1)
        handle = self.canvas.add('sphere')
        self.canvas.setParam("%s.radius" % handle, 5.0)
        vol = 4/3*math.pi*5*5*5
        npts_1 = vol/0.1
        value_1 = self.canvas.getIq(0.001)

        # Change density, the answer should be the same
        self.canvas.setParam('lores_density', 0.2)
        npts_2 = vol/0.2
        value_2 = self.canvas.getIq(0.001)

        self.assert_( (value_1-value_2)/value_1 < 0.1)

    def testSetDensityTiming(self):
        """Testing change in computation time with density"""
        handle = self.canvas.add('sphere')
        self.canvas.setParam("%s.radius" % handle, 15.0)

        self.canvas.setParam('lores_density', 0.6)
        t_0 = time.time()
        self.canvas.getIq(0.001)
        t_1 = time.time()-t_0

        # Change density, the answer should be the same
        self.canvas.setParam('lores_density', 0.1)
        t_0 = time.time()
        self.canvas.getIq(0.001)
        t_2 = time.time()-t_0

        self.assert_( t_2 < t_1 and (t_1-t_2)/t_2 > 2)

    def testGetParamList(self):
        """ Test GetParamList on empty canvas"""
        self.assert_('lores_density' in self.canvas.getParamList())
        handle = self.canvas.add('sphere')

    def testGetParamListWithShape(self):
        """ Test GetParamList on filled canvas"""
        self.canvas.add('sphere')
        self.assert_('lores_density' in self.canvas.getParamList())

    def testAdd(self):
        handle = "s1"
        self.assertEqual(handle, self.canvas.add('sphere', handle))

        #TODO: test for current list of shape
        self.assertEqual( [handle] , self.canvas.getShapeList())

    def testSetRadius(self):
        handle = self.canvas.add('sphere')
        self.canvas.setParam("%s.radius" % handle, 24.0)
        self.assertEqual(self.canvas.getParam("%s.radius" % handle), 24.0)

    def testGetIq(self):
        """ Test the output of I(q) to the analytical solution
            If the normalization is wrong, we will have to fix it.

            getIq() should call getPr() behind the scenes so that
            the user doesnt have to do it if he doesn't need to.
        """
        sphere = SphereModel()
        sphere.setParam('scale', 1.0)
        sphere.setParam('background', 0.0)
        sphere.setParam('sld', 1.0)
        sphere.setParam('sld_solvent', 0.0)
        sphere.setParam('radius', 10.0)

        handle = self.canvas.add('sphere')
        self.canvas.setParam('%s.radius' % handle, 10.0)
        self.canvas.setParam('%s.contrast' % handle, 1.0)


        sim_1 = self.canvas.getIq(0.001)
        ana_1 = sphere.run(0.001)
        sim_2 = self.canvas.getIq(0.01)
        ana_2 = sphere.run(0.01)

        # test the shape of the curve (calculate relative error
        # on the output and it should be compatible with zero
        # THIS WILL DEPEND ON THE NUMBER OF SPACE POINTS:
        # that why we need some error analysis.
        self.assert_( (sim_2*ana_1/sim_1 - ana_2)/ana_2 < 0.1)

        # test the absolute amplitude
        self.assert_( math.fabs(sim_2-ana_2)/ana_2 < 0.1)

    def testGetIq2(self):
        """ Test two different q values
        """
        handle = self.canvas.add('sphere')
        self.canvas.setParam('%s.radius' % handle, 10.0)

        sim_1 = self.canvas.getIq(0.001)
        sim_2 = self.canvas.getIq(0.01)

        self.assertNotAlmostEqual(sim_2, sim_1, 3)

    def testGetIq_Identical(self):
        """ Test for identical model / no param change
        """
        handle = self.canvas.add('sphere')
        self.canvas.setParam('%s.radius' % handle, 10.0)

        sim_1 = self.canvas.getIq(0.01)
        sim_2 = self.canvas.getIq(0.01)

        self.assertEqual(sim_2, sim_1)

    def testGetIq_Identical2(self):
        """ Test for identical model after a parameter change
            Should be different only of the space points
            are regenerated and the random seed is different
        """
        handle = self.canvas.add('sphere')
        self.canvas.setParam('%s.radius' % handle, 10.0)

        self.canvas.setParam('lores_density', 0.1)
        sim_1 = self.canvas.getIq(0.01)

        # Try to fool the code by changing to a different value
        self.canvas.setParam('lores_density', 0.2)
        self.canvas.getIq(0.01)

        self.canvas.setParam('lores_density', 0.1)
        sim_2 = self.canvas.getIq(0.01)

        self.assert_((sim_2-sim_1)/sim_1<0.05)

    def testGetIq_time(self):
        """ Time profile
        """
        handle = self.canvas.add('sphere')
        self.canvas.setParam('%s.radius' % handle, 15.0)


        self.canvas.setParam('lores_density', 0.1)
        t_0 = time.time()
        sim_1 = self.canvas.getIq(0.01)
        delta_1 = time.time()-t_0

        self.canvas.setParam('lores_density', 0.1)

        t_0 = time.time()
        sim_2 = self.canvas.getIq(0.01)
        delta_2 = time.time()-t_0

        self.assert_((delta_2-delta_1)/delta_1<0.05)


    def testGetPr(self):
        """Compare the output of P(r) to the theoretical value"""
        #TODO: find a way to compare you P(r) to the known
        # analytical value.
        pass

    def testLogic1(self):
        """ Test that the internal logic is set so that the user
            get the right output after changing a parameter
        """

        handle = self.canvas.add('sphere')
        self.canvas.setParam('%s.radius' % handle, 10.0)
        result_1 = self.canvas.getIq(0.1)
        self.canvas.setParam('%s.radius' % handle, 20.0)
        result_2 = self.canvas.getIq(0.1)
        self.assertNotAlmostEqual(result_1, result_2, 2)

class TestCanvas(unittest.TestCase):
    """ Unit tests for all shapes in canvas model """

    def setUp(self):
        self.canvas = VolumeCanvas.VolumeCanvas()
        self.canvas.params['lores_density'] = 0.05

    def testGetIq_cylinder(self):
        handle = self.canvas.add('cylinder','cyl')
        self.canvas.setParam('%s.radius' % handle, 15.0)
        self.canvas.setParam('%s.length' % handle, 50.0)
        self.assertEqual(50,self.canvas.getParam('%s.length'%handle))
        result_1 = self.canvas.getIq(0.1)
        result_2 = self.canvas.getIq(0.1)
        self.assertEqual(result_1,result_2)

        self.canvas.delete(handle)
        handle2 = self.canvas.add('cylinder','cyl2')
        self.assertEqual(40,self.canvas.getParam('%s.length'%handle2))
        result_3 = self.canvas.getIq(0.1)
        self.assertNotEqual(result_1, result_3)

    def testGetIq_ellipsoid(self):
        handle = self.canvas.add('ellipsoid','elli')
        self.canvas.setParam('%s.radius_x' % handle, 35)
        self.canvas.setParam('%s.radius_y' % handle, 20)
        self.canvas.setParam('%s.radius_z' % handle, 10)
        result_1 = self.canvas.getIq(0.1)
        result_2 = self.canvas.getIq(0.1)
        self.assertEqual(result_1,result_2)

        self.canvas.delete(handle)
        self.assertEqual(False,self.canvas.hasPr)
        handle2 = self.canvas.add('ellipsoid','elli2')
        result_3 = self.canvas.getIq(0.1)
        self.assertNotEqual(result_1, result_3)

    def testGetIq_singlehelix(self):
        handle = self.canvas.add('singlehelix','shelix')
        self.canvas.setParam('%s.radius_helix' % handle, 11)
        self.canvas.setParam('%s.radius_tube' % handle, 4)
        self.canvas.setParam('%s.pitch' % handle, 30)
        self.canvas.setParam('%s.turns' % handle, 3.2)
        result_1 = self.canvas.getIq(0.1)
        result_2 = self.canvas.getIq(0.1)
        self.assertEqual(result_1,result_2)

        self.canvas.delete(handle)
        self.assertEqual(False,self.canvas.hasPr)
        handle2 = self.canvas.add('singlehelix','shelix2')
        result_3 = self.canvas.getIq(0.1)
        self.assertNotEqual(result_1, result_3)

class TestOrdering(unittest.TestCase):
    """ Unit tests for all shapes in canvas model """

    def setUp(self):
        radius = 15
        thickness = 5
        core_vol = 4.0/3.0*math.pi*radius*radius*radius
        outer_radius = radius+thickness
        shell_vol = 4.0/3.0*math.pi*outer_radius*outer_radius*outer_radius - core_vol
        self.shell_sld = -1.0*core_vol/shell_vol

        self.canvas = VolumeCanvas.VolumeCanvas()
        self.canvas.params['lores_density'] = 0.1

        # Core shell model
        sphere = CoreShellModel()
        sphere.setParam('scale', 1.0)
        sphere.setParam('background', 0.0)
        sphere.setParam('sld_core', 1.0)
        sphere.setParam('sld_shell', self.shell_sld)
        sphere.setParam('sld_solvent', 0.0)
        # Core radius
        sphere.setParam('radius', radius)
        # Shell thickness
        sphere.setParam('thickness', thickness)
        self.sphere = sphere
        self.radius = radius
        self.outer_radius = outer_radius

    def set_coreshell_on_canvas(self, order1=None, order2=None):

        handle = self.canvas.add('sphere')
        self.canvas.setParam('scale' , 1.0)
        self.canvas.setParam('background' , 0.0)

        self.canvas.setParam('%s.radius' % handle, self.outer_radius)
        self.canvas.setParam('%s.contrast' % handle, self.shell_sld)
        if order1 is not None:
            self.canvas.setParam('%s.order' % handle, order1)

        handle2 = self.canvas.add('sphere')
        self.canvas.setParam('%s.radius' % handle2, self.radius)
        self.canvas.setParam('%s.contrast' % handle2, 1.0)
        if order2 is not None:
            self.canvas.setParam('%s.order' % handle2, order2)


    def testDefaultOrder(self):
        self.set_coreshell_on_canvas()

        ana = self.sphere.run(0.05)
        val, err = self.canvas.getIqError(0.05)
        self.assert_(math.fabs(ana-val)<2.0*err)

    def testRightOrder(self):
        self.set_coreshell_on_canvas(3.0, 6.0)

        ana = self.sphere.run(0.05)
        val, err = self.canvas.getIqError(0.05)
        #print 'right', ana, val, err
        self.assert_(math.fabs(ana-val)/ana < 1.1)

    def testWrongOrder(self):
        self.set_coreshell_on_canvas(1, 0)

        sphere = SphereModel()
        sphere.setParam('scale', 1.0)
        sphere.setParam('background', 0.0)
        sphere.setParam('radius', self.outer_radius)
        sphere.setParam('sld', self.shell_sld)
        sphere.setParam('sld_solvent', 0.0)

        ana = sphere.run(0.05)
        val, err = self.canvas.getIqError(0.05)
        #print 'wrong', ana, val, err
        self.assert_(math.fabs(ana-val)/ana < 1.1)


if __name__ == '__main__':
    unittest.main()
