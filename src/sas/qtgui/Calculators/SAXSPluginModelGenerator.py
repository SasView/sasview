from pathlib import Path

from sas.system.user import find_plugins_dir


def get_base_plugin_name() -> str:
    """
    Get the base name for the AUSAXS SAXS plugin model.

    :return: The base name of the plugin model.
    """

    return "SAXS fit"

def write_plugin_model(structure_path: str):
    """
    Write the AUSAXS SAXS plugin model to the plugins directory.
    The current version will be overwritten if it exists.

    :param structure_path: Path to the structure file to be used by the plugin.
    """

    path = Path(find_plugins_dir()) / "ausaxs_saxs_plugin.py"
    text = get_model_text(structure_path)
    with open(path, 'w') as f:
        f.write(text)

def get_model_text(structure_path: str) -> str:
    """
    Generate the text of the AUSAXS SAXS plugin model.

    :param structure_path: Path to the structure file to be used by the plugin.
    :return: The text of the plugin model.
    """

    return (
f'''\
r"""
This file is auto-generated, and any changes will be overwritten. 

This plugin model uses the AUSAXS library (https://doi.org/10.1107/S160057672500562X) to fit the provided SAXS data to the file:
 * \"{structure_path}\"
If this is not the intended structure file, please regenerate the plugin model from the generic scattering calculator.
"""
'''

f'''\
name = "{get_base_plugin_name()} ({Path(structure_path).name.split('.')[0]})"
title = "AUSAXS"
description = "Structural validation using AUSAXS"
category = "plugin"
parameters = [
    # name, units, default, [min, max], type, description
    ['c', '', 1, [0, 100], '', 'Solvent density'],
    #['d', '', 1, [0, 2], '', 'Excluded volume parameter']
]

###
import pyausaxs as ausaxs
ausaxs.settings.set(\"allow_unknown_atoms\", \"false\")
ausaxs.settings.set(\"allow_unknown_residues\", \"false\")

structure_path = "{str(Path(structure_path).as_posix())}"

def Iq(q, c):
    # Initialize on first call to keep objects alive for function lifetime
    if not hasattr(Iq, '_initialized'):
        Iq._mol = ausaxs.create_molecule(structure_path)
        Iq._mol.hydrate()
        Iq._fitobj = ausaxs.manual_fit(Iq._mol)
        Iq._initialized = True
    return Iq._fitobj.evaluate([c], q)
Iq.vectorized = True
''')
