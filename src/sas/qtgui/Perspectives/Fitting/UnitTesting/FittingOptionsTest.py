import sys
import unittest
import webbrowser

import pytest

from bumps import options

from PyQt5 import QtGui, QtWidgets

from unittest.mock import MagicMock

# set up import paths
import sas.qtgui.path_prepare

from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy

# Local
from sas.qtgui.Perspectives.Fitting.FittingOptions import FittingOptions

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class FittingOptionsTest(unittest.TestCase):
    '''Test the FittingOptions dialog'''
    def setUp(self):
        '''Create FittingOptions dialog'''
        self.widget = FittingOptions(None, config=options.FIT_CONFIG)

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        assert isinstance(self.widget, QtWidgets.QDialog)
        # Default title
        assert self.widget.windowTitle() == "Fit Algorithms"

        # The combo box
        assert isinstance(self.widget.cbAlgorithm, QtWidgets.QComboBox)
        assert self.widget.cbAlgorithm.count() == 6
        assert self.widget.cbAlgorithm.itemText(0) == 'Nelder-Mead Simplex'
        assert self.widget.cbAlgorithm.itemText(4) == 'Levenberg-Marquardt (scipy.leastsq)'
        assert self.widget.cbAlgorithm.currentIndex() == 5

    def testAssignValidators(self):
        """
        Check that line edits got correct validators
        """
        # Can't reliably test the method in action, but can easily check the results
        
        # DREAM
        assert isinstance(self.widget.samples_dream.validator(), QtGui.QIntValidator)
        assert isinstance(self.widget.burn_dream.validator(), QtGui.QIntValidator)
        assert isinstance(self.widget.pop_dream.validator(), QtGui.QDoubleValidator)
        assert isinstance(self.widget.thin_dream.validator(), QtGui.QIntValidator)
        assert isinstance(self.widget.steps_dream.validator(), QtGui.QIntValidator)
        # DE
        assert isinstance(self.widget.steps_de.validator(), QtGui.QIntValidator)
        assert isinstance(self.widget.CR_de.validator(), QtGui.QDoubleValidator)
        assert isinstance(self.widget.pop_de.validator(), QtGui.QDoubleValidator)
        assert isinstance(self.widget.F_de.validator(), QtGui.QDoubleValidator)
        assert isinstance(self.widget.ftol_de.validator(), QtGui.QDoubleValidator)
        assert isinstance(self.widget.xtol_de.validator(), QtGui.QDoubleValidator)

        # bottom value for floats and ints
        assert self.widget.steps_de.validator().bottom() == 0
        assert self.widget.CR_de.validator().bottom() == 0

        # Behaviour on empty cell
        self.widget.onAlgorithmChange(3)
        self.widget.steps_de.setText("")
        # This should disable the OK button
        ## self.assertFalse(self.widget.buttonBox.button(QtGui.QDialogButtonBox.Ok).isEnabled())
        # Let's put some valid value in lineedit
        self.widget.steps_de.setText("1")
        # This should enable the OK button
        assert self.widget.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).isEnabled()

    def testOnAlgorithmChange(self):
        '''Test the combo box change callback'''
        # Current ID
        assert self.widget.current_fitter_id == 'lm'
        # index = 0
        self.widget.onAlgorithmChange(0)
        # Check Nelder-Mead
        assert self.widget.stackedWidget.currentIndex() == 1
        assert self.widget.current_fitter_id == 'lm'

        # index = 4
        self.widget.onAlgorithmChange(4)
        # Check Levenberg-Marquad
        assert self.widget.stackedWidget.currentIndex() == 1
        assert self.widget.current_fitter_id == 'lm'

    def testOnApply(self):
        '''Test bumps update'''
        # Spy on the update signal
        spy_apply = QtSignalSpy(self.widget, self.widget.fit_option_changed)

        # Set the DREAM optimizer
        self.widget.cbAlgorithm.setCurrentIndex(2)
        # Change some values
        self.widget.init_dream.setCurrentIndex(2)
        self.widget.steps_dream.setText("50")
        # Apply the new values
        self.widget.onApply()

        assert spy_apply.count() == 1
        assert 'DREAM' in spy_apply.called()[0]['args'][0]

        # Check the parameters
        assert options.FIT_CONFIG.values['dream']['steps'] == 50.0
        assert options.FIT_CONFIG.values['dream']['init'] == 'cov'

    # test disabled until pyQt5 works well
    @pytest.mark.skip(reason="2022-09 already broken - causes test suite hang")
    def testOnHelp(self):
        ''' Test help display'''
        webbrowser.open = MagicMock()

        # Invoke the action on default tab
        self.widget.onHelp()
        # Check if show() got called
        assert webbrowser.open.called
        # Assure the filename is correct
        assert "optimizer.html" in webbrowser.open.call_args[0][0]

        # Change the combo index
        self.widget.cbAlgorithm.setCurrentIndex(2)
        self.widget.onHelp()
        # Check if show() got called
        assert webbrowser.open.call_count == 2
        # Assure the filename is correct
        assert "fit-dream" in webbrowser.open.call_args[0][0]

        # Change the index again
        self.widget.cbAlgorithm.setCurrentIndex(4)
        self.widget.onHelp()
        # Check if show() got called
        assert webbrowser.open.call_count == 3
        # Assure the filename is correct
        assert "fit-lm" in webbrowser.open.call_args[0][0]

    def testWidgetFromOptions(self):
        '''Test the helper function'''
        # test empty call
        assert self.widget.widgetFromOption(None) is None
        # test silly call
        assert self.widget.widgetFromOption('poop') is None
        assert self.widget.widgetFromOption(QtWidgets.QMainWindow()) is None

        # Switch to DREAM
        self.widget.cbAlgorithm.setCurrentIndex(2)
        # test smart call
        assert isinstance(self.widget.widgetFromOption('samples'), QtWidgets.QLineEdit)
        assert isinstance(self.widget.widgetFromOption('init'), QtWidgets.QComboBox)

    def testUpdateWidgetFromBumps(self):
        '''Test the widget update'''
        # modify some value
        options.FIT_CONFIG.values['newton']['steps'] = 1234
        options.FIT_CONFIG.values['newton']['starts'] = 666
        options.FIT_CONFIG.values['newton']['xtol'] = 0.01

        # Invoke the method for the changed 
        self.widget.updateWidgetFromBumps('newton')

        # See that the widget picked up the right values
        assert self.widget.steps_newton.text() == '1234'
        assert self.widget.starts_newton.text() == '666'
        assert self.widget.ftol_newton.text() == '1e-06' # default
        assert self.widget.xtol_newton.text() == '0.01'

if __name__ == "__main__":
    unittest.main()
