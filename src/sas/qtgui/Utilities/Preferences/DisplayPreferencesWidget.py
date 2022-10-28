from sas.system import config

from .PreferencesWidget import PreferencesWidget, config_value_setter_generator


class DisplayPreferencesWidget(PreferencesWidget):
    def __init__(self):
        super(DisplayPreferencesWidget, self).__init__("Display Settings")

    def _addAllWidgets(self):
        self.addTextInput(title="QT Screen Scale Factor",
                         callback=config_value_setter_generator('QT_SCALE_FACTOR', dtype=float),
                         default_text=str(config.QT_SCALE_FACTOR))
        self.addCheckBox(title="Automatic Screen Scale Factor",
                         callback=config_value_setter_generator('QT_AUTO_SCREEN_SCALE_FACTOR', dtype=bool),
                         checked=config.QT_AUTO_SCREEN_SCALE_FACTOR)
