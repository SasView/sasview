"""
    Unit tests for data manipulations
"""

import unittest
import numpy, math
from DataLoader.loader import  Loader
from DataLoader.data_info import Data1D
 
import os.path

class abs_reader(unittest.TestCase):
    
    def setUp(self):
        self.data = Loader().load("jan08002.ABS")
        
    def test_checkdata(self):
        """
            Check the data content to see whether 
            it matches the specific file we loaded.
            Check the units too to see whether the
            Data1D defaults changed. Otherwise the
            tests won't pass
        """
        self.assertEqual(self.data.filename, "jan08002.ABS")
        
        self.assertEqual(self.data.source.wavelength_unit, 'A')
        self.assertEqual(self.data.source.wavelength, 6.0)
        
        self.assertEqual(self.data.detector[0].distance_unit, 'mm')
        self.assertEqual(self.data.detector[0].distance, 1000.0)
        
        self.assertEqual(self.data.sample.transmission, 0.5667)
        
        self.assertEqual(self.data.detector[0].beam_center_unit, 'mm')
        center_x = 114.58*5.0
        center_y = 64.22*5.0
        self.assertEqual(self.data.detector[0].beam_center.x, center_x)
        self.assertEqual(self.data.detector[0].beam_center.y, center_y)
        
        self.assertEqual(self.data.y_unit, '1/cm')
        self.assertEqual(self.data.x[0], 0.002618)
        self.assertEqual(self.data.x[1], 0.007854)
        self.assertEqual(self.data.x[2], 0.01309)
        self.assertEqual(self.data.x[126], 0.5828)
        
        self.assertEqual(self.data.y[0], 0.02198)
        self.assertEqual(self.data.y[1], 0.02201)
        self.assertEqual(self.data.y[2], 0.02695)
        self.assertEqual(self.data.y[126], 0.2958)
        
        self.assertEqual(self.data.dy[0], 0.002704)
        self.assertEqual(self.data.dy[1], 0.001643)
        self.assertEqual(self.data.dy[2], 0.002452)
        self.assertEqual(self.data.dy[126], 1)
        
    def test_checkdata2(self):
        self.assertEqual(self.data.dy[126], 1)

class igor_reader(unittest.TestCase):
    
    def setUp(self):
        self.data = Loader().load("MAR07232_rest.ASC")
        
    def test_checkdata(self):
        """
            Check the data content to see whether 
            it matches the specific file we loaded.
            Check the units too to see whether the
            Data1D defaults changed. Otherwise the
            tests won't pass
        """
        self.assertEqual(self.data.filename, "MAR07232_rest.ASC")
        
        self.assertEqual(self.data.source.wavelength_unit, 'A')
        self.assertEqual(self.data.source.wavelength, 8.4)
        
        self.assertEqual(self.data.detector[0].distance_unit, 'mm')
        self.assertEqual(self.data.detector[0].distance, 13705)
        
        self.assertEqual(self.data.sample.transmission, 0.84357)
        
        self.assertEqual(self.data.detector[0].beam_center_unit, 'mm')
        center_x = 68.76*5.0
        center_y = 62.47*5.0
        self.assertEqual(self.data.detector[0].beam_center.x, center_x)
        self.assertEqual(self.data.detector[0].beam_center.y, center_y)
        
        self.assertEqual(self.data.I_unit, '1/cm')
        self.assertEqual(self.data.data[0][0], 0.279783)
        self.assertEqual(self.data.data[0][1], 0.28951)
        self.assertEqual(self.data.data[0][2], 0.167634)
        
class danse_reader(unittest.TestCase):
    
    def setUp(self):
        self.data = Loader().load("MP_New.sans")

    def test_checkdata(self):
        """
            Check the data content to see whether 
            it matches the specific file we loaded.
            Check the units too to see whether the
            Data1D defaults changed. Otherwise the
            tests won't pass
        """
        self.assertEqual(self.data.filename, "MP_New.sans")
        
        self.assertEqual(self.data.source.wavelength_unit, 'A')
        self.assertEqual(self.data.source.wavelength, 7.5)
        
        self.assertEqual(self.data.detector[0].distance_unit, 'mm')
        self.assertAlmostEqual(self.data.detector[0].distance, 5414.99, 3)
        
        self.assertEqual(self.data.detector[0].beam_center_unit, 'mm')
        center_x = 68.74*5.0
        center_y = 64.77*5.0
        self.assertEqual(self.data.detector[0].beam_center.x, center_x)
        self.assertEqual(self.data.detector[0].beam_center.y, center_y)
        
        self.assertEqual(self.data.I_unit, '1/cm')
        self.assertEqual(self.data.data[0][0], 1.57831)
        self.assertEqual(self.data.data[0][1], 2.70983)
        self.assertEqual(self.data.data[0][2], 3.83422)

        self.assertEqual(self.data.err_data[0][0], 1.37607)
        self.assertEqual(self.data.err_data[0][1], 1.77569)
        self.assertEqual(self.data.err_data[0][2], 2.06313)

 
class cansas_reader(unittest.TestCase):
    
    def setUp(self):
        self.data = Loader().load("cansas1d.xml")
 
    def test_checkdata(self):
        """
            Check the data content to see whether 
            it matches the specific file we loaded.
            Check the units too to see whether the
            Data1D defaults changed. Otherwise the
            tests won't pass
        """
        self.assertEqual(self.data.filename, "cansas1d.xml")
        self.assertEqual(self.data.run, "1234")
        
        # Sample info
        self.assertEqual(self.data.sample.ID, "SI600-new-long")
        self.assertEqual(self.data.sample.thickness_unit, 'mm')
        self.assertEqual(self.data.sample.thickness, 1.03)
        
        self.assertEqual(self.data.sample.transmission, 0.327)
        
        self.assertEqual(self.data.sample.temperature_unit, 'C')
        self.assertEqual(self.data.sample.temperature, 0)

        self.assertEqual(self.data.sample.position_unit, 'mm')
        self.assertEqual(self.data.sample.position.x, 10)
        self.assertEqual(self.data.sample.position.y, 0)

        self.assertEqual(self.data.sample.orientation_unit, 'degree')
        self.assertEqual(self.data.sample.orientation.x, 22.5)
        self.assertEqual(self.data.sample.orientation.y, 0.02)

        self.assertEqual(self.data.sample.details[0], "http://chemtools.chem.soton.ac.uk/projects/blog/blogs.php/bit_id/2720") 
        self.assertEqual(self.data.sample.details[1], "Some text here") 
        
        # Instrument info
        self.assertEqual(self.data.instrument, "TEST instrument")
        
        # Source
        self.assertEqual(self.data.source.radiation, "neutron")
        
        self.assertEqual(self.data.source.beam_size_unit, "mm")
        self.assertEqual(self.data.source.beam_size.x, 12)
        self.assertEqual(self.data.source.beam_size.y, 12)
        
        self.assertEqual(self.data.source.beam_shape, "disc")
        
        self.assertEqual(self.data.source.wavelength_unit, "A")
        self.assertEqual(self.data.source.wavelength, 6)
        
        self.assertEqual(self.data.source.wavelength_max_unit, "nm")
        self.assertEqual(self.data.source.wavelength_max, 1.0)
        self.assertEqual(self.data.source.wavelength_min_unit, "nm")
        self.assertEqual(self.data.source.wavelength_min, 0.22)
        self.assertEqual(self.data.source.wavelength_spread_unit, "percent")
        self.assertEqual(self.data.source.wavelength_spread, 14.3)
        
        # Collimation
        _found1 = False
        _found2 = False
        self.assertEqual(self.data.collimation[0].length, 123.)
        
        for item in self.data.collimation[0].aperture:
            self.assertEqual(item.size_unit,'mm')
            self.assertEqual(item.distance_unit,'mm')
            
            if item.size.x==50 \
                and item.distance==11000.:
                _found1 = True
            elif item.size.x==1.0:
                _found2 = True
                
        if _found1==False or _found2==False:
            print item.distance
            raise RuntimeError, "Could not find all data %s %s" % (_found1, _found2) 
            
        
        
            

if __name__ == '__main__':
    unittest.main()
   