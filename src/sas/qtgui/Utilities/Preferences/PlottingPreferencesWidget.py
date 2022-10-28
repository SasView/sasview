from sas.system import config

from .PreferencesWidget import PreferencesWidget, config_value_setter_generator


class PlottingPreferencesWidget(PreferencesWidget):
    def __init__(self):
        super(PlottingPreferencesWidget, self).__init__("Plotting Settings")
        self.addCheckBox(title="Use full-width plot legends (most compatible)?",
                         callback=config_value_setter_generator('FITTING_PLOT_FULL_WIDTH_LEGENDS', dtype=bool),
                         checked=config.FITTING_PLOT_FULL_WIDTH_LEGENDS)
        self.addCheckBox(title="Use truncated legend entries?",
                         callback=config_value_setter_generator('FITTING_PLOT_LEGEND_TRUNCATE', dtype=bool),
                         checked=config.FITTING_PLOT_LEGEND_TRUNCATE)
        self.addTextInput(title="Legend entry line length",
                          callback=config_value_setter_generator('FITTING_PLOT_LEGEND_MAX_LINE_LENGTH', dtype=int),
                          default_text=str(config.FITTING_PLOT_LEGEND_MAX_LINE_LENGTH))