
import pytest

# Tested module
from sas.qtgui.Perspectives.Fitting.FitPage import FitPage


class FitPageTest:
    '''Test the FitPage methods'''

    @pytest.fixture(autouse=True)
    def page(self, qapp):
        '''Create/Destroy the AboutBox'''
        p = FitPage()
        yield p

    def testDefaults(self, page):
        """
        Test all the global constants defined in the file.
        """
        assert isinstance(page.fit_options, dict)
        assert isinstance(page.smearing_options, dict)
        assert page.current_category == ""
        assert page.current_model == ""
        assert page.current_factor == ""
        assert page.page_id == 0
        assert not page.data_is_loaded
        assert page.name == ""
        assert page.data is None
        assert page.logic.kernel_module is None
        assert page.parameters_to_fit == []

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

