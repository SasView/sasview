# global
import sys
import os
import types
import webbrowser

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from sas.qtgui.UI import images_rc
from sas.qtgui.UI import main_resources_rc
import sas.qtgui.Utilities.GuiUtils as GuiUtils

from bumps import fitters
import bumps.options

from sas.qtgui.Perspectives.Fitting.UI.FittingOptionsUI import Ui_FittingOptions

# Set the default optimizer

def parse_int(value):
    """
    Converts user input to integer numbers. (from bumps)
    """
    float_value = float(value)
    if int(float_value) != float_value:
        raise ValueError("integer expected")
    return int(float_value)

class ChoiceList(object):
    """
    Validates user input for a distinct number of options.
    """
    def __init__(self, *choices):
        self.choices = choices
    def __call__(self, value):
        if not value in self.choices:
            raise ValueError('invalid option "%s": use %s'
                    % (value, '|'.join(self.choices)))
        else:
            return value

class FittingMethodParameter:
    """
    Descriptive meta data of a single parameter of an optimizer.
    """
    _shortName = None
    _longName = None
    _type = None
    _defaultValue = None
    value = None

    def __init__(self, shortName, longName, dtype, defaultValue):
        self._shortName = shortName
        self._longName = longName
        self._type = dtype
        self._defaultValue = defaultValue
        self.value = defaultValue

    @property
    def shortName(self):
        return self._shortName

    @property
    def longName(self):
        return self._longName

    @property
    def type(self):
        return self._type

    @property
    def defaultValue(self):
        return self._defaultValue

    def __str__(self):
        return "'{}' ({}): {} ({})".format(
                self.longName, self.sortName, self.defaultValue, self.type)

class FittingMethod:
    """
    Represents a generic fitting method.
    """
    _shortName = None
    _longName = None
    _params = None    # dict of <param short names>: <FittingMethodParam>

    def __init__(self, shortName, longName, params):
        self._shortName = shortName
        self._longName = longName
        self._params = dict(zip([p.shortName for p in params], params))

    @property
    def shortName(self):
        return self._shortName

    @property
    def longName(self):
        return self._longName

    @property
    def params(self):
        return self._params

    def storeConfig(self):
        """
        To be overridden by subclasses specific to optimizers.
        """
        pass

    def __str__(self):
        return "\n".join(["{} ({})".format(self.longName, self.shortName)]
                + [str(p) for p in self.params])

class FittingMethods:
    """
    A container for the available fitting methods.
    Allows SasView to employ other methods than those provided by the bumps package.
    """
    _methods = None # a dict containing FitMethod objects
    _default = None

    def __init__(self):
        """Receives a list of FittingMethod instances to be initialized with."""
        self._methods = dict()

    def add(self, fittingMethod):
        if not isinstance(fittingMethod, FittingMethod):
            return
        self._methods[fittingMethod.longName] = fittingMethod

    @property
    def longNames(self):
        return list(self._methods.keys())

    @property
    def ids(self):
        return [fm.shortName for fm in self._methods.values()]

    def __getitem__(self, longName):
        return self._methods[longName]

    def __len__(self):
        return len(self._methods)

    def __iter__(self):
        return self._methods.__iter__

    @property
    def default(self):
        return self._default

    def setDefault(self, methodName):
        assert methodName in self._methods # silently fail instead?
        self._default = self._methods[methodName]

    def __str__(self):
        return "\n".join(["{}: {}".format(key, fm) for key, fm in self._methods.items()])

class FittingMethodBumps(FittingMethod):
    def storeConfig(self):
        """
        Writes the user settings of given fitting method back to the optimizer backend
        where it is used once the 'fit' button is hit in the GUI.
        """
        fitConfig = bumps.options.FIT_CONFIG
        fitConfig.selected_id = self.shortName
        for param in self.params.values():
            fitConfig.values[self.shortName][param.shortName] = param.value

class FittingMethodsBumps(FittingMethods):
    def __init__(self):
        """
        Import fitting methods indicated by the provided list of ids from the bumps package.
        """
        super(FittingMethodsBumps, self).__init__()
        ids = fitters.FIT_ACTIVE_IDS
        for f in fitters.FITTERS:
            if f.id not in ids:
                continue
            params = []
            for shortName, defValue in f.settings:
                longName, dtype = bumps.options.FIT_FIELDS[shortName]
                param = FittingMethodParameter(shortName, longName, dtype, defValue)
                params.append(param)
            self.add(FittingMethodBumps(f.id, f.name, params))

class FittingOptions(QtWidgets.QDialog, Ui_FittingOptions):
    """
    Hard-coded version of the fit options dialog available from BUMPS.
    This should be make more "dynamic".
    bumps.options.FIT_FIELDS gives mapping between parameter names, parameter strings and field type
     (double line edit, integer line edit, combo box etc.), e.g.
        FIT_FIELDS = dict(
            samples = ("Samples", parse_int),
            xtol = ("x tolerance", float))

    bumps.fitters.<algorithm>.settings gives mapping between algorithm, parameter name and default value:
        e.g.
        settings = [('steps', 1000), ('starts', 1), ('radius', 0.15), ('xtol', 1e-6), ('ftol', 1e-8)]
    """
    fit_option_changed = QtCore.pyqtSignal(str)
    # storing of fitting methods here for now, dependencies might indicate a better place later
    _fittingMethods = None

    @property
    def fittingMethods(self):
        return self._fittingMethods

    def __init__(self, parent=None):
        super(FittingOptions, self).__init__(parent)
        self.setupUi(self)
        # disable the context help icon
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        # no reason to have this widget resizable
        self.setFixedSize(self.minimumSizeHint())
        self.setWindowTitle("Fit Algorithms")

        # Fill up the algorithm combo, based on what BUMPS says is available
        self._fittingMethods = FittingMethodsBumps()
        # option 1: hardcode the list of bumps fitting methods according to forms
        # option 2: create forms dynamically based on selected fitting methods
        self.fittingMethods.add(FittingMethod('mcsas', 'McSAS', [])) # FIXME just testing for now
        self.fittingMethods.setDefault('Levenberg-Marquardt')
        # build up the comboBox finally
        self.cbAlgorithm.addItems(self.fittingMethods.longNames)

        # Handle the Apply button click
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.onApply)
        # handle the Help button click
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Help).clicked.connect(self.onHelp)

        # Handle the combo box changes
        self.cbAlgorithm.currentIndexChanged.connect(self.onAlgorithmChange)

        # Set the default index
        default_index = self.cbAlgorithm.findText(self.fittingMethods.default.longName)
        self.cbAlgorithm.setCurrentIndex(default_index)
        # previous algorithm choice
        self.previous_index = default_index

        # Assign appropriate validators
        self.assignValidators()

        # Set defaults
        self.current_fitter_id = self.fittingMethods.default.shortName

        # OK has to be initialized to True, after initial validator setup
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

    def assignValidators(self):
        """
        Sets the appropriate validators to the line edits as defined by FittingMethodParameter
        """
        fm = self.fittingMethods[self.currentOptimizer]
        for param in fm.params.values():
            validator = None
            if type(param.type) == types.FunctionType:
                validator = QtGui.QIntValidator()
                validator.setBottom(0)
            elif param.type == float:
                validator = GuiUtils.DoubleValidator()
                validator.setBottom(0)
            else:
                continue
            line_edit = self.paramWidget(fm, param.shortName)
            if hasattr(line_edit, 'setValidator') and validator is not None:
                line_edit.setValidator(validator)
                line_edit.textChanged.connect(self.check_state)
                line_edit.textChanged.emit(line_edit.text())

    def check_state(self, *args, **kwargs):
        sender = self.sender()
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]
        if state == QtGui.QValidator.Acceptable:
            color = '' # default
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        else:
            color = '#fff79a' # yellow
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        sender.setStyleSheet('QLineEdit { background-color: %s }' % color)

    def onAlgorithmChange(self, index):
        """
        Change the page in response to combo box index
        """
        # Find the algorithm ID from name
        selectedName = self.currentOptimizer
        if selectedName in self.fittingMethods.longNames:
            self.current_fitter_id = self.fittingMethods[selectedName].shortName

        # find the right stacked widget
        widget_name = "self.page_"+str(self.current_fitter_id)

        # Convert the name into widget instance
        try:
            widget_to_activate = eval(widget_name)
        except AttributeError:
            # We don't yet have this optimizer.
            # Show message
            msg = "This algorithm has not yet been implemented in SasView.\n"
            msg += "Please choose a different algorithm"
            QtWidgets.QMessageBox.warning(self,
                                        'Warning',
                                        msg,
                                        QtWidgets.QMessageBox.Ok)
            # Move the index to previous position
            self.cbAlgorithm.setCurrentIndex(self.previous_index)
            return

        index_for_this_id = self.stackedWidget.indexOf(widget_to_activate)

        # Select the requested widget
        self.stackedWidget.setCurrentIndex(index_for_this_id)
        self.updateWidgetFromConfig()
        self.assignValidators()

        # OK has to be reinitialized to True
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

        # keep reference
        self.previous_index = index

    def paramWidget(self, fittingMethod, paramShortName):
        """
        Returns the widget associated to a FittingMethodParameter.
        """
        if paramShortName not in fittingMethod.params:
            return None
        widget_name = 'self.'+paramShortName+'_'+fittingMethod.shortName
        widget = None
        try:
            widget = eval(widget_name)
        except AttributeError:
            pass
        return widget

    def onApply(self):
        """
        Update the fitter object
        """
        fm = self.fittingMethods[self.currentOptimizer]
        for param in fm.params.values():
            line_edit = self.paramWidget(fm, param.shortName)
            if line_edit is None or not isinstance(line_edit, QtWidgets.QLineEdit):
                continue
            color = line_edit.palette().color(QtGui.QPalette.Background).name()
            if color == '#fff79a':
                # Show a custom tooltip and return
                tooltip = "<html><b>Please enter valid values in all fields.</html>"
                QtWidgets.QToolTip.showText(line_edit.mapToGlobal(
                    QtCore.QPoint(line_edit.rect().right(), line_edit.rect().bottom() + 2)),
                    tooltip)
                return

        # update config values from widgets before any notification is sent
        try:
            self.updateConfigFromWidget(fm)
        except ValueError:
            # Don't update bumps if widget has bad data
            self.reject

        fm.storeConfig() # write the current settings to bumps module
        # Notify the perspective, so the window title is updated
        self.fit_option_changed.emit(self.cbAlgorithm.currentText())
        self.close()

    def onHelp(self):
        """
        Show the "Fitting options" section of help
        """
        tree_location = GuiUtils.HELP_DIRECTORY_LOCATION
        tree_location += "/user/qtgui/Perspectives/Fitting/"

        # Actual file anchor will depend on the combo box index
        # Note that we can be clusmy here, since bad current_fitter_id
        # will just make the page displayed from the top
        helpfile = "optimizer.html#fit-" + self.current_fitter_id 
        help_location = tree_location + helpfile
        webbrowser.open('file://' + os.path.realpath(help_location))

    @property
    def currentOptimizer(self):
        """
        Sends back the current choice of parameters
        """
        value = self.cbAlgorithm.currentText()
        return str(value) # is str() really needed?

    def updateWidgetFromConfig(self):
        """
        Given the ID of the current optimizer, fetch the values
        and update the widget
        """
        fm = self.fittingMethods[self.currentOptimizer)]
        for param in fm.params.values():
            # Find the widget name of the option
            # e.g. 'samples' for 'dream' is 'self.samples_dream'
            widget_name = 'self.'+param.shortName+'_'+(fm.shortName)
            if isinstance(param.type, ChoiceList):
                control = eval(widget_name)
                control.setCurrentIndex(control.findText(str(param.value)))
            else:
                eval(widget_name).setText(str(param.value))

    def updateConfigFromWidget(self, fittingMethod):
        # update config values from widgets before any notification is sent
        for param in fittingMethod.params.values():
            widget = self.paramWidget(fittingMethod, param.shortName)
            if widget is None:
                continue
            new_value = None
            if isinstance(widget, QtWidgets.QComboBox):
                new_value = widget.currentText()
            else:
                try:
                    new_value = int(widget.text())
                except ValueError:
                    new_value = float(widget.text())
            if new_value is not None:
                fittingMethod.params[param.shortName].value = new_value
