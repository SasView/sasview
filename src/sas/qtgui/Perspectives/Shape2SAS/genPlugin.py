#Global
from pathlib import Path
from typing import Union

#Global SasView
from sas.sascalc.fit import models

#Local Perspectives
from calculations.Shape2SAS import ModelProfile



def generatePlugin(prof: ModelProfile, constrainParameters: tuple[str], fitPar: list[str], Npoints: int, pr_points: int, file_name: str) -> tuple[str, Path]:
    """Generates a theoretical scattering plugin model"""

    plugin_location = Path(models.find_plugins_dir())
    if not file_name.endswith('.py'):
        file_name += '.py'
    full_path = plugin_location / file_name

    model_str = generateModel(prof, constrainParameters, fitPar, Npoints, pr_points, file_name)

    return model_str, full_path
    

def parListsFormat(par: list[list[Union[str, float]]]) -> str:
    """Format lists of parameters to the model string"""

    #k = 5
    for i in range(len(par)):
        for j in range(len(par[i])):
            if not isinstance(par[i][j], str):
                par[i][j] = f'{par[i][j]}'
        par[i] = f'[{", ".join(par[i])}]'
        #if i > k:
        #    par.insert("\n")
        #    k += 5

    return f"[{', '.join(par)}]"

def parListFormat(par: list[Union[str, float]]) -> str:
    """Format a list containing parameters to the model string"""

    for i in range(len(par)):
        if not isinstance(par[i], str):
            par[i] = f'{par[i]}'

    return f"[{', '.join(par)}]"    


def generateModel(prof: ModelProfile, constrainParameters: tuple[str], fitPar: list[str], Npoints: int, pr_points: int, model_name: str) -> str:
    """Generates a theoretical model"""
    importStatement, parameters, translation = constrainParameters

    nl = '\n'
    
    model_str = (f'''
r"""
###TODO: Rewrite this description
This plugin model uses Shape2SAS to generate theoretical small-angle scattering data. Shape2SAS is a program build by Larsen and Brookes
(doi: https://doi.org/10.1107/S1600576723005848) to calculate small-angle scattering data and pair distance distributions
from a user built model. The user builds this model by combining pre-defined geometrical subunits. Each subunit may be rotated and translated to the
users desired position, resulting in a broad range of possible models to be created. 
Besides calculating theoretical scattering, Shape2SAS is also able to simulate small-angle scattering with noise.

###TODO: maybe add a method description on how Shape2SAS generates the scattering data??? bead model                 

Model {model_name.replace('.py', '')} was built from the following subunits:
{', '.join(prof.subunits)}

"""

{nl.join(importStatement)}
from sas.qtgui.Perspectives.Shape2SAS.calculations.Shape2SAS import (ModelProfile, SimulationParameters, 
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

{translation}

def Iq(q, {', '.join(fitPar)}):
    """Fit function using Shape2SAS to calculate the scattering intensity."""
    
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


