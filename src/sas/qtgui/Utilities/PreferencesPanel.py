import logging

from PyQt5.QtWidgets import QMessageBox, QComboBox, QDialog
from typing import Optional

from sas import get_custom_config
from sas.sascalc.data_util.nxsunit import Converter
from sas.qtgui.Utilities.UI.PreferencesUI import Ui_preferencesUI

DEFAULT_I_UNIT = 'cm^{-1}'
DEFAULT_I_ABS2_UNIT = 'cm^{-2}'
DEFAULT_I_SESANS_UNIT = 'A^{-2} cm^{-1}'
DEFAULT_I_ARBITRARY_UNIT = 'a.u.'
DEFAULT_Q_UNIT = 'A^{-1}'
DEFAULT_Q_LENGTH_UNIT = 'A'
DEFAULT_Q_CATEGORY = "Inverse Length"
DEFAULT_I_CATEGORY = "Absolute Units"

logger = logging.getLogger(__name__)


def set_config_value(attr, value):
    # type: (str, Any) -> None
    """Helper method to set any config value, regardless if it exists or not
    :param attr: The configuration attribute that will be set
    :param value: The value the attribute will be set to. This could be a str, int, bool, a class instance, or any other
    """
    custom_config = get_custom_config()
    setattr(custom_config, attr, value)


def get_config_value(attr, default=None):
    # type: (str, Any) -> None
    """Helper method to get any config value, regardless if it exists or not
    :param attr: The configuration attribute that will be returned
    :param default: The assumed value, if the attribute cannot be found
    """
    custom_config = get_custom_config()
    return getattr(custom_config, attr, default) if hasattr(custom_config, attr) else default


def cb_replace_all_items_with_new(cb, new_items, default_item=None):
    # type: (QComboBox, [str], Optional[str]) -> None
    """Helper method that removes existing ComboBox values, replaces them and sets a default item, if defined
    :param cb: A QComboBox object
    :param new_items: A list of strings that will be used to populate the QComboBox
    :param default_item: The value to set the QComboBox to, if set
    """
    cb.clear()
    cb.addItems(new_items)
    if default_item and default_item in new_items:
        cb.setCurrentIndex(cb.findText(default_item))


class PreferencesPanel(QDialog, Ui_preferencesUI):
    """A preferences panel to house all SasView related settings. The left side of the window is a listWidget with a
    options menus available. The right side of the window is a stackedWidget object that houses the options
    associated with each listWidget item.

    **Important Note** When adding new preference widgets, the index for the listWidget and stackedWidget *must* match

    Release notes:
    SasView v5.0.5: Added defaults for loaded data units and plotted units
    """

    def __init__(self, parent=None):
        super(PreferencesPanel, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.setWindowTitle("Preferences")
        self.warning = None
        # A list of callables used to restore the default values for each item in StackedWidget
        self.restoreDefaultMethods = []
        # Set defaults values for the list and stacked widgets
        self.stackedWidget.setCurrentIndex(0)
        self.listWidget.setCurrentRow(0)
        # Add window actions
        self.listWidget.currentItemChanged.connect(self.prefMenuChanged)
        self.buttonBox.clicked.connect(self.onClick)

        ######################################################
        # Setup each widget separately below here
        ######################################################

        ######################################################
        # Plotting preferences
        # Mapping default values to each combo box
        self.plotting_unit_constants = {
            self.cbPlotIAbs: {"PLOTTER_I_ABS_UNIT": DEFAULT_I_UNIT},
            self.cbPlotIAbsSquared: {"PLOTTER_I_ABS_SQUARE_UNIT": DEFAULT_I_ABS2_UNIT},
            self.cbPlotISesans: {"PLOTTER_I_SESANS": DEFAULT_I_SESANS_UNIT},
            self.cbPlotIArbitrary: {"PLOTTER_I_ARB": DEFAULT_I_ARBITRARY_UNIT},
            self.cbPlotQLength: {"PLOTTER_Q_LENGTH": DEFAULT_Q_LENGTH_UNIT},
            self.cbPlotQInvLength: {"PLOTTER_Q_INV_LENGTH": DEFAULT_Q_UNIT}
        }
        self.setupPlottingWidget()
        self.checkBoxPlotQAsLoaded.toggled.connect(self.toggle_scaling_on_plot)
        self.checkBoxPlotIAsLoaded.toggled.connect(self.toggle_scaling_on_plot)
        self.restoreDefaultMethods.append(self.restorePlottingPrefs)
        ######################################################

        ######################################################
        # Data loading preferences
        # Mapping default values to each combo box
        self.data_type_selectors = {
            self.cbLoadIUnitType: {"LOADER_I_UNIT_TYPE": DEFAULT_I_CATEGORY},
            self.cbLoadQUnitType: {"LOADER_Q_UNIT_TYPE": DEFAULT_Q_CATEGORY},
        }
        self.data_unit_selectors = {
            self.cbLoadIUnitSelector: {
                "LOADER_I_UNIT_ON_LOAD": {
                    DEFAULT_I_CATEGORY: DEFAULT_I_UNIT,
                    "(Absolute Units)^2": DEFAULT_I_ABS2_UNIT,
                    "SESANS": DEFAULT_I_SESANS_UNIT,
                    "Arbitrary": DEFAULT_I_ARBITRARY_UNIT
                }
            },
            self.cbLoadQUnitSelector: {
                "LOADER_Q_UNIT_ON_LOAD": {DEFAULT_Q_CATEGORY: DEFAULT_Q_UNIT, "Length": DEFAULT_Q_LENGTH_UNIT}
            }
        }
        self.setupDataLoaderWidget()
        self.checkBoxLoadQOverride.toggled.connect(self.override_file_units)
        self.checkBoxLoadIOverride.toggled.connect(self.override_file_units)
        self.restoreDefaultMethods.append(self.restoreDataLoaderPrefs)
        ######################################################

    def prefMenuChanged(self):
        """When the preferences menu selection changes, change to the appropriate preferences widget """
        row = self.listWidget.currentRow()
        self.stackedWidget.setCurrentIndex(row)

    def onClick(self, btn):
        # type: (QPushButton) -> None
        """Handle button click events in one area"""
        # Reset to the default preferences
        if btn.text() == 'Restore Defaults':
            self.restoreDefaultPrefs()
        elif btn.text() == 'OK':
            self.close()
        elif btn.text() == 'Help':
            self.help()

    def restoreDefaultPrefs(self):
        """Reset all preferences to their default preferences"""
        for method in self.restoreDefaultMethods:
            if callable(method):
                method()
            else:
                logger.warning(f'While restoring defaults, {str(method)} of type {type(method)}'
                               + ' was given. A method or other callable object was expected.')

    def close(self):
        """Save the configuration values when the preferences window is closed"""
        if hasattr(self.parent, 'guiManager'):
            self.parent.guiManager.writeCustomConfig(get_custom_config())
        super(PreferencesPanel, self).close()

    def help(self):
        """Open the help window associated with the preferences window"""
        # TODO: Write the help file and then link to it here
        pass

    ###################################################
    # Plotting options Widget initialization and callbacks
    def setupPlottingWidget(self):
        """Populate plotting preferences widget, set default state, and add triggers"""
        for index, value in self.plotting_unit_constants.items():
            config_locale = list(value.keys())[0]
            default = value.get(config_locale)
            i_unit = get_config_value(config_locale, default)
            i_units = Converter(i_unit).get_compatible_units()
            cb_replace_all_items_with_new(index, i_units, i_unit)
            index.setDisabled(True)
            index.currentIndexChanged.connect(self.set_plotting_values)
            set_config_value(config_locale, i_unit)

    def set_plotting_values(self):
        """Update the custom config whenever a value is changed to ensure the values propagate through SasView"""
        for cBox, defaults in self.plotting_unit_constants.items():
            config_locale = list(defaults.keys())[0]
            unit = cBox.currentText()
            set_config_value(config_locale, unit)

    def toggle_scaling_on_plot(self):
        """Toggle the plot scaling whenever either of the checkboxes is clicked"""
        sender = self.sender()
        toggle = sender.isChecked()
        if sender == self.checkBoxPlotQAsLoaded:
            toggle_enabled_list = list(self.plotting_unit_constants.keys())[4:]
            config_locale = "PLOTTER_PLOT_Q_AS_LOADED"
        elif sender == self.checkBoxPlotIAsLoaded:
            toggle_enabled_list = list(self.plotting_unit_constants.keys())[:4]
            config_locale = "PLOTTER_PLOT_I_AS_LOADED"
        else:
            return
        for combo_box in toggle_enabled_list:
            combo_box.setDisabled(toggle)
        set_config_value(config_locale, toggle)

    def restorePlottingPrefs(self):
        """Restore the default plotting preferences"""
        self.cbPlotIAbs.setCurrentIndex(self.cbPlotIAbs.findText(DEFAULT_I_UNIT))
        self.cbPlotIAbsSquared.setCurrentIndex(self.cbPlotIAbsSquared.findText(DEFAULT_I_ABS2_UNIT))
        self.cbPlotISesans.setCurrentIndex(self.cbPlotISesans.findText(DEFAULT_I_SESANS_UNIT))
        self.cbPlotIArbitrary.setCurrentIndex(self.cbPlotIArbitrary.findText(DEFAULT_I_ARBITRARY_UNIT))
        self.cbPlotQLength.setCurrentIndex(self.cbPlotQLength.findText(DEFAULT_Q_LENGTH_UNIT))
        self.cbPlotQInvLength.setCurrentIndex(self.cbPlotQInvLength.findText(DEFAULT_Q_UNIT))
        self.checkBoxLoadIOverride.setChecked(False)
        self.checkBoxLoadQOverride.setChecked(False)
    ###################################################

    ###################################################
    # Data Loading options Widget initialization and callbacks
    def setupDataLoaderWidget(self):
        """Populate data loading preferences widget, set default state, and add triggers"""
        for index, value in self.data_type_selectors.items():
            config_locale = list(value.keys())[0]
            default = value.get(config_locale)
            selection = get_config_value(config_locale, default)
            index.setCurrentIndex(index.findText(selection))
            index.currentIndexChanged.connect(self.set_loading_type_value)
        for index, value in self.data_unit_selectors.items():
            config_locale = list(value.keys())[0]
            default_map = list(value.values())[0]
            selection = (self.cbLoadIUnitType.currentText() if self.cbLoadIUnitType.currentText() in default_map.keys()
                         else self.cbLoadQUnitType.currentText())
            default = default_map.get(selection)
            unit = get_config_value(config_locale, default)
            cb_replace_all_items_with_new(index, Converter(unit).get_compatible_units(), unit)
            index.currentIndexChanged.connect(self.set_loading_unit_value)
            set_config_value(config_locale, unit)

    def set_loading_type_value(self):
        """Update the custom config whenever a value is changed to ensure the values propagate through SasView"""
        sender = self.sender()
        if sender == self.cbLoadQUnitType:
            new_type = self.cbLoadQUnitType.currentText()
            input = self.cbLoadQUnitSelector
        elif sender == self.cbLoadIUnitType:
            new_type = self.cbLoadIUnitType.currentText()
            input = self.cbLoadIUnitSelector
        else:
            return
        config_locale = list(self.data_type_selectors[sender].keys())[0]
        types = list(self.data_unit_selectors[input].values())[0]
        default_unit = types.get(new_type)
        cb_replace_all_items_with_new(input, Converter(default_unit).get_compatible_units(), default_unit)
        set_config_value(config_locale, default_unit)

    def set_loading_unit_value(self):
        """Define the assumed units of the data on loading"""
        sender = self.sender()
        if sender == self.cbLoadQUnitSelector:
            new_unit = self.cbLoadQUnitSelector.currentText()
        elif sender == self.cbLoadIUnitSelector:
            new_unit = self.cbLoadIUnitSelector.currentText()
        else:
            return
        config_locale = list(self.data_unit_selectors[sender].keys())[0]
        set_config_value(config_locale, new_unit)

    def override_file_units(self):
        """Allow the user to override any units found in the data file, but warn the user before allowing this"""
        sender = self.sender()
        if sender == self.checkBoxLoadQOverride:
            # Q checkbox toggled
            config_locale = "LOAD_Q_OVERRIDE"
            axis = "Q"
            unit = self.cbLoadQUnitSelector.currentText()
        else:
            # I checkbox toggled
            config_locale = "LOAD_I_OVERRIDE"
            axis = "Intensity"
            unit = self.cbLoadIUnitSelector.currentText()
        if sender.isChecked():
            # Warn the user if checking the checkbox
            message = f"By selecting to override {axis} units, the data loader system will ignore any units found in "
            message += f"**all** data files and, instead, will assume the units are {unit}. No data scaling will occur."
            message += "\r\tE.g. you selected 'm^{-1}' as your Intensity unit is but the dataset is '[0.1, 0.2, 0.3] "
            message += "cm^{-1}', the as-loaded data will be treated as '[0.1, 0.2, 0.3] m^{-1}'."
            message += "\r\r**Are you certain you want to do this?**"

            self.warning = QMessageBox(QMessageBox.Warning, "", message, QMessageBox.Yes | QMessageBox.No, self)
            button = self.warning.exec()
            # Uncheck the checkbox if rejected
            if button == QMessageBox.No:
                sender.setChecked(False)
        set_config_value(config_locale, sender.isChecked())

    def restoreDataLoaderPrefs(self):
        """Restore the default data loading preferences"""
        self.cbLoadIUnitType.setCurrentIndex(self.cbLoadIUnitType.findText(DEFAULT_I_CATEGORY))
        self.cbLoadQUnitType.setCurrentIndex(self.cbLoadQUnitType.findText(DEFAULT_Q_CATEGORY))
        self.cbLoadIUnitSelector.setCurrentIndex(self.cbLoadIUnitSelector.findText(DEFAULT_I_UNIT))
        self.cbLoadQUnitSelector.setCurrentIndex(self.cbLoadQUnitSelector.findText(DEFAULT_Q_UNIT))
        self.checkBoxPlotQAsLoaded.setChecked(True)
        self.checkBoxPlotIAsLoaded.setChecked(True)
    ###################################################
