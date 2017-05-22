import sys
import unittest

# set up import paths
import sas.qtgui.path_prepare

# Tested module
from sas.qtgui.Perspectives.Fitting.FitPage import *

class FitPageTest(unittest.TestCase):
    '''Test the FitPage methods'''

    def setUp(self):
        self.page = FitPage()

    def tearDown(self):
        del self.page

    def testDefaults(self):
        """
        Test all the global constants defined in the file.
        """
        self.assertIsInstance(self.page.fit_options, dict)
        self.assertIsInstance(self.page.smearing_options, dict)
        self.assertEqual(self.page.current_category, "")
        self.assertEqual(self.page.current_model, "")
        self.assertEqual(self.page.current_factor, "")
        self.assertEqual(self.page.page_id, 0)
        self.assertFalse(self.page.data_is_loaded)
        self.assertEqual(self.page.filename, "")
        self.assertIsNone(self.page.data)
        self.assertIsNone(self.page.kernel_module)
        self.assertEqual(self.page.parameters_to_fit, [])

    def testSave(self):
        """
        Test state save
        """
        pass

    def testLoad(self):
        """
        Test state load
        """
        pass

