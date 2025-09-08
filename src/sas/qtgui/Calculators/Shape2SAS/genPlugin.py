#Global
import textwrap
from pathlib import Path

#Global SasView
from sas.sascalc.fit import models

#Local Perspectives
from sas.sascalc.shape2sas.Shape2SAS import ModelProfile


def generatePlugin(prof: ModelProfile, constrainParameters: (str), fitPar: [str],
                   Npoints: int, pr_points: int, file_name: str) -> (str, Path):
    """Generates a theoretical scattering plugin model"""

    plugin_location = Path(models.find_plugins_dir())
    full_path = plugin_location / file_name
    full_path = full_path.with_suffix('.py')

    model_str = generateModel(prof, constrainParameters, fitPar, Npoints, pr_points, file_name)

    return model_str, full_path


def parListFormat(par: [[str | float]]) -> str:
    """
    Format a list of parameters to the model string. In this case the list
    is on element for each shape. For a single shape there will be only
    a single value. Mainly for delta Rho.
    """
    return f"[{', '.join(str(x) for x in par)}]"


def parListsFormat(par: [str | float]) -> str:
    """
    Format a list of list containing parameters to the model string. This
    is used for single shape parameter lists like the center of mass of the
    object which will be an element of the list of such COM for each shape
    in a multishape model.
    """
    sub_pars_join =[", ".join(map(str,sub_par)) for sub_par in par]
    return f"[[{'],['.join(sub_pars_join)}]]"


def generateModel(prof: ModelProfile, constrainParameters: (str), fitPar: [str],
                  Npoints: int, pr_points: int, model_name: str) -> str:
    """Generates a theoretical model"""
    importStatement, parameters, translation = constrainParameters

    nl = '\n'

    fitPar.insert(0, "q")

    model_str = (f'''
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

{nl.join(importStatement)}
from sas.sascalc.shape2sas.Shape2SAS import (ModelProfile, SimulationParameters,
                                                        ModelSystem, getPointDistribution,
                                                        TheoreticalScatteringCalculation,
                                                        getTheoreticalScattering)

name = "{model_name.replace('.py', '')}"
title = "Shape2SAS Model"
description = """
Theoretical generation of P(q) using Shape2SAS
"""
category = "plugin"

{parameters}

def Iq({', '.join(fitPar)}):
    """Fit function using Shape2SAS to calculate the scattering intensity."""

{textwrap.indent(translation, '    ')}

    modelProfile = ModelProfile(subunits={prof.subunits},
                                    p_s={parListFormat(prof.p_s)},
                                    dimensions={parListsFormat(prof.dimensions)},
                                    com={parListsFormat(prof.com)},
                                    rotation_points={parListsFormat(prof.rotation_points)},
                                    rotation={parListsFormat(prof.rotation)},
                                    exclude_overlap={prof.exclude_overlap})

    simPar = SimulationParameters(q=q, prpoints={pr_points}, Npoints={Npoints}, model_name="{model_name.replace('.py', '')}")
    dist = getPointDistribution(modelProfile, {Npoints})

    scattering = TheoreticalScatteringCalculation(System=ModelSystem(PointDistribution=dist,
                                                                        Stype="None", par=[],
                                                                        polydispersity=0.0, conc=1,
                                                                        sigma_r=0.0),
                                                                        Calculation=simPar)
    theoreticalScattering = getTheoreticalScattering(scattering)

    return theoreticalScattering.I

Iq.vectorized = True

''').lstrip().rstrip()

    return model_str


