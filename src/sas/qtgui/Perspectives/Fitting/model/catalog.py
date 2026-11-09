"""
ModelCatalog (FW-MVC-DESIGN.md §3.2, Phase 7): the models a fit page can select. Qt-free.

Application-wide: the perspective owns one and passes it to its pages (a page without a
perspective makes its own). It holds

- ``categories``: {category: [[model, enabled], ...]} from the categories file
  (``CategoryInstaller``), without the models sasmodels no longer has, plus the plugin
  models (``CATEGORY_CUSTOM``; plugin structure factors also under ``CATEGORY_STRUCTURE``);
- ``models``: {name: model class}, the standard models and the plugins. ``KernelBuilder``
  holds this dict, so a refresh updates it in place.

``refresh()`` re-reads the categories file (``updateModelCategoriesSignal``) and
``reload_plugins()`` the plugin directory (``customModelDirectoryChanged``).
"""
from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable

from sasmodels.sasview_model import MODELS, load_standard_models

from sas.qtgui.Perspectives.Fitting.FittingConstants import CATEGORY_CUSTOM, CATEGORY_STRUCTURE, SUPPRESSED_MODELS
from sas.qtgui.Utilities.CategoryInstaller import CategoryInstaller

logger = logging.getLogger(__name__)


class ModelCatalog:

    def __init__(self, plugin_models: Callable[[], dict]) -> None:
        self._plugin_models = plugin_models
        self.models: dict = {model.name: model for model in load_standard_models()}
        self.plugins: dict = {}
        self.categories: dict[str, list] = {}
        self.refresh()

    def refresh(self) -> None:
        """Re-read the categories file and the plugin directory."""
        categorization_file = CategoryInstaller.get_user_file()
        if not os.path.isfile(categorization_file):
            categorization_file = CategoryInstaller.get_default_file()
        with open(categorization_file, 'rb') as cat_file:
            self.categories = json.load(cat_file)
        self.regenerate()
        self.reload_plugins()

    def regenerate(self) -> None:
        """Drop the categorised models that sasmodels no longer has."""
        for category, entries in self.categories.items():
            for model, enabled in list(entries):
                if model not in MODELS:
                    logger.warning(f"The model {model} is no longer available in sasmodels. It will be ignored.")
                    entries.remove([model, enabled])

    def reload_plugins(self) -> None:
        """Re-read the plugin models."""
        for name in self.plugins:
            self.models.pop(name, None)
        self.plugins = dict(self._plugin_models())
        self.models.update(self.plugins)
        if self.plugins:
            self.categories[CATEGORY_CUSTOM] = [[name, True] for name in self.plugins]
        if CATEGORY_STRUCTURE in self.categories:
            structures = self.categories[CATEGORY_STRUCTURE]
            structures.extend([name, True] for name, plugin in self.plugins.items()
                              if plugin.is_structure_factor and [name, True] not in structures)

    def category_names(self) -> list[str]:
        """The categories the category combo box lists, in order (structure factors last)."""
        return sorted(c for c in self.categories if c != CATEGORY_STRUCTURE) + [CATEGORY_STRUCTURE]

    def models_in(self, category: str) -> list[str]:
        """The enabled models of *category*, sorted (the model combo box)."""
        return sorted(m for m, enabled in self.categories.get(category, []) if enabled and m not in SUPPRESSED_MODELS)

    def structure_factors(self) -> list[str]:
        """The structure factors that can be loaded (the categories file may list missing ones)."""
        return sorted(m for m, _ in self.categories.get(CATEGORY_STRUCTURE, []) if m in self.models)
