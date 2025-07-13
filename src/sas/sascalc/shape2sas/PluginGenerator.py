import textwrap
from pathlib import Path
import logging

#Global SasView
#Local Perspectives
from sas.sascalc.fit import models
from sas.sascalc.shape2sas.Shape2SAS import ModelProfile
from sas.system.user import find_plugins_dir

def generate_plugin(prof: ModelProfile, constrainParameters: (str), fitPar: list[str],
                   Npoints: int, pr_points: int, file_name: str) -> tuple[str, Path]:
    """Generates a theoretical scattering plugin model"""

    plugin_location = Path(models.find_plugins_dir())
    full_path = plugin_location.joinpath(file_name).with_suffix('.py')
    logging.info(f"Plugin model will be saved to: {full_path}")

    model_str = generate_model(prof, constrainParameters, fitPar, Npoints, pr_points, file_name)

    return model_str, full_path


def format_parameter_list(par: list[list[str | float]]) -> str:
    """
    Format a list of parameters to the model string. In this case the list
    is on element for each shape. For a single shape there will be only
    a single value. Mainly for delta Rho.
    """
    return f"[{', '.join(str(x) for x in par)}]"


def format_parameter_list_of_list(par: list[str | float]) -> str:
    """
    Format a list of list containing parameters to the model string. This
    is used for single shape parameter lists like the center of mass of the
    object which will be an element of the list of such COM for each shape
    in a multishape model.
    """
    sub_pars_join =[", ".join(map(str,sub_par)) for sub_par in par]
    return f"[[{'],['.join(sub_pars_join)}]]"


def generate_model(prof: ModelProfile, constrainParameters: (str), fitPar: list[str],
                  Npoints: int, pr_points: int, model_name: str) -> str:
    """Generates a theoretical model"""
    importStatement, parameters, translation = constrainParameters

    nl = '\n'

    fitPar.insert(0, "q")

    model_str = (
# file header
f'''\
r"""
This plugin model uses Shape2SAS to generate theoretical 1D small-angle scattering.
Shape2SAS is a program built by Larsen and Brookes
(doi: https://doi.org/10.1107/S1600576723005848) that uses the Debye equation to
calculate small-angle scattering on identical particles that have been rotationally
averaged. This is done on a user-designed particle model, which is built from a
combination of pre-defined geometrical subunits. Each subunit may be rotated and
translated to the users desired position, resulting in a broad range of possible
models to be created. Besides calculating theoretical scattering, Shape2SAS is also
able to simulate small-angle scattering with noise and return a pair distance
distribution.

Model {model_name.replace('.py', '')} has been built from the following subunits:
{', '.join(prof.subunits)}

"""
'''

# imports
f'''\
{nl.join(importStatement)}
from sas.sascalc.shape2sas.Shape2SAS import (
    ModelProfile, SimulationParameters, ModelSystem, getPointDistribution, 
    TheoreticalScatteringCalculation, getTheoreticalScattering
)
'''

# model description
f'''\
name = "{model_name.replace('.py', '')}"'
title = "Shape2SAS Model"
description = "Theoretical generation of P(q) using Shape2SAS"
category = "plugin"
'''

# parameter list
f"{parameters}\n"

# define Iq
f'''\
def Iq({', '.join(fitPar)}):
    """Fit function using Shape2SAS to calculate the scattering intensity."""
    {nl.join(translation)}

    modelProfile = ModelProfile(
        subunits={prof.subunits}, 
        p_s={format_parameter_list(prof.p_s)}, 
        dimensions={format_parameter_list_of_list(prof.dimensions)}, 
        com={format_parameter_list_of_list(prof.com)}, 
        rotation_points={format_parameter_list_of_list(prof.rotation_points)}, 
        rotation={format_parameter_list_of_list(prof.rotation)}, 
        exclude_overlap={prof.exclude_overlap}
    )

    simPar = SimulationParameters(q=q, prpoints={pr_points}, Npoints={Npoints}, model_name="{model_name.replace('.py', '')}")
    dist = getPointDistribution(modelProfile, {Npoints})

    scattering = TheoreticalScatteringCalculation(
        System=ModelSystem(
            PointDistribution=dist, 
            Stype="None", par=[], 
            polydispersity=0.0, conc=1, 
            sigma_r=0.0
        ), 
        Calculation=simPar
    )
    theoreticalScattering = getTheoreticalScattering(scattering)

    return theoreticalScattering.I

Iq.vectorized = True

''')
    
    return model_str