"""
Constants shared by the fitting page and its tab widgets.

This module is Qt-free and must stay that way: it is imported by the
Qt-free ``model`` package.
"""

# Tab indices in FittingWidget.tabFitting
TAB_POLY = 3
TAB_MAGNETISM = 4
TAB_ORDERING = 5

# Combo box placeholders and fixed entries
CATEGORY_DEFAULT = "Choose category..."
MODEL_DEFAULT = "Choose model..."
CATEGORY_STRUCTURE = "Structure Factor"
CATEGORY_CUSTOM = "Plugin Models"
STRUCTURE_DEFAULT = "None"

DEFAULT_POLYDISP_FUNCTION = 'gaussian'

# A list of models that are known to not work with how the GUI handles models from sasmodels
#   NOTE: These models are correct when used directly through the sasmodels package, but how qtgui handles them is wrong
SUPPRESSED_MODELS = ['rpa']

# Layered models that have integer parameters are often treated differently. Maintain a list of these models.
LAYERED_MODELS = ['unified_power_Rg', 'core_multi_shell', 'onion', 'spherical_sld']

# Historic list of models with magnetic parameters. This is NOT the capability rule:
# whether a page can have magnetism is decided from the model's own parameter metadata
# (FittingWidget.canHaveMagnetism). Nothing reads this list for decisions.
MAGNETIC_MODELS = ['sphere', 'core_shell_sphere', 'core_multi_shell', 'cylinder', 'parallelepiped']

polydispersity_plot_name = "{} {} polydispersity {}"
