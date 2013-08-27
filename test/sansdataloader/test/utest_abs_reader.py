"""
    Unit tests for data manipulations
"""

import unittest
import numpy, math
from sans.dataloader.loader import  Loader
from sans.dataloader.data_info import Data1D
 
import os.path

class abs_reader(unittest.TestCase):
    
    def setUp(self):
        from sans.dataloader.readers.abs_reader import Reader
        self.data = Reader().read("jan08002.ABS")
        
    def test_abs_checkdata(self):
        """
            Check the data content to see whether 
            it matches the specific file we loaded.
            Check the units too to see whether the
            Data1D defaults changed. Otherwise the
            tests won't pass
        """
        self.assertEqual(self.data.filename, "jan08002.ABS")
        self.assertEqual(self.data.meta_data['loader'], "IGOR 1D")
        
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
        
class hfir_reader(unittest.TestCase):
    
    def setUp(self):
        self.data = Loader().load("S2-30dq.d1d")
        
    def test_hfir_checkdata(self):
        """
            Check the data content to see whether 
            it matches the specific file we loaded.
        """
        self.assertEqual(self.data.filename, "S2-30dq.d1d")
        # THIS FILE FORMAT IS CURRENTLY READ BY THE ASCII READER
        self.assertEqual(self.data.meta_data['loader'], "HFIR 1D")
        self.assertEqual(len(self.data.x), 134)
        self.assertEqual(len(self.data.y), 134)
        #          Q           I               dI          dQ  
        # Point 1: 0.003014    0.003010        0.000315    0.008249
        self.assertEqual(self.data.x[1], 0.003014)
        self.assertEqual(self.data.y[1], 0.003010)
        self.assertEqual(self.data.dy[1], 0.000315)
        self.assertEqual(self.data.dx[1], 0.008249)
        

class igor_reader(unittest.TestCase):
    
    def setUp(self):
        self.data = Loader().load("MAR07232_rest.ASC")
        
    def test_igor_checkdata(self):
        """
            Check the data content to see whether 
            it matches the specific file we loaded.
            Check the units too to see whether the
            Data1D defaults changed. Otherwise the
            tests won't pass
        """
        self.assertEqual(self.data.filename, "MAR07232_rest.ASC")
        self.assertEqual(self.data.meta_data['loader'], "IGOR 2D")
        
        self.assertEqual(self.data.source.wavelength_unit, 'A')
        self.assertEqual(self.data.source.wavelength, 8.4)
        
        self.assertEqual(self.data.detector[0].distance_unit, 'mm')
        self.assertEqual(self.data.detector[0].distance, 13705)
        
        self.assertEqual(self.data.sample.transmission, 0.84357)
        
        self.assertEqual(self.data.detector[0].beam_center_unit, 'mm')
        center_x = (68.76-1)*5.0
        center_y = (62.47-1)*5.0
        self.assertEqual(self.data.detector[0].beam_center.x, center_x)
        self.assertEqual(self.data.detector[0].beam_center.y, center_y)
        
        self.assertEqual(self.data.I_unit, '1/cm')
        self.assertEqual(self.data.data[0], 0.279783)
        self.assertEqual(self.data.data[1], 0.28951)
        self.assertEqual(self.data.data[2], 0.167634)
        
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
        self.assertEqual(self.data.meta_data['loader'], "DANSE")
        
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
        self.assertEqual(self.data.data[0], 1.57831)
        self.assertEqual(self.data.data[1], 2.70983)
        self.assertEqual(self.data.data[2], 3.83422)

        self.assertEqual(self.data.err_data[0], 1.37607)
        self.assertEqual(self.data.err_data[1], 1.77569)
        self.assertEqual(self.data.err_data[2], 2.06313)

 
class cansas_reader(unittest.TestCase):
    
    def setUp(self):
        self.data = Loader().load("cansas1d.xml")
 
    def test_cansas_checkdata(self):
        self.assertEqual(self.data.filename, "cansas1d.xml")
        self._checkdata()
        
    def _checkdata(self):
        """
            Check the data content to see whether 
            it matches the specific file we loaded.
            Check the units too to see whether the
            Data1D defaults changed. Otherwise the
            tests won't pass
        """
        
        self.assertEqual(self.data.run[0], "1234")
        self.assertEqual(self.data.meta_data['loader'], "CanSAS 1D")
        self.assertEqual(len(self.data.errors), 0)
        
        # Data
        self.assertEqual(len(self.data.x), 2)
        self.assertEqual(self.data.x_unit, '1/A')
        self.assertEqual(self.data.y_unit, '1/cm')
        self.assertAlmostEqual(self.data.x[0], 0.02, 6)
        self.assertAlmostEqual(self.data.y[0], 1000, 6)
        self.assertAlmostEqual(self.data.dx[0], 0.01, 6)
        self.assertAlmostEqual(self.data.dy[0], 3, 6)
        self.assertAlmostEqual(self.data.x[1], 0.03, 6)
        self.assertAlmostEqual(self.data.y[1], 1001.0)
        self.assertAlmostEqual(self.data.dx[1], 0.02, 6)
        self.assertAlmostEqual(self.data.dy[1], 4, 6)
        self.assertEqual(self.data.run_name['1234'], 'run name')
        self.assertEqual(self.data.title, "Test title")
        
        # Sample info
        self.assertEqual(self.data.sample.ID, "SI600-new-long")
        self.assertEqual(self.data.sample.name, "my sample")
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
        self.assertEqual(self.data.instrument, "canSAS instrument")
        
        # Source
        self.assertEqual(self.data.source.radiation, "neutron")
        
        self.assertEqual(self.data.source.beam_size_unit, "mm")
        self.assertEqual(self.data.source.beam_size_name, "bm")
        self.assertEqual(self.data.source.beam_size.x, 12)
        self.assertEqual(self.data.source.beam_size.y, 13)
        
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
        self.assertEqual(self.data.collimation[0].name, 'test coll name')
        
        for item in self.data.collimation[0].aperture:
            self.assertEqual(item.size_unit,'mm')
            self.assertEqual(item.distance_unit,'mm')
            
            if item.size.x==50 \
                and item.distance==11000.0 \
                and item.name=='source' \
                and item.type=='radius':
                _found1 = True
            elif item.size.x==1.0 \
                and item.name=='sample' \
                and item.type=='radius':
                _found2 = True
                
        if _found1==False or _found2==False:
            print item.distance
            raise RuntimeError, "Could not find all data %s %s" % (_found1, _found2) 
            
        # Detector
        self.assertEqual(self.data.detector[0].name, "fictional hybrid")
        self.assertEqual(self.data.detector[0].distance_unit, "mm")
        self.assertEqual(self.data.detector[0].distance, 4150)
        
        self.assertEqual(self.data.detector[0].orientation_unit, "degree")
        self.assertEqual(self.data.detector[0].orientation.x, 1.0)
        self.assertEqual(self.data.detector[0].orientation.y, 0.0)
        self.assertEqual(self.data.detector[0].orientation.z, 0.0)
        
        self.assertEqual(self.data.detector[0].offset_unit, "m")
        self.assertEqual(self.data.detector[0].offset.x, .001)
        self.assertEqual(self.data.detector[0].offset.y, .002)
        self.assertEqual(self.data.detector[0].offset.z, None)
        
        self.assertEqual(self.data.detector[0].beam_center_unit, "mm")
        self.assertEqual(self.data.detector[0].beam_center.x, 322.64)
        self.assertEqual(self.data.detector[0].beam_center.y, 327.68)
        self.assertEqual(self.data.detector[0].beam_center.z, None)
        
        self.assertEqual(self.data.detector[0].pixel_size_unit, "mm")
        self.assertEqual(self.data.detector[0].pixel_size.x, 5)
        self.assertEqual(self.data.detector[0].pixel_size.y, 5)
        self.assertEqual(self.data.detector[0].pixel_size.z, None)
        
        # Process
        _found_term1 = False
        _found_term2 = False
        for item in self.data.process:
            self.assertTrue(item.name in ['NCNR-IGOR', 'spol'])
            self.assertTrue(item.date in ['04-Sep-2007 18:35:02',
                                          '03-SEP-2006 11:42:47'])
            for t in item.term:
                if t['name']=="ABS:DSTAND" \
                    and t['unit']=='mm' \
                    and float(t['value'])==1.0:
                    _found_term2 = True
                elif t['name']=="radialstep" \
                    and t['unit']=='mm' \
                    and float(t['value'])==10.0:
                    _found_term1 = True
                    
        if _found_term1==False or _found_term2==False:
            raise RuntimeError, "Could not find all process terms %s %s" % (_found_term1, _found_term2) 
            
        
        
        
    def test_writer(self):
        from sans.dataloader.readers.cansas_reader import Reader
        r = Reader()
        x = numpy.ones(5)
        y = numpy.ones(5)
        dy = numpy.ones(5)
        
        filename = "write_test.xml"
        r.write(filename, self.data)
        self.data = Loader().load(filename)
        self.assertEqual(self.data.filename, filename)
        self._checkdata()
        
    def test_units(self):
        """
            Check units.
            Note that not all units are available.
        """
        filename = "cansas1d_units.xml"
        self.data = Loader().load(filename)
        self.assertEqual(self.data.filename, filename)
        self._checkdata()
        
    def test_badunits(self):
        """
            Check units.
            Note that not all units are available.
        """
        filename = "cansas1d_badunits.xml"
        self.data = Loader().load(filename)
        self.assertEqual(self.data.filename, filename)
        # The followed should not have been loaded
        self.assertEqual(self.data.sample.thickness, None)
        # This one should
        self.assertEqual(self.data.sample.transmission, 0.327)
        
        self.assertEqual(self.data.meta_data['loader'], "CanSAS 1D")
        self.assertEqual(len(self.data.errors), 1)
        
        
    def test_slits(self):
        """
            Check slit data
        """
        filename = "cansas1d_slit.xml"
        self.data = Loader().load(filename)
        self.assertEqual(self.data.filename, filename)
        self.assertEqual(self.data.run[0], "1234")
        
        # Data
        self.assertEqual(len(self.data.x), 2)
        self.assertEqual(self.data.x_unit, '1/A')
        self.assertEqual(self.data.y_unit, '1/cm')
        self.assertEqual(self.data.x[0], 0.02)
        self.assertEqual(self.data.y[0], 1000)
        self.assertEqual(self.data.dxl[0], 0.005)
        self.assertEqual(self.data.dxw[0], 0.001)
        self.assertEqual(self.data.dy[0], 3)
        self.assertEqual(self.data.x[1], 0.03)
        self.assertAlmostEquals(self.data.y[1], 1001.0)
        self.assertEqual(self.data.dx[1], 0.0)
        self.assertEqual(self.data.dxl[1], 0.005)
        self.assertEqual(self.data.dxw[1], 0.001)
        self.assertEqual(self.data.dy[1], 4)
        self.assertEqual(self.data.run_name['1234'], 'run name')
        self.assertEqual(self.data.title, "Test title")

            

if __name__ == '__main__':
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))