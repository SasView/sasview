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
fitters.FIT_DEFAULT_ID = 'lm'


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

    def __init__(self, parent=None, config=None):
        super(FittingOptions, self).__init__(parent)
        self.setupUi(self)

        self.config = config

        # no reason to have this widget resizable
        self.setFixedSize(self.minimumSizeHint())

        self.setWindowTitle("Fit Algorithms")

        # Fill up the algorithm combo, based on what BUMPS says is available
        self.cbAlgorithm.addItems([n.name for n in fitters.FITTERS if n.id in fitters.FIT_ACTIVE_IDS])

        # Handle the Apply button click
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.onApply)
        # handle the Help button click
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Help).clicked.connect(self.onHelp)

        # Handle the combo box changes
        self.cbAlgorithm.currentIndexChanged.connect(self.onAlgorithmChange)

        # Set the default index
        default_name = [n.name for n in fitters.FITTERS if n.id == fitters.FIT_DEFAULT_ID][0]
        default_index = self.cbAlgorithm.findText(default_name)
        self.cbAlgorithm.setCurrentIndex(default_index)

        # Assign appropriate validators
        self.assignValidators()

        # Set defaults
        self.current_fitter_id = fitters.FIT_DEFAULT_ID

        # OK has to be initialized to True, after initial validator setup
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

    def assignValidators(self):
        """
        Use options.FIT_FIELDS to assert which line edit gets what validator
        """
        for option in bumps.options.FIT_FIELDS.keys():
            (f_name, f_type) = bumps.options.FIT_FIELDS[option]
            validator = None
            if type(f_type) == types.FunctionType:
                validator = QtGui.QIntValidator()
                validator.setBottom(0)
            elif f_type == float:
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
            [n.id for n in fitters.FITTERS if n.name == str(self.cbAlgorithm.currentText())][0]

        # find the right stacked widget
        widget_name = "self.page_"+str(self.current_fitter_id)

        # Convert the name into widget instance
        widget_to_activate = eval(widget_name)
        index_for_this_id = self.stackedWidget.indexOf(widget_to_activate)

        # Select the requested widget
        self.stackedWidget.setCurrentIndex(index_for_this_id)

        self.updateWidgetFromBumps(self.current_fitter_id)

        self.assignValidators()

        # OK has to be reinitialized to True
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

    def onApply(self):
        """
        Update the fitter object
        """
        # Notify the perspective, so the window title is updated
        self.fit_option_changed.emit(self.cbAlgorithm.currentText())

        def bumpsUpdate(option):
            """
            Utility method for bumps state update
            """
            widget = self.widgetFromOption(option)
            new_value = widget.currentText() if isinstance(widget, QtWidgets.QComboBox) \
                else float(widget.text())
            self.config.values[self.current_fitter_id][option] = new_value

        # Update the BUMPS singleton
        [bumpsUpdate(o) for o in self.config.values[self.current_fitter_id].keys()]

    def onHelp(self):
        """
        Show the "Fitting options" section of help
        """
        tree_location = GuiUtils.HELP_DIRECTORY_LOCATION
        tree_location += "/user/sasgui/perspectives/fitting/"

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
            widget_name = 'self.'+option+'_'+fitter_id
            if option not in bumps.options.FIT_FIELDS:
                return
            if isinstance(bumps.options.FIT_FIELDS[option][1], bumps.options.ChoiceList):
                control = eval(widget_name)
                control.setCurrentIndex(control.findText(str(options[option])))
            else:
                eval(widget_name).setText(str(options[option]))

        pass
