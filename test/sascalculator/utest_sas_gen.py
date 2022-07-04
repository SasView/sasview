"""
Unit tests for the sas_gen
"""

import os.path
import warnings
warnings.simplefilter("ignore")

import unittest
import numpy as np
import math
from scipy.spatial.transform import Rotation


from sas.sascalc.calculator import sas_gen


def find(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)


class sas_gen_test(unittest.TestCase):

    def setUp(self):
        self.sldloader = sas_gen.SLDReader()
        self.pdbloader = sas_gen.PDBReader()
        self.omfloader = sas_gen.OMFReader()
        self.vtkloader = sas_gen.VTKReader()

    def test_sldreader(self):
        """
        Test .sld file loaded
        """
        f = self.sldloader.read(find("sld_file.sld"))
        self.assertEqual(f.pos_x[0], -40.5)
        self.assertEqual(f.pos_y[0], -13.5)
        self.assertEqual(f.pos_z[0], -13.5)
    
    def test_sldwriter(self):
        """
        Test .sld file is written correctly
        """
        # load in a sample sld file then resave it
        f = self.sldloader.read(find("sld_file.sld"))
        self.sldloader.write(find("write_test.sld"), f)
        # load in the saved file to confirm that Sasview does not reject it within its
        # own loading function
        g = self.sldloader.read(find("write_test.sld"))
        # confirm that the first row of data is as expected
        self.assertEqual(f.pos_x[0], g.pos_x[0])
        self.assertEqual(f.pos_y[0], g.pos_y[0])
        self.assertEqual(f.pos_z[0], g.pos_z[0])
        self.assertEqual(f.sld_n[0], g.sld_n[0])
        self.assertEqual(f.sld_mx[0], g.sld_mx[0])
        self.assertEqual(f.sld_my[0], g.sld_my[0])
        self.assertEqual(f.sld_mz[0], g.sld_mz[0])
        self.assertEqual(f.vol_pix[0], g.vol_pix[0])


    def test_pdbreader(self):
        """
        Test .pdb file loaded
        """
        f = self.pdbloader.read(find("c60.pdb"))
        self.assertEqual(f.pos_x[0], -0.733)
        self.assertEqual(f.pos_y[0], -1.008)
        self.assertEqual(f.pos_z[0], 3.326)

    def test_omfreader(self):
        """
        Test .omf file loaded
        """
        f = self.omfloader.read(find("A_Raw_Example-1.omf"))

        self.assertEqual(f.sld_mx[0], 0)
        self.assertEqual(f.sld_my[0], 0)
        self.assertEqual(f.sld_mz[0], 0)
        self.assertEqual(f.pos_x[0], 0.0)
        self.assertEqual(f.pos_y[0], 0.0)
        self.assertEqual(f.pos_z[0], 0.0)
    
    def test_rotations(self):
        pos_x = np.array([1, 0, 0])
        pos_y = np.array([0, 1, 0])
        pos_z = np.array([0, 0, 1])
        data = sas_gen.MagSLD(pos_x, pos_y, pos_z)
        R1 = Rotation.from_rotvec((2*math.pi/3)*np.array([1,1,1])/math.sqrt(3))
        R2 = Rotation.from_rotvec(np.array([0,1,0])*math.pi/2)
        model = sas_gen.GenSAS()
        model.set_rotations(R2, R1)
        model.set_sld_data(data)
        # assert almost equal due to floating point errors from rotations
        x,y,z = model.transform_positions()
        theta, phi = model.transform_angles()
        self.assertTrue(np.allclose(np.array([0, 0, 1]), x))
        self.assertTrue(np.allclose(np.array([1, 0, 0]), y))
        self.assertTrue(np.allclose(np.array([0, 1, 0]), z))
        self.assertAlmostEqual(theta, 90)
        self.assertAlmostEqual(phi, 0)

    
    def test_vtkreader(self):
        """
        Test .vtkfile loaded
        """
        f = self.vtkloader.read(find("five_tetrahedra_cube.vtk"))
        points = np.array([
            [-1,  -1,   -1],
            [1 , -1 ,  -1 ],
            [-1,   1,   -1],
            [1 ,  1 ,  -1 ],
            [-1,  -1,    1],
            [1 , -1 ,   1 ],
            [-1,   1,    1],
            [1 ,  1 ,   1 ]])
        element_0 = np.array([[1, 4, 2], 
                              [1, 2, 7], 
                              [1, 7, 4], 
                              [2, 4, 7]])
        self.assertTrue(np.array_equal(f.pos_x, points[:, 0]))
        self.assertTrue(np.array_equal(f.pos_y, points[:, 1]))
        self.assertTrue(np.array_equal(f.pos_z, points[:, 2]))
        self.assertEqual(f.sld_mx[0], 1)
        self.assertEqual(f.sld_my[0], 0)
        self.assertEqual(f.sld_mz[0], 0)
        self.assertEqual(f.sld_n[0], 1)
        self.assertTrue(np.array_equal(f.elements[0], element_0))

    def get_box_transform(self, sld, qx, qy, x, y, z):
        """Return the fourier transform of a box at qx, qy with dimensions x by y by z

        """
        return x*y*z * np.sinc(x/2*qx/math.pi)*np.sinc(y/2*qy/math.pi) * sld

    def test_calculator_2D(self):
        """
        Test that the calculator calculates 2D grid type data - both nuclear only and magnetic
        """
        f = sas_gen.OMFData() # create default initialisation data - 60x60x60 angstrom cube
        f.xstepsize = 0.6
        f.ystepsize = 0.3 # convert to 60x30x60 cuboid to test orientation is correct
        f.zstepsize = 0.6
        f.xnodes = 100
        f.ynodes = 100
        f.znodes = 100
        omf2sld = sas_gen.OMF2SLD()
        omf2sld.set_data(f)
        sld = omf2sld.output
        sld.set_sldn(0.1, False)
        model = sas_gen.GenSAS()
        model.set_sld_data(sld)
        # test: point at centre, point near a zero x2, point on the diagonal (for orientation)
        # do not measure at exact centre so arctan2 gives correct value
        qx = np.array([0.0001,    0.105,  0,      0.015])
        qy = np.array([0.0001,    0,      0.21,   0.3])
        # TEST nuclear data only
        output = model.runXY([qx, qy])
        analytical = np.float_power(self.get_box_transform(0.1, qx, qy, 60, 30, 60), 2) * 1E8 / 108000
        # require that percentage error is < 0.1%
        errs = np.abs(output - analytical)/analytical
        for val in np.abs(errs):
            self.assertLessEqual(val, 1e-3)
        # TEST magnetic angular anisotropy
        # formula obtained from: Observation of cross-shaped anisotropy in spin-resolved small-angle neutron scattering
        #                        PHYSICAL REVIEW B 85, 184417 (2012)
        #                        Andreas Michels, Dirk Honecker, Frank Döbrich, Charles D. Dewhurst, Kiyonori Suzuki, André Heinemann
        sld.set_sldms(1.0, 0.0, 0.0)
        theta = np.arctan2(qy, qx)
        N_f = self.get_box_transform(0.1, qx, qy, 60, 30, 60)
        Mx_f = self.get_box_transform(1, qx, qy, 60, 30, 60)
        analytical = np.float_power(N_f, 2) + np.float_power(Mx_f, 2)*np.float_power(np.sin(theta), 4) \
                     - 2*Mx_f*N_f*np.float_power(np.sin(theta), 2)
        analytical = analytical * 1E8 / 108000
        model.set_sld_data(sld)
        model.params['Up_frac_in'] = 0.0
        model.params['Up_frac_out'] = 0.0
        model.params['Up_theta'] = 90.0
        output = model.runXY([qx, qy])
        errs = (output - analytical)/analytical
        for val in np.abs(errs):
            self.assertLessEqual(val, 1e-3)
    
    def test_calculator_1D(self):
        """
        Test the calculator correctly calculates 1D averages. 
        """
        # TEST 1D debye averaging
        # use only a 10x10x10 grid because this algorithm scales quickly
        # use very small Q values otherwise numerical errors appear due to discretisation
        # As pixel size decreases - averaging becomes more accurate at higher Q values
        f = sas_gen.OMFData()
        f.ystepsize = 3 # convert to 60x30x60 cuboid to test orientation is correct
        omf2sld = sas_gen.OMF2SLD()
        omf2sld.set_data(f)
        sld = omf2sld.output
        sld.set_sldn(0.1, False)
        model = sas_gen.GenSAS()
        model.set_sld_data(sld)
        output = model.run([[0.01, 0.03], []])
        # numerical integration to average the analytical solution give the following results:
        analytical = np.array([1.056e11, 8.8100e10])
        errs = (output - analytical)/analytical
        # only require errors <1% due to larger discretisation
        for val in np.abs(errs):
            self.assertLessEqual(val, 1e-2)
    
    def test_calculator_elements(self):
        """
        Test that the calculator correctly calculates scattering for element type data.
        """
        f = self.vtkloader.read(find("five_tetrahedra_cube.vtk"))
        model = sas_gen.GenSAS()
        model.set_sld_data(f)
        # close to centre, a zero, and a diagonal (requires l'hopitals rule)
        # TEST angula anisotropy
        # formula obtained from: Observation of cross-shaped anisotropy in spin-resolved small-angle neutron scattering
        #                        PHYSICAL REVIEW B 85, 184417 (2012)
        #                        Andreas Michels, Dirk Honecker, Frank Döbrich, Charles D. Dewhurst, Kiyonori Suzuki, André Heinemann
        qx = np.array([0.0001,    1.57,  1,   ])
        qy = np.array([0.0001,    0,     1,   ])
        theta = np.arctan2(qy, qx)
        N_f = self.get_box_transform(1, qx, qy, 2, 2, 2)
        Mx_f = self.get_box_transform(1, qx, qy, 2, 2, 2)
        analytical = np.float_power(N_f, 2) + np.float_power(Mx_f, 2)*np.float_power(np.sin(theta), 4) \
                     - 2*Mx_f*N_f*np.float_power(np.sin(theta), 2)
        analytical = analytical * 1E8 / 8.0
        model.set_sld_data(f)
        model.params['Up_frac_in'] = 0.0
        model.params['Up_frac_out'] = 0.0
        model.params['Up_theta'] = 90.0
        output = model.runXY([qx, qy])
        errs = (output - analytical)/analytical
        for val in np.abs(errs):
            self.assertLessEqual(val, 1e-3)
        # TEST nuclear data only
        f.set_sldms(0.0, 0.0, 0.0)
        model.set_sld_data(f)
        output = model.runXY([qx, qy])
        analytical = np.float_power(self.get_box_transform(1, qx, qy, 2, 2, 2), 2) * 1E8 / 8.0
        # require that percentage error is < 0.1%
        errs = np.abs(output - analytical)/analytical
        for val in np.abs(errs):
            self.assertLessEqual(val, 1e-3)



if __name__ == '__main__':
    unittest.main()

