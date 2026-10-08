import io

import pytest
from PySide6.QtWidgets import QDialogButtonBox, QWidget

from sas.qtgui.Utilities.Preferences.GeneralPreferencesWidget import GeneralPreferencesWidget
from sas.qtgui.Utilities.Preferences.PreferencesPanel import PreferencesPanel
from sas.system import config

KEYS = ['OPEN_PLOTS_DETACHED', 'OPEN_PERSPECTIVE_DETACHED']


class GeneralPreferencesWidgetTest:
    @pytest.fixture(autouse=True)
    def saved_config(self):
        """Restore the global configuration after each test"""
        saved = {key: getattr(config, key) for key in KEYS}
        for key in KEYS:
            setattr(config, key, False)
        yield
        for key, value in saved.items():
            setattr(config, key, value)

    @pytest.fixture
    def panel(self, qapp):
        parent = QWidget()
        panel = PreferencesPanel(parent)
        panel.setMenuByName("General Settings")
        yield panel
        panel.close()

    @staticmethod
    def general(panel) -> GeneralPreferencesWidget:
        widget = panel.stackedWidget.currentWidget()
        assert isinstance(widget, GeneralPreferencesWidget)
        return widget

    def testDefaults(self):
        for key in KEYS:
            assert config.defaults.get(key) is False

    def testGeneralSettingsIsFirstPanel(self, panel):
        assert panel.listWidget.item(0).text() == "General Settings"

    @pytest.mark.parametrize("key, checkbox", [
        ('OPEN_PLOTS_DETACHED', 'plotsDetached'),
        ('OPEN_PERSPECTIVE_DETACHED', 'perspectiveDetached'),
    ])
    def testApplyAndCancel(self, panel, key, checkbox):
        widget = self.general(panel)
        box = getattr(widget, checkbox)
        assert not box.isChecked()

        # Staged but not applied
        box.click()
        assert box.isChecked()
        assert panel._staged_changes == {key: True}
        assert getattr(config, key) is False

        # Cancel throws the change away and restores the check box
        panel.buttonBox.button(QDialogButtonBox.Cancel).click()
        assert getattr(config, key) is False
        assert not box.isChecked()

        # Apply writes the configuration
        box.click()
        panel.buttonBox.button(QDialogButtonBox.Apply).click()
        assert getattr(config, key) is True

        # Restore Defaults puts it back
        panel.restoreDefaultPreferences()
        assert getattr(config, key) is False
        assert not box.isChecked()

    def testRestoreFromConfig(self, panel):
        widget = self.general(panel)
        config.OPEN_PLOTS_DETACHED = True
        config.OPEN_PERSPECTIVE_DETACHED = True
        widget.restoreGUIValuesFromConfig()
        assert widget.plotsDetached.isChecked()
        assert widget.perspectiveDetached.isChecked()

    def testSaveAndReloadConfig(self, monkeypatch):
        """Both settings are written to the config file and read back"""
        # Tests normally disable writing; the file here is in memory
        monkeypatch.setattr(config, "_disable_writing", False)
        for key in KEYS:
            setattr(config, key, True)
        saved = io.StringIO()
        config.save_to_file_object(saved)
        for key in KEYS:
            assert f'"{key}": true' in saved.getvalue()
            setattr(config, key, False)

        saved.seek(0)
        config.load_from_file_object(saved)
        for key in KEYS:
            assert getattr(config, key) is True
