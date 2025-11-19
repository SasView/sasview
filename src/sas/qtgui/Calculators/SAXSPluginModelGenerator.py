from pathlib import Path

from sas.system.user import find_plugins_dir

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

This plugin model uses the AUSAXS library (doi: https://doi.org/10.1107/S160057672500562X) to fit the provided SAXS data to the file:
 * \"{structure_path}\"
If this is not the intended structure file, please regenerate the plugin model from the generic scattering calculator.
"""
'''

f'''\
name = "SAXS fitting"
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

structure_path = "{structure_path}"
mol = ausaxs.create_molecule(structure_path)
mol.hydrate()
fit = ausaxs.manual_fit(mol)

def Iq(q, c):
    return fit.evaluate([c], q)
Iq.vectorized = True
''')