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
                dtype = self._convertParamType(dtype)
                param = FittingMethodParameter(shortName, longName, dtype, defValue)
                params.append(param)
            self.add(FittingMethodBumps(f.id, f.name, params))

    @staticmethod
    def _convertParamType(dtype):
        if dtype is bumps.options.parse_int:
            dtype = int
        elif isinstance(dtype, bumps.options.ChoiceList):
            dtype = tuple(dtype.choices)
        return dtype

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
        self.setWindowTitle("Fit Algorithms")
        # no reason to have this widget resizable
        self.layout().setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

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

        # Assign appropriate validators
        self.assignValidators()

        # OK has to be initialized to True, after initial validator setup
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

        # Handle the combo box changes
        self.cbAlgorithm.currentIndexChanged.connect(self.onAlgorithmChange)

        # Set the default index and trigger filling the layout
        default_index = self.cbAlgorithm.findText(self.fittingMethods.default.longName)
        self.cbAlgorithm.setCurrentIndex(default_index)

    def assignValidators(self):
        """
        Sets the appropriate validators to the line edits as defined by FittingMethodParameter
        """
        fm = self.fittingMethods[self.currentOptimizer]
        for param in fm.params.values():
            validator = None
            if param.type == int:
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

    def _clearLayout(self):
        layout = self.groupBox.layout()
        for i in reversed(list(range(layout.count()))):
            # reversed removal avoids renumbering possibly
            item = layout.takeAt(i)
            try: # spaceritem does not have a widget
                if item.widget().objectName() == "cbAlgorithm":
                    continue # do not delete the checkbox, will be added later again
                item.widget().setParent(None)
                item.widget().deleteLater()
            except AttributeError:
                pass

    @staticmethod
    def _makeLabel(name):
        lbl = QtWidgets.QLabel(name + ":")
        lbl.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        lbl.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                                QtWidgets.QSizePolicy.Fixed))
        lbl.setWordWrap(True)
        return lbl

    @staticmethod
    def _inputWidgetFromType(ptype, parent):
        """
        Creates a widget for user input based on the given data type to be entered.
        """
        widget = None
        if ptype in (float, int):
            widget = QtWidgets.QLineEdit(parent)
        elif isinstance(ptype, (tuple, list)):
            widget = QtWidgets.QComboBox(parent)
            widget.addItems(ptype)
        return widget

    def _fillLayout(self):
        fm = self.fittingMethods[self.currentOptimizer]
        layout = self.groupBox.layout()
        layout.addWidget(self.cbAlgorithm, 0, 0, 1, -1)
        for param in fm.params.values():
            row = layout.rowCount()+1
            layout.addWidget(self._makeLabel(param.longName), row, 0)
            widget = self._inputWidgetFromType(param.type, self)
            if widget is None:
                continue
            widgetName = param.shortName+'_'+fm.shortName
            layout.addWidget(widget, row, 1)
            setattr(self, widgetName, widget)
        layout.addItem(QtWidgets.QSpacerItem(0, 0, vPolicy=QtWidgets.QSizePolicy.Expanding))

    def onAlgorithmChange(self, index):
        """
        Change the page in response to combo box index
        """
        # Find the algorithm ID from name
        selectedName = self.currentOptimizer

        self._clearLayout()
        self._fillLayout()

        # Select the requested widget
        self.updateWidgetFromConfig()
        self.assignValidators()

        # OK has to be reinitialized to True
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

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
        current_fitter_id = self.fittingMethods[self.currentOptimizer].shortName
        helpfile = "optimizer.html#fit-" + current_fitter_id
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
        fm = self.fittingMethods[self.currentOptimizer]
        for param in fm.params.values():
            # Find the widget name of the option
            # e.g. 'samples' for 'dream' is 'self.samples_dream'
            widget_name = 'self.'+param.shortName+'_'+fm.shortName
            if isinstance(param.type, (tuple, list)):
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
