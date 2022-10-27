import os
import types
import webbrowser

from bumps.options import FIT_CONFIG, FIT_FIELDS, ChoiceList

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from sas.system import config

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Fitting.FittingPerspective import FittingWindow
from sas.qtgui.Utilities.Preferences.PreferencesWidget import PreferencesWidget, set_config_value


class FittingOptions(PreferencesWidget):
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
    fit_option_changed = QtCore.pyqtSignal(str)

    name = "Fitting Optimizers"

    def __init__(self):
        super(FittingOptions, self).__init__(self.name)
        # Listen to GUI Manager signal updating fit options

    def _addAllWidgets(self):
        # Add default fit algorithm widget
        self.addHeaderText("Values to persist between SasView sessions:")
        self.defaultOptimizer = self.addComboBox("Default Fit Algorithm",
                                                 FIT_CONFIG.names.values(),
                                                 self.setDefaultOptimizer,
                                                 FIT_CONFIG.names[config.DEFAULT_FITTING_OPTIMIZER])
        self.addHorizontalLine()

        # Add all other widgets
        self.addHeaderText("Fitting options for this session only:")
        self.activeOptimizer = self.addComboBox("Default Fit Algorithm",
                                                FIT_CONFIG.names.values(),
                                                self.setActiveOptimizer,
                                                FIT_CONFIG.names[config.DEFAULT_FITTING_OPTIMIZER])

    def setDefaultOptimizer(self):
        """Capture the default optimizer value in the and set it in the config file"""
        text = self.defaultOptimizer.currentText()
        id = dict((new_val, new_k) for new_k, new_val in FIT_CONFIG.names.items()).get(text)
        set_config_value('DEFAULT_FITTING_OPTIMIZER', id)
        self.activeOptimizer.setCurrentIndex(self.defaultOptimizer.currentIndex())
        self.setActiveOptimizer()

    def setActiveOptimizer(self):
        """Grab the optimizer value and set it in the config file"""
        self.parent.guiManager.loadedPerspectives["Fitting"].onFittingOptionsChange(self.activeOptimizer.currentText())

    def assignValidators(self):
        """
        Use options.FIT_FIELDS to assert which line edit gets what validator
        """
        for option in FIT_FIELDS.keys():
            (f_name, f_type) = FIT_FIELDS[option]
            validator = None
            if type(f_type) == types.FunctionType:
                validator = QtGui.QIntValidator()
                validator.setBottom(0)
            elif f_type == float:
                validator = GuiUtils.DoubleValidator()
                validator.setBottom(0)
            else:
                continue
            for fitter_id in FIT_CONFIG.fitters.keys():
                line_edit = self.widgetFromOption(str(option), current_fitter=str(fitter_id))
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
        self.current_fitter_id = \
            [n.id for n in FIT_CONFIG.fitters.values() if n.name == str(self.cbAlgorithm.currentText())][0]

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

        self.updateWidgetFromBumps(self.current_fitter_id)

        self.assignValidators()

        # OK has to be reinitialized to True
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

        # keep reference
        self.previous_index = index

    def onApply(self):
        """
        Update the fitter object
        """
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
            color = line_edit.palette().color(QtGui.QPalette.Background).name()
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

    def widgetFromOption(self, option_id, current_fitter=None):
        """
        returns widget's element linked to the given option_id
        """
        if current_fitter is None:
            current_fitter = self.current_fitter_id
        if option_id not in list(bumps.options.FIT_FIELDS.keys()): return None
        option = option_id + '_' + current_fitter
        if not hasattr(self, option): return None
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
            if option not in FIT_FIELDS:
                return
            if isinstance(FIT_FIELDS[option][1], ChoiceList):
                control = eval(widget_name)
                control.setCurrentIndex(control.findText(str(options[option])))
            else:
                eval(widget_name).setText(str(options[option]))

        pass
