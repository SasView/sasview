from PyQt5 import QtWidgets

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


def cb_replace_all_items_with_new(cb, new_items, default_item=None):
    # type: (QtWidgets.QComboBox, [], str) -> None
    """Helper method that removes any existing ComboBox values, replaces them and sets a default item, if defined"""
    cb.clear()
    cb.addItems(new_items)
    if default_item:
        cb.setCurrentIndex(cb.findText(default_item))


class PreferencesPanel(QtWidgets.QDialog, Ui_preferencesUI):
    """A preferences panel to house all SasView related settings. The left side of the window is a listWidget with a
    list of the options menus available. The right side of the window is a stackedWidget object that houses the options
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
        # Set defaults
        self.stackedWidget.setCurrentIndex(0)
        self.listWidget.setCurrentRow(0)
        # Add window actions
        self.listWidget.currentItemChanged.connect(self.prefMenuChanged)
        # Setup each widget separately
        self.setupPlottingWidget()
        self.setupDataLoaderWidget()

    def prefMenuChanged(self):
        """When the preferences menu selection changes, change to the appropriate preferences widget """
        row = self.listWidget.currentRow()
        self.stackedWidget.setCurrentIndex(row)

    ###################################################
    # Plotting options Widget initialization and callbacks

    def setupPlottingWidget(self):
        custom_config = get_custom_config()
        # Map defaults to each combo box
        self.unit_constants = {
            self.cbPlotIAbs: {"PLOTTER_I_ABS_UNIT": DEFAULT_I_UNIT},
            self.cbPlotIAbsSquared: {"PLOTTER_I_ABS_SQUARE_UNIT": DEFAULT_I_ABS2_UNIT},
            self.cbPlotISesans: {"PLOTTER_I_SESANS": DEFAULT_I_SESANS_UNIT},
            self.cbPlotIArbitrary: {"PLOTTER_I_ARB": DEFAULT_I_ARBITRARY_UNIT},
            self.cbPlotQLength: {"PLOTTER_Q_LENGTH": DEFAULT_Q_LENGTH_UNIT},
            self.cbPlotQInvLength: {"PLOTTER_Q_INV_LENGTH": DEFAULT_Q_UNIT}
        }
        # Populate combo boxes and add triggers to
        for index, value in self.unit_constants.items():
            config_locale = list(value.keys())[0]
            default = value.get(config_locale)
            i_unit = custom_config.get(config_locale, default) if hasattr(custom_config, config_locale) else default
            i_units = Converter(i_unit).get_compatible_units()
            cb_replace_all_items_with_new(index, i_units, i_unit)
            index.currentIndexChanged.connect(self.set_plotting_values)
            setattr(custom_config, config_locale, i_unit)

    def set_plotting_values(self):
        """Update the custom config whenever a value is changed to ensure the values propagate through SasView"""
        for input, map in self.unit_constants.items():
            custom_config = get_custom_config()
            config_locale = list(map.keys())[0]
            unit = input.currentText()
            setattr(custom_config, config_locale, unit)

    ###################################################
    # Data Loading options Widget initialization and callbacks

    def setupDataLoaderWidget(self):
        custom_config = get_custom_config()
        self.type_selectors = {
            self.cbLoadIUnitType: {"LOADER_I_UNIT_TYPE": DEFAULT_I_CATEGORY},
            self.cbLoadQUnitType: {"LOADER_Q_UNIT_TYPE": DEFAULT_Q_CATEGORY},
        }
        self.unit_selectors = {
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
        for index, value in self.type_selectors.items():
            config_locale = list(value.keys())[0]
            default = value.get(config_locale)
            selection = custom_config.get(config_locale, default) if hasattr(custom_config, config_locale) else default
            index.setCurrentIndex(index.findText(selection))
            index.currentIndexChanged.connect(self.set_loading_type_value)
        for index, value in self.unit_selectors.items():
            config_locale = list(value.keys())[0]
            default_map = list(value.values())[0]
            selection = (self.cbLoadIUnitType.currentText() if self.cbLoadIUnitType.currentText() in default_map.keys()
                         else self.cbLoadQUnitType.currentText())
            default = default_map.get(selection)
            unit = custom_config.get(config_locale, default) if hasattr(custom_config, config_locale) else default
            cb_replace_all_items_with_new(index, Converter(unit).get_compatible_units(), unit)
            index.currentIndexChanged.connect(self.set_loading_unit_value)
            setattr(custom_config, config_locale, unit)

    def set_loading_type_value(self):
        """Update the custom config whenever a value is changed to ensure the values propagate through SasView"""
        sender = self.sender()
        custom_config = get_custom_config()
        if sender == self.cbLoadQUnitType:
            new_type = self.cbLoadQUnitType.currentText()
            input = self.cbLoadQUnitSelector
        elif sender == self.cbLoadIUnitType:
            new_type = self.cbLoadIUnitType.currentText()
            input = self.cbLoadIUnitSelector
        else:
            return
        config_locale = list(self.type_selectors[sender].keys())[0]
        types = list(self.unit_selectors[input].values())[0]
        default_unit = types.get(new_type)
        cb_replace_all_items_with_new(input, Converter(default_unit).get_compatible_units(), default_unit)
        setattr(custom_config, config_locale, default_unit)

    def set_loading_unit_value(self):
        sender = self.sender()
        custom_config = get_custom_config()
        if sender == self.cbLoadQUnitSelector:
            new_unit = self.cbLoadQUnitSelector.currentText()
        elif sender == self.cbLoadIUnitSelector:
            new_unit = self.cbLoadIUnitSelector.currentText()
        else:
            return
        config_locale = list(self.unit_selectors[sender].keys())[0]
        setattr(custom_config, config_locale, new_unit)
