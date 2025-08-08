# global
import types

import bumps.options
from bumps import fitters
from PySide6 import QtCore, QtGui, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Fitting.UI.FittingOptionsUI import Ui_FittingOptions
from sas.qtgui.Utilities.Preferences.PreferencesWidget import PreferencesWidget
from sas.system.config.config import config as sasview_config

# Set the default optimizer
fitters.FIT_DEFAULT_ID = 'lm'


class FittingOptions(PreferencesWidget, Ui_FittingOptions):
    """
    Hard-coded version of the fit options dialog available from BUMPS.
    This should be make more "dynamic".
    bumps.options.FIT_FIELDS gives mapping between parameter names, parameter strings and field type
    (double line edit, integer line edit, combo box etc.), e.g.::

        FIT_FIELDS = dict(
            samples = ("Samples", parse_int),
            xtol = ("x tolerance", float),
        )

    bumps.fitters.<algorithm>.settings gives mapping between algorithm, parameter name and default value, e.g.::

        >>> settings = [('steps', 1000), ('starts', 1), ('radius', 0.15), ('xtol', 1e-6), ('ftol', 1e-8)]
    """
    fit_option_changed = QtCore.Signal(str)
    name = "Fit Optimizers"

    def __init__(self, config=None):
        super(FittingOptions, self).__init__(self.name, False)
        # Use pre-built UI
        self.setupUi(self)

        self.config = config
        self.config_params = ['FITTING_DEFAULT_OPTIMIZER']

        # Fill up the algorithm combo, based on what BUMPS says is available
        self.active_fitters = [n.name for n in fitters.FITTERS if n.id in fitters.FIT_ACTIVE_IDS and 'least' not in n.id]
        self.cbAlgorithm.addItems(self.active_fitters)
        self.cbAlgorithmDefault.addItems(self.active_fitters)

        # Set the default index
        self.current_fitter_id = getattr(sasview_config, 'FITTING_DEFAULT_OPTIMIZER', fitters.FIT_DEFAULT_ID)
        default_name = [n.name for n in fitters.FITTERS if n.id == self.current_fitter_id][0]
        default_index = self.cbAlgorithm.findText(default_name)
        self.cbAlgorithmDefault.setCurrentIndex(default_index)
        self.cbAlgorithm.setCurrentIndex(default_index)
        self._algorithm_change(default_index)
        # previous algorithm choice
        self.previous_index = default_index

        # Assign appropriate validators
        self.assignValidators()

        # Assign signals
        self.addSignals()
        self.cmdHelp.setText(f'Help: {self.cbAlgorithm.currentText()}')

        # To prevent errors related to parent, connect the combo box changes once the widget is instantiated
        self.cbAlgorithm.currentIndexChanged.connect(self.onAlgorithmChange)
        self.cbAlgorithmDefault.currentIndexChanged.connect(self.onDefaultAlgorithmChange)

    #
    # Preference Widget required methods

    def _addAllWidgets(self):
        pass

    def _toggleBlockAllSignaling(self, toggle: bool):
        self.cbAlgorithm.blockSignals(toggle)
        self.cbAlgorithmDefault.blockSignals(toggle)

    def _restoreFromConfig(self):
        optimizer_key = sasview_config.FITTING_DEFAULT_OPTIMIZER
        optimizer_name = bumps.options.FIT_CONFIG.names[optimizer_key]
        self.cbAlgorithmDefault.setCurrentIndex(self.cbAlgorithmDefault.findText(optimizer_name))
        name = [n.name for n in fitters.FITTERS if n.id == self.current_fitter_id][0]
        self.cbAlgorithm.setCurrentIndex(self.cbAlgorithm.findText(name))
        self._algorithm_change(self.cbAlgorithm.currentIndex())

    def addSignals(self):
        self.cmdHelp.clicked.connect(self.onHelp)
        self.cbAlgorithm.currentIndexChanged.connect(lambda: self.cmdHelp.setText(f"{self.cmdHelp.text().split(' ')[0]} {self.cbAlgorithm.currentText()}"))

    def assignValidators(self):
        """
        Use options.FIT_FIELDS to assert which line edit gets what validator
        """
        for option in bumps.options.FIT_FIELDS.keys():
            _, f_type = bumps.options.FIT_FIELDS[option]
            validator = None
            if isinstance(f_type, types.FunctionType):
                validator = QtGui.QIntValidator()
                validator.setBottom(0)
            elif isinstance(f_type, float):
                validator = GuiUtils.DoubleValidator()
                validator.setBottom(0)
            else:
                continue
            for fitter_id in fitters.FIT_ACTIVE_IDS:
                line_edit = self.widgetFromOption(str(option), current_fitter=str(fitter_id))
                if hasattr(line_edit, 'setValidator') and validator is not None:
                    line_edit.setValidator(validator)
                    line_edit.textChanged.connect(self.check_state)
                    line_edit.textChanged.emit(line_edit.text())

    def check_state(self, *args, **kwargs):
        sender = self.sender()
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]
        color = '' if state == QtGui.QValidator.Acceptable else '#fff79a'
        sender.setStyleSheet('QLineEdit { background-color: %s }' % color)

    def onDefaultAlgorithmChange(self):
        text = self.cbAlgorithmDefault.currentText()
        self.cbAlgorithm.setCurrentIndex(self.cbAlgorithm.findText(text))
        id = dict((new_val, new_k) for new_k, new_val in bumps.options.FIT_CONFIG.names.items()).get(text)
        self._stageChange('FITTING_DEFAULT_OPTIMIZER', id)

    def onAlgorithmChange(self, index):
        """Triggered method when the index of the combo box changes."""
        self._algorithm_change(index)
        self._stageChange("Fitting.activeAlgorithm", index)

    def _algorithm_change(self, index):
        """
        Change the page in response to combo box index. Can also be called programmatically.
        """
        # Find the algorithm ID from name
        fitter_id = \
            [n.id for n in fitters.FITTERS if n.name == str(self.cbAlgorithm.currentText())][0]

        # find the right stacked widget
        widget_name = "self.page_"+str(fitter_id)

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

        self.updateWidgetFromBumps(fitter_id)

        self.assignValidators()

        # keep reference
        self.previous_index = index

    def applyNonConfigValues(self):
        """Applies values that aren't stored in config. Only widgets that require this need to override this method."""
        self.current_fitter_id = [n.id for n in fitters.FITTERS if n.name == str(self.cbAlgorithm.currentText())][0]
        options = self.config.values[self.current_fitter_id]
        for option in options.keys():
            # Find the widget name of the option
            # e.g. 'samples' for 'dream' is 'self.samples_dream'
            widget_name = 'self.'+option+'_'+self.current_fitter_id
            try:
                line_edit = eval(widget_name)
            except AttributeError:
                # Skip bumps monitors
                continue
            if line_edit is None or not isinstance(line_edit, QtWidgets.QLineEdit):
                continue
            color = line_edit.palette().color(QtGui.QPalette.Window).name()
            if color == '#fff79a':
                # Show a custom tooltip and return
                tooltip = "<html><b>Please enter valid values in all fields.</html>"
                QtWidgets.QToolTip.showText(line_edit.mapToGlobal(
                    QtCore.QPoint(line_edit.rect().right(), line_edit.rect().bottom() + 2)), tooltip)
                return

        # Notify the perspective, so the window title is updated
        self.fit_option_changed.emit(self.cbAlgorithm.currentText())

        def bumpsUpdate(option):
            """
            Utility method for bumps state update
            """
            widget = self.widgetFromOption(option)
            if widget is None:
                return
            try:
                if isinstance(widget, QtWidgets.QComboBox):
                    new_value = widget.currentText()
                else:
                    try:
                        new_value = int(widget.text())
                    except ValueError:
                        new_value = float(widget.text())
                #new_value = widget.currentText() if isinstance(widget, QtWidgets.QComboBox) \
                #    else float(widget.text())
                self.config.values[self.current_fitter_id][option] = new_value
            except ValueError:
                # Don't update bumps if widget has bad data
                self.reject

        # Update the BUMPS singleton
        [bumpsUpdate(o) for o in self.config.values[self.current_fitter_id].keys()]

    def onHelp(self):
        """
        Show the "Fitting options" section of help
        """
        from sas.qtgui.MainWindow.GuiManager import GuiManager
        tree_location = "/user/qtgui/Perspectives/Fitting/"

        # Actual file anchor will depend on the combo box index
        # Note that we can be clusmy here, since bad current_fitter_id
        # will just make the page displayed from the top
        selected_fit_algorithm = self.cbAlgorithm.currentText()
        fitter_id = [n.id for n in fitters.FITTERS if n.name == selected_fit_algorithm][0]
        helpfile = "optimizer.html#fit-" + fitter_id
        help_location = tree_location + helpfile
        GuiManager.showHelp(help_location)

    def widgetFromOption(self, option_id, current_fitter=None):
        """
        returns widget's element linked to the given option_id
        """
        if current_fitter is None:
            current_fitter = self.current_fitter_id
        if option_id not in list(bumps.options.FIT_FIELDS.keys()):
            return None
        option = option_id + '_' + current_fitter
        if not hasattr(self, option):
            return None
        return eval('self.' + option)

    def getResults(self):
        """
        Sends back the current choice of parameters
        """
        algorithm = self.cbAlgorithm.currentText()
        return algorithm

    def updateWidgetFromBumps(self, fitter_id):
        """
        Given the ID of the current optimizer, fetch the values
        and update the widget
        """
        options = self.config.values[fitter_id]
        for option in options.keys():
            # Find the widget name of the option
            # e.g. 'samples' for 'dream' is 'self.samples_dream'
            attribute = option + '_' + fitter_id
            if not hasattr(self, attribute):
                continue
            widget_name = 'self.'+attribute
            if option not in bumps.options.FIT_FIELDS:
                return
            control = eval(widget_name)
            if isinstance(bumps.options.FIT_FIELDS[option][1], bumps.options.ChoiceList):
                control.setCurrentIndex(control.findText(str(options[option])))
                control.currentIndexChanged.connect(lambda: self._stageChange(widget_name, ""))
            else:
                control.setText(str(options[option]))
                control.editingFinished.connect(lambda: self._stageChange(widget_name, ""))

        pass
