import sys
import unittest
import webbrowser

from PyQt5 import QtGui, QtWidgets

from unittest.mock import MagicMock

# set up import paths
import path_prepare

from UnitTesting.TestUtils import QtSignalSpy

# Local
from sas.qtgui.Perspectives.Fitting.FittingOptions import \
        FittingOptions, FittingMethod, FittingMethodParameter

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class FittingOptionsTest(unittest.TestCase):
    '''Test the FittingOptions dialog'''
    def setUp(self):
        '''Create FittingOptions dialog'''
        self.widget = FittingOptions()

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtWidgets.QDialog)
        # Default title
        self.assertEqual(self.widget.windowTitle(), "Fit Algorithms")

        # The combo box
        self.assertIsInstance(self.widget.cbAlgorithm, QtWidgets.QComboBox)
        self.assertTrue(self.widget.cbAlgorithm.count() >= 5) # at least the default bumps algos
        self.assertEqual(self.widget.cbAlgorithm.itemText(0), 'Nelder-Mead Simplex')
        self.assertEqual(self.widget.cbAlgorithm.itemText(4), 'Levenberg-Marquardt')
        self.assertEqual(self.widget.cbAlgorithm.currentIndex(), 4)

    def testAssignValidators(self):
        """
        Check that line edits got correct validators
        """
        # Can't reliably test the method in action, but can easily check the results
        
        # DREAM
        self.widget.cbAlgorithm.setCurrentText("DREAM")
        self.assertIsInstance(self.widget.samples_dream.validator(), QtGui.QIntValidator)
        self.assertIsInstance(self.widget.burn_dream.validator(), QtGui.QIntValidator)
        self.assertIsInstance(self.widget.pop_dream.validator(), QtGui.QDoubleValidator)
        self.assertIsInstance(self.widget.thin_dream.validator(), QtGui.QIntValidator)
        self.assertIsInstance(self.widget.steps_dream.validator(), QtGui.QIntValidator)
        # DE
        self.widget.cbAlgorithm.setCurrentText("Differential Evolution")
        self.assertIsInstance(self.widget.steps_de.validator(), QtGui.QIntValidator)
        self.assertIsInstance(self.widget.CR_de.validator(), QtGui.QDoubleValidator)
        self.assertIsInstance(self.widget.pop_de.validator(), QtGui.QDoubleValidator)
        self.assertIsInstance(self.widget.F_de.validator(), QtGui.QDoubleValidator)
        self.assertIsInstance(self.widget.ftol_de.validator(), QtGui.QDoubleValidator)
        self.assertIsInstance(self.widget.xtol_de.validator(), QtGui.QDoubleValidator)

        # bottom value for floats and ints
        self.assertEqual(self.widget.steps_de.validator().bottom(), 0)
        self.assertEqual(self.widget.CR_de.validator().bottom(), 0)

        # Behaviour on empty cell
        self.widget.onAlgorithmChange(3)
        self.widget.steps_de.setText("")
        # This should disable the OK button
        ## self.assertFalse(self.widget.buttonBox.button(QtGui.QDialogButtonBox.Ok).isEnabled())
        # Let's put some valid value in lineedit
        self.widget.steps_de.setText("1")
        # This should enable the OK button
        self.assertTrue(self.widget.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).isEnabled())

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

        self.assertEqual(spy_apply.count(), 1)
        self.assertIn('DREAM', spy_apply.called()[0]['args'][0])

        # Check the parameters
        self.assertEqual(self.widget.fittingMethods['DREAM'].params['steps'].value, 50.)
        self.assertEqual(self.widget.fittingMethods['DREAM'].params['init'].value, 'cov')

    # test disabled until pyQt5 works well
    def testOnHelp(self):
        ''' Test help display'''
        webbrowser.open = MagicMock()

        # Invoke the action on default tab
        self.widget.onHelp()
        # Check if show() got called
        self.assertTrue(webbrowser.open.called)
        # Assure the filename is correct
        self.assertIn("optimizer.html", webbrowser.open.call_args[0][0])

        # Change the combo index
        self.widget.cbAlgorithm.setCurrentIndex(2)
        self.widget.onHelp()
        # Check if show() got called
        self.assertEqual(webbrowser.open.call_count, 2)
        # Assure the filename is correct
        self.assertIn("fit-dream", webbrowser.open.call_args[0][0])

        # Change the index again
        self.widget.cbAlgorithm.setCurrentIndex(4)
        self.widget.onHelp()
        # Check if show() got called
        self.assertEqual(webbrowser.open.call_count, 3)
        # Assure the filename is correct
        self.assertIn("fit-lm", webbrowser.open.call_args[0][0])

    def testParamWidget(self):
        '''Test the helper function'''
        # test empty call
        self.assertIsNone(self.widget.paramWidget(None, None))
        # test silly call
        self.assertIsNone(self.widget.paramWidget('poop', 'dsfsd'))
        self.assertIsNone(self.widget.paramWidget(QtWidgets.QMainWindow(), None))

        # Switch to DREAM
        self.widget.cbAlgorithm.setCurrentText('DREAM')
        fm = self.widget.fittingMethods['DREAM']
        # test smart call
        self.assertIsInstance(self.widget.paramWidget(fm, 'samples'), QtWidgets.QLineEdit)
        self.assertIsInstance(self.widget.paramWidget(fm, 'init'), QtWidgets.QComboBox)

    def testUpdateConfigFromWidget(self):
        '''Test the config update'''
        # test empty call
        self.assertIsNone(self.widget.updateConfigFromWidget(None))
        # test silly call
        self.assertIsNone(self.widget.updateConfigFromWidget('poop'))
        self.assertIsNone(self.widget.updateConfigFromWidget(QtWidgets.QMainWindow()))

        # Switch to DREAM
        self.widget.cbAlgorithm.setCurrentText('DREAM')
        fm = FittingMethod("dream", "a long dream", [
            FittingMethodParameter("samples", "# samples", int, 0),
            FittingMethodParameter("init", "init func", int, 0)])
        # test smart call
        self.widget.updateConfigFromWidget(fm)
        self.assertEqual(fm.params['samples'].value, 10000)
        self.assertEqual(fm.params['init'].value, 'eps')

    def testUpdateWidgetFromConfig(self):
        '''Test the widget update'''
        self.widget.cbAlgorithm.setCurrentText("Quasi-Newton BFGS")
        # modify some value
        self.assertEqual(self.widget.steps_newton.text(), '3000')
        self.assertEqual(self.widget.starts_newton.text(), '1')
        self.assertEqual(self.widget.ftol_newton.text(), '1e-06') # default
        self.assertEqual(self.widget.xtol_newton.text(), '1e-12')
        fm = self.widget.fittingMethods["Quasi-Newton BFGS"]
        fm.params['steps'].value = 1234
        fm.params['starts'].value = 666
        fm.params['ftol'].value = 1e-6
        fm.params['xtol'].value = 0.01

        # Invoke the method for the changed 
        self.widget.updateWidgetFromConfig()

        # See that the widget picked up the right values
        self.assertEqual(self.widget.steps_newton.text(), '1234')
        self.assertEqual(self.widget.starts_newton.text(), '666')
        self.assertEqual(self.widget.ftol_newton.text(), '1e-06') # default
        self.assertEqual(self.widget.xtol_newton.text(), '0.01')

if __name__ == "__main__":
    unittest.main()
