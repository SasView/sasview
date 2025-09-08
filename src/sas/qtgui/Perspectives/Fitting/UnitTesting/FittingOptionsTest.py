import webbrowser

import pytest
from bumps import options
from PySide6 import QtGui, QtWidgets

# Local
from sas.qtgui.Perspectives.Fitting.FittingOptions import FittingOptions
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy
from sas.qtgui.Utilities.Preferences.PreferencesWidget import PreferencesWidget


class FittingOptionsTest:
    '''Test the FittingOptions dialog'''

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the FittingOptions'''
        w = FittingOptions(config=options.FIT_CONFIG)
        yield w
        w.close()

    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget, PreferencesWidget)

        # The combo box
        assert isinstance(widget.cbAlgorithm, QtWidgets.QComboBox)
        assert widget.cbAlgorithm.count() == 6
        assert widget.cbAlgorithm.itemText(0) == 'Nelder-Mead Simplex'
        assert widget.cbAlgorithm.itemText(4).startswith('Levenberg-Marquardt')
        assert widget.cbAlgorithm.currentIndex() == 5

    def testAssignValidators(self, widget):
        """
        Check that line edits got correct validators
        """
        # Can't reliably test the method in action, but can easily check the results

        # DREAM
        assert isinstance(widget.samples_dream.validator(), QtGui.QIntValidator)
        assert isinstance(widget.burn_dream.validator(), QtGui.QIntValidator)
        assert isinstance(widget.pop_dream.validator(), QtGui.QDoubleValidator)
        assert isinstance(widget.thin_dream.validator(), QtGui.QIntValidator)
        assert isinstance(widget.steps_dream.validator(), QtGui.QIntValidator)
        # DE
        assert isinstance(widget.steps_de.validator(), QtGui.QIntValidator)
        assert isinstance(widget.CR_de.validator(), QtGui.QDoubleValidator)
        assert isinstance(widget.pop_de.validator(), QtGui.QDoubleValidator)
        assert isinstance(widget.F_de.validator(), QtGui.QDoubleValidator)
        assert isinstance(widget.ftol_de.validator(), QtGui.QDoubleValidator)
        assert isinstance(widget.xtol_de.validator(), QtGui.QDoubleValidator)

        # bottom value for floats and ints
        assert widget.steps_de.validator().bottom() == 0
        assert widget.CR_de.validator().bottom() == 0

        # Behaviour on empty cell
        widget.onAlgorithmChange(3)
        widget.steps_de.setText("")
        # This should disable the OK button
        ## assert not widget.buttonBox.button(QtGui.QDialogButtonBox.Ok).isEnabled()
        # Let's put some valid value in lineedit
        widget.steps_de.setText("1")

    def testOnAlgorithmChange(self, widget):
        '''Test the combo box change callback'''
        # Current ID
        assert widget.current_fitter_id == 'lm'
        # index = 0
        widget.onAlgorithmChange(0)
        # Check Nelder-Mead
        assert widget.stackedWidget.currentIndex() == 1
        assert widget.current_fitter_id == 'lm'

        # index = 4
        widget.onAlgorithmChange(4)
        # Check Levenberg-Marquad
        assert widget.stackedWidget.currentIndex() == 1
        assert widget.current_fitter_id == 'lm'

    def testOnApply(self, widget):
        '''Test bumps update'''
        # Spy on the update signal
        spy_apply = QtSignalSpy(widget, widget.fit_option_changed)

        # Set the DREAM optimizer
        widget.cbAlgorithm.setCurrentIndex(2)
        # Change some values
        widget.init_dream.setCurrentIndex(2)
        widget.steps_dream.setText("50")
        # Apply the new values
        widget.onApply()

        assert spy_apply.count() == 1
        assert 'DREAM' in spy_apply.called()[0]['args'][0]

        # Check the parameters
        assert options.FIT_CONFIG.values['dream']['steps'] == 50.0
        assert options.FIT_CONFIG.values['dream']['init'] == 'cov'

    def testOnHelp(self, widget, mocker):
        ''' Test help display'''
        mocker.patch.object(webbrowser, 'open')

        # Invoke the action on default tab
        widget.onHelp()
        # Check if show() got called
        assert webbrowser.open.called
        # Assure the filename is correct
        assert "optimizer.html" in webbrowser.open.call_args[0][0]

        # Change the combo index
        widget.cbAlgorithm.setCurrentIndex(2)
        widget.onHelp()
        # Check if show() got called
        assert webbrowser.open.call_count == 2
        # Assure the filename is correct
        assert "fit-dream" in webbrowser.open.call_args[0][0]

        # Change the index again
        widget.cbAlgorithm.setCurrentIndex(5)
        widget.onHelp()
        # Check if show() got called
        assert webbrowser.open.call_count == 3
        # Assure the filename is correct
        assert "fit-lm" in webbrowser.open.call_args[0][0]

    def testWidgetFromOptions(self, widget):
        '''Test the helper function'''
        # test empty call
        assert widget.widgetFromOption(None) is None
        # test silly call
        assert widget.widgetFromOption('poop') is None
        assert widget.widgetFromOption(QtWidgets.QMainWindow()) is None

        # Switch to DREAM
        widget.cbAlgorithm.setCurrentIndex(2)
        # test smart call
        assert isinstance(widget.widgetFromOption('samples'), QtWidgets.QLineEdit)
        assert isinstance(widget.widgetFromOption('init'), QtWidgets.QComboBox)

    def testUpdateWidgetFromBumps(self, widget):
        '''Test the widget update'''
        # modify some value
        options.FIT_CONFIG.values['newton']['steps'] = 1234
        options.FIT_CONFIG.values['newton']['starts'] = 666
        options.FIT_CONFIG.values['newton']['xtol'] = 0.01

        # Invoke the method for the changed
        widget.updateWidgetFromBumps('newton')

        # See that the widget picked up the right values
        assert widget.steps_newton.text() == '1234'
        assert widget.starts_newton.text() == '666'
        assert widget.ftol_newton.text() == '1e-06' # default
        assert widget.xtol_newton.text() == '0.01'
