from sas.system import config

from .PreferencesWidget import PreferencesWidget, config_value_setter_generator


class FittingPreferencesWidget(PreferencesWidget):
    def __init__(self):
        super(FittingPreferencesWidget, self).__init__("Fitting Settings")
        self.addCheckBox(title="Auto-plot data when sent to fitting perspective",
                         callback=config_value_setter_generator('FITTING_PLOT_ON_SEND_DATA', dtype=bool),
                         checked=config.FITTING_PLOT_ON_SEND_DATA)