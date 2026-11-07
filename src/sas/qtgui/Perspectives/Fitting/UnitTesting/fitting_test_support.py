"""
Shared test doubles for the Fitting perspective tests.

``FittingWidgetMod`` is a ``FittingWidget`` whose plugin models come from the
repository's ``Fitting/plugin_models`` directory instead of the user's plugin
directory, so tests do not depend on the machine they run on.
"""
import glob
import os

from sasmodels.sasview_model import load_custom_model

from sas.qtgui.Perspectives.Fitting import FittingWidget
from sas.qtgui.Perspectives.Fitting.FittingPerspective import FittingWindow
from sas.qtgui.Perspectives.Fitting.UnitTesting.shadow_invariant import ShadowChecker
from sas.qtgui.Utilities import GuiUtils
from sas.sascalc.fit.models import ModelManager, ModelManagerBase


class dummy_manager:
    HELP_DIRECTORY_LOCATION = "html"
    communicator = GuiUtils.communicator

    def __init__(self):
        self._perspective = dummy_perspective()

    def perspective(self):
        return self._perspective


class dummy_perspective:
    # The real lookups, over the pages a test adds to fit_tabs
    getTabByMnemonic = FittingWindow.getTabByMnemonic
    updateFromConstraints = FittingWindow.updateFromConstraints

    def __init__(self):
        self.symbol_dict = {}
        self.constraint_list = []
        self.constraint_tab = None
        self.fit_tabs = []

    def getFitTabs(self):
        return self.fit_tabs

    def getActiveConstraintList(self):
        return self.constraint_list

    def getSymbolDictForConstraints(self):
        return self.symbol_dict

    def getConstraintTab(self):
        return self.constraint_tab


def find_plugin_models_mod():
    """
    Modification to sas.sascalc.fit.models.find_plugin_models().
    Instead of searching for user's plugin directory, the path is set at:
    'sas/qtgui/Perspectives/Fitting/plugin_models'
    """
    plugins_dir = [
        os.path.abspath(path) for path in glob.glob("**/plugin_models", recursive=True)
        if os.path.normpath("qtgui/Perspectives/Fitting/plugin_models") in os.path.abspath(path)
    ][0]

    plugins = {}
    for filename in os.listdir(plugins_dir):
        name, ext = os.path.splitext(filename)
        if ext == '.py' and not name == '__init__':
            path = os.path.abspath(os.path.join(plugins_dir, filename))
            model = load_custom_model(path)
            plugins[model.name] = model

    return plugins


class ModelManagerBaseMod(ModelManagerBase):
    """ModelManagerBase that reads plugins from the repository's plugin_models directory."""

    def _is_plugin_dir_changed(self):
        """The test plugin directory never changes."""
        return False

    def plugins_reset(self):
        """Return the model list, with plugins from find_plugin_models_mod()."""
        self.plugin_models = find_plugin_models_mod()
        self.model_dictionary.clear()
        self.model_dictionary.update(self.standard_models)
        self.model_dictionary.update(self.plugin_models)
        return self.get_model_list()


class ModelManagerMod(ModelManager):
    """ModelManager backed by ModelManagerBaseMod."""
    base = None

    def __init__(self):
        if ModelManagerMod.base is None:
            ModelManagerMod.base = ModelManagerBaseMod()


class FittingWidgetMod(FittingWidget.FittingWidget):
    """FittingWidget that takes its plugin models from the test plugin directory.

    It also checks the Phase 2 shadow invariant after every document commit;
    fixtures call ``shadow_checker.assert_ok()`` at teardown.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shadow_checker = ShadowChecker(self)

    def customModels(cls):
        manager = ModelManagerMod()
        manager.update()
        return manager.base.plugin_models
