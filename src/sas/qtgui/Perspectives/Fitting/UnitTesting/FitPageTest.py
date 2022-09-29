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
        assert isinstance(self.page.fit_options, dict)
        assert isinstance(self.page.smearing_options, dict)
        assert self.page.current_category == ""
        assert self.page.current_model == ""
        assert self.page.current_factor == ""
        assert self.page.page_id == 0
        assert not self.page.data_is_loaded
        assert self.page.name == ""
        assert self.page.data is None
        assert self.page.kernel_module is None
        assert self.page.parameters_to_fit == []

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

