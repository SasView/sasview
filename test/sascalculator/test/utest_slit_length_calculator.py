"""
    Unit tests for slit_length_calculator
"""

import unittest
from sas.sascalc.dataloader.readers.ascii_reader import Reader
from  sas.sascalc.calculator.slit_length_calculator import SlitlengthCalculator as calculator

import os.path

class slit_calculator(unittest.TestCase):
    
    def setUp(self):
        
        self.reader = Reader()
        
    def test_slitlength_calculation(self):
        """
            Test slit_length_calculator"
        """
        f = self.reader.read("beam profile.DAT")
        cal = calculator()
        cal.set_data(f.x,f.y)
        slitlength = cal.calculate_slit_length()
        
        # The value "5.5858" was obtained by manual calculation.
        # It turns out our slit length is FWHM/2
        self.assertAlmostEqual(slitlength,5.5858/2, 3)
        
        
if __name__ == '__main__':
    unittest.main()
   
