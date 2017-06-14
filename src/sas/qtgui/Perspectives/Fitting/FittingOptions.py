# global
import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtWebKit

from sas.qtgui.UI import images_rc
from sas.qtgui.UI import main_resources_rc
#from bumps.fitters import FITTERS, FIT_AVAILABLE_IDS, FIT_ACTIVE_IDS, FIT_DEFAULT_ID
from bumps import fitters
import bumps.options

from sas.qtgui.Perspectives.Fitting.UI.FittingOptionsUI import Ui_FittingOptions

# Set the default optimizer
fitters.FIT_DEFAULT_ID = 'lm'

class FittingOptions(QtGui.QDialog, Ui_FittingOptions):
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
    fit_option_changed = QtCore.pyqtSignal(str, dict)

    def __init__(self, parent=None, config=None):
        super(FittingOptions, self).__init__(parent)
        self.setupUi(self)

        self.config = config

        # no reason to have this widget resizable
        self.setFixedSize(self.minimumSizeHint())

        self.setWindowTitle("Fitting Options")

        # Fill up the algorithm combo, based on what BUMPS says is available
        self.cbAlgorithm.addItems([n.name for n in fitters.FITTERS if n.id in fitters.FIT_ACTIVE_IDS])

        # Handle the Apply button click
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).clicked.connect(self.onApply)

        # Handle the combo box changes
        self.cbAlgorithm.currentIndexChanged.connect(self.onAlgorithmChange)

        # Set the default index
        default_name = [n.name for n in fitters.FITTERS if n.id == fitters.FIT_DEFAULT_ID][0]
        default_index = self.cbAlgorithm.findText(default_name)
        self.cbAlgorithm.setCurrentIndex(default_index)
        self.current_fitter_id = fitters.FIT_DEFAULT_ID

        # Fill in options for all active fitters
        #[self.updateWidgetFromBumps(fitter_id) for fitter_id in fitters.FIT_ACTIVE_IDS]

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

        # Select the requested widget
        self.stackedWidget.setCurrentIndex(self.stackedWidget.indexOf(widget_to_activate))

        self.updateWidgetFromBumps(self.current_fitter_id)

    def onApply(self):
        """
        Update the fitter object in perspective
        """
        self.fit_option_changed.emit(self.cbAlgorithm.currentText(), {})

        # or just do it locally
        for option in self.config.values[self.current_fitter_id].iterkeys():
            widget = self.widgetFromOption(option)
            new_value = ""
            if isinstance(widget, QtGui.QComboBox):
                new_value = widget.currentText()
            else:
                new_value = float(widget.text())
            self.config.values[self.current_fitter_id][option] = new_value

    def widgetFromOption(self, option_id):
        """
        returns widget's element linked to the given option_id
        """
        return eval('self.' + option_id + '_' + self.current_fitter_id)

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
        for option in options.iterkeys():
            # Find the widget name of the option
            # e.g. 'samples' for 'dream' is 'self.samples_dream'
            widget_name = 'self.'+option+'_'+fitter_id
            if isinstance(bumps.options.FIT_FIELDS[option][1], bumps.options.ChoiceList):
                control = eval(widget_name)
                control.setCurrentIndex(control.findText(str(options[option])))
            else:
                eval(widget_name).setText(str(options[option]))

        pass

    def updateBumpsOptions(self, optimizer_id):
        """
        Given the ID of the optimizer, gather widget's values
        and update the bumps options
        """
        pass

